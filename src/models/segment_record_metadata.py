"""Retrieval provenance for the latest stored Strava effort rankings."""
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base


class SegmentEffortRecordMetadata(Base):
    __tablename__ = 'segment_effort_record_metadata'
    segment_effort_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('segment_efforts.segment_effort_id', ondelete='CASCADE'), primary_key=True, autoincrement=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pr_rank_returned: Mapped[bool] = mapped_column(Boolean, nullable=False)
    kom_rank_returned: Mapped[bool] = mapped_column(Boolean, nullable=False)


class SegmentRecordRefresh(Base):
    __tablename__ = 'segment_record_refresh'
    activity_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('activities.activity_id', ondelete='CASCADE'), primary_key=True, autoincrement=False)
    last_attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
