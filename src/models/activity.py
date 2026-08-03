"""SQLAlchemy model for Strava activities."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Activity(Base):
    """Represents a Strava activity."""

    __tablename__ = "activities"

    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )

    athlete_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sport_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    distance_meters: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    moving_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    elapsed_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_elevation_gain_meters: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    average_speed_mps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_speed_mps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_heartrate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_watts: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    kilojoules: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    trainer: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    commute: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    gear_id: Mapped[str | None] = mapped_column(
        String(50),
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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    calories: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    workout_type: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    suffer_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    average_cadence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_heartrate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    has_heartrate: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    detail_loaded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    segments_loaded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    laps_loaded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    splits_loaded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Activity("
            f"id={self.activity_id}, "
            f"name='{self.name}', "
            f"date='{self.start_date}')>"
        )
