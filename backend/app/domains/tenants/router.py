from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, verify_internal_secret
from .schemas import TenantCreate, TenantUpdate, TenantResponse
from . import service

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(verify_internal_secret)],
)

@router.get("/", response_model=list[TenantResponse])
async def list_tenants(
    status: str | None = Query(None),
    country: str | None = Query(None),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_tenants(db, status=status, country=country, q=q)

@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_tenant(db, payload)

@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int, payload: TenantUpdate, db: AsyncSession = Depends(get_db)
):
    tenant = await service.update_tenant(db, tenant_id, payload)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await service.delete_tenant(db, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")
