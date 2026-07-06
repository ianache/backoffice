"""seed_main_menu_namespace_labels

Revision ID: h002
Revises: h001
Create Date: 2026-07-05

Seeds the lazy `main_menu` namespace used by the portal sidebar.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h002"
down_revision: Union[str, None] = "h001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MAIN_MENU_LABELS = [
    ("mm_companies", "LABEL", "Companias", "Companies"),
    ("mm_logaudits", "LABEL", "Logs de Auditoria", "Audit Log"),
    ("mm_platform_settings", "LABEL", "Configuracion de Plataforma", "Platform Settings"),
    ("mm_products", "LABEL", "Productos", "Products"),
    ("mm_segments", "LABEL", "Segmentos", "Segments"),
    ("mm_tenants", "LABEL", "Tenants", "Tenants"),
    ("mm_users", "LABEL", "Usuarios", "Users"),
    ("mm_whitelabels", "LABEL", "Marca Blanca", "White Labels"),
    ("mm_feature_flags", "LABEL", "Feature Flags", "Feature Flags"),
]


def _label_exists(bind, tenant_id: str, locale: str, label_key: str) -> bool:
    row = bind.execute(sa.text(
        "SELECT 1 FROM localized_labels "
        "WHERE tenant_id = :tid AND company_id IS NULL AND product_id IS NULL "
        "AND namespace = 'main_menu' AND locale = :locale AND label_key = :key "
        "LIMIT 1"
    ), {"tid": tenant_id, "locale": locale, "key": label_key}).fetchone()
    return row is not None


def _insert_label(bind, tenant_id: str, locale: str, label_key: str, value: str, label_type: str) -> None:
    bind.execute(sa.text(
        "INSERT INTO localized_labels "
        "(tenant_id, company_id, product_id, namespace, locale, label_key, label_value, label_type, params, version) "
        "VALUES (:tid, NULL, NULL, 'main_menu', :locale, :key, :val, :ltype, '[]', 1)"
    ), {
        "tid": tenant_id,
        "locale": locale,
        "key": label_key,
        "val": value,
        "ltype": label_type,
    })


def upgrade() -> None:
    bind = op.get_bind()

    row = bind.execute(sa.text("SELECT id FROM tenants WHERE name = 'platform'")).fetchone()
    if row is None:
        row = bind.execute(sa.text("SELECT id FROM tenants WHERE id = 5")).fetchone()
    if row is None:
        row = bind.execute(sa.text("SELECT id FROM tenants ORDER BY id LIMIT 1")).fetchone()
    if row is None:
        return

    tenant_id = str(row[0])

    bind.execute(sa.text(
        "INSERT IGNORE INTO namespaces (id, strategy, description) "
        "VALUES ('main_menu', 'lazy', :desc)"
    ), {"desc": "Portal sidebar menu labels"})

    for label_key, label_type, es_value, en_value in MAIN_MENU_LABELS:
        if not _label_exists(bind, tenant_id, "es_PE", label_key):
            _insert_label(bind, tenant_id, "es_PE", label_key, es_value, label_type)
        if not _label_exists(bind, tenant_id, "en_US", label_key):
            _insert_label(bind, tenant_id, "en_US", label_key, en_value, label_type)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM localized_labels WHERE namespace = 'main_menu'"))
    bind.execute(sa.text("DELETE FROM namespaces WHERE id = 'main_menu'"))
