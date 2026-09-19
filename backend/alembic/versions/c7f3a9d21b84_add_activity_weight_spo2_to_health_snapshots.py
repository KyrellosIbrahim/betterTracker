"""add activity/weight/spo2 to health_snapshots

Adds the Phase 4 metrics pulled from Google Health: daily step total, active
minutes, average blood-oxygen %, and body weight (kg). All nullable — a given
day may have any subset depending on which devices reported.

Revision ID: c7f3a9d21b84
Revises: 9aebb1523448
Create Date: 2026-09-19 07:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f3a9d21b84'
down_revision: Union[str, Sequence[str], None] = '9aebb1523448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('health_snapshots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('steps', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('active_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('spo2', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('weight_kg', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('health_snapshots', schema=None) as batch_op:
        batch_op.drop_column('weight_kg')
        batch_op.drop_column('spo2')
        batch_op.drop_column('active_minutes')
        batch_op.drop_column('steps')
