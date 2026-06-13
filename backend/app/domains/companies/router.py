from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.dependencies import verify_internal_secret, get_db
from app.domains.companies import service
from app.domains.companies.schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from app.domains.audit import service as audit_service
from app.domains.audit.schemas import AuditLogCreate, ActionType

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
    dependencies=[Depends(verify_internal_secret)],
)


def _require_companies_role(roles: List[str]) -> None:
    """Raise 403 unless caller has PlatformAdmin, TenantAdmin or TenantOwner role."""
    if not ({'PlatformAdmin', 'TenantAdmin', 'TenantOwner'} & set(roles)):
        raise HTTPException(status_code=403, detail="Not authorized to manage companies")


def _tenant_filter_for(roles: List[str], own_tenant: str) -> Optional[str]:
    """Return None for PlatformAdmin (sees all tenants), else the caller's own tenant_id."""
    if 'PlatformAdmin' in roles:
        return None
    return own_tenant


def _check_create_tenant(roles: List[str], payload_tenant_id: str, own_tenant: str) -> None:
    """Raise 403 if a non-PlatformAdmin tries to create/update a company for another tenant."""
    if 'PlatformAdmin' not in roles and payload_tenant_id != own_tenant:
        raise HTTPException(status_code=403, detail="Cannot manage companies for another tenant")


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    payload: CompanyCreate,
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    """Create a new company. PlatformAdmin manages all tenants; TenantAdmin/TenantOwner only their own."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_companies_role(roles)
    _check_create_tenant(roles, payload.tenant_id, x_user_tenant_id)
    try:
        company = await service.create_company(db, payload)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Company with id '{payload.id}' already exists")

    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=company.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.CREATE_COMPANY,
        environment='production',
        target_type="COMPANY",
        target_id=company.id,
        payload_before=None,
        payload_after=CompanyResponse.model_validate(company).model_dump(mode='json'),
    ))
    return company


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    status: Optional[str] = Query(None),
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    """List companies. PlatformAdmin sees all; TenantAdmin/TenantOwner see only their own tenant's."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_companies_role(roles)
    tenant_id = _tenant_filter_for(roles, x_user_tenant_id)
    return await service.list_companies(db, tenant_id=tenant_id, status=status)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    payload: CompanyUpdate,
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    x_user_sub: str = Header(default=''),
    x_user_email: str = Header(default=''),
    db: AsyncSession = Depends(get_db),
):
    """Update a company. Requires PlatformAdmin or TenantAdmin/TenantOwner of the owning tenant."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    _require_companies_role(roles)
    company = await service.get_company(db, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
    if 'PlatformAdmin' not in roles and company.tenant_id != x_user_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot manage companies for another tenant")

    payload_before = CompanyResponse.model_validate(company).model_dump(mode='json')

    updated = await service.update_company(db, company_id, payload)
    await audit_service.write_audit_log(db, AuditLogCreate(
        tenant_id=updated.tenant_id,
        user_id=x_user_sub,
        user_email=x_user_email,
        action_type=ActionType.UPDATE_COMPANY,
        environment='production',
        target_type="COMPANY",
        target_id=updated.id,
        payload_before=payload_before,
        payload_after=CompanyResponse.model_validate(updated).model_dump(mode='json'),
    ))
    return updated
