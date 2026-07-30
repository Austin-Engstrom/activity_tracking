"""Repository for storing and querying Strava activities."""

from dataclasses import dataclass

from sqlalchemy import func, select
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

    def get_latest_start_date(self):
        """Return the newest stored activity start date."""

        statement = select(func.max(Activity.start_date))
        return self.session.scalar(statement)

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