---
phase: 07-products-domain
plan: "03"
subsystem: database
tags: [alembic, mysql, migration, products, sqlalchemy, pydantic]

# Dependency graph
requires:
  - phase: 07-01
    provides: "Product, TenantSubscription, FlagProduct ORM models registered with Alembic"
  - phase: 04-feature-flags
    provides: "feature_flags table (flag_products FK depends on feature_flags.id)"
provides:
  - "b001: products, tenant_subscriptions, flag_products tables created in MySQL"
  - "b002: tenants.products JSON backfilled into relational tenant_subscriptions rows"
  - "b003: tenants.products legacy column dropped"
  - "Tenant ORM model with products field removed"
  - "TenantCreate/TenantUpdate/TenantResponse schemas with products field removed"
affects: [07-02, 07-04, 08-sdk-core, 09-microfrontends]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "3-step Alembic migration pattern: expand -> backfill -> cleanup for MySQL 5.6 safety"
    - "op.get_bind() synchronous execution in Alembic revisions (never await, never AsyncSession)"
    - "INSERT IGNORE for idempotent backfill inserts on MySQL 5.6"
    - "Graceful JSON parsing in backfill: try/except with isinstance guard on slug list"

key-files:
  created:
    - backend/alembic/versions/b001_expand_products_tables.py
    - backend/alembic/versions/b002_backfill_tenant_subscriptions.py
    - backend/alembic/versions/b003_cleanup_tenants_products_col.py
  modified:
    - backend/app/domains/tenants/models.py
    - backend/app/domains/tenants/schemas.py

key-decisions:
  - "3-step migration used instead of single revision — prevents irreversible data loss on MySQL 5.6"
  - "INSERT IGNORE in b002 ensures idempotency — safe to re-run if migration partially fails"
  - "b003 downgrade re-adds column as nullable TEXT (not JSON) — MySQL 5.6 has no native JSON type"
  - "Tenant ORM model products field removed in same task as b003 — column and model kept in sync"

patterns-established:
  - "Expand-backfill-cleanup: always use 3 chained revisions when migrating data from a column to relational tables"
  - "Backfill with INSERT IGNORE: safe for MySQL 5.6, idempotent, handles concurrent runs"
  - "op.get_bind() pattern: required for synchronous SQL execution inside Alembic revisions"

requirements-completed: [PROD-06]

# Metrics
duration: 2min
completed: 2026-06-08
---

# Phase 7 Plan 03: Products Alembic Migrations Summary

**Three chained Alembic revisions (expand/backfill/cleanup) migrating tenants.products JSON column to relational products and tenant_subscriptions tables on MySQL 5.6**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-08T05:55:18Z
- **Completed:** 2026-06-08T05:57:30Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- b001 creates products (VARCHAR 50 slug PK), tenant_subscriptions (composite PK, no tenant FK), and flag_products tables with correct FK dependencies
- b002 backfills tenant_subscriptions from tenants.products JSON using INSERT IGNORE with malformed JSON guard; downgrade restores data
- b003 drops tenants.products column; downgrade re-adds as nullable TEXT
- Tenant ORM model and all Pydantic schemas (TenantCreate, TenantUpdate, TenantResponse) have products field removed to match b003 schema state

## Task Commits

Each task was committed atomically:

1. **Task 1: Write expand revision (Step 1 — create tables)** - `5d98259` (feat)
2. **Task 2: Write backfill and cleanup revisions (Steps 2 and 3)** - `60be070` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `backend/alembic/versions/b001_expand_products_tables.py` - Creates products, tenant_subscriptions, flag_products tables; chains from a1b2c3d4e5f6
- `backend/alembic/versions/b002_backfill_tenant_subscriptions.py` - Backfills tenant_subscriptions from tenants.products JSON; chains from b001
- `backend/alembic/versions/b003_cleanup_tenants_products_col.py` - Drops tenants.products column; chains from b002
- `backend/app/domains/tenants/models.py` - Removed products Mapped[List[str]] = mapped_column(JSON) field
- `backend/app/domains/tenants/schemas.py` - Removed products field from TenantCreate, TenantUpdate; removed List import

## Decisions Made
- Used 3-step migration (expand/backfill/cleanup) per v1.1 research decision — single revision would risk irreversible data loss
- INSERT IGNORE chosen over ON DUPLICATE KEY UPDATE for idempotent backfill simplicity on MySQL 5.6
- b003 downgrade uses TEXT (not JSON) for re-added column — MySQL 5.6 lacks native JSON type; TEXT matches original stored format

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Migration chain a1b2c3d4e5f6 -> b001 -> b002 -> b003 ready to run via `alembic upgrade head`
- Tenant model and schemas are now products-field-free; Plan 07-04 (CRUD router) should not reference Tenant.products
- Plan 07-02 (products CRUD router) can proceed; tenant_subscriptions table exists for subscription endpoints

---
*Phase: 07-products-domain*
*Completed: 2026-06-08*
