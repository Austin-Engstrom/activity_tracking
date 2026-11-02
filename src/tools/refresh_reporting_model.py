"""Apply local-time reporting views without rebuilding spatial GPS matches."""
from pathlib import Path
from src.database import initialize_database
from src.database.connection import engine
from src.services.reporting_local_time import refresh_local_times


def run():
    initialize_database()
    root=Path(__file__).resolve().parents[2]
    with engine.begin() as conn:
        print('Timezone resolution:',refresh_local_times(conn, force=True),flush=True)
        for line in (root/'sql/build_views.sql').read_text().splitlines():
            if not line.strip().startswith('.read '):continue
            path=root/line.strip()[6:]
            for statement in path.read_text().split(';'):
                if statement.strip():conn.exec_driver_sql(statement)
    print('Reporting views updated. Run a full Parquet export, then refresh and republish the GPS model.')


if __name__=='__main__':run()
