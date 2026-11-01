"""Add effort-rank retrieval provenance and resumable activity refresh state."""
from alembic import op
import sqlalchemy as sa

revision = '20261101_segment_records'
down_revision = '20261031_gps_points'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table('segment_effort_record_metadata'):
        op.create_table('segment_effort_record_metadata',
            sa.Column('segment_effort_id', sa.BigInteger(), sa.ForeignKey('segment_efforts.segment_effort_id', ondelete='CASCADE'), primary_key=True, autoincrement=False),
            sa.Column('retrieved_at', sa.DateTime(), nullable=False),
            sa.Column('pr_rank_returned', sa.Boolean(), nullable=False),
            sa.Column('kom_rank_returned', sa.Boolean(), nullable=False))
    if not sa.inspect(bind).has_table('segment_record_refresh'):
        op.create_table('segment_record_refresh',
            sa.Column('activity_id', sa.BigInteger(), sa.ForeignKey('activities.activity_id', ondelete='CASCADE'), primary_key=True, autoincrement=False),
            sa.Column('last_attempted_at', sa.DateTime(), nullable=False),
            sa.Column('last_refreshed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(32), nullable=False))


def downgrade():
    op.drop_table('segment_effort_record_metadata')
    op.drop_table('segment_record_refresh')
