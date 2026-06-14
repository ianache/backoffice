import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.dependencies import get_db, verify_internal_secret
from app.config import settings
from app.domains.observability.models import ServiceHealthSample
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
    """TestClient with get_db overridden."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_health_services_endpoint_requires_secret(client):
    # Without secret, fails with 401 or 403
    resp = client.get("/observability/health/services")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_services_endpoint(db_session, client):
    # Seed samples
    now = datetime.utcnow()
    sample1 = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=12.5,
        checked_at=now - timedelta(seconds=10),
    )
    sample2 = ServiceHealthSample(
        service_name="mysql",
        status="DEGRADED",
        latency_ms=150.0,
        checked_at=now,
    )
    db_session.add_all([sample1, sample2])
    await db_session.commit()

    resp = client.get("/observability/health/services", headers=INTERNAL_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    items = data["items"]
    # We should have the latest sample for fastapi and mysql
    fastapi_item = next(i for i in items if i["service_name"] == "fastapi")
    mysql_item = next(i for i in items if i["service_name"] == "mysql")
    
    assert fastapi_item["status"] == "UP"
    assert fastapi_item["latency_ms"] == 12.5
    assert mysql_item["status"] == "DEGRADED"
    assert mysql_item["latency_ms"] == 150.0


@pytest.mark.asyncio
async def test_metrics_endpoint_ranges(db_session, client):
    now = datetime.utcnow()
    # Seed samples for fastapi
    sample1 = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=45.0,
        checked_at=now - timedelta(hours=1),
    )
    sample2 = ServiceHealthSample(
        service_name="fastapi",
        status="DOWN",
        latency_ms=None,
        checked_at=now - timedelta(hours=2),
    )
    db_session.add_all([sample1, sample2])
    await db_session.commit()

    resp = client.get("/observability/metrics?range=24h", headers=INTERNAL_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "24h"
    assert "items" in data
    
    fastapi_metrics = next(i for i in data["items"] if i["service_name"] == "fastapi")
    assert fastapi_metrics["sample_count"] == 2
    assert fastapi_metrics["uptime_pct"] == 50.0
    assert fastapi_metrics["error_rate_pct"] == 50.0
    assert fastapi_metrics["p95_latency_ms"] == 45.0
    assert fastapi_metrics["p99_latency_ms"] == 45.0
    assert "history" in fastapi_metrics


@pytest.mark.asyncio
async def test_metrics_history_series_shape(db_session, client):
    now = datetime.utcnow()
    # Seed samples across two distinct hours
    s1 = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=10.0,
        checked_at=now - timedelta(hours=2),
    )
    s2 = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=20.0,
        checked_at=now - timedelta(hours=1),
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    resp = client.get("/observability/metrics?range=24h", headers=INTERNAL_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    
    fastapi_metrics = next(i for i in data["items"] if i["service_name"] == "fastapi")
    history = fastapi_metrics["history"]
    # Should have two points since we grouped hourly and seeded in different hours
    assert len(history) >= 2
    
    # Check shape of history elements
    for pt in history:
        assert "ts" in pt
        assert "avg_latency_ms" in pt
        assert pt["avg_latency_ms"] is None or isinstance(pt["avg_latency_ms"], (int, float))


@pytest.mark.asyncio
async def test_metrics_rejects_bad_range(client):
    resp = client.get("/observability/metrics?range=99y", headers=INTERNAL_HEADERS)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_metrics_accepts_tenant_id_unfiltered(db_session, client):
    # D-05: tenant_id accepted, but does not filter
    now = datetime.utcnow()
    sample = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=15.0,
        checked_at=now,
    )
    db_session.add(sample)
    await db_session.commit()

    resp = client.get("/observability/metrics?range=24h&tenant_id=tenant-123", headers=INTERNAL_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    fastapi_metrics = next(i for i in data["items"] if i["service_name"] == "fastapi")
    assert fastapi_metrics["sample_count"] == 1
