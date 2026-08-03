"""Repository for storing and querying Strava activities."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.models.activity import Activity


@dataclass
class ActivityLoadResult:
    """Summary of an activity database load."""

    inserted: int = 0
    updated: int = 0
    skipped: int = 0


class ActivityRepository:
    """Handles database operations for activities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(
        self,
        activities: list[Activity],
    ) -> ActivityLoadResult:
        """Insert new activities and update changed activities."""

        result = ActivityLoadResult()

        try:
            for activity in activities:
                existing = self.session.get(
                    Activity,
                    activity.activity_id,
                )

                if existing is None:
                    self.session.add(activity)
                    result.inserted += 1
                    continue

                if self._update_existing(existing, activity):
                    result.updated += 1
                else:
                    result.skipped += 1

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return result

    def count(self) -> int:
        """Return the total number of stored activities."""

        statement = select(func.count(Activity.activity_id))
        return int(self.session.scalar(statement) or 0)

    def get_latest_start_date(self) -> datetime | None:
        """Return the newest stored activity start date."""

        statement = select(func.max(Activity.start_date))
        return self.session.scalar(statement)

    def get_pending_detail_activities(
        self,
        limit: int = 25,
    ) -> list[Activity]:
        """Return activities missing details or segment enrichment."""

        if limit < 1:
            raise ValueError("limit must be at least 1.")

        statement = (
            select(Activity)
            .where(
                or_(
                    Activity.detail_loaded_at.is_(None),
                    Activity.segments_loaded_at.is_(None),
                )
            )
            .order_by(Activity.start_date.desc())
            .limit(limit)
        )

        return list(self.session.scalars(statement))

    def count_pending_details(self) -> int:
        """Return activities missing details or segment enrichment."""

        statement = (
            select(func.count(Activity.activity_id))
            .where(
                or_(
                    Activity.detail_loaded_at.is_(None),
                    Activity.segments_loaded_at.is_(None),
                )
            )
        )

        return int(self.session.scalar(statement) or 0)

    def commit(self) -> None:
        """Commit pending repository changes."""

        self.session.commit()

    def rollback(self) -> None:
        """Roll back pending repository changes."""

        self.session.rollback()

    @staticmethod
    def _update_existing(
        existing: Activity,
        incoming: Activity,
    ) -> bool:
        """Update an existing activity when values have changed."""

        fields = (
            "athlete_id",
            "name",
            "sport_type",
            "start_date",
            "distance_meters",
            "moving_time_seconds",
            "elapsed_time_seconds",
            "total_elevation_gain_meters",
            "average_speed_mps",
            "max_speed_mps",
            "average_heartrate",
            "average_watts",
            "kilojoules",
            "trainer",
            "commute",
            "gear_id",
        )

        changed = False

        for field in fields:
            incoming_value = getattr(incoming, field)
            existing_value = getattr(existing, field)

            if existing_value != incoming_value:
                setattr(existing, field, incoming_value)
                changed = True

        return changed
