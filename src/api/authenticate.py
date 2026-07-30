"""Strava OAuth authentication and token refresh logic."""

from dataclasses import dataclass
from typing import Any

import requests

from src.utils.config import settings


STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"


class StravaAuthenticationError(RuntimeError):
    """Raised when Strava authentication fails."""


@dataclass(frozen=True)
class StravaToken:
    """Represents a refreshed Strava OAuth token response."""

    access_token: str
    refresh_token: str
    expires_at: int
    expires_in: int
    token_type: str

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "StravaToken":
        """Create a token object from the Strava OAuth response."""

        required_fields = {
            "access_token",
            "refresh_token",
            "expires_at",
            "expires_in",
            "token_type",
        }

        missing_fields = required_fields.difference(data)

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise StravaAuthenticationError(
                f"Strava token response is missing required fields: {missing}"
            )

        return cls(
            access_token=str(data["access_token"]),
            refresh_token=str(data["refresh_token"]),
            expires_at=int(data["expires_at"]),
            expires_in=int(data["expires_in"]),
            token_type=str(data["token_type"]),
        )


class StravaAuthenticator:
    """Refreshes and returns Strava OAuth access tokens."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    def refresh_access_token(self) -> StravaToken:
        """Exchange the configured refresh token for a valid access token."""

        payload = {
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": settings.strava_refresh_token,
        }

        try:
            response = requests.post(
                STRAVA_TOKEN_URL,
                data=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise StravaAuthenticationError(
                "The Strava authentication request timed out."
            ) from exc
        except requests.RequestException as exc:
            response_body = ""

            if exc.response is not None:
                response_body = exc.response.text

            message = "Strava authentication failed."

            if response_body:
                message = f"{message} Response: {response_body}"

            raise StravaAuthenticationError(message) from exc

        try:
            response_data = response.json()
        except ValueError as exc:
            raise StravaAuthenticationError(
                "Strava returned an invalid JSON authentication response."
            ) from exc

        return StravaToken.from_response(response_data)

    def get_access_token(self) -> str:
        """Return a refreshed Strava access token."""

        token = self.refresh_access_token()
        return token.access_token