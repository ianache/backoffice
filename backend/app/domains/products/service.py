import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.products.models import Product
from app.domains.products.schemas import ProductCreate, ProductUpdate


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    """Create a new product. Raises IntegrityError on duplicate slug — let router handle 409."""
    labels_json = json.dumps(payload.labels)
    product = Product(
        id=payload.id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        labels=labels_json,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def get_product(db: AsyncSession, product_id: str) -> Optional[Product]:
    """Fetch a single product by its slug id."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def list_products(
    db: AsyncSession,
    status: Optional[str] = None,
    label: Optional[str] = None,
) -> List[Product]:
    """List products, optionally filtered by status and/or label.

    status: SQL-level equality filter.
    label: Python-side filter — checks if label is present in deserialized JSON array.
    """
    stmt = select(Product).order_by(Product.created_at.desc())
    if status:
        stmt = stmt.where(Product.status == status)
    result = await db.execute(stmt)
    products = list(result.scalars().all())

    if label:
        products = [
            p for p in products
            if label in json.loads(p.labels or '[]')
        ]

    return products


async def update_product(
    db: AsyncSession,
    product_id: str,
    payload: ProductUpdate,
) -> Optional[Product]:
    """Update a product. Only sets fields explicitly provided in the payload (exclude_unset)."""
    product = await get_product(db, product_id)
    if not product:
        return None

    data = payload.model_dump(exclude_unset=True)

    if 'labels' in data:
        data['labels'] = json.dumps(data['labels'])

    for field, value in data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product
