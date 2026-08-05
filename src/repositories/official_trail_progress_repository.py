"""Repository for official-trail progress records."""

from sqlalchemy.orm import Session

from src.models.official_trail_progress import (
    OfficialTrailProgress,
)


class OfficialTrailProgressRepository:
    """Handles official-trail progress persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        official_trail_id: int,
    ) -> OfficialTrailProgress | None:
        """Return one official-trail progress row."""

        return self.session.get(
            OfficialTrailProgress,
            official_trail_id,
        )

    def add(
        self,
        progress: OfficialTrailProgress,
    ) -> OfficialTrailProgress:
        """Add and flush a progress record."""

        self.session.add(progress)
        self.session.flush()

        return progress