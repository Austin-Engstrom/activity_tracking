"""Resilient client for public Overpass API instances."""

import time
from dataclasses import dataclass
from typing import Any

import requests


DEFAULT_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)


class OverpassError(RuntimeError):
    """Raised when all configured Overpass endpoints fail."""


@dataclass(slots=True)
class OverpassResponse:
    """Successful Overpass response."""

    endpoint: str
    payload: dict[str, Any]


class OverpassClient:
    """Execute Overpass QL with retry and endpoint fallback."""

    def __init__(
        self,
        *,
        user_agent: str,
        endpoints: tuple[str, ...] = DEFAULT_ENDPOINTS,
        timeout_seconds: int = 120,
        attempts_per_endpoint: int = 2,
        retry_delay_seconds: float = 3.0,
    ) -> None:
        if not user_agent.strip():
            raise ValueError("A descriptive user agent is required.")

        self.user_agent = user_agent.strip()
        self.endpoints = endpoints
        self.timeout_seconds = timeout_seconds
        self.attempts_per_endpoint = attempts_per_endpoint
        self.retry_delay_seconds = retry_delay_seconds

    def execute(self, query: str) -> OverpassResponse:
        """Execute a query against available endpoints."""

        failures: list[str] = []

        for endpoint in self.endpoints:
            for attempt in range(1, self.attempts_per_endpoint + 1):
                try:
                    response = requests.post(
                        endpoint,
                        data={"data": query},
                        headers={
                            "User-Agent": self.user_agent,
                            "Accept": "application/json",
                        },
                        timeout=self.timeout_seconds,
                    )
                    response.raise_for_status()
                    payload = response.json()

                    if "elements" not in payload:
                        raise OverpassError(
                            "Response did not contain elements."
                        )

                    return OverpassResponse(endpoint, payload)

                except (
                    requests.RequestException,
                    ValueError,
                    OverpassError,
                ) as exc:
                    failures.append(
                        f"{endpoint} attempt {attempt}: {exc}"
                    )

                    if attempt < self.attempts_per_endpoint:
                        time.sleep(
                            self.retry_delay_seconds * attempt
                        )

        raise OverpassError(
            "All Overpass endpoints failed:\n"
            + "\n".join(failures)
        )
