from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_secret
from . import service
from .schemas import FlagCreate, FlagUpdate, FlagResponse, SegmentCreate, SegmentResponse

# ---------------------------------------------------------------------------
# Flags Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/flags",
    tags=["flags"],
    dependencies=[Depends(verify_internal_secret)],
)


def _get_scope_filter(roles: list[str]) -> Optional[list[str]]:
    """Return allowed scopes based on caller's roles. None means all scopes (PlatformAdmin)."""
    if 'PlatformAdmin' in roles:
        return None  # sees everything
    if 'ProductManager' in roles:
        return ['global', 'tenant', 'product']
    if 'TenantAdmin' in roles or 'TenantOwner' in roles:
        return ['global', 'tenant']
    return ['global']


@router.get("/", response_model=list[FlagResponse])
async def list_flags(
    scope: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    scope_filter = _get_scope_filter(roles)
    if scope:
        # Further restrict to explicitly requested scope if within allowed
        if scope_filter is not None and scope not in scope_filter:
            raise HTTPException(status_code=403, detail="Not authorized to view this scope")
        scope_filter = [scope]
    tenant_id = x_user_tenant_id if x_user_tenant_id else None
    flags = await service.list_flags(db, scope_filter=scope_filter, tenant_id=tenant_id, q=q)
    return [FlagResponse.model_validate(f) for f in flags]


@router.post("/", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
async def create_flag(
    payload: FlagCreate,
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if payload.scope == 'global' and 'PlatformAdmin' not in roles:
        raise HTTPException(status_code=403, detail="Only PlatformAdmin can create global flags")
    if payload.scope == 'tenant' and not {'TenantAdmin', 'TenantOwner'}.intersection(roles):
        raise HTTPException(status_code=403, detail="Only TenantAdmin/TenantOwner can create tenant flags")
    if payload.scope == 'product' and 'ProductManager' not in roles:
        raise HTTPException(status_code=403, detail="Only ProductManager can create product flags")
    if payload.scope == 'company' and 'PlatformAdmin' not in roles:
        raise HTTPException(status_code=403, detail="Only PlatformAdmin can create company-scope flags")
    flag = await service.create_flag(
        db, payload, actor_sub=x_user_sub, tenant_id=x_user_tenant_id or None
    )
    return FlagResponse.model_validate(flag)


@router.patch("/{flag_id}", response_model=FlagResponse)
async def update_flag(
    flag_id: int,
    payload: FlagUpdate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.update_flag(db, flag_id, payload)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return FlagResponse.model_validate(flag)


@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flag(
    flag_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if 'PlatformAdmin' not in roles:
        raise HTTPException(status_code=403, detail="Only PlatformAdmin can delete flags")
    deleted = await service.delete_flag(db, flag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flag not found")


@router.post("/{flag_id}/enable", response_model=FlagResponse)
async def enable_flag(
    flag_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.set_enabled(db, flag_id, True)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return FlagResponse.model_validate(flag)


@router.post("/{flag_id}/disable", response_model=FlagResponse)
async def disable_flag(
    flag_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.set_enabled(db, flag_id, False)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return FlagResponse.model_validate(flag)


# ---------------------------------------------------------------------------
# Segments Router
# ---------------------------------------------------------------------------

segments_router = APIRouter(
    prefix="/segments",
    tags=["segments"],
    dependencies=[Depends(verify_internal_secret)],
)


@segments_router.get("/", response_model=list[SegmentResponse])
async def list_segments(
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    tenant_id = x_user_tenant_id if x_user_tenant_id else None
    if 'PlatformAdmin' in roles:
        tenant_id = None  # PlatformAdmin sees all segments
    segments = await service.list_segments(db, tenant_id=tenant_id)
    return [SegmentResponse.model_validate(s) for s in segments]


@segments_router.post("/", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    payload: SegmentCreate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    segment = await service.create_segment(db, payload)
    return SegmentResponse.model_validate(segment)


@segments_router.delete("/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_segment(
    segment_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service.delete_segment(db, segment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Segment not found")
