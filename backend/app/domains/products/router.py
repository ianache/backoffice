from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.dependencies import verify_internal_secret, get_db
from app.domains.products import service
from app.domains.products.schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a new product. Requires PlatformAdmin role."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if 'PlatformAdmin' not in roles:
        raise HTTPException(status_code=403, detail="Only PlatformAdmin can manage products")
    try:
        product = await service.create_product(db, payload)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Product with id '{payload.id}' already exists")
    return product


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    status: Optional[str] = Query(None),
    label: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all products, optionally filtered by status and/or label."""
    return await service.list_products(db, status=status, label=label)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Update a product. Requires PlatformAdmin role. Returns 404 if product not found."""
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if 'PlatformAdmin' not in roles:
        raise HTTPException(status_code=403, detail="Only PlatformAdmin can manage products")
    product = await service.update_product(db, product_id, payload)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    return product
