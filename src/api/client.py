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

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send an authenticated GET request to Strava."""

        url = f"{STRAVA_API_BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = self.session.get(
                url,
                params=params,
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

        response_data = self.get("/athlete")

        if not isinstance(response_data, dict):
            raise StravaApiError(
                "Strava returned an unexpected athlete response."
            )

        return response_data

    def get_activity(
        self,
        activity_id: int,
        include_all_efforts: bool = False,
    ) -> dict[str, Any]:
        """Retrieve detailed information for one Strava activity."""

        if activity_id <= 0:
            raise ValueError(
                "activity_id must be a positive integer."
            )

        response_data = self.get(
            f"/activities/{activity_id}",
            params={
                "include_all_efforts": str(
                    include_all_efforts
                ).lower()
            },
        )

        if not isinstance(response_data, dict):
            raise StravaApiError(
                "Strava returned an unexpected activity response."
            )

        return response_data

    def get_activity_streams(
        self,
        activity_id: int,
        stream_types: list[str],
    ) -> dict[str, Any]:
        """Retrieve selected streams for one Strava activity."""

        if activity_id <= 0:
            raise ValueError(
                "activity_id must be a positive integer."
            )

        if not stream_types:
            raise ValueError(
                "At least one stream type must be requested."
            )

        response_data = self.get(
            f"/activities/{activity_id}/streams",
            params={
                "keys": ",".join(stream_types),
                "key_by_type": "true",
            },
        )

        if not isinstance(response_data, dict):
            raise StravaApiError(
                "Strava returned an unexpected streams response."
            )

        return response_data
    
    def get_activities_page(
        self,
        page: int = 1,
        per_page: int = 200,
        after: int | None = None,
        before: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve one page of activities for the authenticated athlete."""

        if page < 1:
            raise ValueError("Page must be at least 1.")

        if not 1 <= per_page <= 200:
            raise ValueError("per_page must be between 1 and 200.")

        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if after is not None:
            params["after"] = after

        if before is not None:
            params["before"] = before

        response_data = self.get(
            "/athlete/activities",
            params=params,
        )

        if not isinstance(response_data, list):
            raise StravaApiError(
                "Strava returned an unexpected activities response."
            )

        return response_data

    def get_all_activities(
        self,
        per_page: int = 200,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve all matching Strava activities."""

        activities: list[dict[str, Any]] = []
        page = 1

        while True:
            page_activities = self.get_activities_page(
                page=page,
                per_page=per_page,
                before=before,
                after=after,
            )

            activities.extend(page_activities)

            print(
                f"Retrieved page {page}: "
                f"{len(page_activities)} activities"
            )

            if len(page_activities) < per_page:
                break

            page += 1

        return activities
    