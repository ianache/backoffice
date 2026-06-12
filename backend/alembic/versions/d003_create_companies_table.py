"""create_companies_table

Revision ID: d003
Revises: d002
Create Date: 2026-06-11

Adds the companies table (Phase 14, CMP-01): a per-tenant company catalog
for flag.company_id scope targeting. Brand-new table — single additive
revision, no expand/backfill/cleanup needed.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd003'
down_revision: Union[str, None] = 'd002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'companies',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('tenant_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_companies_tenant_id', 'companies', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_companies_tenant_id', table_name='companies')
    op.drop_table('companies')
