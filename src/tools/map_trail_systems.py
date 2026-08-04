"""Interactive utility for maintaining trail-system mappings."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.segment import Segment
from src.models.segment_trail_system import SegmentTrailSystem
from src.services.trail_system_service import TrailSystemService


def print_header(title: str) -> None:
    """Print a formatted section heading."""

    print()
    print("=" * 60)
    print(title.upper())
    print("=" * 60)


def prompt_optional(prompt_text: str) -> str | None:
    """Prompt for optional text and return None for blank input."""

    value = input(prompt_text).strip()

    return value or None


def get_unmapped_segments(
    session: Session,
) -> list[Segment]:
    """Return segments that have no trail-system mapping."""

    mapped_segment_ids = select(
        SegmentTrailSystem.segment_id
    )

    statement = (
        select(Segment)
        .where(
            Segment.segment_id.not_in(
                mapped_segment_ids
            )
        )
        .order_by(
            Segment.city,
            Segment.name,
        )
    )

    return list(session.scalars(statement))


def display_trail_systems(
    service: TrailSystemService,
) -> None:
    """Print all existing trail systems."""

    trail_systems = service.get_all_trail_systems()

    print_header("Trail Systems")

    if not trail_systems:
        print("No trail systems found.")
        return

    for trail_system in trail_systems:
        location_parts = [
            value
            for value in (
                trail_system.city,
                trail_system.state,
            )
            if value
        ]

        location = ", ".join(location_parts)

        print(
            f"{trail_system.trail_system_id}: "
            f"{trail_system.name}"
            f"{f' ({location})' if location else ''}"
        )


def create_trail_system(
    service: TrailSystemService,
) -> None:
    """Prompt the user to create a trail system."""

    print_header("Create Trail System")

    name = input("Trail-system name: ").strip()

    if not name:
        print("Trail-system name is required.")
        return

    city = prompt_optional("City: ")
    state = prompt_optional("State: ")
    country = input(
        "Country [United States]: "
    ).strip() or "United States"

    description = prompt_optional("Description: ")

    try:
        trail_system = service.create_trail_system(
            name=name,
            city=city,
            state=state,
            country=country,
            description=description,
        )

        print()
        print(
            f"Trail system ready: "
            f"{trail_system.trail_system_id} - "
            f"{trail_system.name}"
        )

    except Exception as exc:
        service.session.rollback()
        print(f"Unable to create trail system: {exc}")


def display_unmapped_segments(
    session: Session,
) -> list[Segment]:
    """Print and return all currently unmapped segments."""

    segments = get_unmapped_segments(session)

    print_header("Unmapped Segments")

    if not segments:
        print("All segments are currently mapped.")
        return []

    for index, segment in enumerate(
        segments,
        start=1,
    ):
        location_parts = [
            value
            for value in (
                segment.city,
                segment.state,
            )
            if value
        ]

        location = ", ".join(location_parts)
        distance_miles = (
            segment.distance_meters / 1609.344
            if segment.distance_meters
            else None
        )

        details = []

        if location:
            details.append(location)

        if distance_miles is not None:
            details.append(
                f"{distance_miles:.2f} mi"
            )

        detail_text = (
            f" — {' | '.join(details)}"
            if details
            else ""
        )

        print(
            f"{index:>3}. "
            f"{segment.name}"
            f"{detail_text}"
            f" [ID: {segment.segment_id}]"
        )

    return segments


def parse_segment_selections(
    selection_text: str,
    segment_count: int,
) -> list[int]:
    """Parse comma-separated indexes and index ranges."""

    selected_indexes: set[int] = set()

    for item in selection_text.split(","):
        item = item.strip()

        if not item:
            continue

        if "-" in item:
            start_text, end_text = item.split(
                "-",
                maxsplit=1,
            )

            start = int(start_text.strip())
            end = int(end_text.strip())

            if start > end:
                start, end = end, start

            selected_indexes.update(
                range(start, end + 1)
            )

        else:
            selected_indexes.add(int(item))

    invalid_indexes = [
        index
        for index in selected_indexes
        if index < 1 or index > segment_count
    ]

    if invalid_indexes:
        raise ValueError(
            "Selections outside the displayed range: "
            + ", ".join(
                str(index)
                for index in sorted(invalid_indexes)
            )
        )

    return sorted(selected_indexes)


def map_segments(
    session: Session,
    service: TrailSystemService,
) -> None:
    """Assign selected unmapped segments to a trail system."""

    trail_systems = service.get_all_trail_systems()

    if not trail_systems:
        print()
        print(
            "Create at least one trail system before "
            "mapping segments."
        )
        return

    display_trail_systems(service)

    trail_id_text = input(
        "\nTrail-system ID: "
    ).strip()

    try:
        trail_system_id = int(trail_id_text)
    except ValueError:
        print("Trail-system ID must be a number.")
        return

    trail_system = service.trail_repository.get_by_id(
        trail_system_id
    )

    if trail_system is None:
        print(
            f"Trail system {trail_system_id} "
            "does not exist."
        )
        return

    segments = display_unmapped_segments(session)

    if not segments:
        return

    print()
    print("Enter selections as:")
    print("  1,3,5")
    print("  1-5")
    print("  1,3-7,10")

    selection_text = input(
        "\nSegment selections: "
    ).strip()

    if not selection_text:
        print("No segments selected.")
        return

    try:
        selected_indexes = parse_segment_selections(
            selection_text,
            len(segments),
        )

        selected_segment_ids = [
            segments[index - 1].segment_id
            for index in selected_indexes
        ]

        inserted = service.assign_segments(
            trail_system_id=trail_system_id,
            segment_ids=selected_segment_ids,
            confidence=1.0,
            mapping_source="manual",
        )

        print()
        print(
            f"Mapped {inserted} segment(s) to "
            f"{trail_system.name}."
        )

    except ValueError as exc:
        print(f"Invalid selection: {exc}")

    except Exception as exc:
        session.rollback()
        print(f"Unable to map segments: {exc}")


def show_trail_segments(
    service: TrailSystemService,
) -> None:
    """Display all segments mapped to a selected trail system."""

    display_trail_systems(service)

    trail_id_text = input(
        "\nTrail-system ID: "
    ).strip()

    try:
        trail_system_id = int(trail_id_text)
    except ValueError:
        print("Trail-system ID must be a number.")
        return

    trail_system = service.trail_repository.get_by_id(
        trail_system_id
    )

    if trail_system is None:
        print(
            f"Trail system {trail_system_id} "
            "does not exist."
        )
        return

    mappings = service.get_segments_for_trail(
        trail_system_id
    )

    print_header(
        f"Segments at {trail_system.name}"
    )

    if not mappings:
        print("No segments are mapped to this trail system.")
        return

    for mapping in sorted(
        mappings,
        key=lambda item: item.segment.name.lower(),
    ):
        segment = mapping.segment

        distance_miles = (
            segment.distance_meters / 1609.344
            if segment.distance_meters
            else None
        )

        distance_text = (
            f" — {distance_miles:.2f} mi"
            if distance_miles is not None
            else ""
        )

        print(
            f"{segment.name}"
            f"{distance_text}"
            f" [ID: {segment.segment_id}]"
        )


def run_mapper() -> None:
    """Run the interactive trail-system mapper."""

    with SessionLocal() as session:
        service = TrailSystemService(session)

        while True:
            print_header("Trail System Mapper")

            print("1. List trail systems")
            print("2. Create trail system")
            print("3. Show unmapped segments")
            print("4. Map segments")
            print("5. Show mapped segments")
            print("6. Exit")

            choice = input(
                "\nSelect an option: "
            ).strip()

            if choice == "1":
                display_trail_systems(service)

            elif choice == "2":
                create_trail_system(service)

            elif choice == "3":
                display_unmapped_segments(session)

            elif choice == "4":
                map_segments(
                    session,
                    service,
                )

            elif choice == "5":
                show_trail_segments(service)

            elif choice == "6":
                print("\nExiting trail-system mapper.")
                break

            else:
                print("\nInvalid option. Choose 1 through 6.")

            input("\nPress Enter to continue...")


if __name__ == "__main__":
    run_mapper()