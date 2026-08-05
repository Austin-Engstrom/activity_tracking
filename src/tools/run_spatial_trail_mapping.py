"""Run polygon-based mapping for unmapped Strava segments."""

from src.database import SessionLocal
from src.services.spatial_trail_mapping_service import (
    SpatialTrailMappingService,
)


def run() -> None:
    """Execute spatial mapping and print a summary."""

    with SessionLocal() as session:
        summary = SpatialTrailMappingService(session).run()

    print()
    print("=" * 60)
    print("SPATIAL TRAIL MAPPING SUMMARY")
    print("=" * 60)
    print(
        f"Trail systems with boundaries: "
        f"{summary.trail_systems_with_boundaries}"
    )
    print(f"Total segments:                {summary.total_segments}")
    print(f"Already mapped:                {summary.already_mapped}")
    print(f"Evaluated:                     {summary.evaluated}")
    print(f"Mapped by OSM polygon:         {summary.mapped}")
    print(f"Still unmatched:               {summary.unmatched}")
    print("=" * 60)


if __name__ == "__main__":
    run()
