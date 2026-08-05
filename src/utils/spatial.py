"""Reusable spatial helpers for trail analytics."""

import json
import math

from pyproj import Transformer
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform


WGS84_TO_WEB_MERCATOR = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:3857",
    always_xy=True,
).transform


def geojson_to_projected_line(
    geometry_geojson: str,
):
    """Parse GeoJSON and project it to meters."""

    geometry = shape(json.loads(geometry_geojson))

    return transform(
        WGS84_TO_WEB_MERCATOR,
        geometry,
    )


def segment_line_from_coordinates(
    start_latitude: float | None,
    start_longitude: float | None,
    end_latitude: float | None,
    end_longitude: float | None,
):
    """Build a projected line from stored Strava segment endpoints."""

    values = (
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude,
    )

    if any(value is None for value in values):
        return None

    line = LineString(
        [
            (start_longitude, start_latitude),
            (end_longitude, end_latitude),
        ]
    )

    return transform(
        WGS84_TO_WEB_MERCATOR,
        line,
    )


def line_distance_meters(
    left_line,
    right_line,
) -> float:
    """Return minimum planar distance between projected lines."""

    return float(left_line.distance(right_line))


def approximate_overlap_percent(
    source_line,
    target_line,
    *,
    tolerance_meters: float,
    sample_count: int = 25,
) -> float:
    """Estimate how much of source_line lies near target_line."""

    if source_line.length == 0:
        return 0.0

    if sample_count < 2:
        sample_count = 2

    matched = 0

    for index in range(sample_count):
        fraction = index / (sample_count - 1)
        point = source_line.interpolate(
            fraction,
            normalized=True,
        )

        if point.distance(target_line) <= tolerance_meters:
            matched += 1

    return matched / sample_count * 100.0


def confidence_from_match(
    *,
    distance_meters: float,
    overlap_percent: float,
    max_distance_meters: float,
) -> float:
    """Calculate an explainable 0-1 confidence score."""

    if max_distance_meters <= 0:
        raise ValueError(
            "max_distance_meters must be greater than zero."
        )

    distance_score = max(
        0.0,
        1.0 - distance_meters / max_distance_meters,
    )

    overlap_score = max(
        0.0,
        min(overlap_percent / 100.0, 1.0),
    )

    confidence = (
        distance_score * 0.35
        + overlap_score * 0.65
    )

    return round(confidence, 4)
