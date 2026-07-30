"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Resolve the project root:
# project/
# ├── .env
# └── src/
#     └── utils/
#         └── config.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    """Environment-based application settings."""

    strava_client_id: str
    strava_client_secret: str
    strava_refresh_token: str


def _required_environment_variable(name: str) -> str:
    """Return an environment variable or raise a clear configuration error."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Required environment variable {name} is missing. "
            f"Check {ENV_FILE}."
        )

    return value.strip()


settings = Settings(
    strava_client_id=_required_environment_variable("STRAVA_CLIENT_ID"),
    strava_client_secret=_required_environment_variable(
        "STRAVA_CLIENT_SECRET"
    ),
    strava_refresh_token=_required_environment_variable(
        "STRAVA_REFRESH_TOKEN"
    ),
)