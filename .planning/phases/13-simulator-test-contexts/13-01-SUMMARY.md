---
phase: 13-simulator-test-contexts
plan: 01
subsystem: database
tags: [alembic, sqlalchemy, pydantic, fastapi, mysql, feature-flags, segments]

# Dependency graph
requires:
  - phase: 07-products-domain
    provides: d001 Alembic migration pattern (additive nullable column)
provides:
  - test_context TEXT column on feature_flags and segments tables (d002 migration, applied to dev DB)
  - FlagUpdate/FlagResponse/SegmentCreate/SegmentResponse.test_context: Optional[str] = None
  - update_segment() persists test_context; update_flag() passes it through generic setattr loop
affects: [13-02, 13-03, 13-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Raw JSON object string passthrough field (test_context) - NOT parsed/validated like rules/tags arrays, stored and returned as-is"

key-files:
  created:
    - backend/alembic/versions/d002_add_test_context.py
  modified:
    - backend/app/domains/feature_flags/models.py
    - backend/app/domains/feature_flags/schemas.py
    - backend/app/domains/feature_flags/service.py
    - backend/tests/test_feature_flags_domain.py

key-decisions:
  - "test_context stored as sa.Text() (not sa.JSON()) - MySQL 5.6 has no native JSON type, matches rules/tags/conditions/members precedent"
  - "Single additive migration (no 3-step expand/backfill/cleanup) - purely additive nullable column, no data backfill needed"
  - "test_context excluded from parse_text_fields()/parse_json_fields() model_validators - it's a JSON object string passed through verbatim, not a JSON array needing deserialization"
  - "update_flag() required no code change - test_context flows through existing exclude_unset+setattr generic loop automatically"

patterns-established:
  - "Pattern: passthrough TEXT field (test_context) coexists with parsed-array TEXT fields (rules/tags/conditions/members) in the same response schema by being excluded from the model_validator loop"

requirements-completed: [SIM-01]

# Metrics
duration: 12min
completed: 2026-06-11
---

# Phase 13 Plan 01: Persist Live Simulator test_context on flags and segments Summary

**Added a nullable `test_context` TEXT column (raw JSON object string) to `feature_flags` and `segments` via Alembic migration d002, threaded through ORM models, Pydantic schemas, and the segment update service so the Live Simulator's "Save Test Context" feature has a backend to persist to.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-11T18:28:00Z
- **Completed:** 2026-06-11T18:40:00Z
- **Tasks:** 3 completed
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments
- d002 Alembic migration applied to dev DB (head now at d002), adding nullable `test_context TEXT` to both `feature_flags` and `segments`
- `FeatureFlag.test_context` and `Segment.test_context` ORM columns added (Mapped[Optional[str]], Text)
- `FlagUpdate`, `FlagResponse`, `SegmentCreate`, `SegmentResponse` all expose `test_context: Optional[str] = None`, passed through verbatim (not JSON-parsed)
- `update_segment()` persists `test_context` via explicit assignment; `update_flag()` requires no change (generic setattr loop handles it)
- 4 new domain tests added, all 38 tests in `test_feature_flags_domain.py` pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic migration d002 — add test_context to feature_flags and segments** - `c74ea35` (feat)
2. **Task 2: ORM models + Pydantic schemas — add test_context field** - `8f8f326` (feat)
3. **Task 3: Service layer — persist test_context on update_segment** - `7eb956a` (feat)

**Plan metadata:** (this commit)

_Note: tdd="true" tasks were implemented directly with tests added alongside the implementation in a single commit per task, matching this plan's existing test-file structure (no separate RED/GREEN commits requested by plan)._

## Files Created/Modified
- `backend/alembic/versions/d002_add_test_context.py` - New migration: adds nullable `test_context TEXT` to `feature_flags` and `segments`; downgrade drops both (segments first)
- `backend/app/domains/feature_flags/models.py` - `FeatureFlag.test_context` and `Segment.test_context` Mapped[Optional[str]] Text columns added
- `backend/app/domains/feature_flags/schemas.py` - `test_context: Optional[str] = None` added to `FlagUpdate`, `FlagResponse`, `SegmentCreate`, `SegmentResponse`; excluded from `parse_text_fields`/`parse_json_fields` validators
- `backend/app/domains/feature_flags/service.py` - `update_segment()` gains `segment.test_context = payload.test_context`; `update_flag()` unchanged
- `backend/tests/test_feature_flags_domain.py` - 4 new tests: `test_flag_response_schema_includes_test_context`, `test_flag_response_test_context_defaults_to_none`, `test_segment_create_schema_accepts_test_context`, `test_update_segment_test_context_assignment_logic`

## Decisions Made
- Used `sa.Text()` for the new column (not `sa.JSON()`) per MySQL 5.6 compatibility precedent established in decision [07-03]
- Single additive migration sufficient — no 3-step expand/backfill/cleanup required since the column is purely additive and nullable with no existing data to migrate
- `test_context` deliberately excluded from the existing `parse_text_fields()`/`parse_json_fields()` model_validator loops since those loops `json.loads()` JSON *arrays* (rules/tags/conditions/members) into typed lists, while `test_context` is a JSON *object* string meant to round-trip verbatim to the frontend Live Simulator

## Deviations from Plan

None - plan executed exactly as written. Migration applied successfully against the dev DB (alembic head now `d002`).

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required. Migration was applied automatically to the dev DB during execution (`alembic upgrade head` succeeded, d001 -> d002).

## Next Phase Readiness
- Backend persistence for `test_context` is complete and verified (38/38 tests pass)
- `FlagResponse`/`SegmentResponse` now return `test_context` (null for existing rows, no data loss)
- Ready for Plan 02+ (frontend Live Simulator wiring to read/write `test_context` via the Flag/Segment update endpoints)

---
*Phase: 13-simulator-test-contexts*
*Completed: 2026-06-11*

## Self-Check: PASSED

- FOUND: backend/alembic/versions/d002_add_test_context.py
- FOUND: .planning/phases/13-simulator-test-contexts/13-01-SUMMARY.md
- FOUND: c74ea35 (Task 1 commit)
- FOUND: 8f8f326 (Task 2 commit)
- FOUND: 7eb956a (Task 3 commit)
