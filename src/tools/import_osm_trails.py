"""Interactive OSM trail importer."""

import os
from pathlib import Path

from src.api.overpass_client import OverpassClient
from src.database import SessionLocal
from src.services.osm_trail_import_service import (
    OsmTrailImportService,
)
from src.services.trail_system_service import TrailSystemService


DEFAULT_USER_AGENT = (
    "activity_tracking_strava_analytics/1.0 "
    "(personal trail analytics project)"
)


def run() -> None:
    """Import OSM ways for one confirmed trail system."""

    with SessionLocal() as session:
        trail_service = TrailSystemService(session)
        trail_systems = [
            trail
            for trail in trail_service.get_all_trail_systems()
            if trail.boundary_confirmed
            and trail.boundary_geojson
        ]

        print()
        print("=" * 70)
        print("OSM TRAIL IMPORTER")
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

        delete_missing = input(
            "Delete previously imported missing ways? [y/N]: "
        ).strip().lower() in {"y", "yes"}

        client = OverpassClient(
            user_agent=os.getenv(
                "OSM_USER_AGENT",
                DEFAULT_USER_AGENT,
            )
        )

        service = OsmTrailImportService(
            session,
            client,
            cache_directory=Path("data/osm/cache"),
        )

        try:
            summary = service.import_trail_system(
                trail_system_id,
                delete_missing=delete_missing,
            )
        except Exception as exc:
            print(f"Import failed: {exc}")
            return

    print()
    print("=" * 70)
    print("OSM TRAIL IMPORT SUMMARY")
    print("=" * 70)
    print(f"Trail system:      {summary.trail_system_name}")
    print(f"Endpoint:          {summary.endpoint}")
    print(f"Returned elements: {summary.returned_elements}")
    print(f"Accepted ways:     {summary.accepted_ways}")
    print(f"Inserted:          {summary.inserted}")
    print(f"Updated:           {summary.updated}")
    print(f"Deleted:           {summary.deleted}")
    print(f"Unnamed:           {summary.unnamed}")
    print(f"Raw cache:         {summary.cache_path}")
    print("=" * 70)


if __name__ == "__main__":
    run()
