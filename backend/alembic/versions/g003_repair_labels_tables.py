"""repair_labels_tables

Revision ID: g003
Revises: g002
Create Date: 2026-06-13

Repairs databases that were stamped through the Phase 20 revisions without
actually creating one or more labels tables. This revision is intentionally
idempotent and does not rewrite the already-published g001/g002 history.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g003"
down_revision: Union[str, None] = "g002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_names(inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("namespaces"):
        op.create_table(
            "namespaces",
            sa.Column("id", sa.String(length=100), nullable=False),
            sa.Column("strategy", sa.String(length=10), server_default="lazy", nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not inspector.has_table("localized_labels"):
        op.create_table(
            "localized_labels",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("tenant_id", sa.String(length=100), nullable=False),
            sa.Column("company_id", sa.String(length=50), nullable=True),
            sa.Column("product_id", sa.String(length=50), nullable=True),
            sa.Column("namespace", sa.String(length=100), nullable=False),
            sa.Column("locale", sa.String(length=10), nullable=False),
            sa.Column("label_key", sa.String(length=150), nullable=False),
            sa.Column("label_value", sa.Text(), nullable=False),
            sa.Column("label_type", sa.String(length=20), nullable=True),
            sa.Column("params", sa.Text(), nullable=True),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(bind)
    localized_indexes = _index_names(inspector, "localized_labels")
    for name, columns, unique in (
        ("ix_localized_labels_tenant_id", ["tenant_id"], False),
        ("ix_localized_labels_company_id", ["company_id"], False),
        ("ix_localized_labels_product_id", ["product_id"], False),
        ("ix_localized_labels_namespace", ["namespace"], False),
        (
            "ux_localized_labels_scope_key",
            ["tenant_id", "company_id", "product_id", "namespace", "locale", "label_key"],
            True,
        ),
    ):
        if name not in localized_indexes:
            kwargs = {}
            if unique:
                kwargs["mysql_length"] = {
                    "tenant_id": 32,
                    "company_id": 32,
                    "product_id": 32,
                    "namespace": 48,
                    "locale": 10,
                    "label_key": 96,
                }
            op.create_index(name, "localized_labels", columns, unique=unique, **kwargs)

    if not inspector.has_table("missing_label_reports"):
        op.create_table(
            "missing_label_reports",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("tenant_id", sa.String(length=100), nullable=False),
            sa.Column("company_id", sa.String(length=50), nullable=True),
            sa.Column("product_id", sa.String(length=50), nullable=True),
            sa.Column("namespace", sa.String(length=100), nullable=False),
            sa.Column("label_key", sa.String(length=150), nullable=False),
            sa.Column("locale", sa.String(length=10), nullable=False),
            sa.Column("hits", sa.Integer(), server_default="1", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.Column("last_reported_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(bind)
    missing_indexes = _index_names(inspector, "missing_label_reports")
    for name, columns, unique in (
        ("ix_missing_label_reports_namespace", ["namespace"], False),
        (
            "ux_missing_label_reports_dedup",
            ["tenant_id", "namespace", "label_key", "locale"],
            True,
        ),
    ):
        if name not in missing_indexes:
            kwargs = {}
            if unique:
                kwargs["mysql_length"] = {
                    "tenant_id": 32,
                    "namespace": 48,
                    "label_key": 96,
                    "locale": 10,
                }
            op.create_index(name, "missing_label_reports", columns, unique=unique, **kwargs)

    bind.execute(
        sa.text(
            "INSERT IGNORE INTO namespaces (id, strategy, description) "
            "VALUES ('common', 'eager', :description)"
        ),
        {"description": "Common UI labels: navigation, buttons, shared messages"},
    )


def downgrade() -> None:
    # Repair migrations must not drop tables that may predate this revision.
    pass
