"""Repository for segment-to-trail-system mappings."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.segment_trail_system import SegmentTrailSystem


class SegmentTrailSystemRepository:
    """Handles segment-to-trail-system mapping operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        segment_id: int,
        trail_system_id: int,
        confidence: float = 1.0,
        mapping_source: str = "manual",
        notes: str | None = None,
    ) -> SegmentTrailSystem:
        """Create a segment-to-trail-system mapping."""

        mapping = SegmentTrailSystem(
            segment_id=segment_id,
            trail_system_id=trail_system_id,
            confidence=confidence,
            mapping_source=mapping_source.strip(),
            notes=notes.strip() if notes else None,
        )

        self.session.add(mapping)
        self.session.flush()

        return mapping

    def get_mapping(
        self,
        segment_id: int,
        trail_system_id: int,
    ) -> SegmentTrailSystem | None:
        """Return a specific segment-to-trail-system mapping."""

        statement = select(SegmentTrailSystem).where(
            SegmentTrailSystem.segment_id == segment_id,
            SegmentTrailSystem.trail_system_id == trail_system_id,
        )

        return self.session.scalar(statement)

    def get_by_segment_id(
        self,
        segment_id: int,
    ) -> list[SegmentTrailSystem]:
        """Return all trail-system mappings for a segment."""

        statement = (
            select(SegmentTrailSystem)
            .options(
                selectinload(
                    SegmentTrailSystem.trail_system
                )
            )
            .where(
                SegmentTrailSystem.segment_id == segment_id
            )
        )

        return list(self.session.scalars(statement))

    def get_by_trail_system_id(
        self,
        trail_system_id: int,
    ) -> list[SegmentTrailSystem]:
        """Return all segment mappings for a trail system."""

        statement = (
            select(SegmentTrailSystem)
            .options(
                selectinload(
                    SegmentTrailSystem.segment
                )
            )
            .where(
                SegmentTrailSystem.trail_system_id
                == trail_system_id
            )
        )

        return list(self.session.scalars(statement))

    def get_all(self) -> list[SegmentTrailSystem]:
        """Return all mappings with related records loaded."""

        statement = (
            select(SegmentTrailSystem)
            .options(
                selectinload(
                    SegmentTrailSystem.segment
                ),
                selectinload(
                    SegmentTrailSystem.trail_system
                ),
            )
            .order_by(
                SegmentTrailSystem.trail_system_id,
                SegmentTrailSystem.segment_id,
            )
        )

        return list(self.session.scalars(statement))

    def delete(
        self,
        mapping: SegmentTrailSystem,
    ) -> None:
        """Delete a segment-to-trail-system mapping."""

        self.session.delete(mapping)
        self.session.flush()