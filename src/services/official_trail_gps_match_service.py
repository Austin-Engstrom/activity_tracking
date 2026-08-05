"""Match activity-stream GPS lines to official trail geometry."""

import json
from dataclasses import dataclass

from pyproj import Transformer
from shapely.geometry import LineString, shape
from shapely.ops import transform
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from src.models.activity_stream import ActivityStream
from src.models.official_trail import OfficialTrail
from src.models.official_trail_activity_match import OfficialTrailActivityMatch
from src.models.trail_systems import TrailSystem


PROJECT = Transformer.from_crs(
    "EPSG:4326", "EPSG:3857", always_xy=True
).transform


@dataclass(slots=True)
class GpsMatchSummary:
    trail_system_id: int
    official_trails: int
    candidate_activities: int
    processed_activities: int
    matched_activities: int
    inserted_matches: int


class OfficialTrailGpsMatchService:
    """Calculate activity-to-trail matches using buffered GPS geometry."""

    def __init__(
        self,
        session: Session,
        *,
        tolerance_meters: float = 12.0,
        minimum_matched_trail_meters: float = 20.0,
        minimum_coverage_percent: float = 2.0,
    ) -> None:
        self.session = session
        self.tolerance_meters = tolerance_meters
        self.minimum_matched_trail_meters = minimum_matched_trail_meters
        self.minimum_coverage_percent = minimum_coverage_percent

    def match_trail_system(
        self,
        trail_system_id: int,
        *,
        batch_size: int | None = None,
    ) -> GpsMatchSummary:
        trail_system = self.session.get(TrailSystem, trail_system_id)

        if trail_system is None:
            raise ValueError(f"Trail system {trail_system_id} does not exist.")

        if not trail_system.boundary_geojson:
            raise ValueError(f"{trail_system.name} has no boundary geometry.")

        trails = list(
            self.session.scalars(
                select(OfficialTrail)
                .where(
                    OfficialTrail.trail_system_id == trail_system_id,
                    OfficialTrail.combined_geometry_geojson.is_not(None),
                )
                .order_by(OfficialTrail.official_trail_id)
            )
        )

        if not trails:
            raise ValueError(f"{trail_system.name} has no official trails.")

        raw_boundary = shape(json.loads(trail_system.boundary_geojson))
        min_lon, min_lat, max_lon, max_lat = raw_boundary.bounds

        activity_ids = list(
            self.session.scalars(
                select(distinct(ActivityStream.activity_id))
                .where(
                    ActivityStream.latitude.between(min_lat, max_lat),
                    ActivityStream.longitude.between(min_lon, max_lon),
                )
                .order_by(ActivityStream.activity_id)
            )
        )

        if batch_size is not None:
            activity_ids = activity_ids[:batch_size]

        projected_trails = {
            trail.official_trail_id: transform(
                PROJECT,
                shape(json.loads(trail.combined_geometry_geojson)),
            )
            for trail in trails
        }

        processed = 0
        matched_activities = 0
        inserted_matches = 0

        try:
            for activity_id in activity_ids:
                rows = list(
                    self.session.scalars(
                        select(ActivityStream)
                        .where(
                            ActivityStream.activity_id == activity_id,
                            ActivityStream.latitude.is_not(None),
                            ActivityStream.longitude.is_not(None),
                        )
                        .order_by(ActivityStream.point_index)
                    )
                )

                coordinates = [
                    (row.longitude, row.latitude)
                    for row in rows
                ]

                if len(coordinates) < 2:
                    continue

                activity_line = transform(PROJECT, LineString(coordinates))
                activity_had_match = False

                # Recalculate this activity cleanly for the selected system.
                existing = list(
                    self.session.scalars(
                        select(OfficialTrailActivityMatch)
                        .where(
                            OfficialTrailActivityMatch.activity_id == activity_id,
                            OfficialTrailActivityMatch.official_trail_id.in_(
                                list(projected_trails)
                            ),
                        )
                    )
                )
                for match in existing:
                    self.session.delete(match)

                # Ensure prior rows are deleted before replacement inserts.
                self.session.flush()

                for trail in trails:
                    trail_geometry = projected_trails[trail.official_trail_id]
                    trail_length = float(trail_geometry.length)

                    if trail_length <= 0:
                        continue

                    matched_trail = trail_geometry.intersection(
                        activity_line.buffer(self.tolerance_meters)
                    )
                    matched_length = float(matched_trail.length)
                    coverage = min(
                        matched_length / trail_length * 100.0,
                        100.0,
                    )

                    if (
                        matched_length < self.minimum_matched_trail_meters
                        and coverage < self.minimum_coverage_percent
                    ):
                        continue

                    ridden_distance = float(
                        activity_line.intersection(
                            trail_geometry.buffer(self.tolerance_meters)
                        ).length
                    )

                    buffered_trail = trail_geometry.buffer(
                        self.tolerance_meters
                    )
                    matched_points = sum(
                        1
                        for longitude, latitude in coordinates
                        if buffered_trail.covers(
                            transform(
                                PROJECT,
                                shape(
                                    {
                                        "type": "Point",
                                        "coordinates": [
                                            longitude,
                                            latitude,
                                        ],
                                    }
                                ),
                            )
                        )
                    )

                    self.session.add(
                        OfficialTrailActivityMatch(
                            official_trail_id=trail.official_trail_id,
                            activity_id=activity_id,
                            matched_trail_length_meters=matched_length,
                            ridden_distance_meters=ridden_distance,
                            trail_coverage_percent=coverage,
                            matched_point_count=matched_points,
                            tolerance_meters=self.tolerance_meters,
                        )
                    )

                    inserted_matches += 1
                    activity_had_match = True

                self.session.commit()
                processed += 1

                if activity_had_match:
                    matched_activities += 1

        except Exception:
            self.session.rollback()
            raise

        return GpsMatchSummary(
            trail_system_id=trail_system_id,
            official_trails=len(trails),
            candidate_activities=len(activity_ids),
            processed_activities=processed,
            matched_activities=matched_activities,
            inserted_matches=inserted_matches,
        )
