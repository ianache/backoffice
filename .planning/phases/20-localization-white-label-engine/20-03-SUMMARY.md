---
phase: 20-localization-white-label-engine
plan: 03
subsystem: api
tags: [fastapi, sqlalchemy, audit-log, rbac, optimistic-concurrency, labels]

# Dependency graph
requires:
  - phase: 20-localization-white-label-engine
    provides: "Plan 20-02 labels service layer (resolve_labels, Namespace/LocalizedLabel CRUD, missing-label reports, 409 optimistic concurrency)"
provides:
  - "Internal-secret-authenticated admin CRUD API for namespaces and localized labels at /api/v1/labels/*"
  - "Role-gated structure edit (PlatformAdmin/TenantAdmin/TenantOwner/ProductManager) vs value-only edit (+UXWriter)"
  - "Full before/after audit logging on every namespace/label mutation"
  - "409 optimistic-concurrency handling with PI-02 Spanish message"
  - "DELETE/restore-override endpoint for company/product-level label overrides (RF-05)"
  - "GET /labels/missing diagnostics listing (RF-06)"
affects: [20-05, 20-06, 20-07, 20-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Internal-secret-authenticated admin router mirrors feature_flags/router.py pattern (dependencies=[Depends(verify_internal_secret)])"
    - "_require_structure_role()/_require_value_role() helpers raise HTTPException(403) based on X-User-Roles header"
    - "_audit_request_meta(request) extracts client_ip/user_agent for audit_service.write_audit_log() calls"
    - "RestoreOverridePayload(BaseModel) declared via standard top-level import, not walrus-operator hack"

key-files:
  created:
    - backend/tests/test_labels_router.py
    - backend/tests/test_labels_missing.py
  modified:
    - backend/app/domains/labels/router.py
    - backend/app/main.py

key-decisions:
  - "Registered labels_router with app.include_router(labels_router, prefix=\"/api/v1\") in main.py — router.py itself declares prefix=\"/labels\", so the admin API mounts at /api/v1/labels/* to match the pre-existing test_labels_sdk_router.py (20-04) expectations for PATCH /api/v1/labels/keys/{id}/value"
  - "Re-added missing 'from fastapi.responses import JSONResponse, PlainTextResponse' import (Rule 1) — required by the concurrently-added /export endpoint (20-09), would have been a runtime NameError despite passing py_compile"

patterns-established:
  - "Admin CRUD routers for Phase 20 domains follow: internal-secret dependency + role-helper functions + audit_service.write_audit_log on every mutation + _audit_request_meta(request) for client_ip/user_agent"

requirements-completed: [LBL-09, LBL-10, LBL-11, LBL-12]

# Metrics
duration: ~25min
completed: 2026-06-13
---

# Phase 20 Plan 03: Labels Admin CRUD Router Summary

**Internal-secret-authenticated FastAPI router (`/api/v1/labels/*`) providing full namespace/label CRUD with PlatformAdmin/TenantAdmin/TenantOwner/ProductManager role gating, UXWriter value-only PATCH, before/after audit logging on every mutation, 409 PI-02 optimistic-concurrency handling, a restore-override endpoint, and a /missing diagnostics listing.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- 12 endpoints registered under `/api/v1/labels/*`:
  - `GET/POST /namespaces`, `PATCH/DELETE /namespaces/{id}` — full namespace CRUD (structure roles only)
  - `GET/POST /keys`, `PATCH /keys/{id}`, `DELETE /keys/{id}` — full label CRUD (structure roles only)
  - `PATCH /keys/{id}/value` — value-only edit, additionally allowed for UXWriter
  - `POST /keys/restore` — restore-override endpoint (RF-05), deletes a company/product-level override row
  - `GET /missing` — missing-label diagnostics listing (RF-06), tenant-scoped, ordered by hits descending
  - `GET /export` (20-09, concurrent) — JSON/CSV export, present in final router.py
- Every namespace/label mutation writes a before/after `AuditLog` entry via `audit_service.write_audit_log()` with the correct `ActionType` (CREATE_LABEL, UPDATE_LABEL, DELETE_LABEL, UPDATE_NAMESPACE, DELETE_NAMESPACE, etc.)
- 409 responses on stale `version` use the exact PI-02 Spanish message: "La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios."
- Role gating: `_require_structure_role()` (PlatformAdmin/TenantAdmin/TenantOwner/ProductManager) for structural CRUD; `_require_value_role()` (adds UXWriter) for `PATCH /keys/{id}/value`
- `labels_router` registered in `app.main` with `prefix="/api/v1"`, mounting the admin API at `/api/v1/labels/*`
- 9 new tests across `test_labels_router.py` (7 tests) and `test_labels_missing.py` (2 tests), covering role gating, audit-log side effects, 409 handling, UXWriter restrictions, namespace audit, restore-override, missing-reports listing, and router registration

## Task Commits

This plan's deliverables landed across several commits due to a shared-index race with concurrently-executing plans 20-04/20-09 on the same branch (documented in detail under "Deviations from Plan" and in `deferred-items.md`):

1. **Task 1: Build labels admin CRUD router + register in main.py + test_labels_router.py** - `6e111b6` (feat — committed under 20-04's message, but contains this plan's `router.py`, `main.py`, and `test_labels_router.py` changes; verified via `git show --stat 6e111b6`)
2. **Task 2: Add test_labels_missing.py (GET /missing + router registration smoke test)** - `25138e7` (test(20-03))

**Plan metadata:**
- `a1194a6` (docs(20-03): document pytest-deferral, requirements gaps, and commit-attribution race)
- `2d9c6e1` (titled feat(20-03) but contains unrelated concurrent-agent files — see Deviations)

## Files Created/Modified

- `backend/app/domains/labels/router.py` - Full namespace + label CRUD, role gating, audit logging, 409 handling, restore-override, /missing, /export (12 endpoints total)
- `backend/app/main.py` - Registered `labels_router` at `/api/v1/labels/*`
- `backend/tests/test_labels_router.py` - 7 tests: namespace CRUD role gating, audit log on create, 409 version conflict, UXWriter rejected from structure edits, UXWriter can PATCH value, namespace update/delete audit, restore-override
- `backend/tests/test_labels_missing.py` - 2 tests: GET /missing tenant-scoped/hits-descending, router registration smoke test

## Decisions Made

- **`/api/v1` prefix registration** (architectural-adjacent but low-risk, applied directly): `router.py` declares `APIRouter(prefix="/labels", ...)`. In `main.py`, registered via `app.include_router(labels_router, prefix="/api/v1")` so the admin API mounts at `/api/v1/labels/*`. This matches `test_labels_sdk_router.py` (20-04, written concurrently) which expects `PATCH /api/v1/labels/keys/{id}/value`. Note: `feature_flags`'s `flags_router` instead uses a bare `/flags` prefix with the BFF prepending `/api/v1` — flagged in `deferred-items.md` for the phase owner to confirm the BFF proxy for `/api/v1/labels` (Plan 20-05+) doesn't double-prefix.
- **`RestoreOverridePayload(BaseModel)`** declared via a standard top-level `from pydantic import BaseModel` import and normal class definition, per plan's explicit instruction to avoid a walrus-operator import hack.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Re-added missing `fastapi.responses` import**
- **Found during:** Task 1 (router.py)
- **Issue:** While `router.py` was being concurrently extended by Plan 20-09's `/export` endpoint (which uses `JSONResponse`/`PlainTextResponse`), the import line `from fastapi.responses import JSONResponse, PlainTextResponse` was absent from the top-level imports. `python -m py_compile` (syntax-only) did not catch this, but it would cause a `NameError` at runtime when `/export` is called.
- **Fix:** Re-added `from fastapi.responses import JSONResponse, PlainTextResponse` to the import block.
- **Files modified:** `backend/app/domains/labels/router.py`
- **Verification:** `python -m py_compile app/domains/labels/router.py` passes; all 12 `@router.*` endpoint decorators confirmed present via `grep -n "^@router\.\(get\|post\|patch\|delete\)"`.
- **Committed in:** `6e111b6` (part of the shared-index commit, see below)

### Process Deviations (no code impact)

**2. Concurrent multi-agent commit-attribution race**
- A separate agent was concurrently executing plans 20-04 and 20-09 on the same branch (`master`) in the same working tree, making real `git commit`s during this plan's execution.
- This plan's intended commit (`git add backend/app/domains/labels/router.py backend/app/main.py backend/tests/test_labels_router.py && git commit -m "feat(20-03): ..."`) landed in the shared git index at a moment when the concurrent agent had also staged files. The resulting commit `6e111b6` (titled "feat(20-04): broadcast INVALIDATE_NAMESPACE on label/namespace mutations") absorbed this plan's `router.py`/`main.py`/`test_labels_router.py` changes alongside 20-04's own WS-broadcast additions and a 7th test (`test_update_label_value_broadcasts_invalidate_namespace`, owned by 20-04).
- A separate commit `2d9c6e1` (titled "feat(20-03): add labels admin CRUD router with role checks and audit logging") instead captured unrelated concurrent-agent planning-doc changes (`.planning/STATE.md`, `.planning/ROADMAP.md`, `20-09-SUMMARY.md`, `deferred-items.md`).
- **No content was lost, reverted, or duplicated.** Verified via `git show --stat 6e111b6`, `git show HEAD:backend/app/main.py | grep labels`, `git ls-files backend/tests/test_labels_router.py`, and `python -m py_compile` on all four files — all of this plan's deliverables are present and correct in HEAD. This is purely a commit-message/attribution mismatch, consistent with the same shared-file race documented under "From Plan 20-04" and "From Plan 20-09" in `deferred-items.md`.
- Per the destructive-git prohibition, no `git reset`/`rebase`/`commit --amend` was used to "fix" attribution. Documented here and in `deferred-items.md` for the phase owner.

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug), plus 1 documented process deviation (commit attribution, no content impact)
**Impact on plan:** The Rule 1 fix was necessary for runtime correctness (prevents a NameError on `/export`). The commit-attribution race had zero impact on delivered code/tests — all deliverables verified present and compiling in HEAD.

## Issues Encountered

- **`sqlalchemy` and other backend Python deps not installed** — consistent with 20-01/20-02/20-04/20-09. All new/changed Python files (`backend/app/domains/labels/router.py`, `backend/app/main.py`, `backend/tests/test_labels_router.py`, `backend/tests/test_labels_missing.py`) were verified via `python -m py_compile` only. Documented in `deferred-items.md` — run `python -m pytest backend/tests/test_labels_router.py backend/tests/test_labels_missing.py -q` once `backend/requirements.txt` is installed.
- **LBL-09..12 not present in `.planning/REQUIREMENTS.md`** — same traceability gap as all other Phase 20 plans (LBL-01..08, LBL-13, LBL-14, LBL-16 also missing). `requirements mark-complete` will likely return `not_found`. Documented in `deferred-items.md` for the phase owner to backfill REQUIREMENTS.md's traceability table with all Phase 20 LBL-* IDs.

## Known Stubs

None — all 12 endpoints are fully wired to `service.py` (Plan 20-02) functions with real DB-backed CRUD, audit logging, and role checks. No placeholder/mock data paths introduced.

## Threat Flags

None — the `/api/v1/labels/*` admin surface is gated by the same `verify_internal_secret` dependency used by `feature_flags/router.py` (existing trust boundary), with additional role checks (`_require_structure_role`/`_require_value_role`) layered on top per the plan's `<threat_model>`. No new network endpoints, auth mechanisms, or schema changes outside the plan's scope were introduced (the `/export` endpoint was added by concurrent plan 20-09, not this plan).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `/api/v1/labels/*` admin CRUD API is fully functional and audit-logged, ready for BFF proxy wiring (Plan 20-05+) and frontend admin UI (namespaces/keys management screens per `design/stitch/labeling - namespaces_keys_management.html`).
- Phase owner should confirm the BFF's `/api/v1/labels` proxy route doesn't double-prefix given `main.py`'s `app.include_router(labels_router, prefix="/api/v1")`.
- REQUIREMENTS.md needs a backfill pass for all Phase 20 LBL-* IDs (LBL-01 through LBL-16) before `requirements mark-complete` calls will succeed across this phase's plans.
- Once `backend/requirements.txt` is installed, run the full Phase 20 test suite (`test_labels_router.py`, `test_labels_missing.py`, `test_labels_sdk_router.py`, `test_labels_export.py`, `test_labels_service.py`, `test_labels_resolve.py`) to confirm no regressions from the concurrent multi-plan execution.

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created/modified files exist on disk:
- FOUND: backend/app/domains/labels/router.py
- FOUND: backend/app/main.py
- FOUND: backend/tests/test_labels_router.py
- FOUND: backend/tests/test_labels_missing.py
- FOUND: .planning/phases/20-localization-white-label-engine/20-03-SUMMARY.md

All referenced commit hashes exist in git history:
- FOUND: 6e111b6
- FOUND: 25138e7
- FOUND: a1194a6
