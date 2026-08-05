"""Repository for imported OpenStreetMap trails."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.osm_trails import OsmTrail


class OsmTrailRepository:
    """Handles persistence for OSM trail ways."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_osm_element(
        self,
        trail_system_id: int,
        osm_element_type: str,
        osm_element_id: int,
    ) -> OsmTrail | None:
        """Return one OSM trail record."""

        statement = select(OsmTrail).where(
            OsmTrail.trail_system_id == trail_system_id,
            OsmTrail.osm_element_type == osm_element_type,
            OsmTrail.osm_element_id == osm_element_id,
        )

        return self.session.scalar(statement)

    def get_by_trail_system(
        self,
        trail_system_id: int,
    ) -> list[OsmTrail]:
        """Return all OSM trails for one trail system."""

        statement = (
            select(OsmTrail)
            .where(
                OsmTrail.trail_system_id == trail_system_id
            )
            .order_by(
                OsmTrail.name,
                OsmTrail.osm_element_id,
            )
        )

        return list(self.session.scalars(statement))

    def add(self, trail: OsmTrail) -> OsmTrail:
        """Add and flush a trail."""

        self.session.add(trail)
        self.session.flush()
        return trail

    def delete_missing(
        self,
        trail_system_id: int,
        retained_keys: set[tuple[str, int]],
    ) -> int:
        """Delete previously imported ways no longer returned."""

        deleted = 0

        for trail in self.get_by_trail_system(trail_system_id):
            key = (
                trail.osm_element_type,
                trail.osm_element_id,
            )

            if key in retained_keys:
                continue

            self.session.delete(trail)
            deleted += 1

        self.session.flush()
        return deleted
