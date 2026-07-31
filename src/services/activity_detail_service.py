"""Service for enriching activities with detailed Strava data."""

from dataclasses import dataclass

from src.api.client import (
    StravaApiError,
    StravaClient,
    StravaRateLimitError,
)
from src.etl.activity_mapper import (
    ActivityMapper,
    ActivityMappingError,
)
from src.repositories.activity_repository import ActivityRepository


@dataclass
class ActivityDetailResult:
    """Summary of a detail-enrichment batch."""

    selected: int = 0
    enriched: int = 0
    failed: int = 0
    deferred: int = 0
    remaining: int = 0
    rate_limit_reached: bool = False


class ActivityDetailService:
    """Loads detailed Strava data for stored activities."""

    def __init__(
        self,
        client: StravaClient,
        repository: ActivityRepository,
    ) -> None:
        self.client = client
        self.repository = repository

    def run_batch(
        self,
        batch_size: int = 25,
    ) -> ActivityDetailResult:
        """Enrich one resumable batch of activities."""

        activities = self.repository.get_pending_detail_activities(
            limit=batch_size
        )

        result = ActivityDetailResult(
            selected=len(activities),
        )

        for index, activity in enumerate(activities):
            try:
                detail_data = self.client.get_activity(
                    activity.activity_id
                )

                ActivityMapper.apply_detail(
                    activity=activity,
                    detail_data=detail_data,
                )

                result.enriched += 1

            except StravaRateLimitError as exc:
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
                TypeError,
                ValueError,
            ) as exc:
                result.failed += 1

                print(
                    f"Failed to enrich activity "
                    f"{activity.activity_id}: "
                    f"{type(exc).__name__}: {exc}"
                )

        try:
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise

        result.remaining = (
            self.repository.count_pending_details()
        )

        return result