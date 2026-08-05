"""Run automatic trail-system mapping rules."""

# Update this import only if your project uses a different session module.
from src.database import SessionLocal
from src.services.trail_mapping_service import TrailMappingService


def run() -> None:
    """Execute automatic trail mapping and print a summary."""

    with SessionLocal() as session:
        service = TrailMappingService(session)
        summary = service.run()

    print()
    print("=" * 50)
    print("TRAIL MAPPING SUMMARY")
    print("=" * 50)
    print(f"Total segments:       {summary.total_segments}")
    print(f"Already mapped:       {summary.already_mapped}")
    print(f"Evaluated:            {summary.evaluated}")
    print(f"Mapped automatically: {summary.mapped}")
    print(f"Still unmatched:      {summary.unmatched}")
    print(f"Coverage:             {summary.coverage_percent:.1f}%")
    print("=" * 50)


if __name__ == "__main__":
    run()
