"""Main entry point for the Strava analytics ETL pipeline."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
from src.database import (
    DATABASE_PATH,
    SessionLocal,
    initialize_database,
)
from src.repositories import ActivityRepository
from src.services import ActivityEtlService


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

        result = etl_service.run_full_load()

    print("\n" + "-" * 45)
    print("ETL SUMMARY")
    print("-" * 45)
    print(f"Retrieved:    {result.retrieved}")
    print(f"Transformed:  {result.transformed}")
    print(f"Failed:       {result.failed}")
    print(f"Inserted:     {result.inserted}")
    print(f"Updated:      {result.updated}")
    print(f"Skipped:      {result.skipped}")
    print(f"Total stored: {result.total_stored}")

    print("\n" + "=" * 45)
    print("MILESTONE 2B COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()