"""
Tests for the GET /labels/missing admin diagnostics endpoint (RF-06) and a
smoke test confirming the labels router is registered in app.main.

Plan: 20-03
Covers: LBL-09..12 (admin router registration + missing-label diagnostics).
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.dependencies import get_db, verify_internal_secret
from app.config import settings
from app.domains.labels.models import LocalizedLabel, MissingLabelReport
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


async def _add_missing_report(
    db_session: AsyncSession,
    *,
    tenant_id: str,
    namespace: str,
    label_key: str,
    locale: str,
    hits: int = 1,
    company_id=None,
    product_id=None,
):
    row = MissingLabelReport(
        tenant_id=tenant_id,
        company_id=company_id,
        product_id=product_id,
        namespace=namespace,
        label_key=label_key,
        locale=locale,
        hits=hits,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


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
# Test 1: GET /labels/missing returns tenant-scoped, hits-descending results
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_missing_label_reports(db_session, client):
    await _add_missing_report(db_session, tenant_id="T", namespace="page_dashboard", label_key="title", locale="es_PE", hits=1)
    await _add_missing_report(db_session, tenant_id="T", namespace="common", label_key="accept", locale="es_PE", hits=3)
    # Different tenant — must not appear in results for T
    await _add_missing_report(db_session, tenant_id="OTHER", namespace="common", label_key="cancel", locale="es_PE", hits=5)

    resp = client.get("/api/v1/labels/missing", params={"tenant_id": "T"}, headers=INTERNAL_HEADERS)
    assert resp.status_code == 200
    body = resp.json()

    assert len(body) == 2
    assert {row["tenant_id"] for row in body} == {"T"}

    # Ordered by hits descending
    assert body[0]["hits"] == 3
    assert body[0]["label_key"] == "accept"
    assert body[0]["namespace"] == "common"
    assert body[0]["locale"] == "es_PE"
    assert "last_reported_at" in body[0]

    assert body[1]["hits"] == 1
    assert body[1]["label_key"] == "title"


# ---------------------------------------------------------------------------
# Test 2: labels router is registered in app.main
# ---------------------------------------------------------------------------

def test_app_includes_labels_router():
    paths = [r.path for r in app.routes]
    assert any("/labels/namespaces" in p for p in paths), f"No /labels/namespaces route found in: {paths}"


@pytest.mark.asyncio
async def test_list_missing_hides_reports_for_existing_resolved_labels(db_session, client):
    await _add_missing_report(
        db_session,
        tenant_id="T",
        product_id="backoffice",
        namespace="main_menu",
        label_key="mm_users",
        locale="es_PE",
        hits=7,
    )
    await _add_label(
        db_session,
        tenant_id="T",
        product_id="backoffice",
        namespace="main_menu",
        locale="es_PE",
        label_key="mm_users",
        label_value="Usuarios",
    )

    resp = client.get("/api/v1/labels/missing", params={"tenant_id": "T"}, headers=INTERNAL_HEADERS)

    assert resp.status_code == 200
    assert resp.json() == []

    reports = await labels_service.list_missing_label_reports(db_session, tenant_id="T")
    assert reports == []


@pytest.mark.asyncio
async def test_list_missing_hides_namespace_prefixed_reports_for_existing_labels(db_session, client):
    await _add_missing_report(
        db_session,
        tenant_id="T",
        product_id="backoffice",
        namespace="main_menu",
        label_key="main_menu.mm_users",
        locale="es_PE",
        hits=7,
    )
    await _add_label(
        db_session,
        tenant_id="T",
        product_id="backoffice",
        namespace="main_menu",
        locale="es_PE",
        label_key="mm_users",
        label_value="Usuarios",
    )

    resp = client.get("/api/v1/labels/missing", params={"tenant_id": "T"}, headers=INTERNAL_HEADERS)

    assert resp.status_code == 200
    assert resp.json() == []

    reports = await labels_service.list_missing_label_reports(db_session, tenant_id="T")
    assert reports == []
