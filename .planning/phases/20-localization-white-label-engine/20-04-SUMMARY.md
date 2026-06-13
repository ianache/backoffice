---
phase: 20-localization-white-label-engine
plan: 04
subsystem: api
tags: [fastapi, sqlalchemy, async, websocket, localization, sdk]

# Dependency graph
requires:
  - phase: 20-localization-white-label-engine
    plan: 20-02
    provides: "labels/service.py resolve_labels()/report_missing_label()/list_namespaces()/list_missing_label_reports()"
  - phase: 20-localization-white-label-engine
    plan: 20-03
    provides: "labels/router.py admin CRUD endpoints (create_key/update_key/update_key_value/delete_key/restore_override/delete_namespace)"
provides:
  - "backend/app/domains/sdk/router.py — GET /api/v1/sdk/labels/bootstrap, GET /api/v1/sdk/labels/prefetch, POST /api/v1/sdk/labels/missing (SDK-key-auth two-phase hydration + RF-06 miss reporting)"
  - "backend/app/domains/labels/router.py — INVALIDATE_NAMESPACE WS broadcast wired into create_key/update_key/update_key_value/delete_key/restore_override/delete_namespace"
  - "backend/tests/test_labels_sdk_router.py — 6 tests covering bootstrap/prefetch/missing + WS broadcast"
affects: [20-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-phase hydration: /labels/bootstrap (eager namespaces) + /labels/prefetch (explicit lazy namespaces, comma-separated) both delegate to labels_service.resolve_labels() per namespace, returning {namespaces: {...}, locale}"
    - "INVALIDATE_NAMESPACE broadcast: getattr(request.app.state, 'ws_manager', None) guard + ws_manager.broadcast(tenant_id, {type: INVALIDATE_NAMESPACE, namespace}) — reuses ConnectionManager//ws/flags/{tenant_id} from feature_flags, no new endpoint, no Redis"

key-files:
  created:
    - backend/tests/test_labels_sdk_router.py
  modified:
    - backend/app/domains/sdk/router.py
    - backend/app/domains/labels/router.py

key-decisions:
  - "labels_report_missing returns 204 with no body (matches plan's status_code=204 spec); service.report_missing_label() return value discarded"
  - "delete_namespace also broadcasts INVALIDATE_NAMESPACE (per plan prose: cascades label invalidation), gated on x_user_tenant_id being non-empty since namespace deletion has no per-row tenant_id to snapshot"
  - "Test 6's PATCH path resolved dynamically via app.routes lookup by route name (update_key_value) to be resilient to the /labels vs /api/v1/labels prefix decision made in app/main.py by concurrent plan 20-03"

requirements-completed: [LBL-05, LBL-06, LBL-07]

# Metrics
duration: 18min
completed: 2026-06-13
---

# Phase 20 Plan 04: SDK Labels Bootstrap/Prefetch/Missing + INVALIDATE_NAMESPACE Broadcast Summary

**Two-phase label hydration endpoints (`/api/v1/sdk/labels/bootstrap` for eager namespaces, `/api/v1/sdk/labels/prefetch` for explicit lazy namespaces) plus RF-06 missing-label reporting on the SDK router, and INVALIDATE_NAMESPACE WebSocket broadcasts wired into all six label/namespace mutation handlers in the admin labels router, reusing the existing ConnectionManager over `/ws/flags/{tenant_id}`.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-06-13T20:00:00Z
- **Completed:** 2026-06-13T20:18:00Z
- **Tasks:** 2 completed
- **Files modified:** 3 (2 modified, 1 created)

## Accomplishments
- `GET /api/v1/sdk/labels/bootstrap` returns `{"namespaces": {<eager_ns>: {...resolved labels...}}, "locale": ...}` for all namespaces with `strategy='eager'`, applying tenant/company/product override-by-proximity via `labels_service.resolve_labels()`
- `GET /api/v1/sdk/labels/prefetch?namespaces=a,b` returns resolved labels for the explicitly requested namespaces, including `{}` for namespaces with no rows (not a 404)
- `POST /api/v1/sdk/labels/missing` ingests RF-06 missing-label reports via `labels_service.report_missing_label()`, returns 204
- All three new endpoints inherit SDK-secret auth from the existing `sdk` router's `dependencies=[Depends(verify_sdk_secret)]`
- `create_key`, `update_key`, `update_key_value`, `delete_key`, `restore_override`, and `delete_namespace` in `labels/router.py` now broadcast `{"type": "INVALIDATE_NAMESPACE", "namespace": <ns>}` to `/ws/flags/{tenant_id}` via `request.app.state.ws_manager`, guarded with `getattr(...)` so test environments without `ws_manager` don't error
- New `backend/tests/test_labels_sdk_router.py` with 6 tests covering bootstrap (eager-only + override-by-proximity), prefetch (including empty-namespace), missing-report dedup/hit-counting, SDK-auth enforcement, and the WS broadcast on `update_key_value`

## Task Commits

1. **Task 1: SDK labels bootstrap/prefetch/missing endpoints** - `c2556e0` (feat)
2. **Task 2: INVALIDATE_NAMESPACE WebSocket broadcast on label/namespace mutations** - `6e111b6` (feat)

**Plan metadata:** `224ccd5` (docs)

## Files Created/Modified
- `backend/app/domains/sdk/router.py` - added `from app.domains.labels import service as labels_service` / `from app.domains.labels.schemas import MissingLabelReportCreate` imports, and three endpoints: `labels_bootstrap`, `labels_prefetch`, `labels_report_missing`
- `backend/app/domains/labels/router.py` - added `INVALIDATE_NAMESPACE` broadcast calls to `create_key`, `update_key`, `update_key_value`, `delete_key` (capturing `namespace_snapshot` before delete), `restore_override`, and `delete_namespace`; also fixed a missing `from fastapi.responses import JSONResponse, PlainTextResponse` import required by the pre-existing `/export` endpoint (Rule 1 bug fix discovered while editing this file)
- `backend/tests/test_labels_sdk_router.py` - new file, 6 async tests using an in-memory SQLite `AsyncSession` overridden into `app.main.app` via `get_db` dependency override + `TestClient`

## Decisions Made
- Followed the plan's prescriptive code listing for Task 1 verbatim (bootstrap/prefetch/missing endpoint bodies)
- For Task 2, added the broadcast block as a small guarded snippet after each handler's `write_audit_log()` call, per the plan's exact pattern
- `delete_namespace` broadcast included per the plan's prose ("delete_namespace SHOULD broadcast too since it cascades label invalidation") even though it wasn't in the plan's concrete handler bullet list — guarded on `x_user_tenant_id` being non-empty since `Namespace` rows have no tenant scoping of their own
- Test 6 resolves its PATCH path dynamically from `app.routes` (matching route name `update_key_value`) rather than hardcoding `/labels/keys/{id}/value`, because a concurrent plan (20-03) was simultaneously deciding whether `app.main.py` mounts `labels_router` at `/labels` or `/api/v1/labels`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing `JSONResponse`/`PlainTextResponse` import in `labels/router.py`**
- **Found during:** Task 2 (re-reading `labels/router.py` before editing)
- **Issue:** The `/export` endpoint (added by concurrent plan 20-09, committed at `d76293c`) calls `JSONResponse(...)` and `PlainTextResponse(...)` but `backend/app/domains/labels/router.py` only imported `from fastapi import ...` — `fastapi.responses` was never imported, which would raise `NameError` at request time for `GET /labels/export`.
- **Fix:** Added `from fastapi.responses import JSONResponse, PlainTextResponse` to the top-level imports.
- **Files modified:** `backend/app/domains/labels/router.py`
- **Verification:** `python -m py_compile backend/app/domains/labels/router.py` passes (syntax-only; full import-level check deferred per environment note)
- **Committed in:** `6e111b6` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (missing import bug in a file shared with concurrent plans)
**Impact on plan:** None — fix is additive and unrelated to this plan's own endpoint logic; it was necessary for `labels/router.py` to import cleanly at all.

## Issues Encountered

- **Backend Python dependencies not installed** — same limitation as 20-01/20-02/20-09 (`sqlalchemy`, `fastapi`, `pytest`, `aiosqlite` all absent from system Python; no venv). The plan's specified verification (`python -m pytest tests/test_labels_sdk_router.py -x -q -k "not broadcast"` and `python -m pytest tests/test_labels_sdk_router.py tests/test_labels_router.py -x -q`) could not be executed. Mitigated via `python -m py_compile` on all three touched/created files (`backend/app/domains/sdk/router.py`, `backend/app/domains/labels/router.py`, `backend/tests/test_labels_sdk_router.py`) — all pass. Logged to `deferred-items.md` with the recommended pytest commands to run once `backend/requirements.txt` is installed.
- **Commit attribution race on shared files** — `git add backend/app/domains/labels/router.py backend/tests/test_labels_sdk_router.py` (Task 2) unintentionally swept in two files written to disk by concurrent agents between my `git status --short` check and the `git add`/`git commit`: `backend/app/main.py` (20-03's `app.include_router(labels_router, prefix="/api/v1")` wiring) and `backend/tests/test_labels_router.py` (a new 308-line test file from 20-03/20-09). Both files were verified to compile correctly (`python -m py_compile`) and their content was not altered or reverted — only the commit message/attribution is "wrong" (commit `6e111b6` is titled for 20-04 but also contains these two files' content). No destructive git operations were used. Logged to `deferred-items.md` for the phase owner to reconcile attribution if needed; content itself is correct and harmless.
- **Backend route prefix inconsistency** — `app/main.py` (modified by concurrent plan 20-03, swept into `6e111b6`) registers `labels_router` with `prefix="/api/v1"`, making the backend serve `/api/v1/labels/*` directly. This differs from the `feature_flags` convention (`flags_router` has `prefix="/flags"`, included with no override; BFF prepends `/api/v1`). Not introduced by this plan — flagged in `deferred-items.md` for the phase owner.
- **LBL-05, LBL-06, LBL-07 not present in `.planning/REQUIREMENTS.md`** — same traceability gap as other Phase 20 plans; `requirements mark-complete` will likely return `not_found` for these IDs. Logged to `deferred-items.md`.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

- `GET /api/v1/sdk/labels/bootstrap`, `GET /api/v1/sdk/labels/prefetch`, and `POST /api/v1/sdk/labels/missing` are ready for the sdk-js `LabelClient` (Plan 20-05) to consume for bootstrap/prefetch/miss-reporting
- `INVALIDATE_NAMESPACE` WS messages are now broadcast on every label/namespace mutation — Plan 20-05's `LabelClient` hot-reload listener can subscribe to `/ws/flags/{tenant_id}` and react to `{"type": "INVALIDATE_NAMESPACE", "namespace": "..."}` by re-calling `/labels/prefetch` for the affected namespace
- **Before Plan 20-05 begins (or at the earliest convenient point):** run `pip install -r backend/requirements.txt` and execute `python -m pytest backend/tests/test_labels_sdk_router.py backend/tests/test_labels_router.py -q` plus the full suite to confirm all new tests pass and no regressions were introduced — this could not be verified in the current environment (no sqlalchemy installed)
- Add LBL-05, LBL-06, LBL-07 (and all other LBL-* IDs referenced across Phase 20 plans) to `.planning/REQUIREMENTS.md`'s traceability table so future `requirements mark-complete` calls succeed
- Phase owner should reconcile the `app/main.py` / `test_labels_router.py` commit-attribution note above with 20-03/20-09's own SUMMARY.md files

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created/modified files found on disk (backend/app/domains/sdk/router.py, backend/app/domains/labels/router.py, backend/tests/test_labels_sdk_router.py, 20-04-SUMMARY.md); all task commits (c2556e0, 6e111b6, 224ccd5) found in git log.
