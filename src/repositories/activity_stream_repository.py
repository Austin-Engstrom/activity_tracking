"""Database access methods for Strava activity stream rows."""

from collections.abc import Iterable

from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from src.models.activity_stream import ActivityStream


class ActivityStreamRepository:
    """Repository for querying and storing activity stream rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def has_streams(
        self,
        activity_id: int,
    ) -> bool:
        """Return whether any stream rows exist for an activity."""

        if activity_id <= 0:
            raise ValueError(
                "activity_id must be a positive integer."
            )

        statement = (
            select(ActivityStream.activity_id)
            .where(ActivityStream.activity_id == activity_id)
            .limit(1)
        )

        return self.session.scalar(statement) is not None

    def count_for_activity(
        self,
        activity_id: int,
    ) -> int:
        """Return the number of stored stream rows for an activity."""

        if activity_id <= 0:
            raise ValueError(
                "activity_id must be a positive integer."
            )

        statement = (
            select(func.count())
            .select_from(ActivityStream)
            .where(ActivityStream.activity_id == activity_id)
        )

        return int(
            self.session.scalar(statement) or 0
        )

    def count_all(self) -> int:
        """Return the total number of stored stream rows."""

        statement = (
            select(func.count())
            .select_from(ActivityStream)
        )

        return int(
            self.session.scalar(statement) or 0
        )

    def delete_for_activity(
        self,
        activity_id: int,
    ) -> int:
        """Delete all stream rows stored for an activity."""

        if activity_id <= 0:
            raise ValueError(
                "activity_id must be a positive integer."
            )

        statement = (
            delete(ActivityStream)
            .where(ActivityStream.activity_id == activity_id)
        )

        result = self.session.execute(statement)

        return int(result.rowcount or 0)

    def insert_many(
        self,
        stream_rows: Iterable[dict],
        replace_existing: bool = False,
    ) -> int:
        """
        Insert transformed activity stream rows.

        When replace_existing is True, existing rows for the activity
        are deleted before the new rows are inserted.
        """

        rows = list(stream_rows)

        if not rows:
            return 0

        activity_ids = {
            row.get("activity_id")
            for row in rows
        }

        if len(activity_ids) != 1:
            raise ValueError(
                "All stream rows must belong to one activity."
            )

        activity_id = next(iter(activity_ids))

        if not isinstance(activity_id, int) or activity_id <= 0:
            raise ValueError(
                "Each stream row must contain a valid activity_id."
            )

        try:
            if replace_existing:
                self.delete_for_activity(activity_id)

            self.session.execute(
                insert(ActivityStream),
                rows,
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return len(rows)