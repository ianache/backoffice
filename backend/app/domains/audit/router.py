from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_secret
from . import service
from .schemas import AuditLogResponse, AuditLogListResponse, AuditLogDiffResponse

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit"],
    dependencies=[Depends(verify_internal_secret)],
)


def _audit_tenant_filter(roles: List[str], own_tenant: str) -> Optional[str]:
    """Return None for PlatformAdmin (sees all tenants), else the caller's own tenant_id."""
    if 'PlatformAdmin' in roles:
        return None
    return own_tenant or None


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs_handler(
    environment: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    tenant_id = _audit_tenant_filter(roles, x_user_tenant_id)
    items, total = await service.list_audit_logs(
        db,
        tenant_id=tenant_id,
        environment=environment,
        action_type=action_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{audit_log_id}/diff", response_model=AuditLogDiffResponse)
async def get_audit_log_diff(
    audit_log_id: int,
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    import json as _json
    entry = await service.get_audit_log(db, audit_log_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if 'PlatformAdmin' not in roles and entry.tenant_id and entry.tenant_id != x_user_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot view audit logs for another tenant")

    before = _json.loads(entry.payload_before) if entry.payload_before else None
    after = _json.loads(entry.payload_after) if entry.payload_after else None
    diff = service.compute_diff(before, after)
    return AuditLogDiffResponse(id=entry.id, **diff)
