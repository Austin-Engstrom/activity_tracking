"""Database access methods for Strava gear records."""

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.activity import Activity
from src.models.gear import Gear


class GearRepository:
    """Repository for querying and storing gear records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(
        self,
        gear_id: str,
    ) -> Gear | None:
        """Return one gear record by its Strava gear ID."""

        if not gear_id or not gear_id.strip():
            raise ValueError(
                "gear_id must be a non-empty string."
            )

        return self.session.get(
            Gear,
            gear_id.strip(),
        )

    def get_missing_gear_ids(self) -> list[str]:
        """Return activity gear IDs that are not yet in the gear table."""

        stored_gear_ids = select(Gear.gear_id)

        statement = (
            select(Activity.gear_id)
            .where(Activity.gear_id.is_not(None))
            .where(Activity.gear_id.not_in(stored_gear_ids))
            .distinct()
            .order_by(Activity.gear_id)
        )

        return list(
            self.session.scalars(statement).all()
        )

    def upsert(
        self,
        gear_data: dict[str, Any],
    ) -> tuple[Gear, bool]:
        """
        Insert or update one gear record.

        Returns the gear record and a Boolean indicating whether it
        was newly inserted.
        """

        gear_id = gear_data.get("gear_id")

        if not isinstance(gear_id, str) or not gear_id.strip():
            raise ValueError(
                "gear_data must contain a valid gear_id."
            )

        normalized_gear_id = gear_id.strip()
        existing_gear = self.session.get(
            Gear,
            normalized_gear_id,
        )

        if existing_gear is None:
            gear_record = Gear(**gear_data)
            self.session.add(gear_record)

            return gear_record, True

        for field_name, field_value in gear_data.items():
            if field_name in {"gear_id", "created_at"}:
                continue

            if hasattr(existing_gear, field_name):
                setattr(
                    existing_gear,
                    field_name,
                    field_value,
                )

        return existing_gear, False

    def upsert_many(
        self,
        gear_records: Iterable[dict[str, Any]],
    ) -> tuple[int, int]:
        """Insert or update multiple transformed gear records."""

        inserted = 0
        updated = 0

        try:
            for gear_data in gear_records:
                _, was_inserted = self.upsert(gear_data)

                if was_inserted:
                    inserted += 1
                else:
                    updated += 1

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return inserted, updated

    def count(self) -> int:
        """Return the number of gear records stored."""

        statement = select(Gear.gear_id)

        return len(
            self.session.scalars(statement).all()
        )