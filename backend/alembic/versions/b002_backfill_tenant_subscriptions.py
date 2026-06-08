"""backfill_tenant_subscriptions

Revision ID: b002
Revises: b001
Create Date: 2026-06-08

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b002'
down_revision: Union[str, None] = 'b001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, products FROM tenants WHERE products IS NOT NULL"
    ))
    for row in rows:
        tenant_id = str(row[0])
        products_raw = row[1]
        try:
            slugs = json.loads(products_raw) if products_raw else []
            if not isinstance(slugs, list):
                slugs = []
        except (json.JSONDecodeError, TypeError):
            slugs = []
        for slug in slugs:
            if not slug or not isinstance(slug, str):
                continue
            bind.execute(sa.text(
                "INSERT IGNORE INTO products (id, name, status, labels) "
                "VALUES (:id, :name, 'active', '[]')"
            ), {"id": slug, "name": slug})
            bind.execute(sa.text(
                "INSERT IGNORE INTO tenant_subscriptions (tenant_id, product_id) "
                "VALUES (:tid, :pid)"
            ), {"tid": tenant_id, "pid": slug})


def downgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT tenant_id, product_id FROM tenant_subscriptions"
    ))
    tenant_map: dict = {}
    for tenant_id, product_id in rows:
        tenant_map.setdefault(tenant_id, []).append(product_id)
    for tenant_id, products in tenant_map.items():
        bind.execute(sa.text(
            "UPDATE tenants SET products = :p WHERE id = :id"
        ), {"p": json.dumps(products), "id": int(tenant_id)})
