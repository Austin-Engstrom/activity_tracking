"""
Import manually drawn GeoJSON boundaries into trail_systems.

Expected directory:
    data/boundaries/manual/

Example filenames:
    blue_river_park.geojson
    back_40.geojson
    little_sugar.geojson

Run from project root:
    python -m src.cli.import_manual_boundaries
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "strava_analytics.db"
)

BOUNDARY_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "manual"
)


def normalize_name(value: str) -> str:
    """
    Normalize a trail-system name or filename for matching.

    Example:
        "Blue River Park" -> "blueriverpark"
        "blue_river_park.geojson" -> "blueriverpark"
    """
    value = Path(value).stem
    return re.sub(r"[^a-z0-9]", "", value.lower())


def get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    rows = connection.execute(
        f"pragma table_info({table_name});"
    ).fetchall()

    return {row[1] for row in rows}


def get_unmapped_trail_systems(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """
    Return trail systems that do not currently have a confirmed boundary.
    """
    query = """
        select
            trail_system_id,
            name,
            city,
            state,
            boundary_geojson,
            boundary_confirmed
        from trail_systems
        where
            boundary_geojson is null
            or trim(boundary_geojson) = ''
            or coalesce(boundary_confirmed, 0) = 0
        order by
            state,
            city,
            name;
    """

    return connection.execute(query).fetchall()


def extract_geometry(data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract a Polygon or MultiPolygon geometry from common GeoJSON formats.

    Supports:
        Polygon
        MultiPolygon
        Feature
        FeatureCollection
    """
    geojson_type = data.get("type")

    if geojson_type in {"Polygon", "MultiPolygon"}:
        geometry = data

    elif geojson_type == "Feature":
        geometry = data.get("geometry")

    elif geojson_type == "FeatureCollection":
        features = data.get("features", [])

        if len(features) != 1:
            raise ValueError(
                "FeatureCollection must contain exactly one feature."
            )

        geometry = features[0].get("geometry")

    else:
        raise ValueError(
            f"Unsupported GeoJSON type: {geojson_type}"
        )

    if not geometry:
        raise ValueError("GeoJSON does not contain a geometry.")

    geometry_type = geometry.get("type")

    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(
            "Boundary must be a Polygon or MultiPolygon. "
            f"Found: {geometry_type}"
        )

    coordinates = geometry.get("coordinates")

    if not coordinates:
        raise ValueError(
            "GeoJSON geometry does not contain coordinates."
        )

    return geometry


def load_geojson(file_path: Path) -> dict[str, Any]:
    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return extract_geometry(data)


def find_automatic_match(
    file_path: Path,
    trail_systems: list[sqlite3.Row],
) -> sqlite3.Row | None:
    """
    Match filename to trail-system name.

    Example:
        blue_river_park.geojson
            ->
        Blue River Park
    """
    file_name = normalize_name(file_path.name)

    matches = [
        trail_system
        for trail_system in trail_systems
        if normalize_name(trail_system["name"]) == file_name
    ]

    if len(matches) == 1:
        return matches[0]

    return None


def select_trail_system(
    trail_systems: list[sqlite3.Row],
) -> sqlite3.Row | None:
    if not trail_systems:
        return None

    print()
    print("Available unmapped trail systems:")
    print()

    for index, trail_system in enumerate(
        trail_systems,
        start=1,
    ):
        location_parts = [
            trail_system["city"],
            trail_system["state"],
        ]

        location = ", ".join(
            part
            for part in location_parts
            if part
        )

        if location:
            location = f" ({location})"

        print(
            f"{index:>2}. "
            f"{trail_system['name']}"
            f"{location}"
        )

    print()

    while True:
        response = input(
            "Select trail system "
            "(Enter to skip): "
        ).strip()

        if not response:
            return None

        try:
            selection = int(response)
        except ValueError:
            print("Enter a valid number.")
            continue

        if 1 <= selection <= len(trail_systems):
            return trail_systems[selection - 1]

        print("Selection out of range.")


def save_boundary(
    connection: sqlite3.Connection,
    trail_system_id: int,
    geometry: dict[str, Any],
    available_columns: set[str],
) -> None:
    """
    Save the manual boundary.

    boundary_source and updated_at are updated automatically if those
    columns exist in the current schema.
    """
    assignments = [
        "boundary_geojson = ?",
        "boundary_confirmed = 1",
    ]

    parameters: list[Any] = [
        json.dumps(
            geometry,
            separators=(",", ":"),
        )
    ]

    if "boundary_source" in available_columns:
        assignments.append(
            "boundary_source = 'manual'"
        )

    if "updated_at" in available_columns:
        assignments.append(
            "updated_at = CURRENT_TIMESTAMP"
        )

    parameters.append(trail_system_id)

    query = f"""
        update trail_systems
        set
            {", ".join(assignments)}
        where trail_system_id = ?;
    """

    connection.execute(
        query,
        parameters,
    )

    connection.commit()


def print_header() -> None:
    print()
    print("=============================================")
    print("IMPORT MANUAL TRAIL SYSTEM BOUNDARIES")
    print("=============================================")
    print()


def main() -> None:
    print_header()

    if not DATABASE_PATH.exists():
        print(
            f"Database not found:\n{DATABASE_PATH}"
        )
        return

    if not BOUNDARY_DIRECTORY.exists():
        BOUNDARY_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "Manual boundary directory created:"
        )
        print(BOUNDARY_DIRECTORY)
        print()
        print(
            "Add .geojson files to this directory "
            "and run the importer again."
        )
        return

    geojson_files = sorted(
        BOUNDARY_DIRECTORY.glob("*.geojson")
    )

    if not geojson_files:
        print(
            "No GeoJSON files found in:"
        )
        print(BOUNDARY_DIRECTORY)
        return

    with sqlite3.connect(
        DATABASE_PATH
    ) as connection:
        connection.row_factory = sqlite3.Row

        columns = get_table_columns(
            connection,
            "trail_systems",
        )

        trail_systems = get_unmapped_trail_systems(
            connection
        )

        print(
            f"GeoJSON files found:      "
            f"{len(geojson_files)}"
        )
        print(
            f"Trail systems unmapped:  "
            f"{len(trail_systems)}"
        )
        print()

        if not trail_systems:
            print(
                "All trail systems already have "
                "confirmed boundaries."
            )
            return

        imported = 0
        skipped = 0
        failed = 0

        for file_path in geojson_files:
            print("---------------------------------------------")
            print(f"File: {file_path.name}")

            try:
                geometry = load_geojson(
                    file_path
                )
            except (
                json.JSONDecodeError,
                ValueError,
            ) as exc:
                print(
                    f"Invalid GeoJSON: {exc}"
                )
                failed += 1
                continue

            print(
                f"Geometry: {geometry['type']}"
            )

            match = find_automatic_match(
                file_path,
                trail_systems,
            )

            if match:
                print(
                    "Automatic match: "
                    f"{match['name']}"
                )

                response = input(
                    "Import this boundary? "
                    "[Y/n]: "
                ).strip().lower()

                if response in {"n", "no"}:
                    skipped += 1
                    continue

            else:
                print(
                    "No automatic filename match found."
                )

                match = select_trail_system(
                    trail_systems
                )

                if match is None:
                    print("Skipped.")
                    skipped += 1
                    continue

            save_boundary(
                connection=connection,
                trail_system_id=match[
                    "trail_system_id"
                ],
                geometry=geometry,
                available_columns=columns,
            )

            print(
                f"Boundary saved: {match['name']}"
            )

            imported += 1

            trail_systems = [
                trail_system
                for trail_system in trail_systems
                if trail_system[
                    "trail_system_id"
                ]
                != match["trail_system_id"]
            ]

        print()
        print("=============================================")
        print("MANUAL BOUNDARY IMPORT SUMMARY")
        print("=============================================")
        print()
        print(f"Imported: {imported}")
        print(f"Skipped:  {skipped}")
        print(f"Failed:   {failed}")
        print()

        remaining = get_unmapped_trail_systems(
            connection
        )

        print(
            f"Trail systems still unmapped: "
            f"{len(remaining)}"
        )


if __name__ == "__main__":
    main()