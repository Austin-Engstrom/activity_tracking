"""Main entry point for the Strava analytics ETL pipeline."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
from src.database import (
    DATABASE_PATH,
    SessionLocal,
    initialize_database,
)
from src.repositories import (
    ActivityRepository,
    ActivityStreamRepository,
    GearRepository,
    SegmentRepository,
)
from src.services import (
    ActivityDetailService,
    ActivityEtlService,
    ActivityStreamService,
    GearService,
)


def print_etl_summary(etl_result) -> bool:
    """Print the activity ETL summary when work occurred."""

    should_print = (
        etl_result.retrieved > 0
        or etl_result.failed > 0
    )

    if not should_print:
        return False

    print("\n" + "-" * 45)
    print("ETL SUMMARY")
    print("-" * 45)
    print(f"Retrieved:    {etl_result.retrieved}")
    print(f"Transformed:  {etl_result.transformed}")
    print(f"Failed:       {etl_result.failed}")
    print(f"Inserted:     {etl_result.inserted}")
    print(f"Updated:      {etl_result.updated}")
    print(f"Skipped:      {etl_result.skipped}")
    print(f"Total stored: {etl_result.total_stored}")

    return True


def print_detail_summary(detail_result) -> bool:
    """Print the detail-enrichment summary when work occurred."""

    should_print = (
        detail_result.selected > 0
        or detail_result.failed > 0
        or detail_result.deferred > 0
        or detail_result.rate_limit_reached
    )

    if not should_print:
        return False

    print("\n" + "-" * 45)
    print("DETAIL ENRICHMENT SUMMARY")
    print("-" * 45)
    print(f"Selected:       {detail_result.selected}")
    print(f"Processed:      {detail_result.enriched}")
    print(
        f"Details loaded: "
        f"{detail_result.detail_activities_loaded}"
    )
    print(
        f"Segments loaded:"
        f" {detail_result.segment_activities_loaded}"
    )
    print(f"Failed:         {detail_result.failed}")
    print(f"Remaining:      {detail_result.remaining}")
    print(f"Deferred:       {detail_result.deferred}")

    if detail_result.rate_limit_reached:
        print("Status:         Stopped at Strava read limit")
    else:
        print("Status:         Batch completed")

    return True

def print_gear_summary(gear_result) -> bool:
    """Print the gear-load summary when work occurred."""

    should_print = (
        gear_result.selected > 0
        or gear_result.failed > 0
        or gear_result.deferred > 0
        or gear_result.rate_limit_reached
    )

    if not should_print:
        return False

    print("\n" + "-" * 45)
    print("GEAR LOAD SUMMARY")
    print("-" * 45)
    print(f"Selected:     {gear_result.selected}")
    print(f"Inserted:     {gear_result.inserted}")
    print(f"Updated:      {gear_result.updated}")
    print(f"Failed:       {gear_result.failed}")
    print(f"Remaining:    {gear_result.remaining}")
    print(f"Deferred:     {gear_result.deferred}")

    if gear_result.rate_limit_reached:
        print("Status:       Stopped at Strava read limit")
    else:
        print("Status:       Load completed")

    return True


def print_stream_summary(stream_result) -> bool:
    """Print the activity-stream summary when work occurred."""

    should_print = (
        stream_result.selected > 0
        or stream_result.failed > 0
        or stream_result.deferred > 0
        or stream_result.rate_limit_reached
    )

    if not should_print:
        return False

    print("\n" + "-" * 45)
    print("ACTIVITY STREAM LOAD SUMMARY")
    print("-" * 45)
    print(f"Selected:      {stream_result.selected}")
    print(f"Loaded:        {stream_result.loaded}")
    print(f"Rows inserted: {stream_result.rows_inserted}")
    print(f"Empty:         {stream_result.empty}")
    print(f"Failed:        {stream_result.failed}")
    print(f"Remaining:     {stream_result.remaining}")
    print(f"Deferred:      {stream_result.deferred}")

    if stream_result.rate_limit_reached:
        print("Status:        Stopped at Strava read limit")
    else:
        print("Status:        Batch completed")

    return True

def print_segment_summary(detail_result) -> bool:
    """Print the segment-load summary when work occurred."""

    should_print = (
        detail_result.segment_activities_loaded > 0
        or detail_result.segments_inserted > 0
        or detail_result.segments_updated > 0
        or detail_result.efforts_inserted > 0
        or detail_result.efforts_updated > 0
    )

    if not should_print:
        return False

    print("\n" + "-" * 45)
    print("SEGMENT LOAD SUMMARY")
    print("-" * 45)
    print(
        f"Activities loaded: "
        f"{detail_result.segment_activities_loaded}"
    )
    print(
        f"Segments inserted: "
        f"{detail_result.segments_inserted}"
    )
    print(
        f"Segments updated:  "
        f"{detail_result.segments_updated}"
    )
    print(
        f"Efforts inserted:  "
        f"{detail_result.efforts_inserted}"
    )
    print(
        f"Efforts updated:   "
        f"{detail_result.efforts_updated}"
    )

    return True

def main() -> None:
    """Run the Strava analytics ETL pipeline."""

    print("=" * 45)
    print("STRAVA ANALYTICS ETL")
    print("=" * 45)

    print("\nLoading configuration...")
    print("Configuration loaded successfully.")

    print("\nRefreshing Strava access token...")
    authenticator = StravaAuthenticator()
    access_token = authenticator.get_access_token()
    print("Authentication successful.")

    print("\nVerifying Strava API connection...")
    client = StravaClient(access_token)
    athlete = client.get_logged_in_athlete()

    print("Strava API connection successful.")
    print(f"Athlete: {athlete['firstname']} {athlete['lastname']}")
    print(f"Athlete ID: {athlete['id']}")

    print("\nInitializing database...")
    initialize_database()

    print("Database initialized successfully.")
    print(f"Database path: {DATABASE_PATH}")

    with SessionLocal() as session:
        activity_repository = ActivityRepository(session)

        etl_service = ActivityEtlService(
            client=client,
            repository=activity_repository,
        )

        etl_result = etl_service.run_incremental_load()

        segment_repository = SegmentRepository(session)

        detail_service = ActivityDetailService(
            client=client,
            repository=activity_repository,
            segment_repository=segment_repository,
        )

        detail_result = detail_service.run_batch(
            batch_size=75
        )

        gear_repository = GearRepository(session)

        gear_service = GearService(
            client=client,
            repository=gear_repository,
            athlete_id=athlete["id"],
        )

        gear_result = gear_service.run()

        stream_repository = ActivityStreamRepository(session)

        stream_service = ActivityStreamService(
            client=client,
            repository=stream_repository,
        )

        stream_result = stream_service.run_batch(
            batch_size=20
        )

    printed_sections = [
        print_etl_summary(etl_result),
        print_detail_summary(detail_result),
        print_segment_summary(detail_result),
        print_gear_summary(gear_result),
        print_stream_summary(stream_result),
    ]

    if not any(printed_sections):
        print("\nNo ETL work was required.")
        print("Database is fully synchronized.")

    print("\n" + "=" * 45)
    print("MILESTONE 7 COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()