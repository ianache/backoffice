from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_secret
from . import service
from .schemas import (
    NamespaceCreate, NamespaceUpdate, NamespaceResponse,
    LabelCreate, LabelUpdate, LabelValueUpdate, LocalizedLabelResponse,
    MissingLabelReportResponse,
)
from app.domains.audit import service as audit_service
from app.domains.audit.schemas import AuditLogCreate, ActionType

router = APIRouter(
    prefix="/labels",
    tags=["labels"],
    dependencies=[Depends(verify_internal_secret)],
)

_STRUCTURE_ROLES = {'PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'}
_VALUE_ROLES = _STRUCTURE_ROLES | {'UXWriter'}


class RestoreOverridePayload(BaseModel):
    """RF-05 'Restaurar' request body — deletes the override row at the active
    context level (company or product), forcing inheritance from the level above."""
    tenant_id: str
    company_id: Optional[str] = None
    product_id: Optional[str] = None
    namespace: str
    locale: str
    label_key: str


def _audit_request_meta(request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
    if request is None:
        return None, None
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")
    return client_ip, user_agent


def _require_structure_role(roles: list[str], action: str) -> None:
    if not _STRUCTURE_ROLES.intersection(roles):
        raise HTTPException(status_code=403, detail=f"Not authorized to {action}")


def _require_value_role(roles: list[str], action: str) -> None:
    if not _VALUE_ROLES.intersection(roles):
        raise HTTPException(status_code=403, detail=f"Not authorized to {action}")


# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------

@router.get("/namespaces", response_model=list[NamespaceResponse])
async def list_namespaces(db: AsyncSession = Depends(get_db)):
    namespaces = await service.list_namespaces(db)
    return [NamespaceResponse.model_validate(n) for n in namespaces]


@router.post("/namespaces", response_model=NamespaceResponse, status_code=status.HTTP_201_CREATED)
async def create_namespace(
    payload: NamespaceCreate,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "create namespaces")
    existing = await service.get_namespace(db, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Namespace '{payload.id}' already exists")
    ns = await service.create_namespace(db, payload)
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=x_user_tenant_id or None,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.CREATE_NAMESPACE,
        target_type="NAMESPACE",
        target_id=ns.id,
        payload_before=None,
        payload_after=NamespaceResponse.model_validate(ns).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    return NamespaceResponse.model_validate(ns)


@router.patch("/namespaces/{namespace_id}", response_model=NamespaceResponse)
async def update_namespace(
    namespace_id: str,
    payload: NamespaceUpdate,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "update namespaces")
    existing = await service.get_namespace(db, namespace_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Namespace not found")
    if payload.id and payload.id != namespace_id:
        duplicate = await service.get_namespace(db, payload.id)
        if duplicate:
            raise HTTPException(status_code=409, detail=f"Namespace '{payload.id}' already exists")
    payload_before = NamespaceResponse.model_validate(existing).model_dump(mode='json')
    updated = await service.update_namespace(db, namespace_id, payload)
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=x_user_tenant_id or None,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.UPDATE_NAMESPACE,
        target_type="NAMESPACE",
        target_id=namespace_id,
        payload_before=payload_before,
        payload_after=NamespaceResponse.model_validate(updated).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    return NamespaceResponse.model_validate(updated)


@router.delete("/namespaces/{namespace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_namespace(
    namespace_id: str,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "delete namespaces")
    existing = await service.get_namespace(db, namespace_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Namespace not found")
    payload_before = NamespaceResponse.model_validate(existing).model_dump(mode='json')
    await service.delete_namespace(db, namespace_id)
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=x_user_tenant_id or None,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.DELETE_NAMESPACE,
        target_type="NAMESPACE",
        target_id=namespace_id,
        payload_before=payload_before,
        payload_after=None,
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    # Namespace deletion cascades label invalidation — broadcast so SDK clients
    # drop their cached resolved labels for this namespace.
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None and x_user_tenant_id:
        await ws_manager.broadcast(x_user_tenant_id, {"type": "INVALIDATE_NAMESPACE", "namespace": namespace_id})


# ---------------------------------------------------------------------------
# Labels (keys)
# ---------------------------------------------------------------------------

@router.get("/keys", response_model=list[LocalizedLabelResponse])
async def list_keys(
    tenant_id: str = Query(...),
    company_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    namespace: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    rows = await service.list_labels(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace)
    return [LocalizedLabelResponse.model_validate(r) for r in rows]


@router.post("/keys", response_model=list[LocalizedLabelResponse], status_code=status.HTTP_201_CREATED)
async def create_key(
    payload: LabelCreate,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "create label keys")
    rows = await service.create_label(db, payload)
    created_labels = [
        LocalizedLabelResponse.model_validate(row).model_dump(mode='json')
        for row in rows
    ]
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=payload.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.CREATE_LABEL,
        target_type="LOCALIZED_LABEL",
        target_id=payload.label_key,
        payload_before=None,
        payload_after={"labels": created_labels},
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        await ws_manager.broadcast(payload.tenant_id, {"type": "INVALIDATE_NAMESPACE", "namespace": payload.namespace})
    return created_labels


@router.patch("/keys/{label_id}", response_model=LocalizedLabelResponse)
async def update_key(
    label_id: int,
    payload: LabelUpdate,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "edit label structure")
    existing = await service.get_label(db, label_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Label not found")
    payload_before = LocalizedLabelResponse.model_validate(existing).model_dump(mode='json')
    updated = await service.update_label(db, label_id, payload)  # raises 409 on version mismatch
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=updated.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.UPDATE_LABEL,
        target_type="LOCALIZED_LABEL",
        target_id=str(label_id),
        payload_before=payload_before,
        payload_after=LocalizedLabelResponse.model_validate(updated).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        await ws_manager.broadcast(updated.tenant_id, {"type": "INVALIDATE_NAMESPACE", "namespace": updated.namespace})
    return LocalizedLabelResponse.model_validate(updated)


@router.patch("/keys/{label_id}/value", response_model=LocalizedLabelResponse)
async def update_key_value(
    label_id: int,
    payload: LabelValueUpdate,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    """Narrow value-only edit — the ONLY label-editing endpoint UXWriter may call (Pitfall 3)."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_value_role(roles, "edit label values")
    existing = await service.get_label(db, label_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Label not found")
    payload_before = LocalizedLabelResponse.model_validate(existing).model_dump(mode='json')
    updated = await service.update_label_value(db, label_id, payload)  # raises 409 on version mismatch
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=updated.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.UPDATE_LABEL,
        target_type="LOCALIZED_LABEL",
        target_id=str(label_id),
        payload_before=payload_before,
        payload_after=LocalizedLabelResponse.model_validate(updated).model_dump(mode='json'),
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        await ws_manager.broadcast(updated.tenant_id, {"type": "INVALIDATE_NAMESPACE", "namespace": updated.namespace})
    return LocalizedLabelResponse.model_validate(updated)


@router.delete("/keys/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    label_id: int,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "delete label keys")
    existing = await service.get_label(db, label_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Label not found")
    payload_before = LocalizedLabelResponse.model_validate(existing).model_dump(mode='json')
    tenant_id_snapshot = existing.tenant_id
    namespace_snapshot = existing.namespace
    await service.delete_label(db, label_id)
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=tenant_id_snapshot,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.DELETE_LABEL,
        target_type="LOCALIZED_LABEL",
        target_id=str(label_id),
        payload_before=payload_before,
        payload_after=None,
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        await ws_manager.broadcast(tenant_id_snapshot, {"type": "INVALIDATE_NAMESPACE", "namespace": namespace_snapshot})


@router.post("/keys/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_override(
    payload: RestoreOverridePayload,
    request: Request,
    x_user_roles: str = Header(...),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    """RF-05 'Restaurar' — deletes the override row at the active context level."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_structure_role(roles, "restore label overrides")
    deleted = await service.delete_label_override(
        db,
        tenant_id=payload.tenant_id,
        company_id=payload.company_id,
        product_id=payload.product_id,
        namespace=payload.namespace,
        locale=payload.locale,
        label_key=payload.label_key,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="No override found at this level")
    client_ip, user_agent = _audit_request_meta(request)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=payload.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.DELETE_LABEL,
        target_type="LOCALIZED_LABEL",
        target_id=f"{payload.namespace}:{payload.label_key}:{payload.locale}",
        payload_before=payload.model_dump(mode='json'),
        payload_after=None,
        client_ip=client_ip,
        user_agent=user_agent,
    ))
    ws_manager = getattr(request.app.state, "ws_manager", None)
    if ws_manager is not None:
        await ws_manager.broadcast(payload.tenant_id, {"type": "INVALIDATE_NAMESPACE", "namespace": payload.namespace})


# ---------------------------------------------------------------------------
# Missing label reports (RF-06 diagnostics — admin view)
# ---------------------------------------------------------------------------

@router.get("/missing", response_model=list[MissingLabelReportResponse])
async def list_missing(
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    rows = await service.list_missing_label_reports(db, tenant_id=tenant_id)
    return [MissingLabelReportResponse.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# Export (RF-07 — JSON / CSV)
# ---------------------------------------------------------------------------

@router.get("/export")
async def export_namespace(
    tenant_id: str = Query(...),
    namespace: str = Query(...),
    format: str = Query(...),
    company_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """RF-07 export-only: format=json returns SDK-bootstrap-like JSON; format=csv
    returns a downloadable CSV (translator-friendly)."""
    if format not in ('json', 'csv'):
        raise HTTPException(status_code=422, detail="format must be 'json' or 'csv'")

    if format == 'json':
        data = await service.export_namespace_json(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace)
        return JSONResponse(content=data)

    csv_content = await service.export_namespace_csv(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{namespace}_{tenant_id}.csv"'},
    )
