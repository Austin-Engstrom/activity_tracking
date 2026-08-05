"""GPS-derived activity usage of an official trail."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.activity import Activity
    from src.models.official_trail import OfficialTrail


class OfficialTrailActivityMatch(Base):
    """One activity's matched usage of one official trail."""

    __tablename__ = "official_trail_activity_matches"

    official_trail_activity_match_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    official_trail_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("official_trails.official_trail_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activities.activity_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matched_trail_length_meters: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    ridden_distance_meters: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    trail_coverage_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    matched_point_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    tolerance_meters: Mapped[float] = mapped_column(
        Float, nullable=False, default=12.0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    official_trail: Mapped["OfficialTrail"] = relationship(
        back_populates="activity_matches"
    )
    activity: Mapped["Activity"] = relationship(
        back_populates="official_trail_matches"
    )

    __table_args__ = (
        UniqueConstraint(
            "official_trail_id",
            "activity_id",
            name="uq_official_trail_activity",
        ),
    )
