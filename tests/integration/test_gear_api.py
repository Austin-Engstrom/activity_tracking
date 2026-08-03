"""Integration test for the Strava gear endpoint."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient


TEST_GEAR_ID = "replace_with_real_gear_id"


def main() -> None:
    """Retrieve and display one Strava gear record."""

    print("=" * 45)
    print("STRAVA GEAR API TEST")
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

    print(f"\nRetrieving gear: {TEST_GEAR_ID}")
    gear = client.get_gear(TEST_GEAR_ID)

    print("\nGear response received successfully.")
    print("-" * 45)
    print(f"Gear ID:     {gear.get('id')}")
    print(f"Name:        {gear.get('name')}")
    print(f"Brand:       {gear.get('brand_name')}")
    print(f"Model:       {gear.get('model_name')}")
    print(f"Distance:    {gear.get('distance')}")
    print(f"Primary:     {gear.get('primary')}")
    print(f"Frame type:  {gear.get('frame_type')}")
    print(f"Description: {gear.get('description')}")

    print("\n" + "=" * 45)
    print("GEAR API TEST COMPLETE")
    print("=" * 45)


if __name__ == "__main__":
    main()