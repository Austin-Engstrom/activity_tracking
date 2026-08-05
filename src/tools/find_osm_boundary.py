"""Interactively discover and confirm OSM trail-system boundaries."""

import json
import os
from datetime import datetime

from src.database import SessionLocal
from src.services.osm_boundary_service import (
    OsmBoundaryCandidate,
    OsmBoundaryService,
)
from src.services.trail_system_service import TrailSystemService


DEFAULT_USER_AGENT = (
    "activity_tracking_strava_analytics/1.0 "
    "(personal trail analytics project)"
)


def print_header(title: str) -> None:
    """Print a formatted heading."""

    print()
    print("=" * 70)
    print(title.upper())
    print("=" * 70)


def display_candidates(
    candidates: list[OsmBoundaryCandidate],
) -> None:
    """Display search results and boundary usability."""

    print_header("OpenStreetMap Search Results")

    if not candidates:
        print("No results found.")
        return

    for index, candidate in enumerate(candidates, start=1):
        status = (
            "USABLE BOUNDARY"
            if candidate.usable_boundary
            else "not polygonal"
        )

        print(f"{index}. {candidate.display_name}")
        print(
            f"   OSM: {candidate.osm_type} "
            f"{candidate.osm_id}"
        )
        print(
            f"   Classification: "
            f"{candidate.category or 'unknown'} / "
            f"{candidate.feature_type or 'unknown'}"
        )
        print(
            f"   Geometry: "
            f"{candidate.geometry_type or 'none'} "
            f"({status})"
        )
        print()


def select_candidate(
    candidates: list[OsmBoundaryCandidate],
) -> OsmBoundaryCandidate | None:
    """Prompt for a usable candidate."""

    while True:
        choice = input(
            "Select a result number, R to search again, "
            "or Q to quit: "
        ).strip().lower()

        if choice == "r":
            return None

        if choice == "q":
            raise KeyboardInterrupt

        try:
            index = int(choice)
        except ValueError:
            print("Enter a result number, R, or Q.")
            continue

        if index < 1 or index > len(candidates):
            print("That result is outside the displayed range.")
            continue

        candidate = candidates[index - 1]

        if not candidate.usable_boundary:
            print(
                "That result is not a Polygon or MultiPolygon "
                "and cannot be saved as a boundary."
            )
            continue

        return candidate


def run() -> None:
    """Run the confirmed OSM boundary workflow."""

    osm_service = OsmBoundaryService(
        user_agent=os.getenv(
            "OSM_USER_AGENT",
            DEFAULT_USER_AGENT,
        ),
        contact_email=os.getenv("OSM_CONTACT_EMAIL"),
    )

    with SessionLocal() as session:
        trail_service = TrailSystemService(session)
        trail_systems = trail_service.get_all_trail_systems()

        print_header("Trail Systems")

        for trail in trail_systems:
            status = (
                "boundary saved"
                if trail.boundary_geojson
                else "missing boundary"
            )
            print(
                f"{trail.trail_system_id}: "
                f"{trail.name} [{status}]"
            )

        trail_id = int(
            input("\nTrail-system ID: ").strip()
        )

        trail = trail_service.trail_repository.get_by_id(
            trail_id
        )

        if trail is None:
            print("Trail system not found.")
            return

        default_query = " ".join(
            value
            for value in (
                trail.name,
                trail.city,
                trail.state,
            )
            if value
        )

        search_text = default_query

        try:
            while True:
                entered = input(
                    f"\nOSM search [{search_text}]: "
                ).strip()

                if entered:
                    search_text = entered

                candidates = osm_service.search(search_text)
                display_candidates(candidates)

                if not candidates:
                    continue

                candidate = select_candidate(candidates)

                if candidate is None:
                    continue

                print_header("Confirm Boundary")
                print(f"Trail system: {trail.name}")
                print(f"OSM result:   {candidate.display_name}")
                print(
                    f"OSM object:   {candidate.osm_type} "
                    f"{candidate.osm_id}"
                )
                print(f"Geometry:     {candidate.geometry_type}")

                confirm = input(
                    "\nSave this confirmed boundary? [y/N]: "
                ).strip().lower()

                if confirm not in {"y", "yes"}:
                    print("Boundary was not saved.")
                    continue

                if trail.boundary_geojson:
                    replace = input(
                        "A boundary already exists. Replace it? [y/N]: "
                    ).strip().lower()

                    if replace not in {"y", "yes"}:
                        print("Existing boundary preserved.")
                        return

                trail.osm_element_type = candidate.osm_type
                trail.osm_element_id = candidate.osm_id
                trail.osm_display_name = candidate.display_name
                trail.boundary_geojson = json.dumps(
                    candidate.geojson,
                    separators=(",", ":"),
                )
                trail.boundary_source = "OpenStreetMap Nominatim"
                trail.boundary_confirmed = True
                trail.boundary_updated_at = datetime.utcnow()

                session.commit()

                print(
                    f"Saved confirmed OSM boundary for "
                    f"{trail.name}."
                )
                return

        except KeyboardInterrupt:
            print("\nBoundary finder exited.")


if __name__ == "__main__":
    run()
