---
phase: 16-mvp2-auditoria
plan: 02
subsystem: api
tags: [audit-log, feature-flags, segments, fastapi, express-bff]

# Dependency graph
requires:
  - phase: 16-mvp2-auditoria
    provides: "write_audit_log() service function, AuditLog model, AuditLogCreate/ActionType schemas (16-01)"
provides:
  - "8 audit-instrumented mutation endpoints in feature_flags router (5 flag + 3 segment)"
  - "_audit_request_meta() helper for client_ip/user_agent extraction"
  - "BFF flags.ts forwards X-User-Email header"
affects: [16-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "payload_before captured via FlagResponse/SegmentResponse.model_validate(...).model_dump(mode='json') BEFORE the mutating service call, payload_after captured after"
    - "_audit_request_meta(request) helper extracts client_ip (X-Forwarded-For fallback to request.client.host) and user_agent from incoming Request"
    - "Segments hardcode environment='production' in audit writes (segments have no environment field)"

key-files:
  created: []
  modified:
    - backend/app/domains/feature_flags/router.py
    - bff/src/routes/flags.ts
    - backend/tests/test_audit_domain.py

key-decisions:
  - "Flag audit writes use the flag's own tenant_id (nullable for global scope) rather than X-User-Tenant-Id header, matching audit_logs.tenant_id nullability"
  - "update_segment/delete_segment fetch existing segment via service.get_segment() before mutation to guarantee a non-trivial payload_before diff"

requirements-completed: [AUD-04]

# Metrics
duration: 8min
completed: 2026-06-13
---

# Phase 16 Plan 02: Feature Flags & Segments Audit Instrumentation Summary

**Instrumented all 8 feature-flag/segment mutation endpoints (create/update/enable/disable/delete flags; create/update/delete segments) to write audit_logs rows via write_audit_log(), with pre-mutation payload_before snapshots and X-User-Email forwarded from the BFF.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-13T04:14:00Z
- **Completed:** 2026-06-13T04:22:44Z
- **Tasks:** 2 completed
- **Files modified:** 3

## Accomplishments
- All 5 flag-mutation endpoints (create/update/enable/disable/delete) now call `audit_service.write_audit_log()` with `target_type=FLAG` and correct `ActionType` (CREATE_FLAG/UPDATE_FLAG/ENABLE_FLAG/DISABLE_FLAG/DELETE_FLAG)
- All 3 segment-mutation endpoints (create/update/delete) now call `audit_service.write_audit_log()` with `target_type=SEGMENT` and correct `ActionType` (CREATE_SEGMENT/UPDATE_SEGMENT/DELETE_SEGMENT)
- `payload_before` always captured prior to the mutating service call (update/enable/disable/delete) via `FlagResponse`/`SegmentResponse.model_validate(...).model_dump(mode='json')`
- BFF `flags.ts` forwards `X-User-Email` so `audit_logs.user_email` is populated for flag/segment writes
- Added `_audit_request_meta()` helper for client_ip/user_agent extraction, reused across all 8 endpoints

## Task Commits

Each task was committed atomically:

1. **Task 1: Instrument feature_flags router (flags: create/update/enable/disable/delete)** - `636fc90` (feat)
2. **Task 2: Instrument segments endpoints + BFF flags.ts X-User-Email + unit tests** - `fe4de22` (feat)

**Plan metadata:** (pending) `docs(16-02): complete plan`

## Files Created/Modified
- `backend/app/domains/feature_flags/router.py` - 8 mutation endpoints (5 flag + 3 segment) now write audit_logs rows; added `_audit_request_meta()` helper and audit imports
- `bff/src/routes/flags.ts` - Added `X-User-Email` header forwarding alongside existing Sub/Roles/Tenant-Id
- `backend/tests/test_audit_domain.py` - Added `test_action_type_constants_cover_flags_and_segments` and `test_audit_request_meta_returns_none_for_none_request`

## Decisions Made
- Flag audit writes use `flag.tenant_id` (the flag's own nullable tenant field) rather than the `X-User-Tenant-Id` header, consistent with `audit_logs.tenant_id` being nullable for global-scope flags
- `update_segment`/`delete_segment` perform an extra `service.get_segment(db, segment_id)` fetch before mutation specifically to capture a non-trivial `payload_before` snapshot (since `update_segment`'s own return value is post-mutation)
- Segments hardcode `environment='production'` in audit payloads since the `Segment` model has no `environment` field

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Plan 16-03 (parallel Wave 2 plan) appended two additional unit tests to `backend/tests/test_audit_domain.py` after this plan's Task 2 commit (`test_action_type_constants_cover_users_tenants_companies`, `test_audit_log_create_defaults_environment_to_production`). Per the plan's shared-file note, these were left in place — full test suite re-verified with all 13 tests passing (this plan's 2 + 16-03's 2 + 16-01's 9... actual count: 11 base + 2 new from this plan = 13).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All flag/segment write-path instrumentation complete; `audit_logs` table will now receive rows for every flag/segment mutation with correct before/after diffs and actor metadata (user_id, user_email, environment, client_ip, user_agent)
- Plan 16-04 (Activity Timeline UI) can now query `/audit-logs` and expect non-empty data for flags/segments domain once mutations occur
- Plan 16-03 (users/tenants/companies instrumentation, parallel Wave 2) proceeds independently using the same `write_audit_log()` pattern

---
*Phase: 16-mvp2-auditoria*
*Completed: 2026-06-13*

## Self-Check: PASSED

- FOUND: .planning/phases/16-mvp2-auditoria/16-02-SUMMARY.md
- FOUND: 636fc90 (Task 1 commit)
- FOUND: fe4de22 (Task 2 commit)
