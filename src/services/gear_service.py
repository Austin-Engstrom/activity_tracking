"""Service for loading Strava gear details into the database."""

from dataclasses import dataclass

from src.api.client import (
    StravaClient,
    StravaRateLimitError,
)
from src.etl.gear_transformer import (
    GearTransformationError,
    transform_gear,
)
from src.repositories.gear_repository import GearRepository


@dataclass
class GearLoadResult:
    """Summary of one gear load run."""

    selected: int
    inserted: int
    updated: int
    failed: int
    remaining: int
    deferred: int
    rate_limit_reached: bool


class GearService:
    """Load missing Strava gear records into the database."""

    def __init__(
        self,
        client: StravaClient,
        repository: GearRepository,
        athlete_id: int,
    ) -> None:
        self.client = client
        self.repository = repository
        self.athlete_id = athlete_id

    def run(self) -> GearLoadResult:
        """Load all missing gear IDs found in activities."""

        missing_gear_ids = self.repository.get_missing_gear_ids()

        selected = len(missing_gear_ids)
        inserted = 0
        updated = 0
        failed = 0
        deferred = 0
        rate_limit_reached = False

        for index, gear_id in enumerate(
            missing_gear_ids,
            start=1,
        ):
            print(
                f"Loading gear {index}/{selected}: "
                f"{gear_id}"
            )

            try:
                raw_gear = self.client.get_gear(gear_id)

                transformed_gear = transform_gear(
                    raw_gear=raw_gear,
                    athlete_id=self.athlete_id,
                )

                _, was_inserted = self.repository.upsert(
                    transformed_gear
                )

                if was_inserted:
                    inserted += 1
                else:
                    updated += 1

            except StravaRateLimitError:
                rate_limit_reached = True
                deferred = selected - index + 1
                break

            except (
                GearTransformationError,
                ValueError,
            ) as exc:
                failed += 1
                print(
                    f"Failed to load gear {gear_id}: "
                    f"{exc}"
                )

            except Exception as exc:
                failed += 1
                print(
                    f"Unexpected error for gear "
                    f"{gear_id}: {exc}"
                )

        try:
            self.repository.session.commit()
        except Exception:
            self.repository.session.rollback()
            raise

        remaining = len(
            self.repository.get_missing_gear_ids()
        )

        return GearLoadResult(
            selected=selected,
            inserted=inserted,
            updated=updated,
            failed=failed,
            remaining=remaining,
            deferred=deferred,
            rate_limit_reached=rate_limit_reached,
        )