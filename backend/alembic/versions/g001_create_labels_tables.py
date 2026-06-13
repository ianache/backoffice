"""create_labels_tables

Revision ID: g001
Revises: e001
Create Date: 2026-06-13

Net-new tables for the Localization White Label Engine (Phase 20, LBL-01/LBL-02):
namespaces, localized_labels, missing_label_reports. params stored as TEXT
(MySQL 5.6 has no native JSON column type), matching the rules/tags/params
precedent. No backfill — purely additive.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'g001'
down_revision: Union[str, None] = 'e001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'namespaces',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('strategy', sa.String(length=10), server_default='lazy', nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'localized_labels',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('company_id', sa.String(length=50), nullable=True),
        sa.Column('product_id', sa.String(length=50), nullable=True),
        sa.Column('namespace', sa.String(length=100), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False),
        sa.Column('label_key', sa.String(length=150), nullable=False),
        sa.Column('label_value', sa.Text(), nullable=False),
        sa.Column('label_type', sa.String(length=20), nullable=True),
        sa.Column('params', sa.Text(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_localized_labels_tenant_id', 'localized_labels', ['tenant_id'], unique=False)
    op.create_index('ix_localized_labels_company_id', 'localized_labels', ['company_id'], unique=False)
    op.create_index('ix_localized_labels_product_id', 'localized_labels', ['product_id'], unique=False)
    op.create_index('ix_localized_labels_namespace', 'localized_labels', ['namespace'], unique=False)
    op.create_index(
        'ux_localized_labels_scope_key',
        'localized_labels',
        ['tenant_id', 'company_id', 'product_id', 'namespace', 'locale', 'label_key'],
        unique=True,
    )

    op.create_table(
        'missing_label_reports',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('company_id', sa.String(length=50), nullable=True),
        sa.Column('product_id', sa.String(length=50), nullable=True),
        sa.Column('namespace', sa.String(length=100), nullable=False),
        sa.Column('label_key', sa.String(length=150), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False),
        sa.Column('hits', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_reported_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_missing_label_reports_namespace', 'missing_label_reports', ['namespace'], unique=False)
    op.create_index(
        'ux_missing_label_reports_dedup',
        'missing_label_reports',
        ['tenant_id', 'namespace', 'label_key', 'locale'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ux_missing_label_reports_dedup', table_name='missing_label_reports')
    op.drop_index('ix_missing_label_reports_namespace', table_name='missing_label_reports')
    op.drop_table('missing_label_reports')

    op.drop_index('ux_localized_labels_scope_key', table_name='localized_labels')
    op.drop_index('ix_localized_labels_namespace', table_name='localized_labels')
    op.drop_index('ix_localized_labels_product_id', table_name='localized_labels')
    op.drop_index('ix_localized_labels_company_id', table_name='localized_labels')
    op.drop_index('ix_localized_labels_tenant_id', table_name='localized_labels')
    op.drop_table('localized_labels')

    op.drop_table('namespaces')
