"""Import gear components and maintenance service history from CSV files."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "database" / "strava_analytics.db"

MAINTENANCE_DIR = PROJECT_ROOT / "data" / "maintenance"

GEAR_COMPONENTS_PATH = MAINTENANCE_DIR / "gear_components.csv"
COMPONENT_SERVICES_PATH = MAINTENANCE_DIR / "component_services.csv"


# =============================================================================
# Result Models
# =============================================================================

@dataclass
class ImportResult:
    read: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0


# =============================================================================
# Database Setup
# =============================================================================

def create_tables(conn: sqlite3.Connection) -> None:
    """Create maintenance tables if they do not already exist."""

    conn.executescript(
        """
        create table if not exists gear_components (
            component_id integer primary key,
            gear_id text not null,
            component_type text not null,
            manufacturer text,
            model text,
            installed_at text not null,
            removed_at text,
            service_interval_hours real,
            notes text,
            foreign key (gear_id)
                references gear(gear_id)
        );

        create table if not exists component_services (
            service_id integer primary key autoincrement,
            component_id integer not null,
            service_date text not null,
            service_type text not null,
            notes text,
            foreign key (component_id)
                references gear_components(component_id),
            unique (
                component_id,
                service_date,
                service_type
            )
        );

        create index if not exists
            idx_gear_components_gear_id
        on gear_components (
            gear_id
        );

        create index if not exists
            idx_component_services_component_id
        on component_services (
            component_id
        );

        create index if not exists
            idx_component_services_service_date
        on component_services (
            service_date
        );
        """
    )


# =============================================================================
# Helpers
# =============================================================================

def clean(value: str | None) -> str | None:
    """Convert blank CSV values to None."""

    if value is None:
        return None

    value = value.strip()

    return value if value else None


def get_existing_gear_ids(conn: sqlite3.Connection) -> set[str]:
    """Return all valid Strava gear IDs."""

    rows = conn.execute(
        """
        select gear_id
        from gear
        """
    ).fetchall()

    return {str(row[0]) for row in rows}


def get_existing_component_ids(
    conn: sqlite3.Connection,
) -> set[int]:
    """Return all existing component IDs."""

    rows = conn.execute(
        """
        select component_id
        from gear_components
        """
    ).fetchall()

    return {int(row[0]) for row in rows}


# =============================================================================
# Gear Component Import
# =============================================================================

def import_gear_components(
    conn: sqlite3.Connection,
    path: Path,
) -> ImportResult:
    """Import gear component definitions."""

    result = ImportResult()

    if not path.exists():
        raise FileNotFoundError(
            f"Gear component CSV not found: {path}"
        )

    valid_gear_ids = get_existing_gear_ids(conn)

    required_columns = {
        "component_id",
        "gear_id",
        "component_type",
        "installed_at",
    }

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"No CSV header found in {path}"
            )

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                "gear_components.csv is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row in reader:
            result.read += 1

            component_id_raw = clean(row.get("component_id"))
            gear_id = clean(row.get("gear_id"))
            component_type = clean(row.get("component_type"))
            installed_at = clean(row.get("installed_at"))

            if not component_id_raw:
                print(
                    f"Skipping row {result.read}: "
                    "component_id is required."
                )
                result.skipped += 1
                continue

            if not gear_id:
                print(
                    f"Skipping component {component_id_raw}: "
                    "gear_id is required."
                )
                result.skipped += 1
                continue

            if gear_id not in valid_gear_ids:
                print(
                    f"Skipping component {component_id_raw}: "
                    f"gear_id '{gear_id}' does not exist."
                )
                result.skipped += 1
                continue

            if not component_type:
                print(
                    f"Skipping component {component_id_raw}: "
                    "component_type is required."
                )
                result.skipped += 1
                continue

            if not installed_at:
                print(
                    f"Skipping component {component_id_raw}: "
                    "installed_at is required."
                )
                result.skipped += 1
                continue

            try:
                component_id = int(component_id_raw)
            except ValueError:
                print(
                    f"Skipping row {result.read}: "
                    f"invalid component_id '{component_id_raw}'."
                )
                result.skipped += 1
                continue

            service_interval_raw = clean(
                row.get("service_interval_hours")
            )

            service_interval_hours = (
                float(service_interval_raw)
                if service_interval_raw
                else None
            )

            exists = conn.execute(
                """
                select 1
                from gear_components
                where component_id = ?
                """,
                (component_id,),
            ).fetchone()

            values = (
                gear_id,
                component_type,
                clean(row.get("manufacturer")),
                clean(row.get("model")),
                installed_at,
                clean(row.get("removed_at")),
                service_interval_hours,
                clean(row.get("notes")),
            )

            if exists:
                conn.execute(
                    """
                    update gear_components
                    set
                        gear_id = ?,
                        component_type = ?,
                        manufacturer = ?,
                        model = ?,
                        installed_at = ?,
                        removed_at = ?,
                        service_interval_hours = ?,
                        notes = ?
                    where component_id = ?
                    """,
                    values + (component_id,),
                )

                result.updated += 1

            else:
                conn.execute(
                    """
                    insert into gear_components (
                        component_id,
                        gear_id,
                        component_type,
                        manufacturer,
                        model,
                        installed_at,
                        removed_at,
                        service_interval_hours,
                        notes
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (component_id,) + values,
                )

                result.inserted += 1

    return result


# =============================================================================
# Service History Import
# =============================================================================

def import_component_services(
    conn: sqlite3.Connection,
    path: Path,
) -> ImportResult:
    """Import component maintenance history."""

    result = ImportResult()

    if not path.exists():
        raise FileNotFoundError(
            f"Component service CSV not found: {path}"
        )

    valid_component_ids = get_existing_component_ids(conn)

    required_columns = {
        "component_id",
        "service_date",
        "service_type",
    }

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"No CSV header found in {path}"
            )

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                "component_services.csv is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row in reader:
            result.read += 1

            component_id_raw = clean(row.get("component_id"))
            service_date = clean(row.get("service_date"))
            service_type = clean(row.get("service_type"))

            if not component_id_raw:
                print(
                    f"Skipping service row {result.read}: "
                    "component_id is required."
                )
                result.skipped += 1
                continue

            try:
                component_id = int(component_id_raw)
            except ValueError:
                print(
                    f"Skipping service row {result.read}: "
                    f"invalid component_id '{component_id_raw}'."
                )
                result.skipped += 1
                continue

            if component_id not in valid_component_ids:
                print(
                    f"Skipping service row {result.read}: "
                    f"component_id {component_id} does not exist."
                )
                result.skipped += 1
                continue

            if not service_date:
                print(
                    f"Skipping service row {result.read}: "
                    "service_date is required."
                )
                result.skipped += 1
                continue

            if not service_type:
                print(
                    f"Skipping service row {result.read}: "
                    "service_type is required."
                )
                result.skipped += 1
                continue

            exists = conn.execute(
                """
                select service_id
                from component_services
                where component_id = ?
                  and service_date = ?
                  and service_type = ?
                """,
                (
                    component_id,
                    service_date,
                    service_type,
                ),
            ).fetchone()

            notes = clean(row.get("notes"))

            if exists:
                conn.execute(
                    """
                    update component_services
                    set notes = ?
                    where service_id = ?
                    """,
                    (
                        notes,
                        exists[0],
                    ),
                )

                result.updated += 1

            else:
                conn.execute(
                    """
                    insert into component_services (
                        component_id,
                        service_date,
                        service_type,
                        notes
                    )
                    values (?, ?, ?, ?)
                    """,
                    (
                        component_id,
                        service_date,
                        service_type,
                        notes,
                    ),
                )

                result.inserted += 1

    return result


# =============================================================================
# Output
# =============================================================================

def print_result(
    label: str,
    result: ImportResult,
) -> None:
    """Print import results."""

    print()
    print(label)
    print("-" * 60)
    print(f"Rows read:     {result.read}")
    print(f"Inserted:      {result.inserted}")
    print(f"Updated:       {result.updated}")
    print(f"Skipped:       {result.skipped}")


# =============================================================================
# Main
# =============================================================================

def run() -> None:
    """Run the maintenance import."""

    parser = argparse.ArgumentParser(
        description=(
            "Import gear components and maintenance "
            "service history."
        )
    )

    parser.add_argument(
        "--components",
        type=Path,
        default=GEAR_COMPONENTS_PATH,
        help="Path to gear_components.csv",
    )

    parser.add_argument(
        "--services",
        type=Path,
        default=COMPONENT_SERVICES_PATH,
        help="Path to component_services.csv",
    )

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("MAINTENANCE IMPORT")
    print("=" * 60)
    print()
    print(f"Database:   {DATABASE_PATH}")
    print(f"Components: {args.components}")
    print(f"Services:   {args.services}")

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("pragma foreign_keys = on")

        create_tables(conn)

        component_result = import_gear_components(
            conn,
            args.components,
        )

        service_result = import_component_services(
            conn,
            args.services,
        )

        conn.commit()

    print_result(
        "GEAR COMPONENTS",
        component_result,
    )

    print_result(
        "COMPONENT SERVICES",
        service_result,
    )

    print()
    print("=" * 60)
    print("MAINTENANCE IMPORT COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    run()