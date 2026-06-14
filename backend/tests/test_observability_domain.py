import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.database import Base
from app.domains.observability.models import ServiceHealthSample
from app.domains.observability.health_checker import _classify, health_checker_loop
from app.domains.observability import service, health_checker


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


def test_classify_thresholds():
    assert _classify(0.5) == "UP"
    assert _classify(99.9) == "UP"
    assert _classify(100.0) == "DEGRADED"
    assert _classify(250.0) == "DEGRADED"


@pytest.mark.asyncio
async def test_service_health_sample_model(db_session):
    sample = await service.write_sample(
        db_session,
        service_name="fastapi",
        status="UP",
        latency_ms=12.5,
        details="Responsive"
    )
    assert sample.id is not None
    assert sample.service_name == "fastapi"
    assert sample.status == "UP"
    assert sample.latency_ms == 12.5
    assert sample.details == "Responsive"

    # Query back
    stmt = select(ServiceHealthSample).where(ServiceHealthSample.service_name == "fastapi")
    loaded = (await db_session.execute(stmt)).scalar_one()
    assert loaded.id == sample.id
    assert loaded.status == "UP"


@pytest.mark.asyncio
async def test_health_checker_resilience(db_session, monkeypatch):
    called = []

    async def _check_fastapi(app):
        called.append("ok")
        return "UP", 10.0, None

    async def _check_mysql(app):
        called.append("fail")
        raise ValueError("Simulated network timeout")

    async def _check_bff(app):
        called.append("ok")
        return "UP", 10.0, None

    async def _check_keycloak(app):
        called.append("ok")
        return "UP", 10.0, None

    async def _check_ws_gateway(app):
        called.append("ok")
        return "UP", 10.0, None

    monkeypatch.setattr("app.domains.observability.health_checker._check_fastapi", _check_fastapi)
    monkeypatch.setattr("app.domains.observability.health_checker._check_mysql", _check_mysql)
    monkeypatch.setattr("app.domains.observability.health_checker._check_bff", _check_bff)
    monkeypatch.setattr("app.domains.observability.health_checker._check_keycloak", _check_keycloak)
    monkeypatch.setattr("app.domains.observability.health_checker._check_ws_gateway", _check_ws_gateway)

    # Mock AsyncSessionFactory to yield our test db_session
    class MockSessionFactory:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.domains.observability.health_checker.AsyncSessionFactory", MockSessionFactory)

    # Mock sleep to raise CancelledError so the infinite loop terminates immediately after first iteration
    async def mock_sleep(seconds):
        raise asyncio.CancelledError()

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    app = FastAPI()
    try:
        await health_checker_loop(app)
    except asyncio.CancelledError:
        pass

    assert len(called) == 5
    assert called.count("ok") == 4
    assert called.count("fail") == 1

    # Verify that DOWN sample was persisted for mysql
    stmt = select(ServiceHealthSample).order_by(ServiceHealthSample.id)
    samples = (await db_session.execute(stmt)).scalars().all()
    assert len(samples) == 5

    mysql_sample = next(s for s in samples if s.service_name == "mysql")
    assert mysql_sample.status == "DOWN"
    assert mysql_sample.latency_ms is None
    assert "Simulated network timeout" in mysql_sample.details


@pytest.mark.asyncio
async def test_prune_old_samples(db_session):
    now = datetime.utcnow()
    old_sample = ServiceHealthSample(
        service_name="mysql",
        status="UP",
        latency_ms=10.0,
        checked_at=now - timedelta(days=31)
    )
    new_sample = ServiceHealthSample(
        service_name="mysql",
        status="UP",
        latency_ms=15.0,
        checked_at=now
    )
    db_session.add_all([old_sample, new_sample])
    await db_session.commit()

    pruned = await service.prune_old_samples(db_session)
    assert pruned == 1

    # Check remaining
    stmt = select(ServiceHealthSample)
    remaining = (await db_session.execute(stmt)).scalars().all()
    assert len(remaining) == 1
    assert remaining[0].latency_ms == 15.0


@pytest.mark.asyncio
async def test_aggregate_metrics_history_buckets(db_session):
    now = datetime.utcnow()
    # Seed samples in distinct hours for "24h" history
    s1 = ServiceHealthSample(
        service_name="mysql",
        status="UP",
        latency_ms=10.0,
        checked_at=now
    )
    s2 = ServiceHealthSample(
        service_name="mysql",
        status="UP",
        latency_ms=20.0,
        checked_at=now
    )
    s3 = ServiceHealthSample(
        service_name="mysql",
        status="UP",
        latency_ms=60.0,
        checked_at=now - timedelta(hours=2)
    )
    db_session.add_all([s1, s2, s3])
    await db_session.commit()

    metrics = await service.aggregate_metrics(db_session, "mysql", "24h")
    assert metrics["service_name"] == "mysql"
    assert metrics["uptime_pct"] == 100.0
    assert metrics["sample_count"] == 3
    assert len(metrics["history"]) == 2

    # Verify average latencies are aggregated by hour bucket
    assert metrics["history"][0]["avg_latency_ms"] == 60.0
    assert metrics["history"][1]["avg_latency_ms"] == 15.0

    # Seed samples in distinct days for "7d" history
    s4 = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=5.0,
        checked_at=now
    )
    s5 = ServiceHealthSample(
        service_name="fastapi",
        status="UP",
        latency_ms=25.0,
        checked_at=now - timedelta(days=2)
    )
    db_session.add_all([s4, s5])
    await db_session.commit()

    metrics_7d = await service.aggregate_metrics(db_session, "fastapi", "7d")
    assert len(metrics_7d["history"]) == 2
    assert metrics_7d["history"][0]["avg_latency_ms"] == 25.0
    assert metrics_7d["history"][1]["avg_latency_ms"] == 5.0
