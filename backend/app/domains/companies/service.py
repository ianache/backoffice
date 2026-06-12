from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.companies.models import Company
from app.domains.companies.schemas import CompanyCreate, CompanyUpdate


async def create_company(db: AsyncSession, payload: CompanyCreate) -> Company:
    """Create a new company. Raises IntegrityError on duplicate slug — let router handle 409."""
    company = Company(
        id=payload.id,
        name=payload.name,
        status=payload.status,
        tenant_id=payload.tenant_id,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def get_company(db: AsyncSession, company_id: str) -> Optional[Company]:
    """Fetch a single company by its slug id."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    return result.scalar_one_or_none()


async def list_companies(
    db: AsyncSession,
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Company]:
    """List companies, optionally filtered by tenant_id and/or status."""
    stmt = select(Company).order_by(Company.created_at.desc())
    if tenant_id:
        stmt = stmt.where(Company.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Company.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_company(
    db: AsyncSession,
    company_id: str,
    payload: CompanyUpdate,
) -> Optional[Company]:
    """Update a company. Only sets fields explicitly provided in the payload (exclude_unset)."""
    company = await get_company(db, company_id)
    if not company:
        return None

    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return company
