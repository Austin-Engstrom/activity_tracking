"""Main entry point for the Strava analytics ETL pipeline."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
from src.database import (
    DATABASE_PATH,
    SessionLocal,
    initialize_database,
)
from src.repositories import ActivityRepository
from src.services import (
    ActivityDetailService,
    ActivityEtlService,
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
            batch_size=25
        )

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

    print("\n" + "=" * 45)
    print("MILESTONE 4C COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()