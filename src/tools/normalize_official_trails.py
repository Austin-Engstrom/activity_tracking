"""Normalize imported OSM ways into official trails."""

from src.database.session import SessionLocal
from src.services.official_trail_normalization_service import (
    OfficialTrailNormalizationService,
)
from src.services.trail_system_service import TrailSystemService


def run() -> None:
    """Run normalization for one trail system."""

    with SessionLocal() as session:
        trail_service = TrailSystemService(session)
        trail_systems = trail_service.get_all_trail_systems()

        print()
        print("=" * 70)
        print("OFFICIAL TRAIL NORMALIZER")
        print("=" * 70)

        for trail in trail_systems:
            print(
                f"{trail.trail_system_id}: "
                f"{trail.name}"
            )

        try:
            trail_system_id = int(
                input("\nTrail-system ID: ").strip()
            )
        except ValueError:
            print("Trail-system ID must be numeric.")
            return

        service = OfficialTrailNormalizationService(
            session
        )

        try:
            summary = service.normalize_trail_system(
                trail_system_id
            )
        except Exception as exc:
            print(f"Normalization failed: {exc}")
            return

    print()
    print("=" * 70)
    print("OFFICIAL TRAIL NORMALIZATION SUMMARY")
    print("=" * 70)
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
        f"Unassigned unnamed sections:"
        f" {summary.orphaned_unnamed_sections}"
    )
    print(
        f"Deleted empty trails:       "
        f"{summary.deleted_empty}"
    )
    print("=" * 70)


if __name__ == "__main__":
    run()
