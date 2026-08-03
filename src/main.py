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
    GearRepository
)
from src.services import (
    ActivityDetailService,
    ActivityEtlService,
    ActivityStreamService,
    GearService,
)

from src.repositories import (
    ActivityRepository,
    ActivityStreamRepository,
    GearRepository,
)

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
        repository = ActivityRepository(session)

        etl_service = ActivityEtlService(
            client=client,
            repository=repository,
        )

        etl_result = etl_service.run_incremental_load()

        detail_service = ActivityDetailService(
            client=client,
            repository=repository,
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

        stream_repository = ActivityStreamRepository(session)

        stream_service = ActivityStreamService(
            client=client,
            repository=stream_repository,
        )

        stream_result = stream_service.run_batch(
            batch_size=5
        )

    gear_result = gear_service.run()
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

    print("\n" + "-" * 45)
    print("DETAIL ENRICHMENT SUMMARY")
    print("-" * 45)
    print(f"Selected:     {detail_result.selected}")
    print(f"Enriched:     {detail_result.enriched}")
    print(f"Failed:       {detail_result.failed}")
    print(f"Remaining:    {detail_result.remaining}")
    print(f"Deferred:     {detail_result.deferred}")

    print("\n" + "-" * 45)
    print("GEAR LOAD SUMMARY")
    print("-" * 45)
    print(f"Selected:     {gear_result.selected}")
    print(f"Inserted:     {gear_result.inserted}")
    print(f"Updated:      {gear_result.updated}")
    print(f"Failed:       {gear_result.failed}")
    print(f"Remaining:    {gear_result.remaining}")
    print(f"Deferred:     {gear_result.deferred}")

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

    if gear_result.rate_limit_reached:
        print("Status:       Stopped at Strava read limit")
    else:
        print("Status:       Load completed")

    if detail_result.rate_limit_reached:
        print("Status:       Stopped at Strava read limit")
    else:
        print("Status:       Batch completed")
    print("\n" + "=" * 45)
    print("MILESTONE 4C COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()