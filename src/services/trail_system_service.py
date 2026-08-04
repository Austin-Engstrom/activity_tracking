"""Business logic for trail system management."""

from sqlalchemy.orm import Session

from src.repositories.segment_trail_system_repository import (
    SegmentTrailSystemRepository,
)
from src.repositories.segment_repository import SegmentRepository
from src.repositories.trail_system_repository import (
    TrailSystemRepository,
)


class TrailSystemService:
    """Coordinates trail system operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

        self.trail_repository = TrailSystemRepository(session)
        self.mapping_repository = SegmentTrailSystemRepository(session)
        self.segment_repository = SegmentRepository(session)

    def create_trail_system(
        self,
        name: str,
        city: str | None = None,
        state: str | None = None,
        country: str = "United States",
        latitude: float | None = None,
        longitude: float | None = None,
        description: str | None = None,
    ):
        """Create a trail system if it doesn't already exist."""

        existing = self.trail_repository.get_by_name(name)

        if existing:
            return existing

        trail = self.trail_repository.create(
            name=name,
            city=city,
            state=state,
            country=country,
            latitude=latitude,
            longitude=longitude,
            description=description,
        )

        self.session.commit()

        return trail

    def assign_segment(
        self,
        segment_id: int,
        trail_system_id: int,
        confidence: float = 1.0,
        mapping_source: str = "manual",
        notes: str | None = None,
    ):
        """Assign a segment to a trail system."""

        segment = self.segment_repository.get_by_id(segment_id)

        if segment is None:
            raise ValueError(
                f"Segment {segment_id} does not exist."
            )

        trail = self.trail_repository.get_by_id(
            trail_system_id
        )

        if trail is None:
            raise ValueError(
                f"Trail system {trail_system_id} does not exist."
            )

        existing = self.mapping_repository.get_mapping(
            segment_id,
            trail_system_id,
        )

        if existing:
            return existing

        mapping = self.mapping_repository.create(
            segment_id=segment_id,
            trail_system_id=trail_system_id,
            confidence=confidence,
            mapping_source=mapping_source,
            notes=notes,
        )

        self.session.commit()

        return mapping

def assign_segments(
    self,
    trail_system_id: int,
    segment_ids: list[int],
    confidence: float = 1.0,
    mapping_source: str = "manual",
) -> int:
    """Assign multiple segments to a trail system."""

    trail_system = self.trail_repository.get_by_id(
        trail_system_id
    )

    if trail_system is None:
        raise ValueError(
            f"Trail system {trail_system_id} does not exist."
        )

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "Confidence must be between 0.0 and 1.0."
        )

    unique_segment_ids = list(
        dict.fromkeys(segment_ids)
    )

    inserted = 0

    try:
        for segment_id in unique_segment_ids:
            segment = self.segment_repository.get_by_id(
                segment_id
            )

            if segment is None:
                raise ValueError(
                    f"Segment {segment_id} does not exist."
                )

            existing = self.mapping_repository.get_mapping(
                segment_id,
                trail_system_id,
            )

            if existing:
                continue

            self.mapping_repository.create(
                segment_id=segment_id,
                trail_system_id=trail_system_id,
                confidence=confidence,
                mapping_source=mapping_source,
            )

            inserted += 1

        self.session.commit()

        return inserted

    except Exception:
        self.session.rollback()
        raise
    
    def get_all_trail_systems(self):
        """Return all trail systems."""

        return self.trail_repository.get_all()

    def get_segments_for_trail(
        self,
        trail_system_id: int,
    ):
        """Return all mapped segments."""

        return self.mapping_repository.get_by_trail_system_id(
            trail_system_id
        )