"""SQLAlchemy model mapping Strava segments to imported OSM trails."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.osm_trails import OsmTrail
    from src.models.segment import Segment


class TrailSegmentMapping(Base):
    """Represents a spatial match between a Strava segment and OSM trail."""

    __tablename__ = "trail_segment_mappings"

    trail_segment_mapping_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    osm_trail_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "osm_trails.osm_trail_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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

    distance_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    overlap_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    mapping_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="geometry_proximity",
    )

    validated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    osm_trail: Mapped["OsmTrail"] = relationship(
        back_populates="segment_mappings",
    )

    segment: Mapped["Segment"] = relationship(
        back_populates="osm_trail_mappings",
    )

    __table_args__ = (
        UniqueConstraint(
            "osm_trail_id",
            "segment_id",
            name="uq_osm_trail_segment",
        ),
    )
