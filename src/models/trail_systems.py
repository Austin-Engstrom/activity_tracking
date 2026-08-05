from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.trail_mapping_rule import TrailMappingRule

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.osm_trails import OsmTrail

if TYPE_CHECKING:
    from src.models.official_trail import OfficialTrail


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

    osm_element_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    osm_element_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        )

    osm_display_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        )

    boundary_geojson: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        )

    boundary_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        )

    boundary_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        )

    boundary_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        )
    
    osm_trails: Mapped[list["OsmTrail"]] = relationship(
        back_populates="trail_system",
    cascade="all, delete-orphan",
    )

    official_trails: Mapped[list["OfficialTrail"]] = relationship(
        back_populates="trail_system",
        cascade="all, delete-orphan",
    )
