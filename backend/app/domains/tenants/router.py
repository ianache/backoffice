from fastapi import APIRouter, Depends, Header, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, verify_internal_secret
from .schemas import TenantCreate, TenantUpdate, TenantResponse
from . import service
from app.domains.products import service as products_service

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


@router.post("/{tenant_id}/products/{product_id}", status_code=200)
async def subscribe_product_to_tenant(
    tenant_id: int,
    product_id: str,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if not {'TenantOwner', 'PlatformAdmin'}.intersection(set(roles)):
        raise HTTPException(status_code=403, detail="Only TenantOwner or PlatformAdmin can subscribe products")
    try:
        result = await products_service.subscribe_product(db, str(tenant_id), product_id)
    except ValueError as e:
        if 'inactive_product' in str(e):
            raise HTTPException(status_code=422, detail="Cannot subscribe to an inactive product")
        raise
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"tenant_id": tenant_id, "product_id": product_id, "subscribed": True}


@router.delete("/{tenant_id}/products/{product_id}", status_code=204)
async def unsubscribe_product_from_tenant(
    tenant_id: int,
    product_id: str,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if not {'TenantOwner', 'PlatformAdmin'}.intersection(set(roles)):
        raise HTTPException(status_code=403, detail="Only TenantOwner or PlatformAdmin can manage subscriptions")
    removed = await products_service.unsubscribe_product(db, str(tenant_id), product_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Subscription not found")
