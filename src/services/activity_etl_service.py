"""Service for extracting, transforming, and loading Strava activities."""

from dataclasses import dataclass

from src.api.client import StravaClient
from src.etl import ActivityMapper, ActivityMappingError
from src.repositories import ActivityLoadResult, ActivityRepository
from datetime import datetime, timezone

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

        return self._run_load(
            after=None,
            load_type="full",
        )

    def run_incremental_load(self) -> ActivityEtlResult:
        """Retrieve and load activities newer than the latest stored activity."""

        latest_start_date = self.repository.get_latest_start_date()

        if latest_start_date is None:
            print(
                "\nNo stored activities found. "
                "Running initial full load."
            )

            return self.run_full_load()

        after_timestamp = self._to_unix_timestamp(
            latest_start_date
        )

        print("\nIncremental load selected.")
        print(
            "Latest stored activity date: "
            f"{latest_start_date.isoformat()}"
        )
        print(f"Strava after timestamp: {after_timestamp}")

        return self._run_load(
            after=after_timestamp,
            load_type="incremental",
        )

    def _run_load(
        self,
        after: int | None,
        load_type: str,
    ) -> ActivityEtlResult:
        """Execute the shared activity ETL workflow."""

        print(f"\nStarting {load_type} activity load...")

        print("\nFetching Strava activities...")

        raw_activities = self.client.get_all_activities(
            after=after
        )

        print("Activity extraction successful.")
        print(
            f"Total activities retrieved: "
            f"{len(raw_activities)}"
        )

        print("\nTransforming activities...")

        activities = []
        failed = 0

        for activity_data in raw_activities:
            try:
                activity = ActivityMapper.from_api(
                    activity_data
                )

                activities.append(activity)

            except ActivityMappingError as exc:
                failed += 1

                activity_id = activity_data.get(
                    "id",
                    "unknown",
                )

                print(
                    f"Skipping activity {activity_id}: {exc}"
                )

        print("Activity transformation complete.")
        print(
            f"Activities transformed: {len(activities)}"
        )
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

    @staticmethod
    def _to_unix_timestamp(value: datetime) -> int:
        """Convert a database datetime into a UTC Unix timestamp."""

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return int(value.timestamp())