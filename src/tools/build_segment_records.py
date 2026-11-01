"""Install additive retrieval metadata and the two segment-record reporting views."""
from pathlib import Path
from src.database import initialize_database
from src.database.connection import engine

ROOT = Path(__file__).resolve().parents[2]


def run():
    initialize_database()
    with engine.begin() as conn:
        for name in ['view_segment_effort_achievement','view_segment_personal_best']:
            for statement in (ROOT/'sql/views/facts'/f'{name}.sql').read_text().split(';'):
                if statement.strip():
                    conn.exec_driver_sql(statement)
            count = conn.exec_driver_sql(f'SELECT count(*) FROM {name}').scalar()
            print(f'{name}: {count} rows', flush=True)
        for field in ['pr_rank_status','kom_rank_status']:
            rows = conn.exec_driver_sql(f'SELECT {field}, count(*) FROM view_segment_effort_achievement GROUP BY {field}').all()
            print(f'{field}: {dict(rows)}', flush=True)


if __name__ == '__main__':
    run()
