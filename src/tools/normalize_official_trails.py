"""Normalize imported OSM ways into official trails."""

import src.models  # noqa: F401

from sqlalchemy import func, select

from src.database.session import SessionLocal
from src.models.osm_trails import OsmTrail
from src.models.trail_systems import TrailSystem
from src.services.official_trail_normalization_service import (
    OfficialTrailNormalizationService,
)


def get_eligible_trail_systems(
    session,
) -> list[TrailSystem]:
    """Return trail systems that have imported OSM trail sections."""

    statement = (
        select(TrailSystem)
        .join(
            OsmTrail,
            OsmTrail.trail_system_id
            == TrailSystem.trail_system_id,
        )
        .group_by(
            TrailSystem.trail_system_id,
            TrailSystem.name,
        )
        .having(
            func.count(OsmTrail.osm_trail_id) > 0
        )
        .order_by(TrailSystem.name)
    )

    return list(session.scalars(statement))


def print_summary(summary) -> None:
    """Print one normalization summary."""

    print()
    print("-" * 70)
    print(
        f"Trail-system ID:            "
        f"{summary.trail_system_id}"
    )
    print(
        f"Imported sections:          "
        f"{summary.imported_sections}"
    )
    print(
        f"Named sections:             "
        f"{summary.named_sections}"
    )
    print(
        f"Unnamed sections:           "
        f"{summary.unnamed_sections}"
    )
    print(
        f"Official trails:            "
        f"{summary.official_trails}"
    )
    print(
        f"Created:                    "
        f"{summary.created}"
    )
    print(
        f"Updated:                    "
        f"{summary.updated}"
    )
    print(
        f"Unassigned unnamed sections: "
        f"{summary.orphaned_unnamed_sections}"
    )
    print(
        f"Deleted empty trails:       "
        f"{summary.deleted_empty}"
    )


def normalize_one(
    service: OfficialTrailNormalizationService,
    trail_systems: list[TrailSystem],
) -> None:
    """Normalize one selected trail system."""

    print()
    print("Trail systems with imported OSM trails")
    print("-" * 70)

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
        trail_system.trail_system_id
        for trail_system in trail_systems
    }

    if trail_system_id not in valid_ids:
        print(
            "Choose a trail system with imported "
            "OSM trail sections."
        )
        return

    summary = service.normalize_trail_system(
        trail_system_id
    )

    print_summary(summary)


def normalize_all(
    service: OfficialTrailNormalizationService,
    trail_systems: list[TrailSystem],
) -> None:
    """Normalize every trail system with imported OSM trails."""

    print()
    print(
        f"This will normalize {len(trail_systems)} "
        "trail system(s)."
    )

    confirmation = input(
        "Continue? [y/N]: "
    ).strip().lower()

    if confirmation not in {"y", "yes"}:
        print("Normalization canceled.")
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
            summary = service.normalize_trail_system(
                trail_system.trail_system_id
            )

            print_summary(summary)
            successful += 1

        except Exception as exc:
            service.session.rollback()

            print(
                f"Normalization failed for "
                f"{trail_system.name}: {exc}"
            )

            failed += 1

    print()
    print("=" * 70)
    print("NORMALIZATION BATCH SUMMARY")
    print("=" * 70)
    print(f"Selected:   {len(trail_systems)}")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print("=" * 70)


def run() -> None:
    """Run the official-trail normalization utility."""

    with SessionLocal() as session:
        trail_systems = get_eligible_trail_systems(
            session
        )

        print()
        print("=" * 70)
        print("OFFICIAL TRAIL NORMALIZER")
        print("=" * 70)

        if not trail_systems:
            print(
                "No trail systems have imported "
                "OSM trail sections."
            )
            return

        print("1. Normalize one trail system")
        print("2. Normalize all eligible trail systems")
        print("3. Exit")

        choice = input(
            "\nSelect an option: "
        ).strip()

        service = OfficialTrailNormalizationService(
            session
        )

        if choice == "1":
            normalize_one(
                service,
                trail_systems,
            )

        elif choice == "2":
            normalize_all(
                service,
                trail_systems,
            )

        elif choice == "3":
            print("Exiting official trail normalizer.")

        else:
            print("Choose option 1, 2, or 3.")


if __name__ == "__main__":
    run()