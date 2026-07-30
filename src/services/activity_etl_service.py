"""Service for extracting, transforming, and loading Strava activities."""

from dataclasses import dataclass

from src.api.client import StravaClient
from src.etl import ActivityMapper, ActivityMappingError
from src.repositories import ActivityLoadResult, ActivityRepository


@dataclass
class ActivityEtlResult:
    """Summary of an activity ETL run."""

    retrieved: int
    transformed: int
    failed: int
    inserted: int
    updated: int
    skipped: int
    total_stored: int


class ActivityEtlService:
    """Coordinates the Strava activity ETL workflow."""

    def __init__(
        self,
        client: StravaClient,
        repository: ActivityRepository,
    ) -> None:
        self.client = client
        self.repository = repository

    def run_full_load(self) -> ActivityEtlResult:
        """Retrieve all activities and load them into the database."""

        print("\nFetching Strava activities...")
        raw_activities = self.client.get_all_activities()

        print("Activity extraction successful.")
        print(f"Total activities retrieved: {len(raw_activities)}")

        print("\nTransforming activities...")

        activities = []
        failed = 0

        for activity_data in raw_activities:
            try:
                activity = ActivityMapper.from_api(activity_data)
                activities.append(activity)
            except ActivityMappingError as exc:
                failed += 1

                activity_id = activity_data.get("id", "unknown")

                print(
                    f"Skipping activity {activity_id}: {exc}"
                )

        print("Activity transformation complete.")
        print(f"Activities transformed: {len(activities)}")
        print(f"Activities failed: {failed}")

        print("\nLoading activities into database...")

        load_result: ActivityLoadResult = (
            self.repository.upsert_many(activities)
        )

        total_stored = self.repository.count()

        print("Activity database load complete.")

        return ActivityEtlResult(
            retrieved=len(raw_activities),
            transformed=len(activities),
            failed=failed,
            inserted=load_result.inserted,
            updated=load_result.updated,
            skipped=load_result.skipped,
            total_stored=total_stored,
        )