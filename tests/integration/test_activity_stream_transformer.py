"""Integration test for Strava activity-stream transformation."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
from src.etl.activity_stream_transformer import (
    transform_activity_streams,
)


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
    """Fetch and transform streams for one Strava activity."""

    print("=" * 45)
    print("ACTIVITY STREAM TRANSFORMER TEST")
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

    print("\nStream transformation successful.")
    print("-" * 45)
    print(f"Returned stream types: {list(raw_streams.keys())}")
    print(f"Transformed rows:      {len(transformed_rows)}")

    if transformed_rows:
        print("\nFirst transformed row:")
        print(transformed_rows[0])

        print("\nLast transformed row:")
        print(transformed_rows[-1])

    print("\n" + "=" * 45)
    print("ACTIVITY STREAM TRANSFORMER TEST COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()