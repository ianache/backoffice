from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_secret
from . import service
from .schemas import FlagCreate, FlagUpdate, FlagResponse, SegmentCreate, SegmentResponse
from app.domains.products import service as products_service
from app.domains.products.schemas import ProductResponse
from app.domains.audit import service as audit_service
from app.domains.audit.schemas import AuditLogCreate, ActionType

# ---------------------------------------------------------------------------
# Flags Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/flags",
    tags=["flags"],
    dependencies=[Depends(verify_internal_secret)],
)


def _audit_request_meta(request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
    """Extract client_ip (X-Forwarded-For first, fallback to request.client.host)
    and user_agent from the incoming request. Returns (None, None) if request is None."""
    if request is None:
        return None, None
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")
    return client_ip, user_agent


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


_TARGET_FIELD_BY_SCOPE = {
    'tenant': 'tenant_id',
    'product': 'product_id',
    'company': 'company_id',
}


def _validate_update_target(flag, update_data: dict) -> dict:
    """Validate merged scope/target state for a PATCH payload.

    If none of {'scope','tenant_id','product_id','company_id'} are present in
    update_data, the update is a legacy edit (e.g. toggling `enabled`) and is
    returned unchanged — no validation is performed (locked decision).

    Otherwise, computes the effective scope+targets (flag state merged with
    update_data), validates that a non-global effective scope has its required
    target non-empty (422 if not), and — if 'scope' is being changed — clears
    the two non-matching target columns to None for mutual exclusivity.
    """
    target_keys = {'scope', 'tenant_id', 'product_id', 'company_id'}
    if not target_keys.intersection(update_data.keys()):
        return update_data

    effective_scope = update_data.get('scope', flag.scope)
    effective_targets = {
        'tenant_id': update_data.get('tenant_id', flag.tenant_id),
        'product_id': update_data.get('product_id', flag.product_id),
        'company_id': update_data.get('company_id', flag.company_id),
    }

    required_field = _TARGET_FIELD_BY_SCOPE.get(effective_scope)
    if required_field and not effective_targets[required_field]:
        raise HTTPException(
            status_code=422,
            detail=f"{required_field} is required when scope is '{effective_scope}'"
        )

    if 'scope' in update_data:
        for scope_name, field_name in _TARGET_FIELD_BY_SCOPE.items():
            if scope_name != effective_scope:
                update_data[field_name] = None

    return update_data


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
    request: Request,
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    x_user_sub: str = Header(...),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(payload.scope, roles, "create")
    flag = await service.create_flag(
        db, payload, actor_sub=x_user_sub, tenant_id=x_user_tenant_id or None
    )
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=flag.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.CREATE_FLAG,
        environment=flag.environment,
        target_type="FLAG",
        target_id=str(flag.id),
        payload_before=None,
        payload_after=FlagResponse.model_validate(flag).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    return FlagResponse.model_validate(flag)


@router.patch("/{flag_id}", response_model=FlagResponse)
async def update_flag(
    flag_id: int,
    payload: FlagUpdate,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "update")

    payload_before = FlagResponse.model_validate(flag).model_dump(mode='json')

    update_data = payload.model_dump(exclude_unset=True)
    if 'scope' in update_data and update_data['scope'] != flag.scope:
        # Changing INTO a different scope also requires permission for that scope
        _check_scope_permission(update_data['scope'], roles, "update")

    validated_data = _validate_update_target(flag, update_data)
    validated_payload = FlagUpdate(**validated_data)

    updated_flag = await service.update_flag(db, flag_id, validated_payload)

    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=updated_flag.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.UPDATE_FLAG,
        environment=updated_flag.environment,
        target_type="FLAG",
        target_id=str(updated_flag.id),
        payload_before=payload_before,
        payload_after=FlagResponse.model_validate(updated_flag).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))

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
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "delete")

    payload_before = FlagResponse.model_validate(flag).model_dump(mode='json')
    tenant_id_snapshot = flag.tenant_id
    environment_snapshot = flag.environment

    deleted = await service.delete_flag(db, flag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flag not found")

    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=tenant_id_snapshot,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.DELETE_FLAG,
        environment=environment_snapshot,
        target_type="FLAG",
        target_id=str(flag_id),
        payload_before=payload_before,
        payload_after=None,
        client_ip=client_ip,
        user_agent=user_agent,
    ))


@router.post("/{flag_id}/enable", response_model=FlagResponse)
async def enable_flag(
    flag_id: int,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "enable")

    payload_before = FlagResponse.model_validate(flag).model_dump(mode='json')

    flag = await service.set_enabled(db, flag_id, True)

    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=flag.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.ENABLE_FLAG,
        environment=flag.environment,
        target_type="FLAG",
        target_id=str(flag.id),
        payload_before=payload_before,
        payload_after=FlagResponse.model_validate(flag).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))

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
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    flag = await service.get_flag(db, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _check_scope_permission(flag.scope, roles, "disable")

    payload_before = FlagResponse.model_validate(flag).model_dump(mode='json')

    flag = await service.set_enabled(db, flag_id, False)

    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=flag.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.DISABLE_FLAG,
        environment=flag.environment,
        target_type="FLAG",
        target_id=str(flag.id),
        payload_before=payload_before,
        payload_after=FlagResponse.model_validate(flag).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))

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


@router.delete("/{flag_id}/segments/{segment_id}", status_code=204)
async def remove_segment_from_flag(
    flag_id: int,
    segment_id: int,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    success = await service.remove_segment_from_flag(db, flag_id, segment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Association not found")


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
