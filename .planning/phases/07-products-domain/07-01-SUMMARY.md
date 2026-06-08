---
phase: 07-products-domain
plan: "01"
subsystem: database
tags: [sqlalchemy, pydantic, alembic, products, mysql]

# Dependency graph
requires:
  - phase: 04-feature-flags
    provides: "FeatureFlag model (feature_flags.id) referenced by FlagProduct FK"
  - phase: 01-foundation-and-auth
    provides: "Base ORM class from app.database and database connection setup"
provides:
  - "Product ORM model with VARCHAR(50) slug PK and TEXT labels"
  - "TenantSubscription composite PK join table (tenant_id + product_id)"
  - "FlagProduct composite PK join table (flag_id + product_id)"
  - "ProductCreate/ProductUpdate/ProductResponse Pydantic v2 schemas"
  - "TenantSubscriptionResponse Pydantic schema"
  - "Alembic autogenerate registration for all 3 products models"
affects: [07-02, 07-03, 07-04, 08-sdk-core, 09-microfrontends]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Slug as PK: VARCHAR(50) user-defined id, no auto-increment integer"
    - "TEXT for JSON arrays: MySQL 5.6 safe storage, deserialized at schema layer"
    - "model_validator(mode=before) pattern for TEXT->list on both dict and ORM object"
    - "Composite PK join tables: no ORM relationships, pure FK references"
    - "tenant_id as String with no FK constraint (Keycloak-managed externally)"

key-files:
  created:
    - backend/app/domains/products/__init__.py
    - backend/app/domains/products/models.py
    - backend/app/domains/products/schemas.py
  modified:
    - backend/alembic/env.py

key-decisions:
  - "Product.id is a user-defined slug (VARCHAR 50), not auto-increment — enables stable cross-system references"
  - "TenantSubscription.tenant_id has no FK to tenants table — matches feature_flags.tenant_id pattern (Keycloak-managed)"
  - "labels stored as TEXT JSON array (MySQL 5.6 safe) — deserialized to List[str] in ProductResponse"

patterns-established:
  - "Slug PK: String(50) primary_key=True with field_validator enforcing ^[a-z0-9_]{1,50}$"
  - "TEXT JSON deserialization: model_validator(mode=before) handles both dict and ORM object inputs"
  - "Alembic registration: explicit import with noqa: F401 comment after feature_flags import line"

requirements-completed: [PROD-01, PROD-02, PROD-03]

# Metrics
duration: 5min
completed: 2026-06-08
---

# Phase 7 Plan 01: Products Domain Foundation Summary

**SQLAlchemy ORM models (Product, TenantSubscription, FlagProduct) and Pydantic v2 schemas with TEXT-to-list model_validator, plus Alembic autogenerate registration**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-08T05:51:22Z
- **Completed:** 2026-06-08T05:52:37Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Product model with VARCHAR(50) slug PK, TEXT labels field, and `onupdate=func.now()` on updated_at
- TenantSubscription and FlagProduct as composite-PK join tables with no unnecessary FK to tenants
- ProductCreate with slug regex field_validator, ProductResponse with model_validator for TEXT->list deserialization
- alembic/env.py updated to register all 3 products models for autogenerate detection

## Task Commits

Each task was committed atomically:

1. **Task 1: Create products domain models** - `1472f63` (feat)
2. **Task 2: Create products domain schemas and register with Alembic** - `ae7bad8` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `backend/app/domains/products/__init__.py` - Empty package marker
- `backend/app/domains/products/models.py` - Product, TenantSubscription, FlagProduct ORM models
- `backend/app/domains/products/schemas.py` - ProductCreate, ProductUpdate, ProductResponse, TenantSubscriptionResponse schemas
- `backend/alembic/env.py` - Added products models import for Alembic autogenerate

## Decisions Made
- Product.id is a user-defined slug (VARCHAR 50) not auto-increment — enables stable cross-system references without integer IDs
- TenantSubscription.tenant_id has no FK constraint to tenants table — consistent with how feature_flags.tenant_id works (Keycloak manages tenant identity externally)
- labels stored as TEXT (MySQL 5.6 safe JSON array) deserialized at schema layer — avoids JSON column type dependency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Products domain contracts established; Plans 02, 03, and 04 can now build CRUD router and Alembic migrations against these models and schemas
- Alembic autogenerate will detect products, tenant_subscriptions, and flag_products tables when a migration is generated

---
*Phase: 07-products-domain*
*Completed: 2026-06-08*
