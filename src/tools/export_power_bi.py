"""Export Power BI reporting views from SQLite to Parquet files."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database import SessionLocal


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIRECTORY = PROJECT_ROOT / "exports" / "power_bi"

POWER_BI_VIEWS = [
    "view_activity",
    "view_activity_type",
    "view_date",
    "view_gear",
    "view_segment",
    "view_segment_effort",
    "view_activity_stream_summary",
    "view_official_trail",
    "view_trail_activity",
    "view_trail_progress",
    "view_trail_system",
    "view_component_service_status",
]

PARQUET_COMPRESSION = "snappy"


# =============================================================================
# Models
# =============================================================================


@dataclass
class ExportResult:
    """Result of exporting one reporting view."""

    view_name: str
    row_count: int = 0
    file_size_bytes: int = 0
    elapsed_seconds: float = 0.0
    success: bool = False
    error: str | None = None


# =============================================================================
# Helpers
# =============================================================================


def format_file_size(size_bytes: int) -> str:
    """Return a human-readable file size."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_kb = size_bytes / 1024

    if size_kb < 1024:
        return f"{size_kb:.2f} KB"

    size_mb = size_kb / 1024

    if size_mb < 1024:
        return f"{size_mb:.2f} MB"

    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"


def validate_view_exists(connection, view_name: str) -> None:
    """Confirm that a reporting view exists in SQLite."""

    statement = text(
        """
        select name
        from sqlite_master
        where type = 'view'
          and name = :view_name
        """
    )

    result = connection.execute(
        statement,
        {"view_name": view_name},
    ).scalar_one_or_none()

    if result is None:
        raise ValueError(
            f"Reporting view does not exist: {view_name}"
        )


def prepare_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare SQLite data for Parquet export.

    SQLite does not enforce dedicated date/datetime storage types, so reporting
    views frequently return these values as strings. Convert clearly named
    date/datetime columns before writing Parquet so Power BI receives stronger
    type information.
    """

    dataframe = dataframe.copy()

    for column in dataframe.columns:
        column_lower = column.lower()

        # Date-only columns.
        if (
            column_lower == "date"
            or column_lower.endswith("_date")
        ):
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
            ).dt.date

        # Timestamp columns.
        elif (
            column_lower.endswith("_at")
            or column_lower in {
                "start_date",
                "start_date_local",
                "first_ridden_at",
                "last_ridden_at",
            }
        ):
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
                utc=True,
            )

    return dataframe


def export_view(
    connection,
    view_name: str,
    export_directory: Path,
) -> ExportResult:
    """Export one SQLite reporting view to Parquet."""

    started_at = time.perf_counter()

    result = ExportResult(view_name=view_name)

    try:
        validate_view_exists(connection, view_name)

        statement = text(f'select * from "{view_name}"')

        dataframe = pd.read_sql_query(
            statement,
            connection,
        )

        dataframe = prepare_dataframe(dataframe)

        output_path = export_directory / f"{view_name}.parquet"
        temporary_path = export_directory / f"{view_name}.parquet.tmp"

        # Write to a temporary file first so an interrupted export does not
        # leave Power BI with a partially written Parquet file.
        dataframe.to_parquet(
            temporary_path,
            engine="pyarrow",
            compression=PARQUET_COMPRESSION,
            index=False,
        )

        temporary_path.replace(output_path)

        result.row_count = len(dataframe)
        result.file_size_bytes = output_path.stat().st_size
        result.success = True

    except Exception as exc:
        result.error = str(exc)

        temporary_path = (
            export_directory / f"{view_name}.parquet.tmp"
        )

        if temporary_path.exists():
            temporary_path.unlink()

    result.elapsed_seconds = time.perf_counter() - started_at

    return result


def print_header() -> None:
    """Print the Power BI export header."""

    print()
    print("=" * 72)
    print("POWER BI PARQUET EXPORT")
    print("=" * 72)
    print()
    print(f"Output directory: {EXPORT_DIRECTORY}")
    print(f"Compression:      {PARQUET_COMPRESSION}")
    print(f"Views selected:   {len(POWER_BI_VIEWS)}")
    print()


def print_result(result: ExportResult) -> None:
    """Print the result of a single view export."""

    if result.success:
        print(
            f"{result.view_name:<36}"
            f"{result.row_count:>10,} rows   "
            f"{format_file_size(result.file_size_bytes):>10}   "
            f"{result.elapsed_seconds:>7.2f}s"
        )
    else:
        print(
            f"{result.view_name:<36}"
            f"{'FAILED':>10}          "
            f"{result.elapsed_seconds:>10.2f}s"
        )
        print(f"    Error: {result.error}")


def print_summary(
    results: list[ExportResult],
    elapsed_seconds: float,
) -> None:
    """Print the final export summary."""

    successful = [
        result for result in results if result.success
    ]
    failed = [
        result for result in results if not result.success
    ]

    total_rows = sum(
        result.row_count for result in successful
    )
    total_size = sum(
        result.file_size_bytes for result in successful
    )

    print()
    print("-" * 72)
    print("EXPORT SUMMARY")
    print("-" * 72)
    print(f"Views selected:   {len(results):>10,}")
    print(f"Views exported:   {len(successful):>10,}")
    print(f"Views failed:     {len(failed):>10,}")
    print(f"Rows exported:    {total_rows:>10,}")
    print(
        f"Total file size:  "
        f"{format_file_size(total_size):>10}"
    )
    print(f"Elapsed time:     {elapsed_seconds:>9.2f}s")
    print()

    if failed:
        print("FAILED VIEWS")
        print("-" * 72)

        for result in failed:
            print(f"{result.view_name}: {result.error}")

        print()

    print(f"Output: {EXPORT_DIRECTORY}")
    print("=" * 72)
    print()


# =============================================================================
# Execution
# =============================================================================


def run(
    exit_on_failure: bool = True,
) -> list[ExportResult]:
    """Export all approved Power BI reporting views."""

    started_at = time.perf_counter()

    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print_header()

    results: list[ExportResult] = []

    with SessionLocal() as session:
        connection = session.connection()

        for view_name in POWER_BI_VIEWS:
            result = export_view(
                connection=connection,
                view_name=view_name,
                export_directory=EXPORT_DIRECTORY,
            )

            results.append(result)
            print_result(result)

    elapsed_seconds = time.perf_counter() - started_at

    print_summary(
        results=results,
        elapsed_seconds=elapsed_seconds,
    )

    has_failures = any(
        not result.success
        for result in results
    )

    if has_failures and exit_on_failure:
        raise SystemExit(1)

    return results

if __name__ == "__main__":
    run()