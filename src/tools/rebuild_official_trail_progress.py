"""Rebuild official-trail progress."""

import src.models  # noqa: F401

from src.database import SessionLocal
from src.services.official_trail_progress_service import (
    OfficialTrailProgressService,
)


def run() -> None:
    """Rebuild progress for one trail system."""

    trail_system_id = int(input("Trail-system ID: ").strip())

    with SessionLocal() as session:
        updated = OfficialTrailProgressService(
            session
        ).rebuild_trail_system(trail_system_id)

    print(f"Rebuilt progress for {updated} official trail(s).")


if __name__ == "__main__":
    run()
