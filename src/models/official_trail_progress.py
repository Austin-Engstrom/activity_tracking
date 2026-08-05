"""Aggregated progress for one official trail."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.official_trail import OfficialTrail


class OfficialTrailProgress(Base):
    """Latest GPS-derived progress for one official trail."""

    __tablename__ = "official_trail_progress"

    official_trail_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("official_trails.official_trail_id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    activity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_ridden_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_ridden_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_ridden_distance_meters: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    estimated_coverage_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    progress_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unridden", index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    official_trail: Mapped["OfficialTrail"] = relationship(
        back_populates="progress"
    )
