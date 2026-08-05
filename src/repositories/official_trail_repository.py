"""Repository for normalized official trails."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.official_trail import OfficialTrail


class OfficialTrailRepository:
    """Handles persistence for normalized official trails."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(
        self,
        trail_system_id: int,
        normalized_name: str,
    ) -> OfficialTrail | None:
        """Return one official trail by normalized name."""

        statement = select(OfficialTrail).where(
            OfficialTrail.trail_system_id == trail_system_id,
            OfficialTrail.normalized_name == normalized_name,
        )

        return self.session.scalar(statement)

    def get_by_trail_system(
        self,
        trail_system_id: int,
    ) -> list[OfficialTrail]:
        """Return official trails and OSM sections for one system."""

        statement = (
            select(OfficialTrail)
            .options(
                selectinload(OfficialTrail.osm_sections)
            )
            .where(
                OfficialTrail.trail_system_id == trail_system_id
            )
            .order_by(OfficialTrail.name)
        )

        return list(self.session.scalars(statement))

    def add(
        self,
        trail: OfficialTrail,
    ) -> OfficialTrail:
        """Add and flush an official trail."""

        self.session.add(trail)
        self.session.flush()

        return trail

    def delete_empty_for_trail_system(
        self,
        trail_system_id: int,
    ) -> int:
        """Delete normalized trails with no assigned OSM sections."""

        deleted = 0

        for trail in self.get_by_trail_system(trail_system_id):
            if trail.osm_sections:
                continue

            self.session.delete(trail)
            deleted += 1

        self.session.flush()

        return deleted
