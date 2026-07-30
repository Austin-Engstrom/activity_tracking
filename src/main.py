"""Main entry point for the Strava analytics ETL pipeline."""

from sqlalchemy import inspect

from src.api.authenticate import StravaAuthenticator
from src.api.client import get_athlete
from src.database import DATABASE_PATH, initialize_database
from src.database.connection import engine


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
    athlete = get_athlete(access_token)

    print("Strava API connection successful.")
    print(f"Athlete: {athlete['firstname']} {athlete['lastname']}")
    print(f"Athlete ID: {athlete['id']}")

    print("\nInitializing database...")
    initialize_database()

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("Database initialized successfully.")
    print(f"Database path: {DATABASE_PATH}")
    print(f"Tables created: {', '.join(tables)}")

    print("\n" + "=" * 45)
    print("MILESTONE 2A COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()