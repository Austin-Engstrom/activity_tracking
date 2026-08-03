"""Transform raw Strava gear data into database-ready values."""

from datetime import datetime, timezone
from typing import Any


class GearTransformationError(ValueError):
    """Raised when a Strava gear record cannot be transformed."""


def _clean_string(value: Any) -> str | None:
    """Return a stripped string or None for blank values."""

    if value is None:
        return None

    cleaned_value = str(value).strip()

    return cleaned_value or None


def transform_gear(
    raw_gear: dict[str, Any],
    athlete_id: int,
) -> dict[str, Any]:
    """Transform one Strava gear response into database-ready values."""

    if not isinstance(raw_gear, dict):
        raise GearTransformationError(
            "Gear data must be provided as a dictionary."
        )

    if athlete_id <= 0:
        raise GearTransformationError(
            "athlete_id must be a positive integer."
        )

    gear_id = _clean_string(raw_gear.get("id"))
    name = _clean_string(raw_gear.get("name"))

    if gear_id is None:
        raise GearTransformationError(
            "Gear response is missing a valid gear ID."
        )

    if name is None:
        raise GearTransformationError(
            f"Gear {gear_id} is missing a valid name."
        )

    loaded_at = datetime.now(timezone.utc)

    return {
        "gear_id": gear_id,
        "athlete_id": athlete_id,
        "name": name,
        "brand_name": _clean_string(
            raw_gear.get("brand_name")
        ),
        "model_name": _clean_string(
            raw_gear.get("model_name")
        ),
        "description": _clean_string(
            raw_gear.get("description")
        ),
        "distance_meters": _to_float(
            raw_gear.get("distance")
        ),
        "is_primary": _to_bool(
            raw_gear.get("primary")
        ),
        "frame_type": _to_int(
            raw_gear.get("frame_type")
        ),
        "is_retired": None,
        "detail_loaded_at": loaded_at,
        "updated_at": loaded_at,
    }


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    """Convert a value to integer when possible."""

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    """Convert a value to boolean when possible."""

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized_value = value.strip().lower()

        if normalized_value in {"true", "1", "yes"}:
            return True

        if normalized_value in {"false", "0", "no"}:
            return False

    if isinstance(value, int):
        return bool(value)

    return None