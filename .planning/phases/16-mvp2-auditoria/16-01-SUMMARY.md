---
phase: 16-mvp2-auditoria
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, alembic, pydantic, express, http-proxy-middleware, audit-log, pagination]

# Dependency graph
requires:
  - phase: 14-flag-scope-targeting-list-valued-rules
    provides: Companies domain pattern (models/schemas/service/router) mirrored for audit domain
  - phase: 03-user-management
    provides: "_write_event pattern in users/service.py — direct template for write_audit_log()"
provides:
  - "audit_logs table (migration e001) with TEXT payload columns and 3 indexes"
  - "write_audit_log(), list_audit_logs() (paginated), get_audit_log(), compute_diff() in backend/app/domains/audit/service.py"
  - "GET /audit-logs (paginated envelope) and GET /audit-logs/{id}/diff (shallow diff) read-only router"
  - "bff/src/routes/audit.ts proxy at /audit-logs, forwarding X-User-Email for future write-path use"
  - "First page/limit/COUNT(*) pagination pattern in the codebase"
affects: [16-mvp2-auditoria, 17-observabilidad-sla-slo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "page/limit/COUNT(*) pagination: separate count query, never fetch-all-then-slice"
    - "Shallow key-union diff (compute_diff) for before/after payload comparison"
    - "Logically immutable domain router: GET-only APIRouter, no POST/PATCH/DELETE"

key-files:
  created:
    - backend/app/domains/audit/__init__.py
    - backend/app/domains/audit/models.py
    - backend/app/domains/audit/schemas.py
    - backend/app/domains/audit/service.py
    - backend/app/domains/audit/router.py
    - backend/alembic/versions/e001_create_audit_logs_table.py
    - backend/tests/test_audit_domain.py
    - bff/src/routes/audit.ts
  modified:
    - backend/app/main.py
    - bff/src/index.ts

key-decisions:
  - "AuditLogResponse excludes payload_before/payload_after to keep list responses light (<150ms target); only the diff endpoint deserializes payloads"
  - "AuditLogCreate is an internal-only schema, never exposed via HTTP — write_audit_log() is the sole insertion point, called from other domains' service/router layers in Plans 16-02/16-03"
  - "e001 down_revision = 'd004' per plan, consistent with existing migration chain (pre-existing multi-head condition in alembic/versions/ is out of scope for this plan)"
  - "BFF audit.ts forwards X-User-Email (in addition to Sub/Roles/Tenant-Id) — needed by future write-path plans, harmless on this read-only route"

patterns-established:
  - "Pagination pattern: list_audit_logs() returns (items, total) tuple via separate select() and count() statements with identical filter chains"
  - "compute_diff(before, after): shallow key-union diff returning {added, removed, modified}, treats nested structures as opaque values"

requirements-completed: [AUD-01, AUD-02, AUD-03]

# Metrics
duration: 12min
completed: 2026-06-13
---

# Phase 16 Plan 01: Audit Log Domain Foundation Summary

**FastAPI audit_logs domain (immutable, paginated) with write_audit_log/list_audit_logs/get_audit_log/compute_diff service, GET-only router, e001 Alembic migration, and Express BFF proxy at /audit-logs**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-13T04:04:00Z
- **Completed:** 2026-06-13T04:16:01Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- Established the `audit_logs` immutable table (migration `e001`, down_revision `d004`) with `ix_audit_logs_tenant_created`, `ix_audit_logs_created_at`, `ix_audit_logs_action_type` indexes
- Implemented `write_audit_log()`, `list_audit_logs()` (page/limit/COUNT(*) pagination), `get_audit_log()`, and `compute_diff()` in `backend/app/domains/audit/service.py`
- Added GET-only `audit_router` (`/audit-logs/` paginated list with environment/action_type/user_id/date filters, `/audit-logs/{id}/diff` shallow diff) with tenant scoping via `_audit_tenant_filter`
- Created `bff/src/routes/audit.ts` proxy mirroring the `tenants.ts` pattern, forwarding `X-User-Email` for future write-path instrumentation (Plans 16-02/16-03)

## Task Commits

Each task was committed atomically (TDD: test -> feat):

1. **Task 1: AuditLog model, schemas, e001 migration + compute_diff/pagination service**
   - `1d22f10` (test) - RED: failing tests for compute_diff and schemas
   - `2853efa` (feat) - GREEN: models.py, schemas.py, service.py, e001 migration
2. **Task 2: Audit router (GET /audit-logs, GET /audit-logs/{id}/diff) + main.py registration**
   - `9814862` (test) - RED: failing tests for _audit_tenant_filter and route methods
   - `53aeaee` (feat) - GREEN: router.py, main.py registration
3. **Task 3: BFF audit.ts proxy route + index.ts registration** - `443080f` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `backend/app/domains/audit/__init__.py` - empty package marker
- `backend/app/domains/audit/models.py` - AuditLog ORM model (TEXT payloads, composite indexes)
- `backend/app/domains/audit/schemas.py` - AuditLogCreate/Response/ListResponse/DiffResponse + ActionType constants
- `backend/app/domains/audit/service.py` - write_audit_log, list_audit_logs, get_audit_log, compute_diff
- `backend/app/domains/audit/router.py` - GET /audit-logs/ and GET /audit-logs/{id}/diff, _audit_tenant_filter
- `backend/alembic/versions/e001_create_audit_logs_table.py` - audit_logs table + 3 indexes migration
- `backend/tests/test_audit_domain.py` - 9 unit tests (compute_diff, schemas, tenant filter, route methods)
- `backend/app/main.py` - registered audit_router after companies_router
- `bff/src/routes/audit.ts` - auditRouter proxy to backend /audit-logs/*
- `bff/src/index.ts` - registered auditRouter at /audit-logs

## Decisions Made
- AuditLogResponse intentionally excludes payload_before/payload_after (kept list responses light); only the diff endpoint deserializes payloads
- AuditLogCreate is internal-only (never exposed via HTTP) — write_audit_log() is the single insertion point for Plans 16-02/16-03
- e001 down_revision set to 'd004' exactly as specified in the plan
- bff audit.ts forwards X-User-Email in addition to Sub/Roles/Tenant-Id for future write-path use

## Deviations from Plan

None - plan executed exactly as written. Test count is 9 (plan's behavior section enumerated 5 for Task 1 + 3 for Task 2 = 8, but Test 4 was split per the plan's own adjustment instructions into two assertions covering both AuditLogCreate dict-acceptance and AuditLogListResponse construction, plus a dedicated AuditLogResponse-excludes-payloads test — net +1 test, all additive and within the plan's described behavior).

## Issues Encountered
- Initial `python -m pytest` invocation used a system Python without sqlalchemy installed; switched to `backend/venv/Scripts/python.exe` (the project's existing virtualenv) for all test runs. No code changes required.

## User Setup Required

None - no external service configuration required. Note: the `e001` migration was not applied to a live database in this plan (no `alembic upgrade` run, consistent with prior plans in this codebase which create migration files without executing them in the execution environment).

## Next Phase Readiness
- `write_audit_log()` is ready to be called from other domains' service/router layers in Plans 16-02 (flags/segments write-path instrumentation) and 16-03 (users/tenants/companies write-path instrumentation)
- `GET /audit-logs` and `GET /audit-logs/{id}/diff` are ready for Plan 16-04's frontend timeline + diff viewer
- No blockers identified

---
*Phase: 16-mvp2-auditoria*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created files verified present on disk; all 5 task/RED-GREEN commits (1d22f10, 2853efa, 9814862, 53aeaee, 443080f) verified present in git log.
