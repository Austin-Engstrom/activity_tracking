"""Review imported OSM trails and segment mappings."""

from sqlalchemy import func, select

from src.database.session import SessionLocal
from src.models.osm_trails import OsmTrail
from src.models.trail_segment_mapping import TrailSegmentMapping
from src.models.trail_systems import TrailSystem


def run() -> None:
    """Print trail-import and mapping coverage summaries."""

    with SessionLocal() as session:
        statement = (
            select(
                TrailSystem.trail_system_id,
                TrailSystem.name,
                func.count(
                    func.distinct(OsmTrail.osm_trail_id)
                ).label("osm_trails"),
                func.count(
                    func.distinct(
                        TrailSegmentMapping.segment_id
                    )
                ).label("mapped_segments"),
            )
            .outerjoin(
                OsmTrail,
                OsmTrail.trail_system_id
                == TrailSystem.trail_system_id,
            )
            .outerjoin(
                TrailSegmentMapping,
                TrailSegmentMapping.osm_trail_id
                == OsmTrail.osm_trail_id,
            )
            .group_by(
                TrailSystem.trail_system_id,
                TrailSystem.name,
            )
            .order_by(
                func.count(
                    func.distinct(OsmTrail.osm_trail_id)
                ).desc(),
                TrailSystem.name,
            )
        )

        rows = session.execute(statement).all()

    print()
    print("=" * 78)
    print("OFFICIAL TRAIL NETWORK VALIDATION")
    print("=" * 78)
    print(
        f"{'ID':>4}  "
        f"{'Trail System':<35}  "
        f"{'OSM Trails':>10}  "
        f"{'Mapped Segments':>15}"
    )
    print("-" * 78)

    for row in rows:
        print(
            f"{row.trail_system_id:>4}  "
            f"{row.name:<35}  "
            f"{row.osm_trails:>10}  "
            f"{row.mapped_segments:>15}"
        )

    print("=" * 78)


if __name__ == "__main__":
    run()
