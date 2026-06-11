from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_secret
from . import service
from .schemas import FlagCreate, FlagUpdate, FlagResponse, SegmentCreate, SegmentResponse
from app.domains.products import service as products_service
from app.domains.products.schemas import ProductResponse

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
    if 'TenantAdmin' in roles or 'TenantOwner' in roles:
        return ['global', 'tenant', 'product', 'company']
    if 'ProductManager' in roles:
        return ['global', 'tenant', 'product']
    return ['global']


def _check_scope_permission(scope: str, roles: list[str], detail_action: str) -> None:
    is_platform_admin = 'PlatformAdmin' in roles
    is_tenant_admin = bool({'TenantAdmin', 'TenantOwner'}.intersection(roles))
    is_product_manager = 'ProductManager' in roles

    if scope == 'global' and not is_platform_admin:
        raise HTTPException(
            status_code=403,
            detail=f"Only PlatformAdmin can {detail_action} global flags"
        )
    elif scope == 'tenant' and not (is_platform_admin or is_tenant_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Only PlatformAdmin or TenantAdmin/TenantOwner can {detail_action} tenant flags"
        )
    elif scope == 'product' and not (is_platform_admin or is_tenant_admin or is_product_manager):
        raise HTTPException(
            status_code=403,
            detail=f"Only PlatformAdmin, TenantAdmin/TenantOwner, or ProductManager can {detail_action} product flags"
        )
    elif scope == 'company' and not (is_platform_admin or is_tenant_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Only PlatformAdmin or TenantAdmin/TenantOwner can {detail_action} company flags"
        )


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
    if 'PlatformAdmin' in roles:
        tenant_id = None  # PlatformAdmin sees all flags
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
    _check_scope_permission(payload.scope, roles, "create")
    flag = await service.create_flag(
        db, payload, actor_sub=x_user_sub, tenant_id=x_user_tenant_id or None
    )
    return FlagResponse.model_validate(flag)


@router.patch("/{flag_id}", response_model=FlagResponse)
async def update_flag(
    flag_id: int,
    payload: FlagUpdate,
    request: Request,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "update")

    updated_flag = await service.update_flag(db, flag_id, payload)
    # Broadcast flag change to SDK WebSocket clients for this tenant
    manager = request.app.state.ws_manager
    if updated_flag.tenant_id:
        await manager.broadcast(updated_flag.tenant_id, {
            "type": "flag_updated",
            "flag_key": updated_flag.name,
        })
    return FlagResponse.model_validate(updated_flag)


@router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flag(
    flag_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "delete")

    deleted = await service.delete_flag(db, flag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flag not found")


@router.post("/{flag_id}/enable", response_model=FlagResponse)
async def enable_flag(
    flag_id: int,
    request: Request,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "enable")

    flag = await service.set_enabled(db, flag_id, True)
    # Broadcast flag change to SDK WebSocket clients for this tenant
    manager = request.app.state.ws_manager
    if flag.tenant_id:
        await manager.broadcast(flag.tenant_id, {
            "type": "flag_updated",
            "flag_key": flag.name,
        })
    return FlagResponse.model_validate(flag)


@router.post("/{flag_id}/disable", response_model=FlagResponse)
async def disable_flag(
    flag_id: int,
    request: Request,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "disable")

    flag = await service.set_enabled(db, flag_id, False)
    # Broadcast flag change to SDK WebSocket clients for this tenant
    manager = request.app.state.ws_manager
    if flag.tenant_id:
        await manager.broadcast(flag.tenant_id, {
            "type": "flag_updated",
            "flag_key": flag.name,
        })
    return FlagResponse.model_validate(flag)


class FlagSegmentCreate(BaseModel):
    segment_id: int


@router.post("/{flag_id}/segments", response_model=SegmentResponse, status_code=201)
async def add_segment_to_flag(
    flag_id: int,
    payload: FlagSegmentCreate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await service.add_segment_to_flag(db, flag_id, payload.segment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Flag or segment not found")
    return SegmentResponse.model_validate(result)


@router.get("/{flag_id}/segments", response_model=list[SegmentResponse])
async def get_flag_segments(
    flag_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    segments = await service.get_flag_segments(db, flag_id)
    return [SegmentResponse.model_validate(s) for s in segments]


@router.post("/{flag_id}/products/{product_id}", status_code=200)
async def add_product_to_flag(
    flag_id: int,
    product_id: str,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if not {'PlatformAdmin', 'TenantAdmin', 'ProductManager'}.intersection(set(roles)):
        raise HTTPException(status_code=403, detail="Insufficient role to associate products to flags")
    result = await products_service.add_flag_product(db, flag_id, product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"flag_id": flag_id, "product_id": product_id, "associated": True}


@router.get("/{flag_id}/products", response_model=List[ProductResponse])
async def get_products_for_flag(
    flag_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await products_service.get_flag_products(db, flag_id)


# ---------------------------------------------------------------------------
# Segments Router
# ---------------------------------------------------------------------------

segments_router = APIRouter(
    prefix="/flags/segments",
    tags=["segments"],
    dependencies=[Depends(verify_internal_secret)],
)


@segments_router.get("/", response_model=list[SegmentResponse])
async def list_segments_handler(
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    tenant_id = x_user_tenant_id if x_user_tenant_id else None
    if 'PlatformAdmin' in roles:
        tenant_id = None  # PlatformAdmin sees all segments
    rows = await service.list_segments(db, tenant_id=tenant_id)
    result = []
    for seg, fc in rows:
        resp = SegmentResponse.model_validate(seg)
        resp.flag_count = fc
        result.append(resp)
    return result


@segments_router.post("/", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    payload: SegmentCreate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    segment = await service.create_segment(db, payload)
    return SegmentResponse.model_validate(segment)


@segments_router.patch("/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: int,
    payload: SegmentCreate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    segment = await service.update_segment(db, segment_id, payload)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
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
