---
phase: 04-feature-flags
plan: "01"
subsystem: database
tags: [fastapi, sqlalchemy, alembic, mysql, pydantic, feature-flags, tdd]

# Dependency graph
requires:
  - phase: 03-user-management
    provides: Backend FastAPI patterns, MySQL TEXT/JSON strategy, asyncmy async session, X-User-Roles header injection

provides:
  - feature_flags, segments, flag_segments tables in MySQL (Alembic migration a1b2c3d4e5f6)
  - FeatureFlag/Segment/FlagSegment SQLAlchemy models
  - Pydantic FlagCreate/FlagUpdate/FlagResponse/SegmentCreate/SegmentResponse schemas with TEXT deserialization
  - evaluate_flag() deterministic hierarchical evaluation engine (company>product>tenant>global)
  - _evaluate_rule() operator dispatch (equals, in, notIn, contains, regex)
  - FastAPI /flags and /segments REST endpoints with scope-based authorization
  - 28 unit tests covering all evaluation, schema, and model behaviors

affects: [04-02-bff-routes, 04-03-portal-store, 04-04-portal-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TEXT columns for JSON arrays (rules, tags, members) — MySQL 5.6 safe, json.dumps/loads in service layer
    - SCOPE_PRIORITY dict for deterministic hierarchy evaluation (not timestamp-based)
    - OPERATORS dict dispatch for rule evaluation — no if/elif chain, no external library
    - model_validator(mode='before') on FlagResponse for ORM-object TEXT deserialization

key-files:
  created:
    - backend/alembic/versions/a1b2c3d4e5f6_create_feature_flags_tables.py
    - backend/app/domains/feature_flags/__init__.py
    - backend/app/domains/feature_flags/models.py
    - backend/app/domains/feature_flags/schemas.py
    - backend/app/domains/feature_flags/service.py
    - backend/app/domains/feature_flags/router.py
    - backend/tests/test_feature_flags_domain.py
  modified:
    - backend/app/main.py
    - backend/alembic/env.py

key-decisions:
  - "evaluate_flag() uses SCOPE_PRIORITY dict + max() for deterministic priority — not recency-based"
  - "_evaluate_rule() returns False on unknown operator and on missing user attribute — never raises"
  - "rules, tags, members stored as TEXT (JSON arrays) — MySQL 5.6 has no JSON column type (established Phase 3 pattern)"
  - "FlagResponse.parse_text_fields model_validator handles both dict input (API) and ORM object (DB) for TEXT deserialization"
  - "scope-based authorization enforced in backend router (defense-in-depth) — PlatformAdmin=global, TenantAdmin/TenantOwner=tenant, ProductManager=product"

patterns-established:
  - "Pattern 1: Hierarchical evaluation — evaluate_flag(flags, context) selects most-specific scope via SCOPE_PRIORITY, not timestamp"
  - "Pattern 2: Operator dispatch — OPERATORS dict of lambdas, unknown operator returns False (no KeyError)"
  - "Pattern 3: TEXT/JSON round-trip — json.dumps on write, json.loads in model_validator on read"

requirements-completed: [FLAG-01, FLAG-02, FLAG-03, FLAG-04, FLAG-05, FLAG-06]

# Metrics
duration: 5min
completed: 2026-06-07
---

# Phase 04 Plan 01: Feature Flags Backend Domain Summary

**FastAPI feature flags domain with 3 MySQL tables, deterministic hierarchical evaluation engine (company>product>tenant>global), and scope-based CRUD authorization for /flags and /segments endpoints**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-07T16:09:22Z
- **Completed:** 2026-06-07T16:14:30Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Alembic migration creating feature_flags, segments, and flag_segments tables with TEXT columns (MySQL 5.6 safe)
- Core evaluation engine: evaluate_flag() with SCOPE_PRIORITY + _evaluate_rule() with 5-operator OPERATORS dispatch dict
- Complete CRUD service (list_flags, create_flag, update_flag, delete_flag, set_enabled) + segment CRUD
- FastAPI routers /flags and /segments with scope-based role authorization (PlatformAdmin/TenantAdmin/TenantOwner/ProductManager)
- 28 unit tests passing covering all evaluation behaviors, operator dispatch edge cases, schema TEXT deserialization

## Task Commits

1. **Task 1: Alembic migration** — `17061fe` (feat)
2. **Task 2: TDD RED — failing tests** — `7a0045d` (test)
3. **Task 2: TDD GREEN — domain implementation** — `3d090fc` (feat)

## Files Created/Modified

- `backend/alembic/versions/a1b2c3d4e5f6_create_feature_flags_tables.py` — Migration: feature_flags, segments, flag_segments tables
- `backend/app/domains/feature_flags/__init__.py` — Package init
- `backend/app/domains/feature_flags/models.py` — FeatureFlag, Segment, FlagSegment SQLAlchemy models
- `backend/app/domains/feature_flags/schemas.py` — Pydantic schemas with TEXT-to-list deserialization validators
- `backend/app/domains/feature_flags/service.py` — CRUD + evaluate_flag() + _evaluate_rule() evaluation engine
- `backend/app/domains/feature_flags/router.py` — /flags router + /segments sub-router with scope authorization
- `backend/tests/test_feature_flags_domain.py` — 28 unit tests (evaluation, operators, models, schemas)
- `backend/app/main.py` — Added include_router(flags_router) and include_router(segments_router)
- `backend/alembic/env.py` — Registered FeatureFlag/Segment/FlagSegment for autogenerate

## Decisions Made

- evaluate_flag() uses SCOPE_PRIORITY dict + max() — tenant flag wins over global even if global was created later
- _evaluate_rule() uses OPERATORS dispatch dict (not if/elif chain) and returns False on unknown operator or missing attribute — no crashes
- TEXT columns for JSON arrays (rules, tags, members) — identical to Phase 3 user_events.context pattern for MySQL 5.6
- FlagResponse.model_validator handles both dict input and ORM objects to support both direct construction in tests and from_attributes=True usage
- Rollout field stored (INT, default 100) but NOT evaluated in Phase 4 — display-only per research scope boundary

## Deviations from Plan

None — plan executed exactly as written. All must_haves satisfied:
- POST /flags returns 201 with correct scope authorization
- GET /flags returns array filtered by caller's scope
- evaluate_flag() returns most-specific scope match (priority, not recency)
- FLAG-04/FLAG-05 operators dispatch correctly via OPERATORS dict
- segments and flag_segments tables exist in database

## Issues Encountered

- Alembic `python -m alembic` fails (module not directly executable on this Python install) — resolved by using `./venv/Scripts/alembic` directly
- pytest requires `PYTHONPATH=.` — same as existing tests

## Next Phase Readiness

- Backend domain complete: /flags and /segments endpoints available at localhost:8000
- BFF plan 04-02 can proxy to /flags with requireRole('PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager')
- evaluate_flag() and _evaluate_rule() available for import in any backend service
- All 39 backend tests pass (7 tenants + 4 users + 28 feature flags)

---
*Phase: 04-feature-flags*
*Completed: 2026-06-07*
