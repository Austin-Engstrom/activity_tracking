"""Calculate lifetime official-trail coverage from all matched activities."""

import json
from dataclasses import dataclass

from pyproj import Transformer
from shapely.geometry import LineString, shape
from shapely.ops import transform, unary_union
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.activity_stream import ActivityStream
from src.models.official_trail import OfficialTrail
from src.models.official_trail_activity_match import OfficialTrailActivityMatch
from src.models.official_trail_progress import OfficialTrailProgress


PROJECT = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:3857",
    always_xy=True,
).transform


@dataclass(slots=True)
class LifetimeProgressSummary:
    """Summary of one lifetime trail-progress rebuild."""

    trail_system_id: int
    official_trails: int
    trails_with_matches: int
    completed: int
    nearly_complete: int
    partial: int
    started: int
    unridden: int


class OfficialTrailLifetimeProgressService:
    """Rebuild progress using the union of all historical GPS coverage."""

    def __init__(
        self,
        session: Session,
        *,
        tolerance_meters: float = 12.0,
    ) -> None:
        self.session = session
        self.tolerance_meters = tolerance_meters

    def rebuild_trail_system(
        self,
        trail_system_id: int,
    ) -> LifetimeProgressSummary:
        """Recalculate cumulative progress for one trail system."""

        trails = list(
            self.session.scalars(
                select(OfficialTrail)
                .where(
                    OfficialTrail.trail_system_id
                    == trail_system_id
                )
                .order_by(
                    OfficialTrail.official_trail_id
                )
            )
        )

        status_counts = {
            "completed": 0,
            "nearly_complete": 0,
            "partial": 0,
            "started": 0,
            "unridden": 0,
        }
        trails_with_matches = 0

        try:
            for trail in trails:
                progress = self.session.get(
                    OfficialTrailProgress,
                    trail.official_trail_id,
                )

                if progress is None:
                    progress = OfficialTrailProgress(
                        official_trail_id=trail.official_trail_id
                    )
                    self.session.add(progress)

                matches = self._get_matches(
                    trail.official_trail_id
                )

                if (
                    not matches
                    or not trail.combined_geometry_geojson
                ):
                    self._set_unridden(progress)
                    status_counts["unridden"] += 1
                    continue

                trails_with_matches += 1

                activity_lines = []

                for match in matches:
                    activity_line = self._build_activity_line(
                        match.activity_id
                    )

                    if activity_line is not None:
                        activity_lines.append(activity_line)

                if not activity_lines:
                    self._set_unridden(progress)
                    status_counts["unridden"] += 1
                    continue

                trail_geometry = transform(
                    PROJECT,
                    shape(
                        json.loads(
                            trail.combined_geometry_geojson
                        )
                    ),
                )

                trail_length = float(trail_geometry.length)

                if trail_length <= 0:
                    self._set_unridden(progress)
                    status_counts["unridden"] += 1
                    continue

                lifetime_buffer = unary_union(
                    [
                        line.buffer(self.tolerance_meters)
                        for line in activity_lines
                    ]
                )

                covered_geometry = trail_geometry.intersection(
                    lifetime_buffer
                )

                covered_length = float(covered_geometry.length)

                coverage_percent = min(
                    covered_length / trail_length * 100.0,
                    100.0,
                )

                dates = [
                    match.activity.start_date
                    for match in matches
                    if match.activity is not None
                    and match.activity.start_date is not None
                ]

                progress.activity_count = len(
                    {match.activity_id for match in matches}
                )
                progress.first_ridden_at = (
                    min(dates) if dates else None
                )
                progress.last_ridden_at = (
                    max(dates) if dates else None
                )
                progress.total_ridden_distance_meters = sum(
                    match.ridden_distance_meters
                    for match in matches
                )
                progress.estimated_coverage_percent = coverage_percent
                progress.progress_status = self._status(
                    progress.activity_count,
                    coverage_percent,
                )

                status_counts[progress.progress_status] += 1

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return LifetimeProgressSummary(
            trail_system_id=trail_system_id,
            official_trails=len(trails),
            trails_with_matches=trails_with_matches,
            completed=status_counts["completed"],
            nearly_complete=status_counts["nearly_complete"],
            partial=status_counts["partial"],
            started=status_counts["started"],
            unridden=status_counts["unridden"],
        )

    def _get_matches(
        self,
        official_trail_id: int,
    ) -> list[OfficialTrailActivityMatch]:
        """Return trail matches with activity metadata."""

        statement = (
            select(OfficialTrailActivityMatch)
            .options(
                selectinload(
                    OfficialTrailActivityMatch.activity
                )
            )
            .where(
                OfficialTrailActivityMatch.official_trail_id
                == official_trail_id
            )
            .order_by(
                OfficialTrailActivityMatch.activity_id
            )
        )

        return list(self.session.scalars(statement))

    def _build_activity_line(
        self,
        activity_id: int,
    ):
        """Return one projected activity GPS line."""

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
            return None

        return transform(
            PROJECT,
            LineString(coordinates),
        )

    @staticmethod
    def _set_unridden(
        progress: OfficialTrailProgress,
    ) -> None:
        """Reset one progress row to unridden."""

        progress.activity_count = 0
        progress.first_ridden_at = None
        progress.last_ridden_at = None
        progress.total_ridden_distance_meters = 0.0
        progress.estimated_coverage_percent = 0.0
        progress.progress_status = "unridden"

    @staticmethod
    def _status(
        activity_count: int,
        coverage_percent: float,
    ) -> str:
        """Return the trail progress classification."""

        if activity_count == 0 or coverage_percent <= 0:
            return "unridden"

        if coverage_percent >= 99.0:
            return "completed"

        if coverage_percent >= 75.0:
            return "nearly_complete"

        if coverage_percent >= 25.0:
            return "partial"

        return "started"
