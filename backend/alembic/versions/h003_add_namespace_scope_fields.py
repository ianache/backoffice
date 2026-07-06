"""add_namespace_scope_fields

Revision ID: h003
Revises: h002
Create Date: 2026-07-05

Adds optional tenant/company/product scope metadata to namespaces.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h003"
down_revision: Union[str, None] = "h002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = _column_names(inspector, "namespaces")

    if "tenant_id" not in columns:
        op.add_column("namespaces", sa.Column("tenant_id", sa.String(length=100), nullable=True))
    if "company_id" not in columns:
        op.add_column("namespaces", sa.Column("company_id", sa.String(length=50), nullable=True))
    if "product_id" not in columns:
        op.add_column("namespaces", sa.Column("product_id", sa.String(length=50), nullable=True))

    inspector = sa.inspect(bind)
    indexes = _index_names(inspector, "namespaces")
    if "ix_namespaces_tenant_id" not in indexes:
        op.create_index("ix_namespaces_tenant_id", "namespaces", ["tenant_id"], unique=False)
    if "ix_namespaces_company_id" not in indexes:
        op.create_index("ix_namespaces_company_id", "namespaces", ["company_id"], unique=False)
    if "ix_namespaces_product_id" not in indexes:
        op.create_index("ix_namespaces_product_id", "namespaces", ["product_id"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = _index_names(inspector, "namespaces")
    if "ix_namespaces_product_id" in indexes:
        op.drop_index("ix_namespaces_product_id", table_name="namespaces")
    if "ix_namespaces_company_id" in indexes:
        op.drop_index("ix_namespaces_company_id", table_name="namespaces")
    if "ix_namespaces_tenant_id" in indexes:
        op.drop_index("ix_namespaces_tenant_id", table_name="namespaces")

    columns = _column_names(sa.inspect(op.get_bind()), "namespaces")
    if "product_id" in columns:
        op.drop_column("namespaces", "product_id")
    if "company_id" in columns:
        op.drop_column("namespaces", "company_id")
    if "tenant_id" in columns:
        op.drop_column("namespaces", "tenant_id")
