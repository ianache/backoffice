"""seed_common_namespace_labels

Revision ID: g002
Revises: g001
Create Date: 2026-06-13

Seeds the `common` namespace (eager strategy) plus realistic es_PE/en_US
nav/button labels for an existing tenant (queried at runtime — Pitfall 4),
plus a company-level override for one label if the tenant has at least one
company. Idempotent via INSERT IGNORE on the unique scope+key index.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'g002'
down_revision: Union[str, None] = 'g001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COMMON_LABELS = [
    # (label_key, label_type, es_PE, en_US)
    ("btn_aceptar", "LABEL", "Aceptar", "Accept"),
    ("btn_cancelar", "LABEL", "Cancelar", "Cancel"),
    ("btn_guardar", "LABEL", "Guardar", "Save"),
    ("nav_inicio", "LABEL", "Inicio", "Home"),
    ("nav_configuracion", "LABEL", "Configuración", "Settings"),
    ("msg_bienvenida", "LABEL", "Bienvenido", "Welcome"),
]


def upgrade() -> None:
    bind = op.get_bind()

    # Pick a real tenant — prefer the dogfooding tenant id=5 (portal VITE_BO_TENANT_ID),
    # fall back to the first tenant if it doesn't exist.
    row = bind.execute(sa.text("SELECT id FROM tenants WHERE id = 5")).fetchone()
    if row is None:
        row = bind.execute(sa.text("SELECT id FROM tenants ORDER BY id LIMIT 1")).fetchone()
    if row is None:
        return  # No tenants exist — nothing to seed (fresh/empty DB)
    tenant_id = str(row[0])

    # 1. Create the `common` namespace (eager strategy)
    bind.execute(sa.text(
        "INSERT IGNORE INTO namespaces (id, strategy, description) "
        "VALUES ('common', 'eager', :desc)"
    ), {"desc": "Common UI labels: navigation, buttons, shared messages"})

    # 2. Seed tenant-level common labels (es_PE + en_US) for both locales
    for label_key, label_type, es_value, en_value in COMMON_LABELS:
        bind.execute(sa.text(
            "INSERT IGNORE INTO localized_labels "
            "(tenant_id, company_id, product_id, namespace, locale, label_key, label_value, label_type, params, version) "
            "VALUES (:tid, NULL, NULL, 'common', 'es_PE', :key, :val, :ltype, '[]', 1)"
        ), {"tid": tenant_id, "key": label_key, "val": es_value, "ltype": label_type})
        bind.execute(sa.text(
            "INSERT IGNORE INTO localized_labels "
            "(tenant_id, company_id, product_id, namespace, locale, label_key, label_value, label_type, params, version) "
            "VALUES (:tid, NULL, NULL, 'common', 'en_US', :key, :val, :ltype, '[]', 1)"
        ), {"tid": tenant_id, "key": label_key, "val": en_value, "ltype": label_type})

    # 3. Company-level override demo (CONTEXT.md: "1-2 company-level overrides")
    #    Only seed if the tenant already has at least one company — do NOT
    #    fabricate a new demo hierarchy (CONTEXT.md decision).
    company_row = bind.execute(sa.text(
        "SELECT id FROM companies WHERE tenant_id = :tid ORDER BY id LIMIT 1"
    ), {"tid": tenant_id}).fetchone()
    if company_row is not None:
        company_id = str(company_row[0])
        # Override btn_aceptar / btn_cancelar at company level to demonstrate the cascade
        overrides = [
            ("btn_aceptar", "es_PE", "Confirmar"),
            ("btn_aceptar", "en_US", "Confirm"),
            ("btn_cancelar", "es_PE", "Volver"),
            ("btn_cancelar", "en_US", "Go Back"),
        ]
        for label_key, locale, value in overrides:
            bind.execute(sa.text(
                "INSERT IGNORE INTO localized_labels "
                "(tenant_id, company_id, product_id, namespace, locale, label_key, label_value, label_type, params, version) "
                "VALUES (:tid, :cid, NULL, 'common', :locale, :key, :val, 'LABEL', '[]', 1)"
            ), {"tid": tenant_id, "cid": company_id, "locale": locale, "key": label_key, "val": value})


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM localized_labels WHERE namespace = 'common'"))
    bind.execute(sa.text("DELETE FROM namespaces WHERE id = 'common'"))
