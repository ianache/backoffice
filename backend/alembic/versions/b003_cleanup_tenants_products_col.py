"""cleanup_tenants_products_col

Revision ID: b003
Revises: b002
Create Date: 2026-06-08

NOTE: This revision drops the tenants.products JSON column.
After applying this migration, the Tenant ORM model must have its
`products` field removed (handled in this same task).
Downgrade for b003 only re-adds the empty column.
Full data restoration requires running b002 downgrade first.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b003'
down_revision: Union[str, None] = 'b002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('tenants', 'products')


def downgrade() -> None:
    # Re-add column as nullable TEXT. Data restoration handled by b002 downgrade.
    op.add_column('tenants', sa.Column('products', sa.Text(), nullable=True))
