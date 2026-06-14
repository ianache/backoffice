"""
Tests for the Labels admin CRUD router: namespace + label CRUD with
role/scope checks, audit logging, optimistic-concurrency 409, UXWriter
value-only access, and the restore-override endpoint.

Plan: 20-03
Covers: LBL-09 (namespace/label CRUD role gating), LBL-10 (audit logging on
every mutation), LBL-11 (409 optimistic concurrency), LBL-12 (UXWriter
value-only PATCH).

Uses an in-memory SQLite AsyncSession (mirrors test_labels_resolve.py /
test_labels_service.py / test_labels_sdk_router.py conventions) wired into
app.main.app via a get_db dependency override, plus FastAPI's TestClient for
HTTP-level assertions (role checks, status codes, audit log side effects).
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.dependencies import get_db, verify_internal_secret
from app.config import settings
from app.domains.audit.models import AuditLog
from app.domains.audit.schemas import ActionType
from app.domains.labels.models import Namespace, LocalizedLabel
from app.domains.labels import service as labels_service
from app.main import app


INTERNAL_HEADERS = {"X-Internal-Secret": settings.internal_secret}


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite AsyncSession, fresh schema per test."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def client(db_session):
    """TestClient with get_db and verify_internal_secret overridden."""
    async def _override_get_db():
        yield db_session

    async def _override_verify_internal_secret():
        return None

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[verify_internal_secret] = _override_verify_internal_secret
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(verify_internal_secret, None)


@pytest.fixture(autouse=True)
def _clear_label_cache():
    """Ensure cache isolation between tests (module-level singleton)."""
    labels_service.clear_cache()
    yield
    labels_service.clear_cache()


async def _add_namespace(db_session: AsyncSession, namespace_id: str = "common", strategy: str = "lazy"):
    ns = Namespace(id=namespace_id, strategy=strategy, description=None)
    db_session.add(ns)
    await db_session.commit()
    return ns


async def _add_label(
    db_session: AsyncSession,
    *,
    tenant_id: str,
    company_id=None,
    product_id=None,
    namespace: str,
    locale: str,
    label_key: str,
    label_value: str,
    version: int = 1,
):
    row = LocalizedLabel(
        tenant_id=tenant_id,
        company_id=company_id,
        product_id=product_id,
        namespace=namespace,
        locale=locale,
        label_key=label_key,
        label_value=label_value,
        label_type="LABEL",
        params="[]",
        description=None,
        version=version,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Test 1: namespace CRUD requires admin role
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_namespace_crud_requires_admin_role(db_session, client):
    headers_viewer = {**INTERNAL_HEADERS, "X-User-Roles": "TenantViewer", "X-User-Sub": "u1", "X-User-Email": "viewer@example.com"}
    resp = client.post("/api/v1/labels/namespaces", json={"id": "common", "strategy": "lazy"}, headers=headers_viewer)
    assert resp.status_code == 403

    for role in ("PlatformAdmin", "TenantAdmin", "TenantOwner", "ProductManager"):
        headers = {**INTERNAL_HEADERS, "X-User-Roles": role, "X-User-Sub": "u1", "X-User-Email": "admin@example.com"}
        resp = client.post(
            "/api/v1/labels/namespaces",
            json={"id": f"ns_{role.lower()}", "strategy": "lazy"},
            headers=headers,
        )
        assert resp.status_code == 201, f"{role} should be able to create namespaces: {resp.text}"


# ---------------------------------------------------------------------------
# Test 2: create_label writes audit log
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_label_writes_audit_log(db_session, client):
    await _add_namespace(db_session, "common", strategy="lazy")

    headers = {**INTERNAL_HEADERS, "X-User-Roles": "TenantAdmin", "X-User-Sub": "u1", "X-User-Email": "admin@example.com"}
    payload = {
        "tenant_id": "T",
        "company_id": None,
        "product_id": None,
        "namespace": "common",
        "label_key": "accept",
        "label_type": "LABEL",
        "params": [],
        "description": None,
        "values": {"es_PE": "Aceptar", "en_US": "Accept"},
    }
    resp = client.post("/api/v1/labels/keys", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert len(body) == 2

    result = await db_session.execute(select(AuditLog).where(AuditLog.action_type == ActionType.CREATE_LABEL))
    entries = result.scalars().all()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.target_type == "LOCALIZED_LABEL"
    import json as _json
    payload_after = _json.loads(entry.payload_after)
    assert isinstance(payload_after, dict)
    assert len(payload_after["labels"]) == 2
    assert payload_after["labels"][0]["label_key"] == "accept"


# ---------------------------------------------------------------------------
# Test 3: update_label version conflict returns 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_label_version_conflict_returns_409(db_session, client):
    await _add_namespace(db_session, "common", strategy="lazy")
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )

    headers = {**INTERNAL_HEADERS, "X-User-Roles": "TenantAdmin", "X-User-Sub": "u1", "X-User-Email": "admin@example.com"}
    resp = client.patch(
        f"/api/v1/labels/keys/{label.id}",
        json={"values": {"es_PE": "Aceptar (nuevo)"}, "version": 999},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios."


# ---------------------------------------------------------------------------
# Test 4: UXWriter rejected from structure-edit endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_uxwriter_rejected_from_structure_edit(db_session, client):
    await _add_namespace(db_session, "common", strategy="lazy")
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )

    headers = {**INTERNAL_HEADERS, "X-User-Roles": "UXWriter", "X-User-Sub": "u2", "X-User-Email": "writer@example.com"}

    resp = client.patch(
        f"/api/v1/labels/keys/{label.id}",
        json={"values": {"es_PE": "Aceptar (nuevo)"}, "version": 1},
        headers=headers,
    )
    assert resp.status_code == 403

    resp = client.post("/api/v1/labels/namespaces", json={"id": "other_ns", "strategy": "lazy"}, headers=headers)
    assert resp.status_code == 403

    resp = client.delete(f"/api/v1/labels/keys/{label.id}", headers=headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Test 5: UXWriter can PATCH /keys/{id}/value
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_uxwriter_can_patch_value(db_session, client):
    await _add_namespace(db_session, "common", strategy="lazy")
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )

    headers = {**INTERNAL_HEADERS, "X-User-Roles": "UXWriter", "X-User-Sub": "u2", "X-User-Email": "writer@example.com"}
    resp = client.patch(
        f"/api/v1/labels/keys/{label.id}/value",
        json={"locale": "es_PE", "label_value": "Aceptar (editado)", "version": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["label_value"] == "Aceptar (editado)"
    assert body["version"] == 2

    result = await db_session.execute(select(AuditLog).where(AuditLog.action_type == ActionType.UPDATE_LABEL))
    entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].user_id == "u2"


# ---------------------------------------------------------------------------
# Test 6: namespace update + delete write audit entries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_namespace_update_and_delete_audit(db_session, client):
    await _add_namespace(db_session, "common", strategy="lazy")

    headers = {**INTERNAL_HEADERS, "X-User-Roles": "TenantAdmin", "X-User-Sub": "u1", "X-User-Email": "admin@example.com", "X-User-Tenant-Id": "T"}

    resp = client.patch("/api/v1/labels/namespaces/common", json={"strategy": "eager"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["strategy"] == "eager"

    resp = client.delete("/api/v1/labels/namespaces/common", headers=headers)
    assert resp.status_code == 204

    result = await db_session.execute(select(AuditLog).where(AuditLog.action_type == ActionType.UPDATE_NAMESPACE))
    assert len(result.scalars().all()) == 1

    result = await db_session.execute(select(AuditLog).where(AuditLog.action_type == ActionType.DELETE_NAMESPACE))
    assert len(result.scalars().all()) == 1


# ---------------------------------------------------------------------------
# Test 7: restore override endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_restore_override_endpoint(db_session, client):
    await _add_namespace(db_session, "common", strategy="lazy")
    # Tenant-level base value
    await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )
    # Company-level override
    await _add_label(
        db_session, tenant_id="T", company_id="C1", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar (Empresa)", version=1,
    )

    headers = {**INTERNAL_HEADERS, "X-User-Roles": "TenantAdmin", "X-User-Sub": "u1", "X-User-Email": "admin@example.com"}
    restore_payload = {
        "tenant_id": "T",
        "company_id": "C1",
        "product_id": None,
        "namespace": "common",
        "locale": "es_PE",
        "label_key": "accept",
    }

    resp = client.post("/api/v1/labels/keys/restore", json=restore_payload, headers=headers)
    assert resp.status_code == 204

    result = await db_session.execute(select(AuditLog).where(AuditLog.action_type == ActionType.DELETE_LABEL))
    entries = result.scalars().all()
    assert len(entries) == 1

    # Second restore on the same (now-deleted) override returns 404
    resp = client.post("/api/v1/labels/keys/restore", json=restore_payload, headers=headers)
    assert resp.status_code == 404
