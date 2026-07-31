"""Service for enriching activities with detailed Strava data."""

from dataclasses import dataclass

from src.api.client import StravaApiError, StravaClient
from src.etl.activity_mapper import ActivityMapper, ActivityMappingError
from src.repositories.activity_repository import ActivityRepository


@dataclass
class ActivityDetailResult:
    """Summary of a detail-enrichment batch."""

    selected: int = 0
    enriched: int = 0
    failed: int = 0
    remaining: int = 0


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

        for activity in activities:
            try:
                detail_data = self.client.get_activity(
                    activity.activity_id
                )

                ActivityMapper.apply_detail(
                    activity=activity,
                    detail_data=detail_data,
                )

                result.enriched += 1

            except (
                StravaApiError,
                ActivityMappingError,
                TypeError,
                ValueError,
            ) as exc:
                result.failed += 1

                print(
                    f"Failed to enrich activity "
                    f"{activity.activity_id}: {exc}"
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