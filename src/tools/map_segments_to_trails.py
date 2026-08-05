"""Map Strava segments to imported OSM trail lines."""

from src.database.session import SessionLocal
from src.services.trail_segment_mapping_service import (
    TrailSegmentMappingService,
)
from src.services.trail_system_service import TrailSystemService


def run() -> None:
    """Run one interactive trail-to-segment mapping batch."""

    with SessionLocal() as session:
        trail_service = TrailSystemService(session)
        trail_systems = trail_service.get_all_trail_systems()

        print()
        print("=" * 70)
        print("TRAIL-TO-SEGMENT MAPPER")
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

        service = TrailSegmentMappingService(session)

        try:
            summary = service.map_trail_system(
                trail_system_id,
                replace_unvalidated=True,
            )
        except Exception as exc:
            print(f"Mapping failed: {exc}")
            return

    print()
    print("=" * 70)
    print("TRAIL-TO-SEGMENT MAPPING SUMMARY")
    print("=" * 70)
    print(f"Trail-system ID:    {summary.trail_system_id}")
    print(f"OSM trails:         {summary.osm_trails}")
    print(f"Candidate segments: {summary.candidate_segments}")
    print(f"Pairs evaluated:    {summary.evaluated_pairs}")
    print(f"Inserted:           {summary.inserted}")
    print(f"Updated:            {summary.updated}")
    print(
        f"Unmatched segments: "
        f"{summary.unmatched_segments}"
    )
    print("=" * 70)


if __name__ == "__main__":
    run()
