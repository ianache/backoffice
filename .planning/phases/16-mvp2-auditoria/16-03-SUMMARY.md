---
phase: 16-mvp2-auditoria
plan: 03
subsystem: api
tags: [audit-log, fastapi, users-domain, tenants-domain, companies-domain, bff]

# Dependency graph
requires:
  - phase: 16-mvp2-auditoria
    provides: "AuditLog model, write_audit_log() service, AuditLogCreate/ActionType schemas (Plan 16-01)"
provides:
  - "audit_logs writes for CREATE_USER/UPDATE_USER/ENABLE_USER/DISABLE_USER/RESET_MFA (target_type=USER)"
  - "audit_logs writes for CREATE_TENANT/UPDATE_TENANT/DELETE_TENANT (target_type=TENANT, includes whitelabel fields)"
  - "audit_logs writes for CREATE_COMPANY/UPDATE_COMPANY (target_type=COMPANY)"
  - "bff companies.ts forwards X-User-Email"
affects: ["16-04 (Activity Timeline UI consumes these audit_logs rows)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "write_audit_log() called alongside existing _write_event()/router logic - dual writes, neither replaces the other"
    - "Router-level before/after snapshot capture via *Response.model_validate(model).model_dump(mode='json') for diffable payloads"
    - "environment='production' hardcoded default for non-environment-scoped domains (users/tenants/companies) per CONTEXT.md open question #1"

key-files:
  created: []
  modified:
    - backend/app/domains/users/service.py
    - backend/app/domains/tenants/router.py
    - backend/app/domains/companies/router.py
    - bff/src/routes/companies.ts
    - backend/tests/test_audit_domain.py

key-decisions:
  - "users/service.py write_audit_log() calls use user_email=None for the target user - Keycloak Admin API service layer has no FastAPI Request/Header context; documented inline as deliberate limitation"
  - "tenants router update_tenant/delete_tenant perform an extra pre-fetch (select(Tenant)) to capture payload_before snapshot before calling service layer - accepted double-fetch for MVP scope, no service signature changes"
  - "companies router create_company/update_company gained x_user_sub and x_user_email Header(default='') params for audit actor attribution"

patterns-established:
  - "Diff-friendly before/after snapshots use Pydantic Response models (TenantResponse/CompanyResponse/UserResponse) with model_dump(mode='json') for JSON-serializable payloads"

requirements-completed: [AUD-05]

# Metrics
duration: 8min
completed: 2026-06-13
---

# Phase 16 Plan 03: Users/Tenants/Companies Audit Instrumentation Summary

**Wired write_audit_log() into all user, tenant, and company mutation paths (create/update/enable/disable/reset-mfa/delete) alongside existing user_events writes, defaulting environment='production' for these non-environment-scoped domains, and added X-User-Email forwarding to the BFF companies proxy.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-13T04:16:01Z
- **Completed:** 2026-06-13T04:23:18Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- `users/service.py`: create_user/update_user/set_enabled/reset_mfa each now write an `audit_logs` row (target_type=USER) in addition to the existing `user_events` row — neither write replaces the other
- `tenants/router.py`: create_tenant/update_tenant/delete_tenant each write an `audit_logs` row (target_type=TENANT) with before/after `TenantResponse` snapshots including whitelabel fields (logo_url, primary_color, secondary_color, accent_color, font_family, font_weight, domain)
- `companies/router.py`: create_company/update_company each write an `audit_logs` row (target_type=COMPANY) with before/after `CompanyResponse` snapshots
- `bff/src/routes/companies.ts` now forwards `X-User-Email` alongside `X-User-Sub`/`X-User-Roles`/`X-User-Tenant-Id`
- Added 2 new unit tests to `test_audit_domain.py` covering the new ActionType constants and the environment='production' default

## Task Commits

Each task was committed atomically:

1. **Task 1: Instrument users/service.py (create/update/enable-disable/reset-mfa)** - `030ac43` (feat)
2. **Task 2: Instrument tenants + companies routers + BFF companies.ts X-User-Email + unit tests** - `5c127e2` (feat)

**Plan metadata:** (pending — this commit)

## Files Created/Modified
- `backend/app/domains/users/service.py` - create_user/update_user/set_enabled/reset_mfa now call audit_service.write_audit_log() with target_type=USER, alongside existing _write_event() calls
- `backend/app/domains/tenants/router.py` - create_tenant/update_tenant/delete_tenant write audit_logs rows with target_type=TENANT; added Request/Header(X-User-Sub, X-User-Email) params; pre-fetch Tenant for before-snapshots on update/delete
- `backend/app/domains/companies/router.py` - create_company/update_company write audit_logs rows with target_type=COMPANY; added x_user_sub/x_user_email Header params
- `bff/src/routes/companies.ts` - proxyReq now sets X-User-Email header from (req as any).user?.email
- `backend/tests/test_audit_domain.py` - added test_action_type_constants_cover_users_tenants_companies and test_audit_log_create_defaults_environment_to_production

## Decisions Made
- `user_email=None` for all 4 users/service.py audit writes — service layer operates purely via Keycloak Admin API with no HTTP request context; documented inline as a deliberate, known limitation (target user's email not captured on the audit row, only actor_sub via user_id)
- tenants router update_tenant/delete_tenant accept a second DB fetch (pre-check `select(Tenant)` for before-snapshot, then `service.update_tenant`/`service.delete_tenant`'s own internal fetch) — acceptable double-fetch for MVP scope per plan note, no service signature refactor
- companies router create_company/update_company gained `x_user_sub`/`x_user_email` Header(default='') params for audit actor attribution, matching the pattern already used by tenants/flags routers

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All verification commands passed on first attempt:
- `pytest tests/test_audit_domain.py -v` — 13/13 passed
- `python -c "from app.domains.users import service; from app.domains.tenants import router; from app.domains.companies import router as cr"` — imports ok
- `npx tsc --noEmit` (bff) — no type errors
- grep counts: users/service.py=4, tenants/router.py=3, companies/router.py=2 (all match plan expectations)
- Regression check: `pytest tests/test_tenants*.py tests/test_companies*.py tests/test_users*.py -q` — 26/26 passed

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- AUD-05 complete: users/tenants/companies write paths now produce audit_logs rows alongside flags/segments (16-02) and the foundation (16-01)
- Plan 16-04 (Activity Timeline + Diff Viewer UI) can now query a complete set of audit_logs entries across flags, segments, users, tenants, and companies
- No blockers identified

---
*Phase: 16-mvp2-auditoria*
*Completed: 2026-06-13*

## Self-Check: PASSED

- FOUND: .planning/phases/16-mvp2-auditoria/16-03-SUMMARY.md
- FOUND: 030ac43 (Task 1 commit)
- FOUND: 5c127e2 (Task 2 commit)
