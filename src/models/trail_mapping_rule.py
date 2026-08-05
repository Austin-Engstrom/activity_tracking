"""SQLAlchemy model for automated trail-system mapping rules."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.trail_system import TrailSystem


class TrailMappingRule(Base):
    """Defines a deterministic rule for assigning segments to trail systems."""

    __tablename__ = "trail_mapping_rules"

    rule_id: Mapped[int] = mapped_column(
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

    rule_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    match_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    min_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    min_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.90,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
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
        back_populates="mapping_rules",
    )

    __table_args__ = (
        CheckConstraint(
            "confidence >= 0.0 and confidence <= 1.0",
            name="ck_trail_mapping_rule_confidence",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_trail_mapping_rule_priority",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TrailMappingRule("
            f"id={self.rule_id}, "
            f"type='{self.rule_type}', "
            f"trail_system_id={self.trail_system_id})>"
        )
