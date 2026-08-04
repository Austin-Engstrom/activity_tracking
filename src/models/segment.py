"""SQLAlchemy model for Strava segments."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
)

from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Segment(Base):
    """Represents a unique Strava segment."""

    __tablename__ = "segments"

    segment_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    activity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    distance_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_grade: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_grade: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_high_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_low_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    start_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    start_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    end_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    end_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    climb_category: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    private: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    hazardous: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    starred: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    effort_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    athlete_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    star_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    trail_system_mappings = relationship(
        "SegmentTrailSystem",
        back_populates="segment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Segment("
            f"id={self.segment_id}, "
            f"name='{self.name}')>"
        )
