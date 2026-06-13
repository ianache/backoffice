---
phase: 20-localization-white-label-engine
plan: 01
subsystem: database
tags: [sqlalchemy, pydantic, alembic, mysql, keycloak, localization]

# Dependency graph
requires:
  - phase: 16-mvp2-auditoria
    provides: audit_logs table (e001) and ActionType convention extended for label/namespace actions
provides:
  - "backend/app/domains/labels/ domain package (models.py, schemas.py) — interface contract for service/router layers"
  - "g001/g002 Alembic migrations creating and seeding namespaces/localized_labels/missing_label_reports tables"
  - "UXWriter Keycloak realm role for narrow label-value-only editing"
  - "Extended audit ActionType constants for namespace/label CRUD"
affects: [20-02, 20-03, 20-04, 20-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "params (JSON array) stored as TEXT column, matching rules/tags/conditions precedent for MySQL 5.6 compatibility"
    - "Runtime-queried seed migration (SELECT id FROM tenants ... INSERT IGNORE) avoids hardcoding tenant/company IDs"

key-files:
  created:
    - backend/app/domains/labels/__init__.py
    - backend/app/domains/labels/models.py
    - backend/app/domains/labels/schemas.py
    - backend/alembic/versions/g001_create_labels_tables.py
    - backend/alembic/versions/g002_seed_common_namespace_labels.py
  modified:
    - backend/app/domains/audit/schemas.py
    - keycloak/realm-export.json

key-decisions:
  - "Namespace.id is a user-defined String(100) slug PK (mirrors Product.id convention), not auto-increment"
  - "LocalizedLabel unique index covers (tenant_id, company_id, product_id, namespace, locale, label_key) for DAG-inheritance scoping"
  - "g002 seed targets real tenant id=5 (dogfooding tenant) with fallback to first tenant, and only adds company-level overrides if a company already exists for that tenant"
  - "UXWriter role inserted as the last entry in realm-export.json roles.realm array (actual last role was CompanyUser, not ProductQA as plan described — same intent, append-as-last)"

patterns-established:
  - "Localization label schemas follow feature_flags conventions: model_validator(mode='before') for TEXT->List[str] JSON params, ConfigDict(from_attributes=True) for ORM responses"

requirements-completed: [LBL-01, LBL-02, LBL-16]

# Metrics
duration: 15min
completed: 2026-06-13
---

# Phase 20 Plan 01: Labels Domain Models, Schemas & Migrations Summary

**New `labels` domain package (Namespace/LocalizedLabel/MissingLabelReport models + Pydantic schemas), two Alembic migrations (g001 additive tables, g002 runtime-targeted seed), extended audit ActionType constants, and a new UXWriter Keycloak realm role.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-06-13T16:40:00Z
- **Completed:** 2026-06-13T16:54:46Z
- **Tasks:** 3 completed
- **Files modified:** 7

## Accomplishments
- Created `backend/app/domains/labels/` package with `Namespace`, `LocalizedLabel`, `MissingLabelReport` SQLAlchemy models mirroring `feature_flags/models.py` conventions
- Created Pydantic schemas for namespace/label CRUD, value-only edits (UXWriter), and missing-label reporting, including a `params` TEXT<->List[str] model_validator matching the existing pattern
- Added `g001` (additive table creation, down_revision='e001') and `g002` (runtime-targeted seed of `common` namespace + 6 label keys x 2 locales, plus company-level overrides) Alembic migrations
- Extended `audit/schemas.py` ActionType with CREATE/UPDATE/DELETE_NAMESPACE and CREATE/UPDATE/DELETE_LABEL
- Added `UXWriter` realm role to `keycloak/realm-export.json`

## Task Commits

1. **Task 1: Create labels domain models and schemas** - `a3a67c7` (feat)
2. **Task 2: Alembic migration — create namespaces/localized_labels/missing_label_reports tables** - `999aaf3` (feat)
3. **Task 3: Seed migration (g002) + UXWriter Keycloak role** - `5399cf9` (feat)

**Plan metadata:** (pending — see final commit below)

## Files Created/Modified
- `backend/app/domains/labels/__init__.py` - empty package marker, mirrors other domains
- `backend/app/domains/labels/models.py` - Namespace, LocalizedLabel, MissingLabelReport SQLAlchemy models
- `backend/app/domains/labels/schemas.py` - Pydantic schemas: NamespaceCreate/Update/Response, LabelCreate/Update/ValueUpdate, LocalizedLabelResponse, MissingLabelReportCreate/Response
- `backend/app/domains/audit/schemas.py` - added 6 new ActionType constants for namespace/label CRUD
- `backend/alembic/versions/g001_create_labels_tables.py` - additive migration creating namespaces/localized_labels/missing_label_reports tables and indexes (down_revision='e001')
- `backend/alembic/versions/g002_seed_common_namespace_labels.py` - seed migration: common namespace + 6 keys x 2 locales for real tenant, company-level overrides if a company exists (down_revision='g001')
- `keycloak/realm-export.json` - added UXWriter realm role

## Decisions Made
- Followed plan exactly for models/schemas/migrations content (copy-paste from plan's `<action>` blocks, since plan was fully prescriptive/interface-first).
- UXWriter role appended after the actual last realm role entry (`CompanyUser`) rather than `ProductQA` as the plan's prose described — the plan's intent ("append as last realm role, preserve JSON validity") was preserved; `ProductQA` was simply not the last entry in the current file.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Minor inaccuracy] UXWriter role insertion point**
- **Found during:** Task 3
- **Issue:** Plan's prose said to insert the new role "immediately after" the `ProductQA` role object, describing it as "the last role in the realm roles array." In the actual `keycloak/realm-export.json`, `ProductQA` is followed by `CompanyAdmin` and `CompanyUser` — `CompanyUser` is the actual last entry.
- **Fix:** Inserted the UXWriter role object immediately after `CompanyUser` (the true last realm role), preserving valid JSON and the plan's stated intent (append as the final realm role).
- **Files modified:** keycloak/realm-export.json
- **Verification:** `python -c "import json; ... assert 'UXWriter' in names"` passed; JSON remains valid.
- **Committed in:** 5399cf9 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 minor inaccuracy in plan prose, no functional impact)
**Impact on plan:** None — UXWriter role added correctly, file remains valid JSON.

## Issues Encountered
- Backend Python dependencies (sqlalchemy, pydantic, alembic, fastapi) are not installed in any available Python environment on this machine (system Python 3.14 lacks them; only `sdk/sdk-python/.venv` exists, which is a separate isolated venv for the SDK package). The plan's specified verification commands (`python -c "from app.domains.labels.models import ..."`, `python -m alembic heads`) could not be executed as written.
- **Mitigation:** Verified all new/modified Python files compile cleanly via `python -m py_compile` (syntax-level check), confirmed no other migration declares `down_revision='e001'` (no multi-head conflict introduced), and confirmed `keycloak/realm-export.json` remains valid JSON with the `UXWriter` role present via the plan's exact JSON verification command (which only needs stdlib `json`, no project deps).
- Full import-level and `alembic heads`/upgrade verification should be run in an environment with `backend/requirements.txt` installed before Plan 02 (service layer) begins, to confirm the migration chain applies cleanly against the dev MySQL database.

## User Setup Required

None - no external service configuration required for this plan. Note: the new Keycloak `UXWriter` realm role exists only in `keycloak/realm-export.json` (the source-of-truth export file); it will need to be imported/applied to the running Keycloak realm before Plan 04/05 (admin UI / SDK) can assign it to users — this is expected to be handled by the existing realm-import process used for prior role additions.

## Next Phase Readiness
- `backend/app/domains/labels/` models and schemas are ready for Plan 02 (service layer + router) to build against.
- g001/g002 migrations are ready to apply to the dev database (pending dependency installation / environment with alembic configured).
- audit ActionType constants are ready for use by Plan 02's write_audit_log() calls.
- UXWriter role is defined in realm-export.json for Plan 04/05 role-based authorization checks.

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created files found on disk; all three task commits (a3a67c7, 999aaf3, 5399cf9) found in git log.
