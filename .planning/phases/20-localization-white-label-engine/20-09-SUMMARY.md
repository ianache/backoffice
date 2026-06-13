---
phase: 20-localization-white-label-engine
plan: 09
subsystem: api
tags: [fastapi, sqlalchemy, csv, async, localization, export]

# Dependency graph
requires:
  - phase: 20-localization-white-label-engine
    plan: 20-02
    provides: "resolve_labels() 3-level inheritance resolver and labels/service.py module"
provides:
  - "export_namespace_json() and export_namespace_csv() helpers in backend/app/domains/labels/service.py"
  - "GET /labels/export?tenant_id=&company_id=&product_id=&namespace=&format=json|csv endpoint in backend/app/domains/labels/router.py"
  - "backend/tests/test_labels_export.py — 7 async tests covering service-level export shapes and router-level endpoint behavior"
affects: [20-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Python stdlib csv module (csv.writer/io.StringIO) for RFC 4180-compliant CSV export, per RESEARCH.md 'Don't Hand-Roll' guidance"
    - "_resolve_with_level() helper extends resolve_labels()'s override-by-proximity merge to also track which level (tenant/company/product) contributed each key, for the CSV 'level' column"

key-files:
  created:
    - backend/tests/test_labels_export.py
  modified:
    - backend/app/domains/labels/service.py
    - backend/app/domains/labels/router.py

key-decisions:
  - "level column reflects the most-specific level contributing the es_PE value (documented via code comment in _resolve_with_level/export_namespace_csv), per plan's Test 4 spec"
  - "GET /labels/export inherits the router-level verify_internal_secret dependency (X-Internal-Secret header) like all other /labels/* endpoints — no new auth mechanism introduced"
  - "Actual mounted path is /labels/export (router prefix is '/labels', not '/api/v1/labels' despite main.py's inline comment) — tests use settings.internal_secret for the X-Internal-Secret header"

patterns-established:
  - "Export endpoints return JSONResponse for format=json and PlainTextResponse with Content-Disposition: attachment for format=csv, with 422 raised explicitly for unrecognized format values"

requirements-completed: [LBL-14]

# Metrics
duration: 12min
completed: 2026-06-13
---

# Phase 20 Plan 09: Labels Export Endpoint (RF-07 JSON/CSV) Summary

**`export_namespace_json()`/`export_namespace_csv()` service helpers (override-by-proximity resolved, stdlib `csv` module for RFC 4180 output) plus a new `GET /labels/export?format=json|csv` router endpoint, covered by 7 async tests.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-13T19:58:38Z
- **Completed:** 2026-06-13T20:04:49Z
- **Tasks:** 2 completed
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- `export_namespace_json()` returns the SDK-bootstrap-like nested shape `{namespace: {label_key: {es_PE: ..., en_US: ...}}}`, resolved via the existing `resolve_labels()` 3-level inheritance resolver (tenant -> company -> product override-by-proximity)
- `export_namespace_csv()` produces RFC 4180-compliant CSV (`namespace,label_key,es_PE,en_US,level` columns) using Python's stdlib `csv` module — correctly quotes/escapes values containing commas
- New `_resolve_with_level()` helper tracks which level (tenant/company/product) contributed each resolved key, feeding the CSV `level` column
- `GET /labels/export` endpoint added to `backend/app/domains/labels/router.py`: `format=json` returns `JSONResponse`, `format=csv` returns `PlainTextResponse` with `Content-Disposition: attachment; filename="{namespace}_{tenant_id}.csv"`, and `format=xml` (or any other value) returns `422`
- 7 async tests in `backend/tests/test_labels_export.py`: 4 service-level (JSON shape, company-override application, CSV header/RFC-4180 comma round-trip, CSV level column) + 3 router-level (JSON endpoint, CSV endpoint with headers, invalid-format 422)

## Task Commits

1. **Task 1: export_namespace_json() and export_namespace_csv() service helpers** - `7a2cb30` (feat)
2. **Task 2: GET /labels/export router endpoint** - `d76293c` (feat)

**Plan metadata:** (pending — see final commit below)

## Files Created/Modified
- `backend/app/domains/labels/service.py` - added `import csv, io`, `export_namespace_json()`, `_resolve_with_level()`, `export_namespace_csv()`
- `backend/app/domains/labels/router.py` - added `from fastapi.responses import JSONResponse, PlainTextResponse` and the `GET /export` endpoint handler
- `backend/tests/test_labels_export.py` - new file: 7 async tests (4 service-level via in-memory SQLite AsyncSession + autouse `clear_cache()` fixture matching `test_labels_resolve.py` conventions; 3 router-level via FastAPI `TestClient` with `get_db` dependency override, matching `test_labels_sdk_router.py` conventions)

## Decisions Made
- Followed the plan's prescriptive code listings for `export_namespace_json()`, `_resolve_with_level()`, and `export_namespace_csv()` verbatim (interface-first plan).
- For router-level tests, used `settings.internal_secret` (the actual configured default) as the `X-Internal-Secret` header value rather than overriding `verify_internal_secret`, since the `/labels` router-level dependency requires this header for all endpoints including `/export`.
- Confirmed the actual mounted path is `/labels/export` (router prefix is `"/labels"`, not `/api/v1/labels` as `main.py`'s inline comment suggests) — tests target `/labels/export` directly.

## Deviations from Plan

None (functional) - plan executed as written for both tasks' code content. One process-level deviation documented below regarding the shared `router.py` file.

### Auto-fixed Issues

**1. [Rule 3 - Blocking/shared-file] Committed router.py including 20-03's uncommitted base content**
- **Found during:** Task 2
- **Issue:** Per the plan's concurrency note, `backend/app/domains/labels/router.py` is created by parallel plan 20-03 and also touched by 20-04 (WS broadcast wiring). At the time Task 2 was ready to commit, `router.py` existed in the shared worktree (with 20-03's namespace/label CRUD endpoints) but was still **untracked** — 20-03 had not yet committed it. Committing only a diff was not possible for an untracked file.
- **Fix:** Added the `/export` endpoint additively to the existing `router.py` content, then committed the full file (20-03's base CRUD endpoints + this plan's `/export` endpoint) along with `test_labels_export.py`, with an explicit note in the commit message documenting this captures the shared-worktree state at commit time. This ensures the `/export` endpoint is not lost to a subsequent overwrite by another agent.
- **Files modified:** `backend/app/domains/labels/router.py`
- **Verification:** `python -m py_compile` passed on the full file; `git show c2556e0 --stat` confirmed 20-04's most recent commit did not touch `labels/router.py` (only `sdk/router.py` and its test file), so no WS-wiring content was overwritten.
- **Committed in:** `d76293c` (Task 2 commit)
- **Follow-up flagged:** Logged to `deferred-items.md` — if 20-04's INVALIDATE_NAMESPACE WS broadcast wiring (expected in `update_label_value`'s router handler per `test_labels_sdk_router.py` Test 6) is added in a separate commit, the phase owner should verify it survives/merges correctly with `d76293c`.

---

**Total deviations:** 1 auto-fixed (Rule 3, shared-file coordination — no functional code change beyond the plan's spec)
**Impact on plan:** None on this plan's deliverables. Documented as a cross-plan coordination note for the phase owner to verify after 20-03/20-04 land their own commits.

## Issues Encountered
- Same backend dependency-installation limitation as 20-01/20-02: `sqlalchemy`/`fastapi`/etc. are not installed in this environment (`ModuleNotFoundError: No module named 'sqlalchemy'`). The plan's specified verification (`cd backend && python -m pytest tests/test_labels_export.py -x -q`) could not be executed.
- **Mitigation:** Verified `backend/app/domains/labels/service.py`, `backend/app/domains/labels/router.py`, and `backend/tests/test_labels_export.py` all compile cleanly via `python -m py_compile`. Full pytest execution (all 7 tests) deferred — logged in `deferred-items.md`.
- `LBL-14` is not present in `.planning/REQUIREMENTS.md`'s traceability table (same gap pattern as LBL-01/02/03/04/13/16 from prior plans) — `requirements mark-complete LBL-14` is expected to return `not_found`. Logged to `deferred-items.md`.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness
- `GET /labels/export?tenant_id=&namespace=&format=json|csv` is ready for the mui-labeling admin UI's ImportExportModal (20-08) to call directly via fetch+Blob (CSV) or fetch+JSON.
- Before merging this phase: run `pip install -r backend/requirements.txt` (dedicated venv) and `python -m pytest backend/tests/test_labels_export.py -q` plus the full suite to confirm all 7 new tests pass and 20-03/20-04's concurrent `router.py` changes coexist correctly with the `/export` endpoint added here.
- Add LBL-14 (and all other pending LBL-* IDs) to `.planning/REQUIREMENTS.md`'s traceability table.

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created/modified files found on disk (test_labels_export.py, labels/router.py, 20-09-SUMMARY.md); both task commits (7a2cb30, d76293c) found in git log.
