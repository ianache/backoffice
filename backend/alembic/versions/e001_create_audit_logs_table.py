"""create_audit_logs_table

Revision ID: e001
Revises: d004
Create Date: 2026-06-12

Net-new immutable audit_logs table (Phase 16, AUD-01). payload_before/
payload_after stored as TEXT (MySQL 5.6 has no native JSON column type),
matching the rules/tags/conditions/test_context precedent. No backfill —
purely additive.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e001'
down_revision: Union[str, None] = 'd004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('environment', sa.String(length=20), server_default='production', nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.String(length=50), nullable=False),
        sa.Column('payload_before', sa.Text(), nullable=True),
        sa.Column('payload_after', sa.Text(), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('ix_audit_logs_tenant_created', 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_action_type', 'audit_logs', ['action_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_logs_action_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_table('audit_logs')
