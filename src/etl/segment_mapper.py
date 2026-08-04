"""Transform Strava segment and segment-effort data into models."""

from typing import Any

from src.etl.activity_mapper import ActivityMapper
from src.models.segment import Segment
from src.models.segment_effort import SegmentEffort


class SegmentMappingError(ValueError):
    """Raised when segment data cannot be mapped."""


class SegmentMapper:
    """Maps nested Strava segment data to SQLAlchemy models."""

    @classmethod
    def segment_from_effort(
        cls,
        effort_data: dict[str, Any],
    ) -> Segment:
        """Create a Segment model from a segment-effort payload."""

        segment_data = effort_data.get("segment") or {}
        segment_id = segment_data.get("id")
        name = segment_data.get("name")

        if segment_id is None:
            raise SegmentMappingError(
                "Segment effort is missing segment.id."
            )

        if not name:
            raise SegmentMappingError(
                f"Segment {segment_id} is missing a name."
            )

        start_latlng = segment_data.get("start_latlng") or []
        end_latlng = segment_data.get("end_latlng") or []

        start_latitude, start_longitude = cls._parse_latlng(
            start_latlng
        )
        end_latitude, end_longitude = cls._parse_latlng(
            end_latlng
        )

        return Segment(
            segment_id=int(segment_id),
            name=str(name),
            activity_type=ActivityMapper.optional_string(
                segment_data.get("activity_type")
            ),
            distance_meters=ActivityMapper.optional_float(
                segment_data.get("distance")
            ),
            average_grade=ActivityMapper.optional_float(
                segment_data.get("average_grade")
            ),
            maximum_grade=ActivityMapper.optional_float(
                segment_data.get("maximum_grade")
            ),
            elevation_high_meters=ActivityMapper.optional_float(
                segment_data.get("elevation_high")
            ),
            elevation_low_meters=ActivityMapper.optional_float(
                segment_data.get("elevation_low")
            ),
            start_latitude=start_latitude,
            start_longitude=start_longitude,
            end_latitude=end_latitude,
            end_longitude=end_longitude,
            climb_category=ActivityMapper.optional_int(
                segment_data.get("climb_category")
            ),
            city=ActivityMapper.optional_string(
                segment_data.get("city")
            ),
            state=ActivityMapper.optional_string(
                segment_data.get("state")
            ),
            country=ActivityMapper.optional_string(
                segment_data.get("country")
            ),
            private=ActivityMapper.optional_bool(
                segment_data.get("private")
            ),
            hazardous=ActivityMapper.optional_bool(
                segment_data.get("hazardous")
            ),
            starred=ActivityMapper.optional_bool(
                segment_data.get("starred")
            ),
            effort_count=ActivityMapper.optional_int(
                segment_data.get("effort_count")
            ),
            athlete_count=ActivityMapper.optional_int(
                segment_data.get("athlete_count")
            ),
            star_count=ActivityMapper.optional_int(
                segment_data.get("star_count")
            ),
        )

    @classmethod
    def effort_from_api(
        cls,
        activity_id: int,
        effort_data: dict[str, Any],
    ) -> SegmentEffort:
        """Create a SegmentEffort model from a Strava payload."""

        effort_id = effort_data.get("id")
        segment_data = effort_data.get("segment") or {}
        segment_id = segment_data.get("id")
        name = effort_data.get("name") or segment_data.get("name")
        start_date = effort_data.get("start_date")

        missing_fields = []

        if effort_id is None:
            missing_fields.append("id")

        if segment_id is None:
            missing_fields.append("segment.id")

        if not name:
            missing_fields.append("name")

        if not start_date:
            missing_fields.append("start_date")

        if missing_fields:
            raise SegmentMappingError(
                "Segment effort is missing required fields: "
                + ", ".join(missing_fields)
            )

        start_date_local_raw = effort_data.get("start_date_local")

        return SegmentEffort(
            segment_effort_id=int(effort_id),
            activity_id=int(activity_id),
            segment_id=int(segment_id),
            name=str(name),
            elapsed_time_seconds=int(
                effort_data.get("elapsed_time") or 0
            ),
            moving_time_seconds=int(
                effort_data.get("moving_time") or 0
            ),
            start_date=ActivityMapper.parse_datetime(
                str(start_date)
            ),
            start_date_local=(
                ActivityMapper.parse_datetime(
                    str(start_date_local_raw)
                )
                if start_date_local_raw
                else None
            ),
            distance_meters=ActivityMapper.optional_float(
                effort_data.get("distance")
            ),
            start_index=ActivityMapper.optional_int(
                effort_data.get("start_index")
            ),
            end_index=ActivityMapper.optional_int(
                effort_data.get("end_index")
            ),
            average_cadence=ActivityMapper.optional_float(
                effort_data.get("average_cadence")
            ),
            average_watts=ActivityMapper.optional_float(
                effort_data.get("average_watts")
            ),
            device_watts=ActivityMapper.optional_bool(
                effort_data.get("device_watts")
            ),
            average_heartrate=ActivityMapper.optional_float(
                effort_data.get("average_heartrate")
            ),
            max_heartrate=ActivityMapper.optional_float(
                effort_data.get("max_heartrate")
            ),
            kom_rank=ActivityMapper.optional_int(
                effort_data.get("kom_rank")
            ),
            pr_rank=ActivityMapper.optional_int(
                effort_data.get("pr_rank")
            ),
            hidden=ActivityMapper.optional_bool(
                effort_data.get("hidden")
            ),
        )

    @staticmethod
    def _parse_latlng(
        value: list[Any],
    ) -> tuple[float | None, float | None]:
        """Convert a Strava latitude/longitude array."""

        if len(value) < 2:
            return None, None

        return float(value[0]), float(value[1])
