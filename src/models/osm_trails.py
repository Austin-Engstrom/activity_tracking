"""SQLAlchemy model for OpenStreetMap trail ways."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
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
    from src.models.trail_systems import TrailSystem


class OsmTrail(Base):
    """Represents one OSM way imported as trail geometry."""

    __tablename__ = "osm_trails"

    osm_trail_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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

    osm_element_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="way",
    )

    osm_element_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    highway_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    surface: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    bicycle_access: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    access: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    mtb_scale: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    mtb_scale_uphill: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    mtb_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    oneway: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    length_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    vertex_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_loop: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    geometry_geojson: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tags_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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

    trail_system: Mapped["TrailSystem"] = relationship(
        back_populates="osm_trails",
    )

    __table_args__ = (
        UniqueConstraint(
            "trail_system_id",
            "osm_element_type",
            "osm_element_id",
            name="uq_osm_trail_system_element",
        ),
    )
