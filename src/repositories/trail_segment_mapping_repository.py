"""Repository for trail-to-segment mappings."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.trail_segment_mapping import TrailSegmentMapping


class TrailSegmentMappingRepository:
    """Handles persistence for OSM trail and Strava segment mappings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_mapping(
        self,
        osm_trail_id: int,
        segment_id: int,
    ) -> TrailSegmentMapping | None:
        """Return a specific OSM-trail-to-segment mapping."""

        statement = select(TrailSegmentMapping).where(
            TrailSegmentMapping.osm_trail_id == osm_trail_id,
            TrailSegmentMapping.segment_id == segment_id,
        )

        return self.session.scalar(statement)

    def get_by_trail_system(
        self,
        trail_system_id: int,
    ) -> list[TrailSegmentMapping]:
        """Return mappings for one trail system."""

        statement = (
            select(TrailSegmentMapping)
            .join(TrailSegmentMapping.osm_trail)
            .options(
                selectinload(TrailSegmentMapping.osm_trail),
                selectinload(TrailSegmentMapping.segment),
            )
            .where(
                TrailSegmentMapping.osm_trail.has(
                    trail_system_id=trail_system_id
                )
            )
            .order_by(
                TrailSegmentMapping.confidence.desc(),
                TrailSegmentMapping.segment_id,
            )
        )

        return list(self.session.scalars(statement))

    def add(
        self,
        mapping: TrailSegmentMapping,
    ) -> TrailSegmentMapping:
        """Add and flush a mapping."""

        self.session.add(mapping)
        self.session.flush()

        return mapping

    def delete_unvalidated_for_trail_system(
        self,
        trail_system_id: int,
    ) -> int:
        """Delete unvalidated mappings for one trail system."""

        mappings = self.get_by_trail_system(trail_system_id)
        deleted = 0

        for mapping in mappings:
            if mapping.validated:
                continue

            self.session.delete(mapping)
            deleted += 1

        self.session.flush()

        return deleted
