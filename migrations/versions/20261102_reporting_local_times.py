"""Add reporting timezone provenance and offset intervals."""
from alembic import op
revision = '20261102_reporting_local_times'
down_revision = '20261101_segment_records'
branch_labels = None
depends_on = None
DDL = '\nCREATE TABLE IF NOT EXISTS reporting_activity_timezones (\n activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),\n timezone_name TEXT, timezone_source TEXT NOT NULL,\n utc_start TEXT, utc_end TEXT\n);\nCREATE TABLE IF NOT EXISTS reporting_timezone_offsets (\n activity_id INTEGER NOT NULL REFERENCES activities(activity_id),\n utc_start TEXT NOT NULL, utc_end TEXT NOT NULL, offset_seconds INTEGER NOT NULL,\n PRIMARY KEY(activity_id,utc_start)\n);\n'


def upgrade():
    for statement in DDL.split(';'):
        if statement.strip():op.execute(statement)


def downgrade():
    op.drop_table('reporting_timezone_offsets')
    op.drop_table('reporting_activity_timezones')
