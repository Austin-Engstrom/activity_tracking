from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.trail_mapping_rule import TrailMappingRule


class TrailSystem(Base):
    __tablename__ = "trail_systems"

    trail_system_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="United States",
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
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

    segment_mappings = relationship(
        "SegmentTrailSystem",
        back_populates="trail_system",
        cascade="all, delete-orphan",
    )

    mapping_rules: Mapped[list["TrailMappingRule"]] = relationship(
    back_populates="trail_system",
    cascade="all, delete-orphan",
    )