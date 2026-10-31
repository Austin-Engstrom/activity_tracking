"""Add derived point reporting tables without changing source data."""
from alembic import op
revision = '20261031_gps_points'
down_revision = '8cce63d090ff'
branch_labels = None
depends_on = None

DDL = '\nCREATE TABLE IF NOT EXISTS activity_points (\n activity_point_key TEXT PRIMARY KEY,\n activity_id INTEGER NOT NULL REFERENCES activities(activity_id),\n point_index INTEGER NOT NULL,\n recorded_at_utc TEXT, date_key INTEGER,\n trail_system_key INTEGER REFERENCES trail_systems(trail_system_id),\n trail_key INTEGER REFERENCES official_trails(official_trail_id),\n incremental_distance_meters REAL, incremental_time_seconds REAL,\n quality_status TEXT NOT NULL, match_method TEXT NOT NULL,\n UNIQUE(activity_id, point_index)\n);\nCREATE INDEX IF NOT EXISTS ix_points_activity ON activity_points(activity_id);\nCREATE INDEX IF NOT EXISTS ix_points_system ON activity_points(trail_system_key);\nCREATE TABLE IF NOT EXISTS stream_index_alignment (\n activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),\n verified INTEGER NOT NULL CHECK(verified IN (0,1))\n);\nCREATE TABLE IF NOT EXISTS point_reporting_metadata (\n activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),\n timezone_name TEXT\n);\n'


def upgrade():
    for statement in DDL.split(';'):
        if statement.strip():
            op.execute(statement)


def downgrade():
    raise NotImplementedError(
        'GPS reporting cutover changes canonical views. Restore the prior views '
        'and validate report compatibility before removing derived tables.'
    )
