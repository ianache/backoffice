"""
Tests for the Labels domain service: Namespace/LocalizedLabel CRUD and
missing-label report upsert/dedup.
Covers: namespace CRUD, create_label() per-locale rows + cache invalidation,
update_label_value() 409 on version mismatch, report_missing_label() dedup
and hit-counting, and missing-report auto-cleanup on create_label().
"""
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.domains.labels.models import Namespace, LocalizedLabel, MissingLabelReport
from app.domains.labels.schemas import (
    NamespaceCreate, NamespaceUpdate, LabelCreate, LabelValueUpdate, MissingLabelReportCreate,
)
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
    company_id: str | None = None,
    product_id: str | None = None,
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
        params=None,
        description=None,
        version=version,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Test 1: Namespace CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_namespace_crud(db_session: AsyncSession):
    created = await service.create_namespace(
        db_session,
        NamespaceCreate(
            id="common",
            tenant_id="T",
            company_id="C",
            product_id="P",
            strategy="lazy",
            description="Common labels",
        ),
    )
    assert created.id == "common"
    assert created.tenant_id == "T"
    assert created.company_id == "C"
    assert created.product_id == "P"
    assert created.strategy == "lazy"
    assert created.description == "Common labels"

    namespaces = await service.list_namespaces(db_session)
    assert any(ns.id == "common" for ns in namespaces)

    updated = await service.update_namespace(
        db_session,
        "common",
        NamespaceUpdate(tenant_id="T2", company_id=None, product_id="P2", strategy="eager", description="Updated description"),
    )
    assert updated is not None
    assert updated.tenant_id == "T2"
    assert updated.company_id is None
    assert updated.product_id == "P2"
    assert updated.strategy == "eager"
    assert updated.description == "Updated description"

    deleted = await service.delete_namespace(db_session, "common")
    assert deleted is True

    namespaces_after = await service.list_namespaces(db_session)
    assert all(ns.id != "common" for ns in namespaces_after)


@pytest.mark.asyncio
async def test_update_namespace_renames_referenced_labels_and_missing_reports(db_session: AsyncSession):
    await service.create_namespace(db_session, NamespaceCreate(id="old_ns", strategy="lazy"))
    await _add_label(
        db_session,
        tenant_id="T",
        product_id="backoffice",
        namespace="old_ns",
        locale="es_PE",
        label_key="title",
        label_value="Titulo",
    )
    db_session.add(MissingLabelReport(
        tenant_id="T",
        product_id="backoffice",
        namespace="old_ns",
        label_key="subtitle",
        locale="es_PE",
        hits=1,
    ))
    await db_session.commit()

    updated = await service.update_namespace(
        db_session,
        "old_ns",
        NamespaceUpdate(id="new_ns", strategy="eager", description="Renamed"),
    )

    assert updated is not None
    assert updated.id == "new_ns"
    assert updated.strategy == "eager"
    assert updated.description == "Renamed"
    assert await service.get_namespace(db_session, "old_ns") is None

    labels = (await db_session.execute(select(LocalizedLabel))).scalars().all()
    reports = (await db_session.execute(select(MissingLabelReport))).scalars().all()
    assert {label.namespace for label in labels} == {"new_ns"}
    assert {report.namespace for report in reports} == {"new_ns"}


# ---------------------------------------------------------------------------
# Test 2: create_label() persists one row per locale + invalidates cache
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_label_persists_one_row_per_locale_and_invalidates_cache(db_session: AsyncSession):
    await _add_namespace(db_session)

    # Prime the cache for tenant T / namespace common / es_PE
    first = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert first == {}

    payload = LabelCreate(
        tenant_id="T",
        company_id=None,
        product_id=None,
        namespace="common",
        label_key="accept",
        label_type="LABEL",
        params=[],
        description=None,
        values={"es_PE": "Aceptar", "en_US": "Accept"},
    )
    created = await service.create_label(db_session, payload)

    assert len(created) == 2
    locales = {row.locale: row.label_value for row in created}
    assert locales == {"es_PE": "Aceptar", "en_US": "Accept"}
    for row in created:
        assert row.label_key == "accept"
        assert row.tenant_id == "T"
        assert row.version == 1

    # Cache invalidated — resolve_labels() now reflects the new label
    second = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert second == {"accept": "Aceptar"}
    # Different dict object — proves the cache was refreshed, not stale
    assert first is not second


# ---------------------------------------------------------------------------
# Test 3: update_label_value() — 409 on version mismatch, success increments version
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_label_value_version_mismatch_raises_409(db_session: AsyncSession):
    await _add_namespace(db_session)
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_label_value(
            db_session, label.id,
            LabelValueUpdate(locale="es_PE", label_value="Aceptar (nuevo)", version=999),
        )

    assert exc_info.value.status_code == 409
    assert "modificada por otro usuario" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_label_value_success_increments_version_and_invalidates_cache(db_session: AsyncSession):
    await _add_namespace(db_session)
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )

    # Prime the cache
    first = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert first == {"accept": "Aceptar"}

    updated = await service.update_label_value(
        db_session, label.id,
        LabelValueUpdate(locale="es_PE", label_value="Aceptar (editado)", version=1),
    )

    assert updated.label_value == "Aceptar (editado)"
    assert updated.version == 2

    second = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert second == {"accept": "Aceptar (editado)"}
    assert first is not second


# ---------------------------------------------------------------------------
# Test 4: report_missing_label() dedup + hit-counting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_report_missing_label_dedup_and_hit_counting(db_session: AsyncSession):
    await _add_namespace(db_session)

    payload = MissingLabelReportCreate(
        tenant_id="T", company_id=None, product_id=None,
        namespace="common", label_key="missing_key", locale="es_PE",
    )

    first = await service.report_missing_label(db_session, payload)
    assert first.hits == 1
    assert first.tenant_id == "T"
    assert first.label_key == "missing_key"

    second = await service.report_missing_label(db_session, payload)
    assert second.hits == 2
    # Same row (dedup), not a new row
    assert second.id == first.id

    reports = await service.list_missing_label_reports(db_session, tenant_id="T")
    assert len(reports) == 1
    assert reports[0].hits == 2


# ---------------------------------------------------------------------------
# Test 5: create_label() clears matching MissingLabelReport rows (RF-06 auto-cleanup)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_label_clears_matching_missing_label_report(db_session: AsyncSession):
    await _add_namespace(db_session)

    # Report a missing key first
    await service.report_missing_label(
        db_session,
        MissingLabelReportCreate(
            tenant_id="T", company_id=None, product_id=None,
            namespace="common", label_key="accept", locale="es_PE",
        ),
    )
    reports_before = await service.list_missing_label_reports(db_session, tenant_id="T")
    assert len(reports_before) == 1

    # Now create the label for that key — should clear the missing report
    payload = LabelCreate(
        tenant_id="T",
        company_id=None,
        product_id=None,
        namespace="common",
        label_key="accept",
        label_type="LABEL",
        params=[],
        description=None,
        values={"es_PE": "Aceptar"},
    )
    await service.create_label(db_session, payload)

    reports_after = await service.list_missing_label_reports(db_session, tenant_id="T")
    assert reports_after == []


# ---------------------------------------------------------------------------
# delete_label() — removes row and invalidates cache
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_label_removes_row_and_invalidates_cache(db_session: AsyncSession):
    await _add_namespace(db_session)
    label = await _add_label(
        db_session, tenant_id="T", namespace="common", locale="es_PE",
        label_key="accept", label_value="Aceptar", version=1,
    )

    first = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert first == {"accept": "Aceptar"}

    deleted = await service.delete_label(db_session, label.id)
    assert deleted is True

    second = await service.resolve_labels(
        db_session, tenant_id="T", company_id=None, product_id=None,
        namespace="common", locale="es_PE",
    )
    assert second == {}

    # Deleting a non-existent label returns False
    deleted_again = await service.delete_label(db_session, label.id)
    assert deleted_again is False
