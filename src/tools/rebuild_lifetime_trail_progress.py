"""Rebuild lifetime trail coverage from historical GPS activity lines."""

import src.models  # noqa: F401

from sqlalchemy import func, select

from src.database import SessionLocal
from src.models.official_trail import OfficialTrail
from src.models.official_trail_activity_match import OfficialTrailActivityMatch
from src.models.trail_systems import TrailSystem
from src.services.official_trail_lifetime_progress_service import (
    OfficialTrailLifetimeProgressService,
)


def get_eligible_trail_systems(session) -> list[TrailSystem]:
    """Return systems with GPS-derived trail matches."""

    statement = (
        select(TrailSystem)
        .join(
            OfficialTrail,
            OfficialTrail.trail_system_id
            == TrailSystem.trail_system_id,
        )
        .join(
            OfficialTrailActivityMatch,
            OfficialTrailActivityMatch.official_trail_id
            == OfficialTrail.official_trail_id,
        )
        .group_by(
            TrailSystem.trail_system_id,
            TrailSystem.name,
        )
        .having(
            func.count(
                OfficialTrailActivityMatch
                .official_trail_activity_match_id
            ) > 0
        )
        .order_by(TrailSystem.name)
    )

    return list(session.scalars(statement))


def print_summary(summary) -> None:
    """Print one rebuild summary."""

    print()
    print("-" * 70)
    print(f"Trail-system ID:     {summary.trail_system_id}")
    print(f"Official trails:     {summary.official_trails}")
    print(f"Trails with matches: {summary.trails_with_matches}")
    print(f"Completed:           {summary.completed}")
    print(f"Nearly complete:     {summary.nearly_complete}")
    print(f"Partial:             {summary.partial}")
    print(f"Started:             {summary.started}")
    print(f"Unridden:            {summary.unridden}")


def run() -> None:
    """Run lifetime progress for one or all eligible systems."""

    with SessionLocal() as session:
        trail_systems = get_eligible_trail_systems(session)

        print()
        print("=" * 70)
        print("LIFETIME OFFICIAL TRAIL PROGRESS")
        print("=" * 70)

        if not trail_systems:
            print("No trail systems have GPS-derived trail matches.")
            return

        print("1. Rebuild one trail system")
        print("2. Rebuild all eligible trail systems")
        print("3. Exit")

        choice = input("\nSelect an option: ").strip()

        service = OfficialTrailLifetimeProgressService(
            session,
            tolerance_meters=12.0,
        )

        if choice == "1":
            for trail_system in trail_systems:
                print(
                    f"{trail_system.trail_system_id}: "
                    f"{trail_system.name}"
                )

            try:
                trail_system_id = int(
                    input("\nTrail-system ID: ").strip()
                )
            except ValueError:
                print("Trail-system ID must be numeric.")
                return

            valid_ids = {
                item.trail_system_id
                for item in trail_systems
            }

            if trail_system_id not in valid_ids:
                print("Choose a system with GPS trail matches.")
                return

            print_summary(
                service.rebuild_trail_system(
                    trail_system_id
                )
            )

        elif choice == "2":
            confirmation = input(
                f"Rebuild {len(trail_systems)} "
                "trail system(s)? [y/N]: "
            ).strip().lower()

            if confirmation not in {"y", "yes"}:
                print("Lifetime progress rebuild canceled.")
                return

            successful = 0
            failed = 0

            for index, trail_system in enumerate(
                trail_systems,
                start=1,
            ):
                print()
                print("=" * 70)
                print(
                    f"[{index}/{len(trail_systems)}] "
                    f"{trail_system.name}"
                )
                print("=" * 70)

                try:
                    print_summary(
                        service.rebuild_trail_system(
                            trail_system.trail_system_id
                        )
                    )
                    successful += 1

                except Exception as exc:
                    session.rollback()
                    print(
                        f"Rebuild failed for "
                        f"{trail_system.name}: {exc}"
                    )
                    failed += 1

            print()
            print("=" * 70)
            print("LIFETIME PROGRESS BATCH SUMMARY")
            print("=" * 70)
            print(f"Selected:   {len(trail_systems)}")
            print(f"Successful: {successful}")
            print(f"Failed:     {failed}")
            print("=" * 70)

        elif choice == "3":
            print("Exiting lifetime progress rebuild.")

        else:
            print("Choose option 1, 2, or 3.")


if __name__ == "__main__":
    run()
