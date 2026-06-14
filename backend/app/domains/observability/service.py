from datetime import datetime, timedelta
from sqlalchemy import select, delete, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from app.domains.observability.models import ServiceHealthSample


async def write_sample(
    db: AsyncSession,
    service_name: str,
    status: str,
    latency_ms: Optional[float],
    details: Optional[str]
) -> ServiceHealthSample:
    sample = ServiceHealthSample(
        service_name=service_name,
        status=status,
        latency_ms=latency_ms,
        details=details
    )
    db.add(sample)
    await db.commit()
    await db.refresh(sample)
    return sample


async def list_current_status(db: AsyncSession) -> List[ServiceHealthSample]:
    # MySQL 5.6 compatible latest-row-per-service query (subquery max(checked_at) grouped by service_name)
    subq = select(
        ServiceHealthSample.service_name,
        func.max(ServiceHealthSample.checked_at).label("max_checked_at")
    ).group_by(ServiceHealthSample.service_name).subquery()

    stmt = select(ServiceHealthSample).join(
        subq,
        and_(
            ServiceHealthSample.service_name == subq.c.service_name,
            ServiceHealthSample.checked_at == subq.c.max_checked_at
        )
    )
    results = (await db.execute(stmt)).scalars().all()
    
    # In case multiple samples have the exact same max_checked_at, de-duplicate in memory by service_name (keeping the last)
    seen = set()
    unique_results = []
    for r in reversed(results):
        if r.service_name not in seen:
            seen.add(r.service_name)
            unique_results.append(r)
    return list(reversed(unique_results))


async def prune_old_samples(db: AsyncSession) -> int:
    cutoff = datetime.utcnow() - timedelta(days=30)
    stmt = delete(ServiceHealthSample).where(ServiceHealthSample.checked_at < cutoff)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


RANGE_TO_TIMEDELTA = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


async def aggregate_metrics(db: AsyncSession, service_name: str, range_key: str) -> Dict[str, Any]:
    delta = RANGE_TO_TIMEDELTA.get(range_key, timedelta(hours=24))
    since = datetime.utcnow() - delta

    # 1. Total counts, uptime %, error rate %
    stmt = select(
        func.count().label("total"),
        func.sum(case((ServiceHealthSample.status == "UP", 1), else_=0)).label("up_count"),
        func.sum(case((ServiceHealthSample.status == "DOWN", 1), else_=0)).label("down_count"),
    ).where(
        ServiceHealthSample.service_name == service_name,
        ServiceHealthSample.checked_at >= since,
    )
    row = (await db.execute(stmt)).one()
    total = row.total or 0
    up_count = row.up_count or 0
    down_count = row.down_count or 0

    uptime_pct = (up_count / total * 100) if total > 0 else 0.0
    error_rate_pct = (down_count / total * 100) if total > 0 else 0.0

    # 2. p95/p99 latency (compute in Python to avoid database-specific dialect requirements)
    latencies_stmt = select(ServiceHealthSample.latency_ms).where(
        ServiceHealthSample.service_name == service_name,
        ServiceHealthSample.checked_at >= since,
        ServiceHealthSample.latency_ms.isnot(None),
    ).order_by(ServiceHealthSample.latency_ms)
    latencies = (await db.execute(latencies_stmt)).scalars().all()

    p95 = None
    p99 = None
    if latencies:
        n = len(latencies)
        p95 = latencies[min(int(n * 0.95), n - 1)]
        p99 = latencies[min(int(n * 0.99), n - 1)]

    # 3. History time-series (SQLite & MySQL compatible DATE_FORMAT / strftime helper)
    is_sqlite = db.bind.dialect.name == "sqlite"
    if is_sqlite:
        if range_key == "24h":
            bucket_expr = func.strftime("%Y-%m-%d %H:00:00", ServiceHealthSample.checked_at)
        else:
            bucket_expr = func.strftime("%Y-%m-%d", ServiceHealthSample.checked_at)
    else:
        if range_key == "24h":
            bucket_expr = func.date_format(ServiceHealthSample.checked_at, "%Y-%m-%d %H:00:00")
        else:
            bucket_expr = func.date_format(ServiceHealthSample.checked_at, "%Y-%m-%d")

    history_stmt = select(
        bucket_expr.label("bucket"),
        func.avg(ServiceHealthSample.latency_ms).label("avg_latency")
    ).where(
        ServiceHealthSample.service_name == service_name,
        ServiceHealthSample.checked_at >= since,
        ServiceHealthSample.latency_ms.isnot(None)
    ).group_by(bucket_expr).order_by(bucket_expr)

    history_rows = (await db.execute(history_stmt)).all()
    history = []
    for r in history_rows:
        history.append({
            "ts": str(r.bucket),
            "avg_latency_ms": round(float(r.avg_latency), 2) if r.avg_latency is not None else None
        })

    return {
        "service_name": service_name,
        "uptime_pct": round(uptime_pct, 2),
        "error_rate_pct": round(error_rate_pct, 2),
        "p95_latency_ms": round(p95, 2) if p95 is not None else None,
        "p99_latency_ms": round(p99, 2) if p99 is not None else None,
        "sample_count": total,
        "history": history
    }
