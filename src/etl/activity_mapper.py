"""Transform raw Strava API responses into Activity models."""

from datetime import datetime, timezone
from typing import Any

from src.models.activity import Activity


class ActivityMappingError(ValueError):
    """Raised when a Strava activity cannot be mapped."""


class ActivityMapper:
    """Maps Strava API activity data to SQLAlchemy models."""

    @staticmethod
    def parse_datetime(value: str | None) -> datetime:
        """Convert a Strava ISO-8601 timestamp into a naive UTC datetime."""

        if not value:
            raise ActivityMappingError(
                "Activity is missing a required start date."
            )

        try:
            parsed_datetime = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if parsed_datetime.tzinfo is not None:
                parsed_datetime = parsed_datetime.astimezone(
                    timezone.utc
                ).replace(tzinfo=None)

            return parsed_datetime

        except ValueError as exc:
            raise ActivityMappingError(
                f"Invalid Strava datetime value: {value}"
            ) from exc

    @classmethod
    def from_api(
        cls,
        activity_data: dict[str, Any],
    ) -> Activity:
        """Create an Activity model from a Strava API response."""

        athlete_data = activity_data.get("athlete") or {}

        activity_id = activity_data.get("id")
        athlete_id = athlete_data.get("id")
        name = activity_data.get("name")
        sport_type = (
            activity_data.get("sport_type")
            or activity_data.get("type")
        )
        start_date = activity_data.get("start_date")

        missing_fields = []

        if activity_id is None:
            missing_fields.append("id")

        if athlete_id is None:
            missing_fields.append("athlete.id")

        if not name:
            missing_fields.append("name")

        if not sport_type:
            missing_fields.append("sport_type")

        if not start_date:
            missing_fields.append("start_date")

        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ActivityMappingError(
                f"Activity is missing required fields: {missing}"
            )

        return Activity(
            activity_id=int(activity_id),
            athlete_id=int(athlete_id),
            name=str(name),
            sport_type=str(sport_type),
            start_date=cls.parse_datetime(str(start_date)),
            distance_meters=float(
                activity_data.get("distance") or 0.0
            ),
            moving_time_seconds=int(
                activity_data.get("moving_time") or 0
            ),
            elapsed_time_seconds=int(
                activity_data.get("elapsed_time") or 0
            ),
            total_elevation_gain_meters=float(
                activity_data.get("total_elevation_gain") or 0.0
            ),
            average_speed_mps=cls.optional_float(
                activity_data.get("average_speed")
            ),
            max_speed_mps=cls.optional_float(
                activity_data.get("max_speed")
            ),
            average_heartrate=cls.optional_float(
                activity_data.get("average_heartrate")
            ),
            average_watts=cls.optional_float(
                activity_data.get("average_watts")
            ),
            kilojoules=cls.optional_float(
                activity_data.get("kilojoules")
            ),
            trainer=bool(activity_data.get("trainer", False)),
            commute=bool(activity_data.get("commute", False)),
            gear_id=cls.optional_string(
                activity_data.get("gear_id")
            ),
        )
    @classmethod
    def apply_detail(
        cls,
        activity: Activity,
        detail_data: dict[str, Any],
    ) -> Activity:
        """Apply detailed Strava fields to an existing activity."""

        detail_activity_id = detail_data.get("id")

        if detail_activity_id is None:
            raise ActivityMappingError(
                "Detailed activity response is missing an ID."
            )

        if int(detail_activity_id) != activity.activity_id:
            raise ActivityMappingError(
                "Detailed activity ID does not match the stored activity."
            )

        activity.description = cls.optional_string(
            detail_data.get("description")
        )
        activity.calories = cls.optional_float(
            detail_data.get("calories")
        )
        activity.device_name = cls.optional_string(
            detail_data.get("device_name")
        )
        activity.workout_type = cls.optional_int(
            detail_data.get("workout_type")
        )
        activity.suffer_score = cls.optional_int(
            detail_data.get("suffer_score")
        )
        activity.average_cadence = cls.optional_float(
            detail_data.get("average_cadence")
        )
        activity.max_heartrate = cls.optional_float(
            detail_data.get("max_heartrate")
        )
        activity.has_heartrate = cls.optional_bool(
            detail_data.get("has_heartrate")
        )
        activity.detail_loaded_at = datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

        return activity

    @staticmethod
    def optional_float(value: Any) -> float | None:
        """Convert an optional API value to a float."""

        if value is None:
            return None

        return float(value)

    @staticmethod
    def optional_string(value: Any) -> str | None:
        """Convert an optional API value to a string."""

        if value is None:
            return None

        return str(value)
    
    @staticmethod
    def optional_int(value: Any) -> int | None:
        """Convert an optional API value to an integer."""

        if value is None:
            return None

        return int(value)

    @staticmethod
    def optional_bool(value: Any) -> bool | None:
        """Convert an optional API value to a boolean."""

        if value is None:
            return None

        return bool(value)