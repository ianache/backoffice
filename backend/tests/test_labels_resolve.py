"""
Tests for the Labels domain resolver: resolve_labels() inheritance + in-memory cache.
Covers: TC-01 (no overrides), TC-02 (company override), TC-03 (product override),
cache hit, and cache invalidation.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

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


# ---------------------------------------------------------------------------
# TC-01: no overrides — tenant-level labels returned
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_labels_tenant_only_no_overrides(db_session: AsyncSession):
    await _add_namespace(db_session)
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="cancel", label_value="Cancelar",
    )

    resolved = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )

    assert resolved == {"accept": "Aceptar", "cancel": "Cancelar"}


# ---------------------------------------------------------------------------
# TC-02: company override — company value wins for overridden key only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_labels_company_override(db_session: AsyncSession):
    await _add_namespace(db_session)
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="cancel", label_value="Cancelar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id="C", product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar (C)",
    )

    resolved = await service.resolve_labels(
        db_session, tenant_id="T", company_id="C", product_id=None,
        namespace="common", locale="es_PE",
    )

    assert resolved == {"accept": "Aceptar (C)", "cancel": "Cancelar"}


# ---------------------------------------------------------------------------
# TC-03: product override — product wins over company wins over tenant
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_labels_product_override(db_session: AsyncSession):
    await _add_namespace(db_session)
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="cancel", label_value="Cancelar",
    )
    await _add_label(
        db_session, tenant_id="T", company_id="C", product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar (C)",
    )
    await _add_label(
        db_session, tenant_id="T", company_id="C", product_id="P",
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar (P)",
    )

    resolved = await service.resolve_labels(
        db_session, tenant_id="T", company_id="C", product_id="P",
        namespace="common", locale="es_PE",
    )

    assert resolved == {"accept": "Aceptar (P)", "cancel": "Cancelar"}


# ---------------------------------------------------------------------------
# Cache hit: second call returns cached (possibly stale) data without re-query
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_labels_cache_hit_returns_stale_data(db_session: AsyncSession):
    await _add_namespace(db_session)
    row = await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar",
    )

    first = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert first == {"accept": "Aceptar"}

    # Mutate the DB row directly without invalidating the cache
    row.label_value = "Aceptar (changed)"
    db_session.add(row)
    await db_session.commit()

    second = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )

    # Still the stale cached value
    assert second == {"accept": "Aceptar"}
    # Same dict object returned from cache
    assert first is second


# ---------------------------------------------------------------------------
# Cache invalidation: invalidate_namespace_cache() forces a fresh resolution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_invalidation(db_session: AsyncSession):
    await _add_namespace(db_session)
    row = await _add_label(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE", label_key="accept", label_value="Aceptar",
    )

    first = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert first == {"accept": "Aceptar"}

    row.label_value = "Aceptar (changed)"
    db_session.add(row)
    await db_session.commit()

    service.invalidate_namespace_cache("T", "common")

    second = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )

    assert second == {"accept": "Aceptar (changed)"}
