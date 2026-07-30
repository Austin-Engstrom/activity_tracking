"""HTTP client for the Strava API."""

from typing import Any

import requests


STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"


class StravaApiError(RuntimeError):
    """Raised when a Strava API request fails."""


class StravaClient:
    """Small HTTP client for authenticated Strava API requests."""

    def __init__(
        self,
        access_token: str,
        timeout_seconds: int = 30,
    ) -> None:
        if not access_token:
            raise ValueError("An access token is required.")

        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
        )

    def get(self, endpoint: str) -> dict[str, Any]:
        """Send an authenticated GET request to Strava."""

        url = f"{STRAVA_API_BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = self.session.get(
                url,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise StravaApiError(
                f"Strava request timed out: {endpoint}"
            ) from exc
        except requests.RequestException as exc:
            response_body = ""

            if exc.response is not None:
                response_body = exc.response.text

            message = f"Strava request failed: {endpoint}"

            if response_body:
                message = f"{message}. Response: {response_body}"

            raise StravaApiError(message) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise StravaApiError(
                f"Strava returned invalid JSON for endpoint: {endpoint}"
            ) from exc

    def get_logged_in_athlete(self) -> dict[str, Any]:
        """Retrieve the authenticated athlete's profile."""

        return self.get("/athlete")