"""add_tenant_owner

Revision ID: d001
Revises: c002
Create Date: 2026-06-10

Adds tenants.owner (nullable) so the Owner column in the tenants UI
reflects real data instead of client-side mock names.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd001'
down_revision: Union[str, None] = 'c002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('owner', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'owner')
