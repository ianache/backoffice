---
phase: 14-flag-scope-targeting-list-valued-rules
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, alembic, express, bff, companies]

# Dependency graph
requires:
  - phase: 07-products-domain
    provides: products domain template (models/schemas/service/router pattern), BFF proxy route pattern
provides:
  - companies domain (CRUD API) at /companies, role + tenant isolation enforced
  - companies table (Alembic d003) for flags.company_id scope targeting
  - BFF /companies proxy route forwarding identity headers
affects: [14-05 (FlagForm company-scope combobox), 14-06 (Companies UI)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Companies domain mirrors products domain structure exactly (models/schemas/service/router)"
    - "Tenant isolation via _tenant_filter_for() helper - None for PlatformAdmin, own_tenant otherwise"
    - "Cross-tenant write guard via _check_create_tenant() - 403 'Cannot manage companies for another tenant'"

key-files:
  created:
    - backend/app/domains/companies/__init__.py
    - backend/app/domains/companies/models.py
    - backend/app/domains/companies/schemas.py
    - backend/app/domains/companies/service.py
    - backend/app/domains/companies/router.py
    - backend/alembic/versions/d003_create_companies_table.py
    - backend/tests/test_companies_router.py
    - bff/src/routes/companies.ts
  modified:
    - backend/app/main.py
    - backend/alembic/env.py
    - bff/src/index.ts

key-decisions:
  - "Company.id is a user-defined slug (VARCHAR 50, regex ^[a-z0-9_]{1,50}$), immutable like Product.id"
  - "Company.tenant_id has no FK constraint - consistent with feature_flags/products tenant_id pattern (Keycloak-managed)"
  - "CompanyUpdate excludes both id and tenant_id - both immutable after creation"
  - "BFF /companies route uses requireAuth only (no requireRole) - backend enforces role+tenant via X-User-Roles/X-User-Tenant-Id, per resolved open question #3"

patterns-established:
  - "Pattern: new catalog domains mirror products domain 1:1 (models/schemas/service/router/tests) for consistency"

requirements-completed: [CMP-01]

# Metrics
duration: ~12min
completed: 2026-06-12
---

# Phase 14 Plan 01: Companies Catalog Backend Summary

**Companies CRUD API (/companies) with PlatformAdmin/TenantAdmin/TenantOwner role gating and tenant isolation, backed by new Alembic d003 companies table, reachable through a BFF proxy route**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-11T23:58:40Z
- **Completed:** 2026-06-12T00:08:02Z
- **Tasks:** 3 completed
- **Files modified:** 11

## Accomplishments
- New `companies` domain (models/schemas/service/router) mirroring the products domain, with 15 passing DB-free unit tests covering schema validation, role gating, and tenant isolation helpers
- Alembic migration d003 creates the `companies` table (id, name, status, tenant_id, timestamps + tenant_id index), applied to the dev DB (d002 -> d003)
- BFF `/companies` proxy route forwarding X-Internal-Secret, X-User-Sub, X-User-Roles, and X-User-Tenant-Id, registered in index.ts

## Task Commits

Each task was committed atomically:

1. **Task 1: Companies domain (models, schemas, service, router) + main.py registration + tests** - `7d4be6e` (test, RED) + `d1c6742` (feat, GREEN)
2. **Task 2: Alembic migration d003 (companies table) + env.py model registration** - `9e61e11` (feat)
3. **Task 3: BFF /companies proxy route** - `97a21f1` (feat)

**Plan metadata:** (pending) docs: complete plan

_Note: Task 1 used TDD - test commit (RED) then implementation commit (GREEN)._

## Files Created/Modified
- `backend/app/domains/companies/models.py` - Company ORM model (id slug PK, name, status, tenant_id indexed, timestamps)
- `backend/app/domains/companies/schemas.py` - CompanyCreate/Update/Response Pydantic schemas with slug regex validator
- `backend/app/domains/companies/service.py` - pure async CRUD (create/get/list/update_company)
- `backend/app/domains/companies/router.py` - POST/GET/PATCH /companies with _require_companies_role, _tenant_filter_for, _check_create_tenant helpers
- `backend/app/domains/companies/__init__.py` - empty package marker
- `backend/app/main.py` - registered companies_router
- `backend/alembic/versions/d003_create_companies_table.py` - creates companies table + ix_companies_tenant_id index
- `backend/alembic/env.py` - registered Company model for metadata/autogenerate
- `backend/tests/test_companies_router.py` - 15 DB-free tests for schemas + router helpers
- `bff/src/routes/companies.ts` - BFF proxy route (requireAuth only, full identity header forwarding)
- `bff/src/index.ts` - registered companiesRouter at /companies

## Decisions Made
- Followed the products domain template exactly (file structure, helper extraction pattern, IntegrityError -> 409 handling) for consistency across catalog domains.
- No JSON/TEXT fields on Company, so no model_validator was needed in CompanyResponse (unlike ProductResponse's labels handling).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `backend/tests/test_feature_flags_router.py` fails to collect (`ImportError: cannot import name '_validate_update_target'`) due to **pre-existing uncommitted working-tree changes** to `backend/app/domains/feature_flags/router.py` unrelated to this plan (out of scope per 14-01 `files_modified`). Verified on a clean tree (changes stashed) that this test file passes 8/8. Logged to `.planning/phases/14-flag-scope-targeting-list-valued-rules/deferred-items.md`. Full backend suite excluding that one file: 127/127 passed (includes the 15 new companies tests).

## User Setup Required

None - no external service configuration required. Alembic migration d003 was applied successfully to the dev DB during execution.

## Next Phase Readiness
- `/companies` CRUD API is live and reachable through the BFF, ready for the company-scope combobox in FlagForm (Plan 14-05) and the Companies management UI (Plan 14-06).
- No blockers for downstream plans in this phase.

---
*Phase: 14-flag-scope-targeting-list-valued-rules*
*Completed: 2026-06-12*

## Self-Check: PASSED

All created files found on disk; all 4 task commits (7d4be6e, d1c6742, 9e61e11, 97a21f1) verified present in git log.
