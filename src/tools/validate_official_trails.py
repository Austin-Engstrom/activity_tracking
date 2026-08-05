"""Validate normalized official trails."""

from sqlalchemy import func, select

import src.models  # noqa: F401

from src.database import SessionLocal
from src.models.official_trail import OfficialTrail
from src.models.osm_trails import OsmTrail
from src.models.trail_systems import TrailSystem


def run() -> None:
    """Print normalized trail summaries."""

    with SessionLocal() as session:
        statement = (
            select(
                TrailSystem.name.label(
                    "trail_system"
                ),
                OfficialTrail.name.label(
                    "official_trail"
                ),
                OfficialTrail.section_count,
                OfficialTrail.total_length_meters,
                OfficialTrail.primary_surface,
            )
            .join(
                OfficialTrail,
                OfficialTrail.trail_system_id
                == TrailSystem.trail_system_id,
            )
            .order_by(
                TrailSystem.name,
                OfficialTrail.name,
            )
        )

        rows = session.execute(statement).all()

    print()
    print("=" * 100)
    print("OFFICIAL TRAIL VALIDATION")
    print("=" * 100)
    print(
        f"{'Trail System':<25} "
        f"{'Official Trail':<35} "
        f"{'Sections':>8} "
        f"{'Miles':>8} "
        f"{'Surface':<15}"
    )
    print("-" * 100)

    for row in rows:
        miles = (
            row.total_length_meters / 1609.344
            if row.total_length_meters
            else 0.0
        )

        print(
            f"{row.trail_system:<25} "
            f"{row.official_trail:<35} "
            f"{row.section_count:>8} "
            f"{miles:>8.2f} "
            f"{(row.primary_surface or ''):<15}"
        )

    print("=" * 100)


if __name__ == "__main__":
    run()
