"""Repository for Strava segments and segment efforts."""

from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.models.segment import Segment
from src.models.segment_effort import SegmentEffort


@dataclass
class SegmentLoadResult:
    """Summary of a segment and effort load."""

    segments_inserted: int = 0
    segments_updated: int = 0
    efforts_inserted: int = 0
    efforts_updated: int = 0


class SegmentRepository:
    """Handles database operations for segments and efforts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_activity_segments(
        self,
        activity_id: int,
        segments: list[Segment],
        efforts: list[SegmentEffort],
    ) -> SegmentLoadResult:
        """Upsert segments and replace efforts for one activity."""

        result = SegmentLoadResult()

        unique_segments = {
            segment.segment_id: segment
            for segment in segments
        }

        for segment in unique_segments.values():
            existing = self.session.get(
                Segment,
                segment.segment_id,
            )

            if existing is None:
                self.session.add(segment)
                result.segments_inserted += 1
            elif self._copy_changed_values(existing, segment):
                result.segments_updated += 1

        existing_efforts = {
            effort.segment_effort_id: effort
            for effort in self.session.scalars(
                select(SegmentEffort).where(
                    SegmentEffort.activity_id == activity_id
                )
            )
        }

        incoming_effort_ids = {
            effort.segment_effort_id
            for effort in efforts
        }

        for effort in efforts:
            existing = existing_efforts.get(
                effort.segment_effort_id
            )

            if existing is None:
                self.session.add(effort)
                result.efforts_inserted += 1
            elif self._copy_changed_values(existing, effort):
                result.efforts_updated += 1

        stale_effort_ids = (
            set(existing_efforts) - incoming_effort_ids
        )

        if stale_effort_ids:
            self.session.execute(
                delete(SegmentEffort).where(
                    SegmentEffort.segment_effort_id.in_(
                        stale_effort_ids
                    )
                )
            )

        return result

    def count_segments(self) -> int:
        """Return the total number of segments."""

        statement = select(func.count(Segment.segment_id))
        return int(self.session.scalar(statement) or 0)

    def count_efforts(self) -> int:
        """Return the total number of segment efforts."""

        statement = select(
            func.count(SegmentEffort.segment_effort_id)
        )
        return int(self.session.scalar(statement) or 0)

    @staticmethod
    def _copy_changed_values(
        existing,
        incoming,
    ) -> bool:
        """Copy changed mapped column values onto an existing row."""

        changed = False

        for column in incoming.__table__.columns:
            if column.primary_key:
                continue

            field = column.name

            if field in {"created_at", "updated_at"}:
                continue

            incoming_value = getattr(incoming, field)
            existing_value = getattr(existing, field)

            if incoming_value != existing_value:
                setattr(existing, field, incoming_value)
                changed = True

        return changed
