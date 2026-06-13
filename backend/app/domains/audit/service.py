import json
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog
from .schemas import AuditLogCreate


async def write_audit_log(db: AsyncSession, payload: AuditLogCreate) -> AuditLog:
    """Append an immutable row to audit_logs. Payloads are JSON-serialized to TEXT.
    Mirrors users/service.py::_write_event. Never call update/delete on the result."""
    entry = AuditLog(
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
        user_email=payload.user_email,
        action_type=payload.action_type,
        environment=payload.environment,
        target_type=payload.target_type,
        target_id=str(payload.target_id),
        payload_before=json.dumps(payload.payload_before) if payload.payload_before is not None else None,
        payload_after=json.dumps(payload.payload_after) if payload.payload_after is not None else None,
        client_ip=payload.client_ip,
        user_agent=payload.user_agent,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_audit_logs(
    db: AsyncSession,
    *,
    tenant_id: Optional[str] = None,
    environment: Optional[str] = None,
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 25,
) -> Tuple[List[AuditLog], int]:
    """Paginated, filtered list. Returns (items, total). LIMIT/OFFSET applied
    AFTER all filters; total computed via a separate COUNT(*) query — never
    fetch all rows then slice in Python (PRD §10.1 <150ms target)."""
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    filters = []
    if tenant_id is not None:
        filters.append(AuditLog.tenant_id == tenant_id)
    if environment is not None:
        filters.append(AuditLog.environment == environment)
    if action_type is not None:
        filters.append(AuditLog.action_type == action_type)
    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)
    if start_date is not None:
        filters.append(AuditLog.created_at >= start_date)
    if end_date is not None:
        filters.append(AuditLog.created_at <= end_date)

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    stmt = stmt.order_by(AuditLog.created_at.desc())
    offset = (page - 1) * limit
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    return items, total


async def get_audit_log(db: AsyncSession, audit_log_id: int) -> Optional[AuditLog]:
    result = await db.execute(select(AuditLog).where(AuditLog.id == audit_log_id))
    return result.scalar_one_or_none()


def compute_diff(before: Optional[dict], after: Optional[dict]) -> dict:
    """Shallow key-union diff. Nested objects/arrays (e.g. rules, tags) are
    treated as opaque values in the 'modified' bucket — value-level diff,
    not recursive tree-diff. No external dependency."""
    before = before or {}
    after = after or {}
    all_keys = set(before.keys()) | set(after.keys())
    added, removed, modified = {}, {}, {}
    for key in all_keys:
        if key not in before:
            added[key] = after[key]
        elif key not in after:
            removed[key] = before[key]
        elif before[key] != after[key]:
            modified[key] = {"before": before[key], "after": after[key]}
    return {"added": added, "removed": removed, "modified": modified}
