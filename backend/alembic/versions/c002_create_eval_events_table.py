"""create eval_events table

Revision ID: c002
Revises: c001
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'c002'
down_revision = 'c001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'eval_events',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('flag_key', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('result', sa.SmallInteger(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.String(100), nullable=True),
        sa.Column('product_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_eval_events_tenant_id', 'eval_events', ['tenant_id'])
    op.create_index('ix_eval_events_flag_key', 'eval_events', ['flag_key'])


def downgrade() -> None:
    op.drop_index('ix_eval_events_flag_key', table_name='eval_events')
    op.drop_index('ix_eval_events_tenant_id', table_name='eval_events')
    op.drop_table('eval_events')
