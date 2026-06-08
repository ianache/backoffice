# Phase 7: Products Domain - Research

**Researched:** 2026-06-08
**Domain:** FastAPI / SQLAlchemy async / Alembic 3-step migration on MySQL 5.6
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Product ID design
- Product ID is a **user-defined slug** — PlatformAdmin provides it at creation time (not auto-generated)
- Format: `^[a-z0-9_]{1,50}$` — lowercase alphanumeric + underscores only (e.g. `premium_plan`, `enterprise_v2`)
- **Immutable after creation** — the slug is the permanent primary key; name and description can be edited freely
- Fields: `id` (VARCHAR slug PK), `name`, `description`, `status` (active|inactive), `labels` (TEXT/JSON)
- No additional fields in Phase 7 (display metadata deferred to Phase 10)

#### Labels storage
- Stored as **TEXT column with JSON array** (e.g. `'["crm","analytics"]'`) — same pattern as `feature_flags.tags`
- MySQL 5.6 safe; consistent with existing codebase pattern
- PROD-03 label filtering: **filter in Python after fetch** in the service layer — acceptable given catalog size
- Labels are **free-form strings** — no predefined enum; PlatformAdmin types any label at creation/edit time

#### Subscription API style
- **POST + DELETE per product** — `POST /tenants/{id}/products/{product_id}` to subscribe, `DELETE /tenants/{id}/products/{product_id}` to unsubscribe
- Granular and idempotent; matches existing flag-segment association pattern (`/flags/{id}/segments`)
- **Reject with HTTP 422** if TenantOwner tries to subscribe to an inactive product
- `tenant_subscriptions` table: composite PK (`tenant_id VARCHAR` + `product_id VARCHAR`) + `subscribed_at DATETIME`
- No per-subscription status field (active/suspended deferred)

#### Migration backfill scope (3-step Alembic)
- **Step 1 — Expand**: Create `products`, `tenant_subscriptions`, and `flag_products` tables; no data moved yet
- **Step 2 — Backfill**: Read `tenants.products` JSON column (holds product slug strings e.g. `["premium_plan","crm"]`) → insert rows into `tenant_subscriptions`; if a slug has no matching `products` row, auto-create a stub product (`id=slug`, `name=slug`, `status=active`, `labels=[]`)
- **Step 3 — Cleanup**: Drop `tenants.products` JSON column from the `tenants` table
- Each revision independently reversible (`downgrade()` implemented for all three)
- **`feature_flags.product_id` (String column) is NOT migrated in Phase 7** — the `flag_products` table is created for new M:M associations only; the existing `product_id` scope field is left as-is and will be addressed in a future phase

#### flag_products association semantics
- A feature flag **may or may not** be associated with products (optional M:M relationship)
- `flag_products` table: composite PK (`flag_id INT FK`, `product_id VARCHAR FK`)
- New associations are made via `flag_products`; the legacy `feature_flags.product_id` scope field remains separate with different semantics

### Claude's Discretion
- Exact Alembic revision IDs and file naming convention
- `downgrade()` implementation details for the cleanup step
- Pydantic schema field ordering and validation details
- Error message wording for 422 responses

### Deferred Ideas (OUT OF SCOPE)
- Migrating `feature_flags.product_id` (String column) to `flag_products` table — deferred to a future phase; the column stays as-is
- Per-subscription status (active/suspended per tenant-product pair) — deferred
- Display metadata for products (icon_url, brand color) — Phase 10 when UI is built
- Label autocomplete/suggestions endpoint — deferred

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROD-01 | PlatformAdmin puede crear un producto con id alfanumérico, name, description, status y labels (tags) | New `products` domain with slug-PK model, Pydantic regex validator for id, TEXT/JSON labels pattern from `feature_flags.tags` |
| PROD-02 | PlatformAdmin puede editar metadatos de un producto y activarlo/desactivarlo | PATCH endpoint on products router; `exclude_unset=True` pattern from `update_flag()`; id is immutable (excluded from update schema) |
| PROD-03 | La lista de productos soporta filtro por status y por label tags | GET /products with Query params; status filter in SQLAlchemy where clause; label filter in Python after fetch (per decision) |
| PROD-04 | TenantOwner puede suscribir y desuscribir productos para su tenant desde la UI de gestión de tenants | New endpoints on tenants router: `POST /tenants/{id}/products/{product_id}` and `DELETE /tenants/{id}/products/{product_id}`; idempotent pattern from `add_segment_to_flag()` |
| PROD-05 | Las feature flags pueden asociarse a uno o más productos (migración desde campo JSON en tenants a tabla relacional `flag_products`) | New `flag_products` join table (composite PK: flag_id INT + product_id VARCHAR); CRUD endpoints on flags router mirroring `/{flag_id}/segments` |
| PROD-06 | La migración de productos usa tres revisiones Alembic separadas (expand → backfill → cleanup) | 3 chained Alembic revisions; expand creates tables; backfill reads `tenants.products` JSON + upserts; cleanup drops column; each with full `downgrade()` |

</phase_requirements>

---

## Summary

Phase 7 is entirely backend — no Vue UI. The scope covers a new `products` domain, extending the `tenants` router with subscription endpoints, and a safe 3-step Alembic migration that relocates `tenants.products` JSON into relational tables without data loss on MySQL 5.6.

The codebase has strong, consistent patterns: every domain lives in `backend/app/domains/{domain}/` with `models.py + schemas.py + service.py + router.py`. TEXT-as-JSON fields, composite-PK join tables, `verify_internal_secret` + `x_user_roles` auth, async SQLAlchemy with `mapped_column`, and `model_validator(mode='before')` for TEXT→list deserialization are all established and must be replicated exactly. No new libraries are needed.

The critical complexity is the 3-step Alembic migration. The pattern is already proven in this project (see `a1b2c3d4e5f6`). The backfill step requires inline Python inside `upgrade()` — reading existing `tenants.products` data and bulk-inserting into `tenant_subscriptions` and `products`. The cleanup downgrade must restore the `tenants.products` column and repopulate it from `tenant_subscriptions` to be truly reversible.

**Primary recommendation:** Build the `products` domain first (models → schemas → service → router), then add subscription endpoints to the tenants router, then write the 3 Alembic revisions in chain — each independently testable with `alembic upgrade <rev>` and `alembic downgrade <prev_rev>`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (existing) | HTTP router, dependency injection | Project standard — all existing domains use it |
| SQLAlchemy async | (existing) | ORM, `AsyncSession`, `mapped_column` | Project standard — `Base` from `app.database` |
| Alembic | (existing) | Schema migrations | Already used for all 5 prior migrations |
| Pydantic v2 | (existing) | Request/response schemas, validation | Project standard — `model_validator`, `ConfigDict` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic.field_validator` | (existing) | Slug format validation `^[a-z0-9_]{1,50}$` | ProductCreate.id validation |
| `json` stdlib | (existing) | Serialize/deserialize TEXT ↔ list | In service layer and `model_validator` |
| `sqlalchemy.text()` | (existing) | Raw SQL in backfill migration | Inline SELECT + INSERT in Alembic backfill |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TEXT+JSON for labels | MySQL 5.7+ JSON type | JSON type not available on MySQL 5.6 — TEXT is the only option |
| Python-side label filter | SQL LIKE on TEXT | SQL LIKE on serialized JSON is fragile — Python filter after fetch is safer |
| 3-step migration | Single migration | Single migration cannot be safely rolled back if backfill partially completes |

**Installation:** No new packages needed — all dependencies already present in the project.

---

## Architecture Patterns

### Recommended Project Structure
```
backend/app/domains/products/
├── __init__.py          # empty
├── models.py            # Product, TenantSubscription, FlagProduct ORM models
├── schemas.py           # ProductCreate, ProductUpdate, ProductResponse
├── service.py           # CRUD + subscription + flag-product association logic
└── router.py            # /products endpoints (PlatformAdmin only)

backend/alembic/versions/
├── <rev1>_expand_products_tables.py      # Step 1: create 3 tables
├── <rev2>_backfill_tenant_subscriptions.py  # Step 2: migrate data
└── <rev3>_cleanup_tenants_products_col.py   # Step 3: drop old column

backend/app/domains/tenants/router.py   # ADD: /tenants/{id}/products/{product_id} POST + DELETE
backend/app/domains/feature_flags/router.py  # ADD: /flags/{id}/products POST + GET
backend/app/main.py                     # ADD: include products_router
backend/alembic/env.py                  # ADD: import new models to register with metadata
```

### Pattern 1: Slug-PK Model with TEXT/JSON labels
**What:** Product model uses a VARCHAR slug as primary key (not auto-int). Labels stored as TEXT (JSON array).
**When to use:** Any catalog entity where human-readable IDs are required and must be immutable.
**Example:**
```python
# Source: derived from existing feature_flags/models.py pattern
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime
from typing import Optional

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # user-defined slug, immutable
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default='active', nullable=False)
    labels: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as TEXT — MySQL 5.6 safe
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Pattern 2: Composite-PK Join Tables
**What:** Join tables use composite PKs (no surrogate key). FK types must match referenced column types exactly.
**When to use:** All M:M associations in this project.
**Example:**
```python
# Source: derived from existing feature_flags/models.py FlagSegment pattern
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime

class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"
    # Note: tenants.id is Integer but CONTEXT says tenant_id VARCHAR — use String to match BFF header pattern
    tenant_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(50), ForeignKey("products.id"), primary_key=True)
    subscribed_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

class FlagProduct(Base):
    __tablename__ = "flag_products"
    flag_id: Mapped[int] = mapped_column(Integer, ForeignKey("feature_flags.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(50), ForeignKey("products.id"), primary_key=True)
```

**CRITICAL NOTE on `tenant_id` type:** The `tenants` table has `id: Integer` PK, but `tenant_subscriptions.tenant_id` from the CONTEXT spec is `VARCHAR`. Cross-reference: the tenants router uses integer tenant IDs in routes (`/tenants/{tenant_id}`). The subscription endpoint is `POST /tenants/{id}/products/{product_id}` where `{id}` is the tenant's integer ID. The `tenant_subscriptions.tenant_id` should be `VARCHAR(100)` to match the `x_user_tenant_id` header pattern used in the flags domain — but the FK relationship must be verified against actual `tenants.id` type. **Resolution: use `String(100)` for `tenant_id` on `TenantSubscription` WITHOUT a FK constraint** (consistent with how `feature_flags.tenant_id` works — it stores the tenant ID as a string with no FK to tenants table).

### Pattern 3: model_validator for TEXT→list deserialization
**What:** Pydantic `model_validator(mode='before')` handles both ORM objects and dict inputs.
**When to use:** Any Response schema where TEXT columns hold JSON arrays.
**Example:**
```python
# Source: exact pattern from feature_flags/schemas.py FlagResponse
import json
from pydantic import BaseModel, ConfigDict, model_validator
from typing import List

class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    labels: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def parse_text_fields(cls, values):
        if isinstance(values, dict):
            v = values.get('labels')
            if isinstance(v, str):
                values['labels'] = json.loads(v) if v else []
            elif v is None:
                values['labels'] = []
            return values
        obj = values
        labels_raw = getattr(obj, 'labels', None)
        obj.labels = json.loads(labels_raw) if labels_raw else []
        return obj
```

### Pattern 4: Idempotent association endpoints
**What:** POST to add association checks for existing link before inserting; DELETE returns False (→ 404) if not found.
**When to use:** All join-table operations. Already established in `add_segment_to_flag()`.
**Example:**
```python
# Source: exact pattern from feature_flags/service.py add_segment_to_flag
async def subscribe_product(db: AsyncSession, tenant_id: str, product_id: str) -> Optional[Product]:
    product = await get_product(db, product_id)
    if not product:
        return None
    if product.status == 'inactive':
        raise ValueError("inactive_product")  # Router converts to HTTP 422
    existing = await db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.product_id == product_id,
        )
    )
    if existing.scalar_one_or_none():
        return product  # idempotent
    link = TenantSubscription(tenant_id=tenant_id, product_id=product_id)
    db.add(link)
    await db.commit()
    return product
```

### Pattern 5: 3-Step Alembic Migration with inline backfill
**What:** Three chained revisions — each `down_revision` points to the previous. Backfill uses `op.get_bind()` to execute raw SQL.
**When to use:** Any data migration where an existing column must be relocated to a new table without data loss.
**Example:**
```python
# Step 1 — Expand (no data movement)
# revision: <rev1>, down_revision: 'a1b2c3d4e5f6'
def upgrade() -> None:
    op.create_table('products', ...)
    op.create_table('tenant_subscriptions', ...)
    op.create_table('flag_products', ...)

def downgrade() -> None:
    op.drop_table('flag_products')
    op.drop_table('tenant_subscriptions')
    op.drop_table('products')

# Step 2 — Backfill (data migration)
# revision: <rev2>, down_revision: '<rev1>'
def upgrade() -> None:
    bind = op.get_bind()
    # Fetch all tenants with non-null products JSON
    rows = bind.execute(sa.text("SELECT id, products FROM tenants WHERE products IS NOT NULL AND products != 'null' AND products != '[]'"))
    for tenant_id, products_json in rows:
        slugs = json.loads(products_json) if products_json else []
        for slug in slugs:
            # Upsert stub product if not exists
            bind.execute(sa.text(
                "INSERT IGNORE INTO products (id, name, status, labels) VALUES (:id, :name, 'active', '[]')"
            ), {"id": slug, "name": slug})
            # Insert subscription
            bind.execute(sa.text(
                "INSERT IGNORE INTO tenant_subscriptions (tenant_id, product_id) VALUES (:tenant_id, :product_id)"
            ), {"tenant_id": str(tenant_id), "product_id": slug})

def downgrade() -> None:
    # Reconstruct tenants.products JSON from tenant_subscriptions
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT tenant_id, product_id FROM tenant_subscriptions"))
    tenant_products: dict = {}
    for tenant_id, product_id in rows:
        tenant_products.setdefault(tenant_id, []).append(product_id)
    for tenant_id, products in tenant_products.items():
        bind.execute(sa.text(
            "UPDATE tenants SET products = :products WHERE id = :id"
        ), {"products": json.dumps(products), "id": int(tenant_id)})

# Step 3 — Cleanup (drop old column)
# revision: <rev3>, down_revision: '<rev2>'
def upgrade() -> None:
    op.drop_column('tenants', 'products')

def downgrade() -> None:
    op.add_column('tenants', sa.Column('products', sa.Text(), nullable=True))
    # Note: data already restored by step 2 downgrade if full rollback
```

### Anti-Patterns to Avoid
- **Slug uniqueness by accident:** The slug is the PK — a duplicate insert will raise IntegrityError. Catch it in the router and return HTTP 409.
- **Mutating `id` in PATCH:** ProductUpdate schema must NOT include the `id` field. Slug is immutable post-creation.
- **Using `on_conflict_do_nothing` in async ORM for idempotency:** Use explicit SELECT-first pattern (as in `add_segment_to_flag`) — it is the established pattern in this codebase.
- **Running backfill in upgrade() with async engine:** Alembic migration functions run synchronously via `op.get_bind()`. Do NOT use `AsyncSession` in migration files. Use `bind.execute(sa.text(...))` exclusively.
- **Forgetting `onupdate=func.now()` on `updated_at`:** This is required on Product but NOT on TenantSubscription/FlagProduct (they are append-only join rows).
- **Importing new models but not registering with `alembic/env.py`:** The `env.py` explicitly imports models to register them with `Base.metadata`. New `products` domain models must be imported there, or Alembic autogenerate will not detect them.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Slug PK conflict detection | Custom duplicate check service | Standard `try/except IntegrityError` → HTTP 409 | DB enforces uniqueness at PK level; Python check adds race condition risk |
| JSON-in-TEXT serialization | Custom encoder class | `json.dumps()` / `json.loads()` inline (as in `feature_flags/service.py`) | Already the established pattern; no extra abstraction needed |
| Migration data backfill | Complex ORM query inside Alembic | `op.get_bind()` + `sa.text()` raw SQL | Alembic runs sync; async ORM unavailable; raw SQL with `INSERT IGNORE` is simplest and most portable for MySQL 5.6 |
| Label filtering | SQL LIKE '%label%' on TEXT | Fetch all + Python list membership check | JSON-in-TEXT is not queryable by SQL safely; Python filter is correct |
| Idempotent association | `INSERT OR REPLACE` / `ON CONFLICT` | SELECT-then-INSERT pattern (as in `add_segment_to_flag`) | Established project pattern; avoids touching `subscribed_at` on re-insert |

**Key insight:** This phase adds zero new libraries. All complexity is structural (new domain) and data (migration). Following existing patterns exactly is the correct approach.

---

## Common Pitfalls

### Pitfall 1: `tenant_id` type mismatch in TenantSubscription
**What goes wrong:** `tenants.id` is `Integer` but the subscription endpoint receives tenant ID as a path parameter (integer) and `x_user_tenant_id` header (string). If `tenant_subscriptions.tenant_id` is typed as Integer FK to tenants, it conflicts with the `VARCHAR` pattern used everywhere else in the flags domain.
**Why it happens:** The CONTEXT spec says `tenant_id VARCHAR` on `tenant_subscriptions` — matching the `x_user_tenant_id` header pattern, not the tenants table PK type.
**How to avoid:** Use `String(100)` for `tenant_subscriptions.tenant_id` WITHOUT a FK constraint (same as `feature_flags.tenant_id`). Store `str(tenant_id)` when inserting from an integer path param.
**Warning signs:** Alembic complaining about FK type mismatch during migration or SQLAlchemy type errors at insert time.

### Pitfall 2: `tenants.products` column type discrepancy (TEXT vs JSON in ORM)
**What goes wrong:** `tenants/models.py` line 27 uses `mapped_column(JSON, ...)` for `products`, but the Alembic migration (`7f8bdd389265`) created the column as `sa.Text()`. MySQL 5.6 does not have a JSON type — `JSON` in SQLAlchemy ORM silently falls back to TEXT-like storage, but the column definition in Alembic should use `sa.Text()`.
**Why it happens:** SQLAlchemy ORM `JSON` type is dialect-aware — on MySQL 5.6 without JSON support it stores as TEXT. The cleanup step drops this column entirely, so the mismatch is transient.
**How to avoid:** The cleanup migration drops the column — no fix needed. But the backfill migration must read it correctly: use `sa.text("SELECT products FROM tenants")` which returns raw string, then `json.loads()`.
**Warning signs:** Backfill fails to read products data, getting Python objects instead of strings.

### Pitfall 3: Alembic async engine in migration files
**What goes wrong:** Trying to use `AsyncSession` or `await` inside an Alembic `upgrade()`/`downgrade()` function. The async engine in `env.py` wraps the sync execution via `connection.run_sync(do_run_migrations)` — individual revision files execute synchronously.
**Why it happens:** `env.py` uses `create_async_engine` but bridges to sync context for migrations. Developers familiar with the app's async service layer assume they can use `await` in migrations.
**How to avoid:** In all migration files: use `op.get_bind()` for raw SQL, never `await`, never `AsyncSession`. Import `json` directly.
**Warning signs:** `RuntimeError: no running event loop` or `coroutine was never awaited` during migration.

### Pitfall 4: `downgrade()` for cleanup step is non-trivial
**What goes wrong:** The cleanup step drops `tenants.products`. A naive `downgrade()` that just calls `op.add_column()` leaves the column empty — data was already re-populated by step 2's downgrade. If downgrading step 3 alone (without step 2), data is lost.
**Why it happens:** 3-step migrations require careful thought about partial rollback scenarios.
**How to avoid:** Step 3's `downgrade()` only needs to re-add the column (with `nullable=True`). The assumption is that step 2 `downgrade()` handles data restoration when doing a full rollback. Document this dependency clearly in the revision file.
**Warning signs:** Empty `tenants.products` column after running only step 3 downgrade.

### Pitfall 5: Forgetting `__init__.py` and `env.py` import
**What goes wrong:** New `products` domain models are defined but Alembic's `autogenerate` cannot see them because `env.py` only imports from tenants, users, and feature_flags.
**Why it happens:** `env.py` maintains explicit model imports (lines 12-13 in current file). Adding a new domain requires adding an import.
**How to avoid:** Add `from app.domains.products.models import Product, TenantSubscription, FlagProduct  # noqa: F401` to `alembic/env.py` as part of Wave 1 (model creation task).
**Warning signs:** `alembic check` shows no pending migrations after creating models; autogenerate produces empty revision.

### Pitfall 6: INSERT IGNORE vs standard INSERT for backfill
**What goes wrong:** Using standard `INSERT INTO` in backfill raises an error if a product slug already exists (e.g., if backfill was run partially before). Standard INSERT fails on duplicate PK.
**Why it happens:** The backfill is designed to be idempotent (re-runnable).
**How to avoid:** Use `INSERT IGNORE INTO` for MySQL (skips duplicates silently). This is MySQL 5.6 compatible.
**Warning signs:** `IntegrityError: Duplicate entry` during backfill if re-run.

---

## Code Examples

Verified patterns from existing codebase:

### Router with x_user_roles auth guard (for products router)
```python
# Source: backend/app/domains/feature_flags/router.py (lines 14-18, 63-65)
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
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if 'PlatformAdmin' not in roles:
        raise HTTPException(status_code=403, detail="Only PlatformAdmin can manage products")
    ...
```

### Slug validator in Pydantic (ProductCreate)
```python
# Source: derived from tenants/schemas.py @field_validator pattern
import re
from pydantic import BaseModel, field_validator

class ProductCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str = 'active'
    labels: List[str] = []

    @field_validator('id')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9_]{1,50}$', v):
            raise ValueError("Product id must match ^[a-z0-9_]{1,50}$")
        return v
```

### Subscription endpoint on tenants router (POST + DELETE)
```python
# Source: pattern from feature_flags/router.py /{flag_id}/segments (lines 132-151)
# Added to backend/app/domains/tenants/router.py

@router.post("/{tenant_id}/products/{product_id}", status_code=200)
async def subscribe_product(
    tenant_id: int,
    product_id: str,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if not {'TenantOwner', 'PlatformAdmin'}.intersection(roles):
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
async def unsubscribe_product(
    tenant_id: int,
    product_id: str,
    x_user_roles: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = [r.strip() for r in x_user_roles.split(',') if r.strip()]
    if not {'TenantOwner', 'PlatformAdmin'}.intersection(roles):
        raise HTTPException(status_code=403, detail="Only TenantOwner or PlatformAdmin can manage subscriptions")
    removed = await products_service.unsubscribe_product(db, str(tenant_id), product_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Subscription not found")
```

### Alembic expand revision (Step 1 template)
```python
# Source: pattern from backend/alembic/versions/a1b2c3d4e5f6_create_feature_flags_tables.py
"""expand_products_tables

Revision ID: <rev1>
Revises: a1b2c3d4e5f6
Create Date: ...
"""
revision: str = '<rev1>'
down_revision: str = 'a1b2c3d4e5f6'

def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('labels', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'tenant_subscriptions',
        sa.Column('tenant_id', sa.String(100), nullable=False),
        sa.Column('product_id', sa.String(50), nullable=False),
        sa.Column('subscribed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('tenant_id', 'product_id'),
    )
    op.create_table(
        'flag_products',
        sa.Column('flag_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(['flag_id'], ['feature_flags.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('flag_id', 'product_id'),
    )

def downgrade() -> None:
    op.drop_table('flag_products')
    op.drop_table('tenant_subscriptions')
    op.drop_table('products')
```

### Alembic backfill revision (Step 2 template)
```python
# revision: <rev2>, down_revision: '<rev1>'
import json
import sqlalchemy as sa
from alembic import op

def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, products FROM tenants WHERE products IS NOT NULL"
    ))
    for row in rows:
        tenant_id = str(row[0])
        products_raw = row[1]
        try:
            slugs = json.loads(products_raw) if products_raw else []
        except (json.JSONDecodeError, TypeError):
            slugs = []
        for slug in slugs:
            if not slug:
                continue
            bind.execute(sa.text(
                "INSERT IGNORE INTO products (id, name, status, labels) VALUES (:id, :name, 'active', '[]')"
            ), {"id": slug, "name": slug})
            bind.execute(sa.text(
                "INSERT IGNORE INTO tenant_subscriptions (tenant_id, product_id) VALUES (:tid, :pid)"
            ), {"tid": tenant_id, "pid": slug})

def downgrade() -> None:
    # Restore tenants.products from tenant_subscriptions
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT tenant_id, product_id FROM tenant_subscriptions"
    ))
    tenant_map: dict = {}
    for tenant_id, product_id in rows:
        tenant_map.setdefault(tenant_id, []).append(product_id)
    for tenant_id, products in tenant_map.items():
        bind.execute(sa.text(
            "UPDATE tenants SET products = :p WHERE id = :id"
        ), {"p": json.dumps(products), "id": int(tenant_id)})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tenants.products` JSON column | `tenant_subscriptions` relational table | Phase 7 migration | Enables proper FK constraints, queryability, and subscribed_at tracking |
| No products table | `products` catalog table | Phase 7 | Enables product management CRUD |
| No flag-product M:M | `flag_products` join table | Phase 7 | Enables flags scoped to specific products via explicit association |

**Deprecated/outdated after Phase 7:**
- `tenants.products` JSON column: dropped in Step 3 cleanup migration
- `Tenant.products` field in `tenants/models.py`: must be removed from the ORM model after cleanup migration runs (or left nullable until cleanup is applied)

---

## Open Questions

1. **`Tenant.products` ORM field lifecycle**
   - What we know: `models.py` has `products: Mapped[List[str]] = mapped_column(JSON, ...)`. After Step 3 migration drops the column, this field will cause errors on any Tenant query.
   - What's unclear: Should the ORM field be removed in the same wave as the cleanup migration, or is it safe to leave it until the column is dropped?
   - Recommendation: Remove the `products` field from `Tenant` model in the same task that writes the cleanup migration (Wave 3 / Step 3 task). Also remove `products` from `TenantCreate`, `TenantUpdate`, and `TenantResponse` schemas at that point. This is a breaking change to the tenants API — document it.

2. **`tenants.products` TEXT vs JSON column in backfill**
   - What we know: ORM uses `mapped_column(JSON, ...)` but Alembic created it as `sa.Text()`. MySQL 5.6 stores both as TEXT. The `SELECT products FROM tenants` raw SQL will return a JSON string.
   - What's unclear: Could there be any tenant rows where `products` is already stored as Python list (via ORM JSON type) vs raw string?
   - Recommendation: In backfill `upgrade()`, always `json.loads()` with a try/except around it. If the value is already a list (somehow), handle that case too.

3. **`alembic.ini` `sqlalchemy.url` placeholder**
   - What we know: `alembic.ini` has `sqlalchemy.url = driver://user:pass@localhost/dbname` (placeholder). The actual URL is injected via `settings.database_url` in `env.py` (line 21: `url = settings.database_url`).
   - What's unclear: Whether `alembic revision --autogenerate` works correctly with the placeholder URL (it should, since env.py overrides it).
   - Recommendation: The placeholder is fine — `env.py` always overrides it. Confirmed in `run_migrations_offline()` and `run_migrations_online()`.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection:
  - `backend/app/domains/feature_flags/models.py` — FlagSegment composite PK pattern, TEXT/JSON fields
  - `backend/app/domains/feature_flags/router.py` — auth header pattern, `/{flag_id}/segments` association endpoints
  - `backend/app/domains/feature_flags/service.py` — `add_segment_to_flag()` idempotent pattern, TEXT→list in CRUD
  - `backend/app/domains/feature_flags/schemas.py` — `model_validator(mode='before')` TEXT→list deserialization
  - `backend/app/domains/tenants/models.py` — `Tenant.products` JSON column (the field being migrated)
  - `backend/alembic/versions/a1b2c3d4e5f6_create_feature_flags_tables.py` — established migration style
  - `backend/alembic/env.py` — async migration setup, model import pattern
  - `backend/alembic.ini` — location confirmed at `backend/alembic.ini`
  - `backend/app/main.py` — router registration pattern
  - `backend/app/dependencies.py` — `verify_internal_secret` + `get_db` pattern

### Secondary (MEDIUM confidence)
- STATE.md accumulated context: "3-step Alembic migration mandatory for MySQL 5.6 (expand → backfill → cleanup)" — team decision documented from prior research
- CONTEXT.md implementation decisions — gathered from product owner discussion 2026-06-08

### Tertiary (LOW confidence)
- MySQL 5.6 `INSERT IGNORE` behavior — widely documented MySQL feature, not verified against live instance

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all patterns verified from existing codebase
- Architecture: HIGH — domain structure, file names, and patterns directly copied from 3 existing domains
- Migration patterns: HIGH — Alembic revision style verified from 5 existing migrations in repo
- `tenant_id` type decision: MEDIUM — derived from CONTEXT spec + existing flag domain pattern; FK omission is a deliberate choice matching the codebase, not formally documented
- Pitfalls: HIGH — most are codebase-specific observations from reading actual code

**Research date:** 2026-06-08
**Valid until:** 2026-07-08 (stable domain — no fast-moving dependencies)
