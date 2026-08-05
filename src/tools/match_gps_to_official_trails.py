"""Run GPS-to-official-trail matching."""

import src.models  # noqa: F401

from src.database import SessionLocal
from src.services.official_trail_gps_match_service import (
    OfficialTrailGpsMatchService,
)


def run() -> None:
    """Run a GPS matching batch."""

    trail_system_id = int(input("Trail-system ID: ").strip())
    batch_text = input("Activity batch size [all]: ").strip()
    batch_size = int(batch_text) if batch_text else None

    with SessionLocal() as session:
        summary = OfficialTrailGpsMatchService(
            session,
            tolerance_meters=12.0,
            minimum_matched_trail_meters=20.0,
            minimum_coverage_percent=2.0,
        ).match_trail_system(
            trail_system_id,
            batch_size=batch_size,
        )

    print()
    print("=" * 60)
    print("GPS TRAIL MATCH SUMMARY")
    print("=" * 60)
    print(f"Official trails:      {summary.official_trails}")
    print(f"Candidate activities: {summary.candidate_activities}")
    print(f"Processed activities: {summary.processed_activities}")
    print(f"Matched activities:   {summary.matched_activities}")
    print(f"Inserted matches:     {summary.inserted_matches}")
    print("=" * 60)


if __name__ == "__main__":
    run()
