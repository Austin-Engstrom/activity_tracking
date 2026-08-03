"""SQLAlchemy model for Strava activity stream points."""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ActivityStream(Base):
    """One aligned stream observation for a Strava activity."""

    __tablename__ = "activity_streams"

    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.activity_id"),
        nullable=False,
    )

    point_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    distance_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    altitude_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    velocity_mps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    heartrate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    cadence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    watts: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_moving: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    grade_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "activity_id",
            "point_index",
            name="pk_activity_streams",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityStream("
            f"activity_id={self.activity_id!r}, "
            f"point_index={self.point_index!r}, "
            f"time_seconds={self.time_seconds!r}"
            f")>"
        )