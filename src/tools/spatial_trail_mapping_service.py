"""Assign stored Strava segments using confirmed trail-system polygons."""

import json
from dataclasses import dataclass

from shapely.geometry import Point, shape
from shapely.prepared import prep
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.segment import Segment
from src.models.segment_trail_system import SegmentTrailSystem
from src.models.trail_system import TrailSystem
from src.repositories.segment_trail_system_repository import (
    SegmentTrailSystemRepository,
)


@dataclass(slots=True)
class SpatialMappingSummary:
    """Summary of one spatial mapping run."""

    trail_systems_with_boundaries: int
    total_segments: int
    already_mapped: int
    evaluated: int
    mapped: int
    unmatched: int


class SpatialTrailMappingService:
    """Map unmapped segments whose midpoint falls inside an OSM polygon."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.mapping_repository = SegmentTrailSystemRepository(session)

    def run(self) -> SpatialMappingSummary:
        """Apply confirmed boundaries to currently unmapped segments."""

        trail_systems = self._get_trail_systems_with_boundaries()
        mapped_segment_ids = self._get_mapped_segment_ids()
        segments = self._get_unmapped_segments(mapped_segment_ids)

        prepared_boundaries = []

        for trail_system in trail_systems:
            geometry = shape(json.loads(trail_system.boundary_geojson))

            if geometry.is_empty:
                continue

            if not geometry.is_valid:
                geometry = geometry.buffer(0)

            prepared_boundaries.append(
                (trail_system, prep(geometry))
            )

        inserted = 0

        try:
            for segment in segments:
                midpoint = self._segment_midpoint(segment)

                if midpoint is None:
                    continue

                for trail_system, boundary in prepared_boundaries:
                    if not boundary.covers(midpoint):
                        continue

                    self.mapping_repository.create(
                        segment_id=segment.segment_id,
                        trail_system_id=trail_system.trail_system_id,
                        confidence=0.98,
                        mapping_source="osm_polygon",
                        notes=(
                            "Automatically mapped using a confirmed "
                            "OpenStreetMap boundary."
                        ),
                    )
                    inserted += 1
                    break

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return SpatialMappingSummary(
            trail_systems_with_boundaries=len(prepared_boundaries),
            total_segments=self._count_segments(),
            already_mapped=len(mapped_segment_ids),
            evaluated=len(segments),
            mapped=inserted,
            unmatched=len(segments) - inserted,
        )

    @staticmethod
    def _segment_midpoint(segment: Segment) -> Point | None:
        """Return segment midpoint in longitude/latitude order."""

        values = (
            segment.start_latitude,
            segment.start_longitude,
            segment.end_latitude,
            segment.end_longitude,
        )

        if any(value is None for value in values):
            return None

        latitude = (
            segment.start_latitude + segment.end_latitude
        ) / 2

        longitude = (
            segment.start_longitude + segment.end_longitude
        ) / 2

        return Point(longitude, latitude)

    def _get_trail_systems_with_boundaries(
        self,
    ) -> list[TrailSystem]:
        """Return trail systems with confirmed geometry."""

        statement = (
            select(TrailSystem)
            .where(
                TrailSystem.boundary_geojson.is_not(None),
                TrailSystem.boundary_confirmed.is_(True),
            )
            .order_by(TrailSystem.trail_system_id)
        )

        return list(self.session.scalars(statement))

    def _get_mapped_segment_ids(self) -> set[int]:
        """Return all mapped segment IDs."""

        statement = select(
            SegmentTrailSystem.segment_id
        ).distinct()

        return set(self.session.scalars(statement))

    def _get_unmapped_segments(
        self,
        mapped_segment_ids: set[int],
    ) -> list[Segment]:
        """Return unmapped segments."""

        statement = select(Segment).order_by(
            Segment.city,
            Segment.name,
        )

        if mapped_segment_ids:
            statement = statement.where(
                Segment.segment_id.not_in(mapped_segment_ids)
            )

        return list(self.session.scalars(statement))

    def _count_segments(self) -> int:
        """Return total stored segments."""

        return len(
            list(
                self.session.scalars(
                    select(Segment.segment_id)
                )
            )
        )
