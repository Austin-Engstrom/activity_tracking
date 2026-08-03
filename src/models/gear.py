from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Gear(Base):
    __tablename__ = "gear"

    gear_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
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

    brand_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    distance_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_primary: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    is_retired: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    detail_loaded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Gear("
            f"gear_id={self.gear_id!r}, "
            f"name={self.name!r}, "
            f"brand_name={self.brand_name!r}, "
            f"model_name={self.model_name!r}"
            f")>"
        )