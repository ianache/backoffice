"""expand segments: add type and conditions columns

Revision ID: c001
Revises: b003
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'c001'
down_revision = 'b003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('segments',
        sa.Column('type', sa.String(20), nullable=True))
    op.add_column('segments',
        sa.Column('conditions', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('segments', 'conditions')
    op.drop_column('segments', 'type')
