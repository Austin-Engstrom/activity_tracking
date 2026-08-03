"""Service for enriching activities with detailed Strava data."""

from dataclasses import dataclass
from datetime import datetime, timezone

from src.api.client import (
    StravaApiError,
    StravaClient,
    StravaRateLimitError,
)
from src.etl.activity_mapper import (
    ActivityMapper,
    ActivityMappingError,
)
from src.etl.segment_mapper import (
    SegmentMapper,
    SegmentMappingError,
)
from src.repositories.activity_repository import ActivityRepository
from src.repositories.segment_repository import SegmentRepository


@dataclass
class ActivityDetailResult:
    """Summary of a detail-enrichment batch."""

    selected: int = 0
    enriched: int = 0
    detail_activities_loaded: int = 0
    segment_activities_loaded: int = 0
    failed: int = 0
    deferred: int = 0
    remaining: int = 0
    rate_limit_reached: bool = False
    segments_inserted: int = 0
    segments_updated: int = 0
    efforts_inserted: int = 0
    efforts_updated: int = 0


class ActivityDetailService:
    """Loads detail-endpoint enrichments for stored activities."""

    def __init__(
        self,
        client: StravaClient,
        repository: ActivityRepository,
        segment_repository: SegmentRepository,
    ) -> None:
        self.client = client
        self.repository = repository
        self.segment_repository = segment_repository

    def run_batch(
        self,
        batch_size: int = 25,
    ) -> ActivityDetailResult:
        """Enrich one resumable batch with one API call per activity."""

        activities = self.repository.get_pending_detail_activities(
            limit=batch_size
        )

        result = ActivityDetailResult(
            selected=len(activities),
        )

        for index, activity in enumerate(activities):
            try:
                needs_detail = activity.detail_loaded_at is None
                needs_segments = activity.segments_loaded_at is None

                detail_data = self.client.get_activity(
                    activity.activity_id,
                    include_all_efforts=needs_segments,
                )

                if needs_detail:
                    ActivityMapper.apply_detail(
                        activity=activity,
                        detail_data=detail_data,
                    )
                    result.detail_activities_loaded += 1

                if needs_segments:
                    raw_efforts = (
                        detail_data.get("segment_efforts") or []
                    )

                    segments = []
                    efforts = []

                    for effort_data in raw_efforts:
                        segments.append(
                            SegmentMapper.segment_from_effort(
                                effort_data
                            )
                        )
                        efforts.append(
                            SegmentMapper.effort_from_api(
                                activity_id=activity.activity_id,
                                effort_data=effort_data,
                            )
                        )

                    load_result = (
                        self.segment_repository
                        .upsert_activity_segments(
                            activity_id=activity.activity_id,
                            segments=segments,
                            efforts=efforts,
                        )
                    )

                    activity.segments_loaded_at = datetime.now(
                        timezone.utc
                    ).replace(tzinfo=None)

                    result.segment_activities_loaded += 1
                    result.segments_inserted += (
                        load_result.segments_inserted
                    )
                    result.segments_updated += (
                        load_result.segments_updated
                    )
                    result.efforts_inserted += (
                        load_result.efforts_inserted
                    )
                    result.efforts_updated += (
                        load_result.efforts_updated
                    )

                self.repository.commit()
                result.enriched += 1

            except StravaRateLimitError as exc:
                self.repository.rollback()

                result.rate_limit_reached = True
                result.deferred = len(activities) - index

                print(
                    "\nStrava read rate limit reached. "
                    "Stopping detail enrichment cleanly."
                )

                if exc.read_usage and exc.read_limit:
                    short_usage, daily_usage = exc.read_usage
                    short_limit, daily_limit = exc.read_limit

                    print(
                        "Read usage: "
                        f"{short_usage}/{short_limit} short-term, "
                        f"{daily_usage}/{daily_limit} daily"
                    )

                break

            except (
                StravaApiError,
                ActivityMappingError,
                SegmentMappingError,
                TypeError,
                ValueError,
            ) as exc:
                self.repository.rollback()
                result.failed += 1

                print(
                    f"Failed to enrich activity "
                    f"{activity.activity_id}: "
                    f"{type(exc).__name__}: {exc}"
                )

            except Exception:
                self.repository.rollback()
                raise

        result.remaining = (
            self.repository.count_pending_details()
        )

        return result
