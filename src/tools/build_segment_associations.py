"""Install/refresh the observed segment association view without rebuilding points."""
from pathlib import Path
import time
from sqlalchemy import text
from src.database.connection import engine

ROOT = Path(__file__).resolve().parents[2]


def run():
    started = time.perf_counter()
    print('[START] Refresh GPS-scoped dimensions and segment associations', flush=True)
    files = ['sql/views/dimensions/view_activity_type.sql',
             'sql/views/dimensions/view_gear.sql',
             'sql/views/dimensions/view_segment.sql',
             'sql/views/points/view_segment_trail_association.sql']
    with engine.begin() as conn:
        for filename in files:
            sql = (ROOT/filename).read_text()
            for statement in sql.split(';'):
                if statement.strip():
                    conn.exec_driver_sql(statement)
        # Query once to check dependencies and report the actual observed scope.
        row = conn.execute(text('''SELECT count(*) AS associations,
            count(DISTINCT segment_key) AS segments,
            count(DISTINCT trail_key) AS trails,
            count(DISTINCT trail_system_key) AS systems
            FROM view_segment_trail_association''')).mappings().one()
    print(dict(row), flush=True)
    print(f'[COMPLETED] {time.perf_counter()-started:.2f}s. Re-export Parquet and refresh Power BI.', flush=True)


if __name__ == '__main__':
    run()
