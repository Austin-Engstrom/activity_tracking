"""Display official-trail GPS progress results."""

import src.models  # noqa: F401

from sqlalchemy import select

from src.database import SessionLocal
from src.models.official_trail import OfficialTrail
from src.models.official_trail_progress import OfficialTrailProgress
from src.models.trail_systems import TrailSystem


def run() -> None:
    """Print official-trail progress rows."""

    with SessionLocal() as session:
        statement = (
            select(
                TrailSystem.name.label("trail_system"),
                OfficialTrail.name.label("official_trail"),
                OfficialTrail.total_length_meters,
                OfficialTrailProgress.activity_count,
                OfficialTrailProgress.estimated_coverage_percent,
                OfficialTrailProgress.total_ridden_distance_meters,
                OfficialTrailProgress.last_ridden_at,
                OfficialTrailProgress.progress_status,
            )
            .join(
                OfficialTrail,
                OfficialTrail.trail_system_id
                == TrailSystem.trail_system_id,
            )
            .outerjoin(
                OfficialTrailProgress,
                OfficialTrailProgress.official_trail_id
                == OfficialTrail.official_trail_id,
            )
            .order_by(
                TrailSystem.name,
                OfficialTrail.name,
            )
        )

        rows = session.execute(statement).all()

    print()
    print("=" * 130)
    print("OFFICIAL TRAIL PROGRESS")
    print("=" * 130)
    print(
        f"{'Trail System':<24} "
        f"{'Official Trail':<34} "
        f"{'Miles':>7} "
        f"{'Rides':>7} "
        f"{'Coverage':>10} "
        f"{'Status':<10} "
        f"{'Last Ridden':<20}"
    )
    print("-" * 130)

    for row in rows:
        miles = (
            row.total_length_meters / 1609.344
            if row.total_length_meters
            else 0.0
        )

        coverage = (
            row.estimated_coverage_percent
            if row.estimated_coverage_percent is not None
            else 0.0
        )

        rides = row.activity_count or 0
        status = row.progress_status or "unridden"

        last_ridden = (
            str(row.last_ridden_at)
            if row.last_ridden_at
            else ""
        )

        print(
            f"{row.trail_system:<24} "
            f"{row.official_trail:<34} "
            f"{miles:>7.2f} "
            f"{rides:>7} "
            f"{coverage:>9.1f}% "
            f"{status:<10} "
            f"{last_ridden:<20}"
        )

    print("=" * 130)


if __name__ == "__main__":
    run()