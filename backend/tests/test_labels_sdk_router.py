"""
Tests for SDK-facing labels endpoints (two-phase hydration + missing-label
reporting) and INVALIDATE_NAMESPACE WebSocket broadcast on admin label
mutations.

Plan: 20-04
Covers: LBL-05 (bootstrap, eager namespaces), LBL-06 (prefetch, lazy
namespaces), LBL-07 (missing-label reporting + INVALIDATE_NAMESPACE broadcast).

Uses an in-memory SQLite AsyncSession (mirrors test_labels_resolve.py /
test_labels_service.py conventions) wired into app.main.app via a get_db
dependency override, plus FastAPI's TestClient for HTTP-level assertions
(SDK auth, status codes, response shapes).
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.dependencies import get_db
from app.config import settings
from app.domains.labels.models import Namespace, LocalizedLabel, MissingLabelReport
from app.domains.labels import service as labels_service
from app.main import app


SDK_HEADERS = {"Authorization": f"Bearer {settings.sdk_secret_key}"}


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
    """TestClient with get_db overridden to the in-memory SQLite session."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def _clear_label_cache():
    """Ensure cache isolation between tests (module-level singleton)."""
    labels_service.clear_cache()
    yield
    labels_service.clear_cache()


async def _add_namespace(db_session: AsyncSession, namespace_id: str, strategy: str = "lazy"):
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
        version=1,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Test 1: /labels/bootstrap — eager namespaces only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_labels_bootstrap_returns_eager_namespaces(db_session, client):
    await _add_namespace(db_session, "common", strategy="eager")
    await _add_namespace(db_session, "page_dashboard", strategy="lazy")
    await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="btn_aceptar", label_value="Aceptar",
    )
    await _add_label(
        db_session, tenant_id="T", namespace="page_dashboard", locale="es_PE",
        label_key="title", label_value="Dashboard",
    )

    resp = client.get("/api/v1/sdk/labels/bootstrap", params={"tenant_id": "T", "locale": "es_PE"}, headers=SDK_HEADERS)

    assert resp.status_code == 200
    body = resp.json()
    assert body["locale"] == "es_PE"
    assert body["namespaces"] == {"common": {"btn_aceptar": "Aceptar"}}
    assert "page_dashboard" not in body["namespaces"]


# ---------------------------------------------------------------------------
# Test 2: /labels/bootstrap — company/product override-by-proximity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_labels_bootstrap_applies_company_product_overrides(db_session, client):
    await _add_namespace(db_session, "common", strategy="eager")
    # Tenant-level base value
    await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="btn_aceptar", label_value="Aceptar",
    )
    # Company-level override
    await _add_label(
        db_session, tenant_id="T", company_id="C1", namespace="common", locale="es_PE",
        label_key="btn_aceptar", label_value="Aceptar (Empresa)",
    )
    # Product-level override (most specific)
    await _add_label(
        db_session, tenant_id="T", company_id="C1", product_id="P1", namespace="common", locale="es_PE",
        label_key="btn_aceptar", label_value="Aceptar (Producto)",
    )

    resp = client.get(
        "/api/v1/sdk/labels/bootstrap",
        params={"tenant_id": "T", "locale": "es_PE", "company_id": "C1", "product_id": "P1"},
        headers=SDK_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["namespaces"]["common"]["btn_aceptar"] == "Aceptar (Producto)"


# ---------------------------------------------------------------------------
# Test 3: /labels/prefetch — lazy namespaces, including empty
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_labels_prefetch_returns_requested_namespaces(db_session, client):
    await _add_namespace(db_session, "page_dashboard", strategy="lazy")
    await _add_namespace(db_session, "page_settings", strategy="lazy")
    await _add_label(
        db_session, tenant_id="T", namespace="page_dashboard", locale="es_PE",
        label_key="title", label_value="Tablero",
    )
    # page_settings intentionally has no label rows

    resp = client.get(
        "/api/v1/sdk/labels/prefetch",
        params={"tenant_id": "T", "locale": "es_PE", "namespaces": "page_dashboard,page_settings"},
        headers=SDK_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["namespaces"]["page_dashboard"] == {"title": "Tablero"}
    assert body["namespaces"]["page_settings"] == {}


# ---------------------------------------------------------------------------
# Test 4: POST /labels/missing — creates dedup'd, hit-counted report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_labels_missing_endpoint_creates_report(db_session, client):
    payload = {
        "tenant_id": "T",
        "company_id": None,
        "product_id": None,
        "namespace": "page_dashboard",
        "label_key": "missing_key",
        "locale": "es_PE",
    }

    resp1 = client.post("/api/v1/sdk/labels/missing", json=payload, headers=SDK_HEADERS)
    assert resp1.status_code == 204

    reports = await labels_service.list_missing_label_reports(db_session, tenant_id="T")
    assert len(reports) == 1
    assert reports[0].hits == 1
    assert reports[0].label_key == "missing_key"

    resp2 = client.post("/api/v1/sdk/labels/missing", json=payload, headers=SDK_HEADERS)
    assert resp2.status_code == 204

    reports = await labels_service.list_missing_label_reports(db_session, tenant_id="T")
    assert len(reports) == 1
    assert reports[0].hits == 2


# ---------------------------------------------------------------------------
# Test 5: SDK auth required for all 3 new endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sdk_labels_endpoints_require_sdk_auth(db_session, client):
    resp = client.get("/api/v1/sdk/labels/bootstrap", params={"tenant_id": "T", "locale": "es_PE"})
    assert resp.status_code in (401, 403)

    resp = client.get(
        "/api/v1/sdk/labels/prefetch",
        params={"tenant_id": "T", "locale": "es_PE", "namespaces": "page_dashboard"},
    )
    assert resp.status_code in (401, 403)

    resp = client.post(
        "/api/v1/sdk/labels/missing",
        json={
            "tenant_id": "T",
            "namespace": "page_dashboard",
            "label_key": "missing_key",
            "locale": "es_PE",
        },
    )
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Test 6: admin label mutation broadcasts INVALIDATE_NAMESPACE over WS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_label_value_broadcasts_invalidate_namespace(db_session, client):
    from app.dependencies import verify_internal_secret

    await _add_namespace(db_session, "common", strategy="eager")
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="btn_aceptar", label_value="Aceptar",
    )

    async def _override_verify_internal_secret():
        return None

    app.dependency_overrides[verify_internal_secret] = _override_verify_internal_secret

    broadcast_mock = AsyncMock()
    original_ws_manager = app.state.ws_manager
    app.state.ws_manager = SimpleNamespace(broadcast=broadcast_mock)

    # Resolve the actual mounted path for update_key_value — the labels router
    # may be included with or without an "/api/v1" prefix depending on how
    # app.main wires it up (concurrent plans 20-03/20-09 own that wiring).
    path_template = next(
        r.path for r in app.routes
        if getattr(r, "name", None) == "update_key_value"
    )
    path = path_template.format(label_id=label.id)

    try:
        resp = client.patch(
            path,
            json={"locale": "es_PE", "label_value": "Aceptar (actualizado)", "version": 1},
            headers={
                "X-Internal-Secret": "test",
                "X-User-Roles": "PlatformAdmin",
            },
        )
        assert resp.status_code == 200
        broadcast_mock.assert_awaited_once_with("T", {"type": "INVALIDATE_NAMESPACE", "namespace": "common"})
    finally:
        app.state.ws_manager = original_ws_manager
        app.dependency_overrides.pop(verify_internal_secret, None)
