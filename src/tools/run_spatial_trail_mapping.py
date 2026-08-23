"""Run polygon-based mapping for unmapped Strava segments."""

from src.database import SessionLocal
from src.services.spatial_trail_mapping_service import (
    SpatialTrailMappingService,
)


def run() -> None:
    """Execute spatial mapping and print a detailed summary."""

    with SessionLocal() as session:
        summary = SpatialTrailMappingService(session).run()

    mapped_this_run = summary.mapped

    total_mapped = (
        summary.already_mapped
        + mapped_this_run
    )

    mapped_pct = (
        (total_mapped / summary.total_segments) * 100
        if summary.total_segments
        else 0
    )

    run_match_pct = (
        (mapped_this_run / summary.evaluated) * 100
        if summary.evaluated
        else 0
    )

    print()
    print("=" * 60)
    print("SPATIAL TRAIL MAPPING SUMMARY")
    print("=" * 60)

    print(
        f"Trail systems with boundaries: "
        f"{summary.trail_systems_with_boundaries}"
    )

    print()
    print("SEGMENTS")
    print("-" * 60)
    print(
        f"Total segments:                "
        f"{summary.total_segments}"
    )
    print(
        f"Already mapped:                "
        f"{summary.already_mapped}"
    )
    print(
        f"Evaluated this run:             "
        f"{summary.evaluated}"
    )

    print()
    print("NEW MAPPINGS")
    print("-" * 60)
    print(
        f"Mapped by polygon:             "
        f"{mapped_this_run}"
    )
    print(
        f"Match rate this run:           "
        f"{run_match_pct:.2f}%"
    )

    print()
    print("OVERALL")
    print("-" * 60)
    print(
        f"Total mapped:                  "
        f"{total_mapped}"
    )
    print(
        f"Total mapped percent:          "
        f"{mapped_pct:.2f}%"
    )
    print(
        f"Still unmatched:               "
        f"{summary.unmatched}"
    )

    print("=" * 60)


if __name__ == "__main__":
    run()