"""seed_dogfood_feature_flags

Revision ID: h004
Revises: h003
Create Date: 2026-07-05

Seeds the BackOffice dogfooding feature flags used by the portal shell:
- bo.feature
- bo.feature.create
- bo.feature.update

These are inserted explicitly so nav visibility and action gates do not
depend on manual data entry. Idempotent via INSERT IGNORE.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h004"
down_revision: Union[str, None] = "h003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    flags = [
        ("bo.feature", "Feature Flags + Segments menu visibility"),
        ("bo.feature.create", "Create Flag button visibility"),
        ("bo.feature.update", "Edit Flag action visibility"),
    ]

    for name, description in flags:
        bind.execute(
            sa.text(
                "INSERT IGNORE INTO feature_flags "
                "(name, description, scope, tenant_id, product_id, company_id, enabled, default_val, complex, ttl, environment, rollout, rules, tags, rule_combination_mode, created_by) "
                "VALUES (:name, :description, 'global', NULL, NULL, NULL, 1, 1, 0, NULL, 'production', 100, '[]', '[]', NULL, NULL)"
            ),
            {"name": name, "description": description},
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM feature_flags "
            "WHERE name IN ('bo.feature', 'bo.feature.create', 'bo.feature.update')"
        )
    )
