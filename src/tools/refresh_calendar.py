"""Refresh reporting calendar attributes without rebuilding GPS points."""
from pathlib import Path
from src.database.connection import engine


def run():
    sql=(Path(__file__).resolve().parents[2]/'sql/views/dimensions/view_date.sql').read_text()
    with engine.begin() as conn:
        for statement in sql.split(';'):
            if statement.strip():conn.exec_driver_sql(statement)
        count=conn.exec_driver_sql('SELECT count(*) FROM view_date').scalar()
    print(f'Calendar view refreshed: {count} dates. Export view_date and refresh Power BI.',flush=True)


if __name__=='__main__':
    run()
