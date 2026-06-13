"""seed_login_namespace_labels

Revision ID: g004
Revises: g003
Create Date: 2026-06-13

Seeds the `login` namespace (eager strategy) plus bilingual tenant-level labels
for the login screen. Idempotent via INSERT IGNORE on the unique scope+key index.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'g004'
down_revision: Union[str, None] = 'g003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LOGIN_LABELS = [
    # (label_key, label_type, es_PE, en_US)
    ("brand_tagline", "LABEL", "Centro de Control y Administracion Multi-tenant", "Control Center & Multi-tenant Administration"),
    ("welcome_title", "LABEL", "Bienvenido nuevamente", "Welcome back"),
    ("welcome_body", "LABEL", "Accede a tu panel administrativo usando credenciales empresariales.", "Access your administrative dashboard using enterprise credentials."),
    ("sso_action", "LABEL", "Iniciar sesion con Keycloak", "Sign in with Keycloak"),
    ("sso_connecting", "LABEL", "Conectando...", "Connecting..."),
    ("divider_or", "LABEL", "o", "or"),
    ("local_action", "LABEL", "Acceso de administrador local", "Local Admin Login"),
    ("email_label", "LABEL", "Correo electronico", "Email"),
    ("password_label", "LABEL", "Contrasena", "Password"),
    ("submit_action", "LABEL", "Iniciar sesion", "Sign In"),
    ("submit_loading", "LABEL", "Iniciando sesion...", "Signing in..."),
    ("help_prompt", "LABEL", "Problemas para iniciar sesion?", "Trouble signing in?"),
    ("help_action", "LABEL", "Contactar soporte", "Contact Support"),
    ("error_invalid_credentials", "LABEL", "Correo o contrasena invalidos.", "Invalid email or password."),
    ("error_authentication_failed", "LABEL", "No se pudo completar la autenticacion. Intenta nuevamente.", "Authentication could not be completed. Please try again."),
    ("error_generic", "LABEL", "El inicio de sesion fallo. Intenta nuevamente o contacta a soporte.", "Sign-in failed. Please try again or contact support."),
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

    # 1. Create the `login` namespace (eager strategy)
    bind.execute(sa.text(
        "INSERT IGNORE INTO namespaces (id, strategy, description) "
        "VALUES ('login', 'eager', :desc)"
    ), {"desc": "Login page localized labels"})

    # 2. Seed tenant-level login labels (es_PE + en_US) for both locales
    for label_key, label_type, es_value, en_value in LOGIN_LABELS:
        bind.execute(sa.text(
            "INSERT IGNORE INTO localized_labels "
            "(tenant_id, company_id, product_id, namespace, locale, label_key, label_value, label_type, params, version) "
            "VALUES (:tid, NULL, NULL, 'login', 'es_PE', :key, :val, :ltype, '[]', 1)"
        ), {"tid": tenant_id, "key": label_key, "val": es_value, "ltype": label_type})
        bind.execute(sa.text(
            "INSERT IGNORE INTO localized_labels "
            "(tenant_id, company_id, product_id, namespace, locale, label_key, label_value, label_type, params, version) "
            "VALUES (:tid, NULL, NULL, 'login', 'en_US', :key, :val, :ltype, '[]', 1)"
        ), {"tid": tenant_id, "key": label_key, "val": en_value, "ltype": label_type})


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM localized_labels WHERE namespace = 'login'"))
    bind.execute(sa.text("DELETE FROM namespaces WHERE id = 'login'"))
