"""Entry point for the Strava analytics ETL application."""

import sys
from typing import Any

from src.api.authenticate import (
    StravaAuthenticationError,
    StravaAuthenticator,
)
from src.api.client import StravaApiError, StravaClient


def format_athlete_name(athlete: dict[str, Any]) -> str:
    """Return the athlete's display name."""

    first_name = str(athlete.get("firstname") or "").strip()
    last_name = str(athlete.get("lastname") or "").strip()

    full_name = f"{first_name} {last_name}".strip()

    return full_name or "Unknown athlete"


def main() -> int:
    """Run the current ETL milestone."""

    print("=" * 45)
    print("STRAVA ANALYTICS ETL")
    print("=" * 45)

    try:
        print("\nLoading configuration...")
        authenticator = StravaAuthenticator()
        print("Configuration loaded successfully.")

        print("\nRefreshing Strava access token...")
        token = authenticator.refresh_access_token()
        print("Authentication successful.")

        print("\nVerifying Strava API connection...")
        client = StravaClient(token.access_token)
        athlete = client.get_logged_in_athlete()

        athlete_name = format_athlete_name(athlete)
        athlete_id = athlete.get("id", "Unknown")

        print("Strava API connection successful.")
        print(f"Athlete: {athlete_name}")
        print(f"Athlete ID: {athlete_id}")

    except (
        RuntimeError,
        StravaAuthenticationError,
        StravaApiError,
    ) as exc:
        print(f"\nETL failed: {exc}")
        print("=" * 45)
        return 1

    print("\n" + "=" * 45)
    print("MILESTONE 1 COMPLETE")
    print("=" * 45)

    return 0


if __name__ == "__main__":
    sys.exit(main())