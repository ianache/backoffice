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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('namespaces'):
        op.create_table(
            'namespaces',
            sa.Column('id', sa.String(length=100), nullable=False),
            sa.Column('strategy', sa.String(length=10), server_default='lazy', nullable=False),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    if not inspector.has_table('localized_labels'):
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

    inspector = sa.inspect(bind)
    localized_indexes = {index['name'] for index in inspector.get_indexes('localized_labels')}
    for name, columns in (
        ('ix_localized_labels_tenant_id', ['tenant_id']),
        ('ix_localized_labels_company_id', ['company_id']),
        ('ix_localized_labels_product_id', ['product_id']),
        ('ix_localized_labels_namespace', ['namespace']),
    ):
        if name not in localized_indexes:
            op.create_index(name, 'localized_labels', columns, unique=False)
    if 'ux_localized_labels_scope_key' not in localized_indexes:
        op.create_index(
            'ux_localized_labels_scope_key',
            'localized_labels',
            ['tenant_id', 'company_id', 'product_id', 'namespace', 'locale', 'label_key'],
            unique=True,
            mysql_length={
                'tenant_id': 32,
                'company_id': 32,
                'product_id': 32,
                'namespace': 48,
                'locale': 10,
                'label_key': 96,
            },
        )

    if not inspector.has_table('missing_label_reports'):
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
    inspector = sa.inspect(bind)
    missing_indexes = {index['name'] for index in inspector.get_indexes('missing_label_reports')}
    if 'ix_missing_label_reports_namespace' not in missing_indexes:
        op.create_index('ix_missing_label_reports_namespace', 'missing_label_reports', ['namespace'], unique=False)
    if 'ux_missing_label_reports_dedup' not in missing_indexes:
        op.create_index(
            'ux_missing_label_reports_dedup',
            'missing_label_reports',
            ['tenant_id', 'namespace', 'label_key', 'locale'],
            unique=True,
            mysql_length={'tenant_id': 32, 'namespace': 48, 'label_key': 96, 'locale': 10},
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
