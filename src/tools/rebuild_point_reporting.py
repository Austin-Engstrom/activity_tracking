"""Build the GPS reporting model from existing source data."""
from pathlib import Path
from src.database.connection import engine, initialize_database
from src.services.point_reporting_service import rebuild_points


def run(max_gap_seconds=60, tolerance_feet=40, ambiguity_feet=10):
    initialize_database()
    from src.loader.activity_type_category_loader import load_activity_type_categories
    load_activity_type_categories()
    with engine.begin() as connection:
        count = rebuild_points(connection, max_gap_seconds, tolerance_feet, ambiguity_feet)
        root = Path(__file__).resolve().parents[2]
        files = [line.strip()[6:] for line in (root/'sql/build_views.sql').read_text().splitlines()
                 if line.strip().startswith('.read ')]
        for filename in files:
            sql = (root / filename).read_text()
            # SQLite executescript commits implicitly; execute statements individually.
            for statement in sql.split(';'):
                if statement.strip():
                    connection.exec_driver_sql(statement)
    print(f'Rebuilt {count} GPS points')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-gap-seconds', type=float, default=60)
    parser.add_argument('--tolerance-feet', type=float, default=40)
    parser.add_argument('--ambiguity-feet', type=float, default=10)
    args = parser.parse_args()
    run(args.max_gap_seconds, args.tolerance_feet, args.ambiguity_feet)
