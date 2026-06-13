---
phase: 20-localization-white-label-engine
plan: 02
subsystem: api
tags: [sqlalchemy, fastapi, pydantic, async, in-memory-cache, localization]

# Dependency graph
requires:
  - phase: 20-localization-white-label-engine
    plan: 20-01
    provides: "labels domain models/schemas (Namespace, LocalizedLabel, MissingLabelReport) and g001/g002 migrations"
provides:
  - "backend/app/domains/labels/service.py — resolve_labels() 3-level inheritance resolver with in-memory cache, invalidate_namespace_cache(), Namespace/Label CRUD, missing-label report upsert/dedup"
  - "Unit tests for resolution/cache (test_labels_resolve.py) and CRUD/dedup (test_labels_service.py)"
affects: [20-03, 20-04, 20-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level dict cache (_label_cache) keyed by 'tenant:company:product:namespace:locale' — Redis upgrade path preserves resolve_labels()/invalidate_namespace_cache() signatures (Pitfall 1, no Redis client in codebase)"
    - "Optimistic concurrency via integer version column + HTTPException(409) raised directly in service layer (PI-02 fixed Spanish message), matching feature_flags convention of HTTP semantics in service"
    - "Missing-label reports deduped via SELECT-then-UPDATE/INSERT (no raw upsert SQL) keyed on (tenant_id, namespace, label_key, locale); auto-cleared by create_label() per RF-06"

key-files:
  created:
    - backend/app/domains/labels/service.py
    - backend/tests/test_labels_resolve.py
    - backend/tests/test_labels_service.py
  modified: []

key-decisions:
  - "service.py written as a single file containing both Task 1 (resolver/cache) and Task 2 (CRUD/missing-report) logic per the plan's full code listing; commits split logically by test file rather than by physical file diff, since both tasks' code landed in the same file"
  - "test_labels_service.py follows the same async SQLite AsyncSession + autouse clear_cache() fixture conventions as test_labels_resolve.py (20-02 Task 1), not the no-DB MockFlag style used in test_feature_flags_domain.py"

patterns-established:
  - "Async unit tests for the labels domain use an in-memory SQLite engine (create_async_engine('sqlite+aiosqlite://')) with Base.metadata.create_all per test, plus an autouse service.clear_cache() fixture for module-level cache isolation"

requirements-completed: [LBL-03, LBL-04, LBL-13]

# Metrics
duration: 20min
completed: 2026-06-13
---

# Phase 20 Plan 02: Labels Service Layer (Resolver, Cache, CRUD, Missing-Label Reports) Summary

**`labels/service.py` implementing the 3-level inheritance resolver (`resolve_labels()`) with an in-memory cache, Namespace/Label CRUD with optimistic-concurrency 409s, and missing-label-report dedup/auto-cleanup — covered by 11 async unit tests across two test files.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-06-13T19:36:00Z (continuation from prior session's uncommitted work)
- **Completed:** 2026-06-13T19:56:04Z
- **Tasks:** 2 completed
- **Files modified:** 3 (2 created new, 1 verified pre-existing)

## Accomplishments
- `resolve_labels()` merges tenant/company/product `LocalizedLabel` rows with override-by-proximity (product > company > tenant), results cached in-memory keyed by `tenant:company:product:namespace:locale`
- `invalidate_namespace_cache()` and `clear_cache()` provide explicit cache invalidation called from every label-mutating operation
- Full Namespace CRUD (`list/get/create/update/delete_namespace`) and LocalizedLabel CRUD (`list/get/create_label`, `update_label`, `update_label_value`, `delete_label`, `delete_label_override`)
- Optimistic concurrency: `update_label()` and `update_label_value()` raise `HTTPException(409, ...)` with the exact PI-02 Spanish message on version mismatch, and increment `version` on success
- `report_missing_label()` dedups via SELECT-then-UPDATE/INSERT on `(tenant_id, namespace, label_key, locale)`, incrementing `hits` and `last_reported_at` on repeat reports
- `create_label()` auto-clears matching `MissingLabelReport` rows (RF-06: "alerts clean up automatically when the key is added")
- 11 async unit tests across `test_labels_resolve.py` (5 tests: TC-01..TC-03, cache hit, cache invalidation) and `test_labels_service.py` (6 tests: namespace CRUD, create_label per-locale rows + cache invalidation, update_label_value 409 + success path, missing-label dedup/hit-counting, create_label auto-clearing missing reports, delete_label)

## Task Commits

1. **Task 1: resolve_labels() inheritance resolver + in-memory cache (TC-01..TC-03)** - `738f966` (feat)
2. **Task 2: Namespace/Label CRUD + missing-label report upsert** - `7aeed0b` (feat)

**Plan metadata:** (pending — see final commit below)

_Note: `service.py` was written as a single file containing both tasks' code in the prior session (per the plan's full prescriptive code listing); Task 1's commit includes the entire `service.py` (resolver+cache+CRUD+missing-report sections) plus `test_labels_resolve.py`. Task 2's commit adds `test_labels_service.py` only, with a note in the commit message clarifying that the CRUD/missing-report implementation was already captured in Task 1's commit._

## Files Created/Modified
- `backend/app/domains/labels/service.py` - Full service layer: `_label_cache`/`_cache_key`/`_fetch_labels`/`resolve_labels`/`invalidate_namespace_cache`/`clear_cache` (resolver+cache), plus Namespace CRUD, LocalizedLabel CRUD (`create_label`, `update_label`, `update_label_value`, `delete_label`, `delete_label_override`), and missing-label report functions (`report_missing_label`, `list_missing_label_reports`)
- `backend/tests/test_labels_resolve.py` - 5 async tests: TC-01 (tenant-only), TC-02 (company override), TC-03 (product override), cache-hit-returns-stale-data, cache invalidation
- `backend/tests/test_labels_service.py` - 6 async tests: namespace CRUD, create_label per-locale rows + cache invalidation, update_label_value 409 on version mismatch + success path (version increment + cache invalidation), report_missing_label dedup/hit-counting, create_label auto-clearing matching MissingLabelReport, delete_label removing row + invalidating cache

## Decisions Made
- Verified `service.py` and `test_labels_resolve.py` (written in a prior session) against the plan's must_haves/behavior specs line-by-line — both matched the plan's prescriptive code listing exactly, no fixes needed.
- Wrote `test_labels_service.py` following the same async SQLite AsyncSession + autouse `clear_cache()` fixture pattern established by `test_labels_resolve.py`, rather than the no-DB `MockFlag` style used in `test_feature_flags_domain.py` — the labels service is DB-dependent (CRUD + cache interplay), so an in-memory SQLite session is the more faithful test harness.
- Added an extra `delete_label()` test (beyond the plan's literal Test 5 wording, which described delete-as-auto-cleanup-trigger) to directly exercise `delete_label()`'s cache invalidation and not-found path — Test 5's auto-cleanup behavior is covered via `create_label()` clearing a pending `MissingLabelReport`, matching the PRD RF-06 footer note literally ("alerts clean up automatically when the key is added").
- Split commits by test file (Task 1 = service.py + test_labels_resolve.py; Task 2 = test_labels_service.py only) since both tasks' service code physically landed in one file during the prior session — this preserves one commit per plan task while avoiding re-committing identical service.py content twice.

## Deviations from Plan

None - plan executed exactly as written. The pre-existing `service.py` and `test_labels_resolve.py` (written in a prior, uncommitted session) matched the plan's full code listing for both tasks without modification. `test_labels_service.py` was newly written per the plan's Task 2 behavior spec.

## Issues Encountered
- `sqlalchemy` is not installed in any accessible Python environment on this machine (confirmed via `python -c "import sqlalchemy"` → `ModuleNotFoundError`; no venv exists), so the plan's specified verification commands (`python -m pytest tests/test_labels_resolve.py -x -q`, `python -m pytest tests/test_labels_service.py -x -q`) could not be executed as written. This is the same limitation documented in Plan 20-01.
- **Mitigation:** Verified `backend/app/domains/labels/service.py`, `backend/tests/test_labels_resolve.py`, and `backend/tests/test_labels_service.py` all compile cleanly via `python -m py_compile` (syntax-level check only). Full `pytest` execution against an environment with `backend/requirements.txt` installed is required to confirm all 11 tests actually pass — flagged below.
- `requirements mark-complete LBL-03 LBL-04 LBL-13` returned `not_found` for all three IDs — same gap as Plan 20-01 (LBL-01/LBL-02/LBL-16). These requirement IDs are referenced in `20-02-PLAN.md` frontmatter but not present in `.planning/REQUIREMENTS.md`'s traceability table. Logged to `deferred-items.md`.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness
- `backend/app/domains/labels/service.py` exposes the full CRUD + resolution + cache + missing-report API surface needed by Plan 20-03 (admin CRUD router), Plan 20-04 (SDK bootstrap/prefetch router), and Plan 20-05 (missing-label ingestion router).
- All callers in 20-03/20-04/20-05 can wrap CRUD calls with `write_audit_log()` using the `audit/schemas.py` ActionType constants added in 20-01.
- **Before Plan 20-03 begins (or at the earliest convenient point):** run `pip install -r backend/requirements.txt` (in a dedicated venv) and execute `python -m pytest backend/tests/test_labels_resolve.py backend/tests/test_labels_service.py -q` plus the full suite (`python -m pytest`) to confirm all 11 new tests pass and no regressions were introduced — this could not be verified in the current environment (no sqlalchemy installed).
- Add LBL-01, LBL-02, LBL-03, LBL-04, LBL-13, LBL-16 (and any other LBL-* IDs referenced across Phase 20 plans) to `.planning/REQUIREMENTS.md`'s traceability table so future `requirements mark-complete` calls succeed.

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created files found on disk (service.py, test_labels_resolve.py, test_labels_service.py, 20-02-SUMMARY.md); both task commits (738f966, 7aeed0b) found in git log.
