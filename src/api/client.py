"""HTTP client for the Strava API."""

from typing import Any

import requests


STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"


class StravaApiError(RuntimeError):
    """Raised when a Strava API request fails."""

class StravaRateLimitError(StravaApiError):
    """Raised when the Strava API read limit has been reached."""

    def __init__(
        self,
        message: str,
        read_usage: tuple[int, int] | None = None,
        read_limit: tuple[int, int] | None = None,
    ) -> None:
        super().__init__(message)

        self.read_usage = read_usage
        self.read_limit = read_limit

class StravaClient:
    """Small HTTP client for authenticated Strava API requests."""

    def __init__(
        self,
        access_token: str,
        timeout_seconds: int = 30,
    ) -> None:
        if not access_token:
            raise ValueError("An access token is required.")

        self.base_url = STRAVA_API_BASE_URL
        self.timeout_seconds = timeout_seconds

        self.read_rate_limit: tuple[int, int] | None = None
        self.read_rate_usage: tuple[int, int] | None = None

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
        params: dict | None = None,
    ) -> dict:
        """Send an authenticated GET request to Strava."""

        if not self.has_read_capacity():
            raise StravaRateLimitError(
                message=(
                    "Strava read quota is nearly exhausted. "
                    "Request deferred."
                ),
                read_usage=self.read_rate_usage,
                read_limit=self.read_rate_limit,
            )

        response = self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            timeout=self.timeout_seconds,
        )

        self._update_rate_limit_state(response)

        if response.status_code == 429:
            raise StravaRateLimitError(
                message=(
                    f"Strava read rate limit reached for {endpoint}."
                ),
                read_usage=self.read_rate_usage,
                read_limit=self.read_rate_limit,
            )

        if not response.ok:
            raise StravaApiError(
                f"Strava request failed: {endpoint}. "
                f"Response: {response.text}"
            )

        return response.json()

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
        
    @staticmethod
    def _parse_rate_limit_header(
        value: str | None,
    ) -> tuple[int, int] | None:
        """Parse a Strava rate-limit header into short and daily values."""
        if not value:
            return None

        try:
            short_term, daily = value.split(",")

            return (
                int(short_term.strip()),
                int(daily.strip()),
            )

        except (TypeError, ValueError):
            return None


    def _update_rate_limit_state(
        self,
        response,
    ) -> None:
        """Update the client with rate-limit values from a response."""

        self.read_rate_limit = self._parse_rate_limit_header(
            response.headers.get("X-ReadRateLimit-Limit")
        )

        self.read_rate_usage = self._parse_rate_limit_header(
            response.headers.get("X-ReadRateLimit-Usage")
        )
    
    def has_read_capacity(
        self,
        reserve: int = 2,
    ) -> bool:
        """Return whether another read request can safely be made."""

        if (
            self.read_rate_limit is None
            or self.read_rate_usage is None
        ):
            return True

        short_limit, daily_limit = self.read_rate_limit
        short_usage, daily_usage = self.read_rate_usage

        short_remaining = short_limit - short_usage
        daily_remaining = daily_limit - daily_usage

        return (
            short_remaining > reserve
            and daily_remaining > reserve
        )