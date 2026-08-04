"""Repository for trail system database operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.trail_systems import TrailSystem


class TrailSystemRepository:
    """Handles persistence operations for trail systems."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        name: str,
        city: str | None = None,
        state: str | None = None,
        country: str = "United States",
        latitude: float | None = None,
        longitude: float | None = None,
        description: str | None = None,
    ) -> TrailSystem:
        """Create and persist a new trail system."""

        trail_system = TrailSystem(
            name=name.strip(),
            city=city.strip() if city else None,
            state=state.strip() if state else None,
            country=country.strip(),
            latitude=latitude,
            longitude=longitude,
            description=description.strip() if description else None,
        )

        self.session.add(trail_system)
        self.session.flush()

        return trail_system

    def get_by_id(
        self,
        trail_system_id: int,
    ) -> TrailSystem | None:
        """Return a trail system by primary key."""

        return self.session.get(
            TrailSystem,
            trail_system_id,
        )

    def get_by_name(
        self,
        name: str,
    ) -> TrailSystem | None:
        """Return a trail system using a case-insensitive name match."""

        statement = select(TrailSystem).where(
            TrailSystem.name.ilike(name.strip())
        )

        return self.session.scalar(statement)

    def get_all(self) -> list[TrailSystem]:
        """Return all trail systems ordered by name."""

        statement = select(TrailSystem).order_by(
            TrailSystem.name
        )

        return list(self.session.scalars(statement))

    def update(
        self,
        trail_system: TrailSystem,
        *,
        name: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        description: str | None = None,
    ) -> TrailSystem:
        """Update the supplied trail system."""

        if name is not None:
            trail_system.name = name.strip()

        if city is not None:
            trail_system.city = city.strip() or None

        if state is not None:
            trail_system.state = state.strip() or None

        if country is not None:
            trail_system.country = country.strip()

        if latitude is not None:
            trail_system.latitude = latitude

        if longitude is not None:
            trail_system.longitude = longitude

        if description is not None:
            trail_system.description = description.strip() or None

        self.session.flush()

        return trail_system

    def delete(
        self,
        trail_system: TrailSystem,
    ) -> None:
        """Delete a trail system."""

        self.session.delete(trail_system)
        self.session.flush()