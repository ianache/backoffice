"""expand_products_tables

Revision ID: b001
Revises: a1b2c3d4e5f6
Create Date: 2026-06-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b001'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create products table (no dependencies)
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('labels', sa.Text(), nullable=True),   # JSON array serialized as TEXT — MySQL 5.6 safe
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Step 2: Create tenant_subscriptions table (FK → products)
    op.create_table(
        'tenant_subscriptions',
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('subscribed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('tenant_id', 'product_id'),
        # NO FK on tenant_id — consistent with feature_flags.tenant_id pattern (Keycloak-managed)
    )

    # Step 3: Create flag_products table (FK → feature_flags and → products)
    op.create_table(
        'flag_products',
        sa.Column('flag_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['flag_id'], ['feature_flags.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('flag_id', 'product_id'),
    )


def downgrade() -> None:
    # Drop FK-dependent tables first
    op.drop_table('flag_products')
    op.drop_table('tenant_subscriptions')
    op.drop_table('products')
