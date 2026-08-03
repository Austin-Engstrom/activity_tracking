"""Integration test for the activity stream repository."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
from src.database import SessionLocal, initialize_database
from src.etl.activity_stream_transformer import (
    transform_activity_streams,
)
from src.repositories import ActivityStreamRepository


TEST_ACTIVITY_ID = 19574317510

STREAM_TYPES = [
    "time",
    "latlng",
    "distance",
    "altitude",
    "velocity_smooth",
    "heartrate",
    "cadence",
    "watts",
    "temp",
    "moving",
    "grade_smooth",
]


def main() -> None:
    """Fetch, transform, and store one activity's streams."""

    print("=" * 45)
    print("ACTIVITY STREAM REPOSITORY TEST")
    print("=" * 45)

    authenticator = StravaAuthenticator()
    access_token = authenticator.get_access_token()

    client = StravaClient(access_token)

    print(f"\nRetrieving streams for: {TEST_ACTIVITY_ID}")

    raw_streams = client.get_activity_streams(
        activity_id=TEST_ACTIVITY_ID,
        stream_types=STREAM_TYPES,
    )

    transformed_rows = transform_activity_streams(
        activity_id=TEST_ACTIVITY_ID,
        raw_streams=raw_streams,
    )

    initialize_database()

    with SessionLocal() as session:
        repository = ActivityStreamRepository(session)

        inserted = repository.insert_many(
            transformed_rows,
            replace_existing=True,
        )

        stored_for_activity = repository.count_for_activity(
            TEST_ACTIVITY_ID
        )

        total_stored = repository.count_all()

    print("\nStream rows stored successfully.")
    print("-" * 45)
    print(f"Inserted:            {inserted}")
    print(f"Stored for activity: {stored_for_activity}")
    print(f"Total stream rows:   {total_stored}")

    print("\n" + "=" * 45)
    print("ACTIVITY STREAM REPOSITORY TEST COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()