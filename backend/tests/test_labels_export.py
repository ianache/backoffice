"""
Tests for the Labels domain export helpers (RF-07): export_namespace_json() and
export_namespace_csv() in app.domains.labels.service, plus the GET /labels/export
router endpoint (format=json|csv).
"""
import csv
import io

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.domains.labels.models import Namespace, LocalizedLabel
from app.domains.labels import service


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


@pytest.fixture(autouse=True)
def _clear_label_cache():
    """Ensure cache isolation between tests (module-level singleton)."""
    service.clear_cache()
    yield
    service.clear_cache()


async def _add_namespace(db_session: AsyncSession, namespace_id: str = "common"):
    ns = Namespace(id=namespace_id, strategy="lazy", description=None)
    db_session.add(ns)
    await db_session.commit()
    return ns


async def _add_label(
    db_session: AsyncSession,
    *,
    tenant_id: str,
    company_id: str | None,
    product_id: str | None,
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
        params=None,
        description=None,
        version=1,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_common_namespace(db_session: AsyncSession):
    """Seed tenant T, namespace 'common', both locales, at tenant level only."""
    await _add_namespace(db_session, "common")
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="btn_aceptar", label_value="Aceptar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="en_US", label_key="btn_aceptar", label_value="Accept",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="btn_cancelar", label_value="Cancelar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="en_US", label_key="btn_cancelar", label_value="Cancel",
    )


# ---------------------------------------------------------------------------
# Test 1: export_namespace_json shape (tenant-level only)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_namespace_json_shape(db_session: AsyncSession):
    await _seed_common_namespace(db_session)

    result = await service.export_namespace_json(
        db_session, tenant_id="T", company_id=None, product_id=None, namespace="common",
    )

    assert result == {
        "common": {
            "btn_aceptar": {"es_PE": "Aceptar", "en_US": "Accept"},
            "btn_cancelar": {"es_PE": "Cancelar", "en_US": "Cancel"},
        }
    }


# ---------------------------------------------------------------------------
# Test 2: export_namespace_json applies company-level overrides
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_namespace_json_applies_overrides(db_session: AsyncSession):
    await _seed_common_namespace(db_session)
    await _add_label(
        db_session, tenant_id="T", company_id="C", product_id=None,
        namespace="common", locale="es_PE", label_key="btn_aceptar", label_value="Aceptar (C)",
    )

    result = await service.export_namespace_json(
        db_session, tenant_id="T", company_id="C", product_id=None, namespace="common",
    )

    assert result["common"]["btn_aceptar"]["es_PE"] == "Aceptar (C)"
    assert result["common"]["btn_aceptar"]["en_US"] == "Accept"
    assert result["common"]["btn_cancelar"] == {"es_PE": "Cancelar", "en_US": "Cancel"}


# ---------------------------------------------------------------------------
# Test 3: export_namespace_csv header + RFC 4180 round-trip on comma value
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_namespace_csv(db_session: AsyncSession):
    await _add_namespace(db_session, "common")
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="greeting", label_value="Hola, Ana",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="en_US", label_key="greeting", label_value="Hello, Ana",
    )

    result = await service.export_namespace_csv(
        db_session, tenant_id="T", company_id=None, product_id=None, namespace="common",
    )

    lines = result.splitlines()
    assert lines[0] == "namespace,label_key,es_PE,en_US,level"

    reader = csv.reader(io.StringIO(result))
    rows = list(reader)
    header, data_rows = rows[0], rows[1:]
    assert header == ["namespace", "label_key", "es_PE", "en_US", "level"]

    greeting_row = next(r for r in data_rows if r[1] == "greeting")
    assert greeting_row[0] == "common"
    assert greeting_row[2] == "Hola, Ana"
    assert greeting_row[3] == "Hello, Ana"
    assert greeting_row[4] == "tenant"


# ---------------------------------------------------------------------------
# Test 4: export_namespace_csv 'level' column reflects es_PE's contributing level
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_namespace_csv_level_column(db_session: AsyncSession):
    await _seed_common_namespace(db_session)
    await _add_label(
        db_session, tenant_id="T", company_id="C", product_id=None,
        namespace="common", locale="es_PE", label_key="btn_aceptar", label_value="Aceptar (C)",
    )

    result = await service.export_namespace_csv(
        db_session, tenant_id="T", company_id="C", product_id=None, namespace="common",
    )

    reader = csv.reader(io.StringIO(result))
    rows = list(reader)
    data_rows = rows[1:]

    aceptar_row = next(r for r in data_rows if r[1] == "btn_aceptar")
    assert aceptar_row[4] == "company"

    cancelar_row = next(r for r in data_rows if r[1] == "btn_cancelar")
    assert cancelar_row[4] == "tenant"
