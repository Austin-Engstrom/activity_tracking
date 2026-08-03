"""Transform raw Strava activity streams into database-ready rows."""

from datetime import datetime, timezone
from typing import Any


class ActivityStreamTransformationError(ValueError):
    """Raised when Strava activity streams cannot be transformed."""


STREAM_FIELD_MAP = {
    "time": "time_seconds",
    "distance": "distance_meters",
    "altitude": "altitude_meters",
    "velocity_smooth": "velocity_mps",
    "heartrate": "heartrate",
    "cadence": "cadence",
    "watts": "watts",
    "temp": "temperature_c",
    "moving": "is_moving",
    "grade_smooth": "grade_percent",
}


def transform_activity_streams(
    activity_id: int,
    raw_streams: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform aligned Strava stream arrays into one row per point.

    Strava streams are keyed by stream type. Each stream contains a
    data array whose indexes correspond to the same sampled point.
    """

    if activity_id <= 0:
        raise ActivityStreamTransformationError(
            "activity_id must be a positive integer."
        )

    if not isinstance(raw_streams, dict):
        raise ActivityStreamTransformationError(
            "Activity streams must be provided as a dictionary."
        )

    stream_data = _extract_stream_data(raw_streams)

    if not stream_data:
        return []

    point_count = max(
        len(values)
        for values in stream_data.values()
    )

    loaded_at = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []

    for point_index in range(point_count):
        row: dict[str, Any] = {
            "activity_id": activity_id,
            "point_index": point_index,
            "time_seconds": None,
            "distance_meters": None,
            "latitude": None,
            "longitude": None,
            "altitude_meters": None,
            "velocity_mps": None,
            "heartrate": None,
            "cadence": None,
            "watts": None,
            "temperature_c": None,
            "is_moving": None,
            "grade_percent": None,
            "created_at": loaded_at,
        }

        for stream_name, field_name in STREAM_FIELD_MAP.items():
            values = stream_data.get(stream_name)

            if values is None or point_index >= len(values):
                continue

            raw_value = values[point_index]

            row[field_name] = _convert_stream_value(
                stream_name=stream_name,
                value=raw_value,
            )

        latlng_values = stream_data.get("latlng")

        if (
            latlng_values is not None
            and point_index < len(latlng_values)
        ):
            latitude, longitude = _parse_latlng(
                latlng_values[point_index]
            )

            row["latitude"] = latitude
            row["longitude"] = longitude

        rows.append(row)

    return rows


def _extract_stream_data(
    raw_streams: dict[str, Any],
) -> dict[str, list[Any]]:
    """Extract data arrays from Strava's keyed stream response."""

    extracted: dict[str, list[Any]] = {}

    for stream_name, stream_payload in raw_streams.items():
        if not isinstance(stream_payload, dict):
            continue

        values = stream_payload.get("data")

        if isinstance(values, list):
            extracted[stream_name] = values

    return extracted


def _convert_stream_value(
    stream_name: str,
    value: Any,
) -> Any:
    """Convert one stream value to its database-ready type."""

    if value is None:
        return None

    if stream_name in {"time", "heartrate"}:
        return _to_int(value)

    if stream_name == "moving":
        return _to_bool(value)

    return _to_float(value)


def _parse_latlng(
    value: Any,
) -> tuple[float | None, float | None]:
    """Convert one Strava latitude/longitude pair."""

    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
    ):
        return None, None

    latitude = _to_float(value[0])
    longitude = _to_float(value[1])

    return latitude, longitude


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
    """Convert a value to Boolean when possible."""

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