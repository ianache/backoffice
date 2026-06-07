"""create_tenants_table

Revision ID: 7f8bdd389265
Revises: 
Create Date: 2026-06-06 20:08:53.020560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f8bdd389265'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("default_language", sa.String(length=5), nullable=False),
        sa.Column("default_currency", sa.String(length=3), nullable=False),
        sa.Column("default_units", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("primary_color", sa.String(length=20), nullable=True),
        sa.Column("secondary_color", sa.String(length=20), nullable=True),
        sa.Column("accent_color", sa.String(length=20), nullable=True),
        sa.Column("font_family", sa.String(length=100), nullable=True),
        sa.Column("font_weight", sa.String(length=20), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("products", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tenants")
