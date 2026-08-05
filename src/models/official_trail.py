"""SQLAlchemy model for normalized official trails."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    from src.models.osm_trails import OsmTrail
    from src.models.trail_systems import TrailSystem


class OfficialTrail(Base):
    """Represents one logical trail grouped from one or more OSM ways."""

    __tablename__ = "official_trails"

    official_trail_id: Mapped[int] = mapped_column(
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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    total_length_meters: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    section_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    primary_surface: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    bicycle_access: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    mtb_scale: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    mtb_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    combined_geometry_geojson: Mapped[str | None] = mapped_column(
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

    trail_system: Mapped["TrailSystem"] = relationship(
        back_populates="official_trails",
    )

    osm_sections: Mapped[list["OsmTrail"]] = relationship(
        back_populates="official_trail",
    )

    __table_args__ = (
        UniqueConstraint(
            "trail_system_id",
            "normalized_name",
            name="uq_official_trail_system_name",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OfficialTrail("
            f"id={self.official_trail_id}, "
            f"name={self.name!r}, "
            f"trail_system_id={self.trail_system_id})>"
        )
