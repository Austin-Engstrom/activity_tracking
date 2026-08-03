"""SQLAlchemy model for Strava segment efforts."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SegmentEffort(Base):
    """Represents an athlete's effort on a segment within an activity."""

    __tablename__ = "segment_efforts"

    segment_effort_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )

    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.activity_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    segment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("segments.segment_id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    elapsed_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    moving_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    start_date_local: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    distance_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    start_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    end_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    average_cadence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_watts: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    device_watts: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    average_heartrate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_heartrate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    kom_rank: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    pr_rank: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    hidden: Mapped[bool | None] = mapped_column(
        Boolean,
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

    def __repr__(self) -> str:
        return (
            f"<SegmentEffort("
            f"id={self.segment_effort_id}, "
            f"activity_id={self.activity_id}, "
            f"segment_id={self.segment_id})>"
        )
