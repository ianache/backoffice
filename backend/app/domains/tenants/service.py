from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from .models import Tenant
from .schemas import TenantCreate, TenantUpdate

async def list_tenants(
    db: AsyncSession,
    status: Optional[str] = None,
    country: Optional[str] = None,
    q: Optional[str] = None,
) -> list[Tenant]:
    stmt = select(Tenant)
    if status:
        stmt = stmt.where(Tenant.status == status)
    if country:
        stmt = stmt.where(Tenant.country == country)
    if q:
        stmt = stmt.where(Tenant.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def create_tenant(db: AsyncSession, payload: TenantCreate) -> Tenant:
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant

async def update_tenant(db: AsyncSession, tenant_id: int, payload: TenantUpdate) -> Optional[Tenant]:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    await db.commit()
    await db.refresh(tenant)
    return tenant

async def delete_tenant(db: AsyncSession, tenant_id: int) -> bool:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return False
    await db.delete(tenant)
    await db.commit()
    return True
