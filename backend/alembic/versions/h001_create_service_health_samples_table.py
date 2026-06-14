"""create_service_health_samples_table

Revision ID: h001
Revises: g004
Create Date: 2026-06-13

Net-new service_health_samples table (Phase 17, OBS-01). details stored as
TEXT (MySQL 5.6 has no native JSON column type), matching audit_logs precedent.
No backfill — purely additive.
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'h001'
down_revision: Union[str, None] = 'g004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'service_health_samples',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('checked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),  # UP|DEGRADED|DOWN
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_service_health_samples_checked_at', 'service_health_samples', ['checked_at'], unique=False)
    op.create_index('ix_service_health_samples_service_checked', 'service_health_samples', ['service_name', 'checked_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_service_health_samples_service_checked', table_name='service_health_samples')
    op.drop_index('ix_service_health_samples_checked_at', table_name='service_health_samples')
    op.drop_table('service_health_samples')
