"""Main entry point for the Strava analytics ETL pipeline."""

from http import client
from sqlalchemy import inspect

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
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
    client = StravaClient(access_token)
    athlete = client.get_logged_in_athlete()
    
    print("Strava API connection successful.")
    print(f"Athlete: {athlete['firstname']} {athlete['lastname']}")
    print(f"Athlete ID: {athlete['id']}")

    print("\nFetching Strava activities...")
    activities = client.get_all_activities()

    print("Activity extraction successful.")
    print(f"Total activities retrieved: {len(activities)}")

    if activities:
        newest_activity = activities[0]

        print("\nMost recent activity:")
        print(f"Name: {newest_activity.get('name')}")
        print(f"Sport type: {newest_activity.get('sport_type')}")
        print(f"Start date: {newest_activity.get('start_date')}")
        print(f"Distance: {newest_activity.get('distance', 0)} meters")

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