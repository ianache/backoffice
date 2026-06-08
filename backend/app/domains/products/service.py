import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.products.models import FlagProduct, Product, TenantSubscription
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


async def subscribe_product(
    db: AsyncSession,
    tenant_id: str,
    product_id: str,
) -> Optional[Product]:
    """Subscribe a tenant to a product.

    Returns the Product on success (idempotent — re-subscribing returns the product).
    Returns None if the product does not exist.
    Raises ValueError('inactive_product') if the product is inactive — router converts to 422.
    """
    product = await get_product(db, product_id)
    if not product:
        return None
    if product.status == 'inactive':
        raise ValueError("inactive_product")

    existing = await db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.product_id == product_id,
        )
    )
    if existing.scalar_one_or_none():
        return product  # idempotent — already subscribed

    subscription = TenantSubscription(tenant_id=tenant_id, product_id=product_id)
    db.add(subscription)
    await db.commit()
    return product


async def unsubscribe_product(
    db: AsyncSession,
    tenant_id: str,
    product_id: str,
) -> bool:
    """Remove a tenant subscription for a product.

    Returns True if the subscription was found and removed, False if not found.
    """
    result = await db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.product_id == product_id,
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        return False
    await db.delete(subscription)
    await db.commit()
    return True


async def add_flag_product(
    db: AsyncSession,
    flag_id: int,
    product_id: str,
) -> Optional[str]:
    """Associate a product with a feature flag.

    Returns product_id on success (idempotent — re-associating returns product_id).
    Returns None if the product does not exist.
    """
    product = await get_product(db, product_id)
    if not product:
        return None

    existing = await db.execute(
        select(FlagProduct).where(
            FlagProduct.flag_id == flag_id,
            FlagProduct.product_id == product_id,
        )
    )
    if existing.scalar_one_or_none():
        return product_id  # idempotent — already associated

    db.add(FlagProduct(flag_id=flag_id, product_id=product_id))
    await db.commit()
    return product_id


async def get_flag_products(
    db: AsyncSession,
    flag_id: int,
) -> List[Product]:
    """Return all products associated with a given feature flag."""
    result = await db.execute(
        select(Product)
        .join(FlagProduct, FlagProduct.product_id == Product.id)
        .where(FlagProduct.flag_id == flag_id)
    )
    return list(result.scalars().all())
