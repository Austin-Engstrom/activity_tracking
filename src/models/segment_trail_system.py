"""SQLAlchemy model mapping segments to trail systems."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.segment import Segment
    from src.models.trail_system import TrailSystem


class SegmentTrailSystem(Base):
    """Maps a Strava segment to a trail system."""

    __tablename__ = "segment_trail_systems"

    segment_trail_system_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    segment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "segments.segment_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    trail_system_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "trail_systems.trail_system_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    mapping_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="manual",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    segment: Mapped["Segment"] = relationship(
        back_populates="trail_system_mappings",
    )

    trail_system: Mapped["TrailSystem"] = relationship(
        back_populates="segment_mappings",
    )

    __table_args__ = (
        UniqueConstraint(
            "segment_id",
            "trail_system_id",
            name="uq_segment_trail_system",
        ),
        CheckConstraint(
            "confidence >= 0.0 and confidence <= 1.0",
            name="ck_segment_trail_system_confidence",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SegmentTrailSystem("
            f"segment_id={self.segment_id}, "
            f"trail_system_id={self.trail_system_id})>"
        )