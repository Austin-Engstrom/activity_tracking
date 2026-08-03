"""Service for loading detailed Strava activity streams."""

from dataclasses import dataclass

from sqlalchemy import select

from src.api.client import (
    StravaApiError,
    StravaClient,
    StravaRateLimitError,
)
from src.etl.activity_stream_transformer import (
    ActivityStreamTransformationError,
    transform_activity_streams,
)
from src.models.activity import Activity
from src.repositories.activity_stream_repository import (
    ActivityStreamRepository,
)


DEFAULT_STREAM_TYPES = [
    "time",
    "latlng",
    "distance",
    "altitude",
    "velocity_smooth",
    "heartrate",
    "cadence",
    "watts",
    "temp",
    "moving",
    "grade_smooth",
]


@dataclass
class ActivityStreamLoadResult:
    """Summary of one activity-stream loading batch."""

    selected: int
    loaded: int
    rows_inserted: int
    empty: int
    failed: int
    remaining: int
    deferred: int
    rate_limit_reached: bool


class ActivityStreamService:
    """Load streams for activities that do not have stored stream rows."""

    def __init__(
        self,
        client: StravaClient,
        repository: ActivityStreamRepository,
    ) -> None:
        self.client = client
        self.repository = repository

    def run_batch(
        self,
        batch_size: int = 5,
        stream_types: list[str] | None = None,
    ) -> ActivityStreamLoadResult:
        """Load streams for a batch of activities."""

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be a positive integer."
            )

        requested_stream_types = (
            stream_types
            if stream_types is not None
            else DEFAULT_STREAM_TYPES
        )

        activity_ids = self._get_missing_activity_ids(
            limit=batch_size
        )

        selected = len(activity_ids)
        loaded = 0
        rows_inserted = 0
        empty = 0
        failed = 0
        deferred = 0
        rate_limit_reached = False

        for index, activity_id in enumerate(
            activity_ids,
            start=1,
        ):
            print(
                f"Loading streams {index}/{selected}: "
                f"{activity_id}"
            )

            try:
                raw_streams = self.client.get_activity_streams(
                    activity_id=activity_id,
                    stream_types=requested_stream_types,
                )

                transformed_rows = transform_activity_streams(
                    activity_id=activity_id,
                    raw_streams=raw_streams,
                )

                if not transformed_rows:
                    empty += 1
                    print(
                        f"No stream rows returned for "
                        f"activity {activity_id}."
                    )
                    continue

                inserted = self.repository.insert_many(
                    transformed_rows,
                    replace_existing=True,
                )

                loaded += 1
                rows_inserted += inserted

            except StravaRateLimitError:
                rate_limit_reached = True
                deferred = selected - index + 1
                break

            except (
                ActivityStreamTransformationError,
                StravaApiError,
                ValueError,
            ) as exc:
                failed += 1
                print(
                    f"Failed to load streams for "
                    f"{activity_id}: {exc}"
                )

            except Exception as exc:
                failed += 1
                print(
                    f"Unexpected stream error for "
                    f"{activity_id}: {exc}"
                )

        remaining = self._count_missing_activities()

        return ActivityStreamLoadResult(
            selected=selected,
            loaded=loaded,
            rows_inserted=rows_inserted,
            empty=empty,
            failed=failed,
            remaining=remaining,
            deferred=deferred,
            rate_limit_reached=rate_limit_reached,
        )

    def _get_missing_activity_ids(
        self,
        limit: int,
    ) -> list[int]:
        """Return activity IDs without stored stream rows."""

        session = self.repository.session

        stored_activity_ids = (
            select(
                self.repository.model.activity_id
            )
            .distinct()
        )

        statement = (
            select(Activity.activity_id)
            .where(
                Activity.activity_id.not_in(
                    stored_activity_ids
                )
            )
            .order_by(Activity.start_date.desc())
            .limit(limit)
        )

        return list(
            session.scalars(statement).all()
        )

    def _count_missing_activities(self) -> int:
        """Return the number of activities without streams."""

        session = self.repository.session

        stored_activity_ids = (
            select(
                self.repository.model.activity_id
            )
            .distinct()
        )

        statement = (
            select(Activity.activity_id)
            .where(
                Activity.activity_id.not_in(
                    stored_activity_ids
                )
            )
        )

        return len(
            session.scalars(statement).all()
        )