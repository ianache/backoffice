---
phase: 08-advanced-segments-sdk-backend
plan: "01"
subsystem: database
tags: [alembic, mysql, sqlalchemy, pydantic, feature-flags, segments, eval-events]

# Dependency graph
requires:
  - phase: 07-products-domain
    provides: b003 alembic head revision; FlagSegment join table for flag_count subquery
provides:
  - c001 migration: nullable type + conditions columns on segments table
  - c002 migration: eval_events table with tenant_id and flag_key indexes
  - Segment ORM extended with type and conditions mapped columns
  - EvalEvent ORM model mapped to eval_events table
  - SegmentCreate accepts type='rule_based' and conditions=[RuleSchema]
  - SegmentResponse.type coerces NULL -> 'manual'; flag_count field injected at query time
  - list_segments() returns (Segment, int) tuples via LEFT JOIN subquery (no N+1)
affects:
  - 08-02 (segments router must unpack tuples, build SegmentResponse with flag_count)
  - 08-03 (SDK evaluator uses conditions from Segment model)
  - 08-04 (eval_events table consumed by analytics/telemetry endpoints)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "NULL-coerce-to-default in model_validator: type=NULL treated as 'manual' at schema layer"
    - "LEFT JOIN subquery for count aggregation: avoids N+1 flag_count queries per segment"
    - "TDD: tests written before implementation; RED commit then GREEN commit"

key-files:
  created:
    - backend/alembic/versions/c001_expand_segments_type_conditions.py
    - backend/alembic/versions/c002_create_eval_events_table.py
  modified:
    - backend/app/domains/feature_flags/models.py
    - backend/app/domains/feature_flags/schemas.py
    - backend/app/domains/feature_flags/service.py
    - backend/tests/test_feature_flags_domain.py

key-decisions:
  - "No server_default on segments.type — NULL treated as 'manual' in service layer; avoids MySQL 5.6 table rewrite"
  - "list_segments() returns (Segment, int) tuples not ORM objects — router update deferred to Plan 02 with TODO comment"
  - "EvalEvent added to models.py now (Plan 03 bulk insert dependency) even though table used only in Plan 03+"
  - "create_segment() refactored from model_dump() pattern to explicit field assignment — allows type/conditions without extra dict manipulation"

patterns-established:
  - "NULL-to-default coercion: model_validator(mode='before') handles both dict and ORM object paths"
  - "Aggregate subquery pattern: LEFT JOIN count_subq for flag_count avoids N+1 queries"

requirements-completed: [SEG-01, SEG-02, SEG-04]

# Metrics
duration: 12min
completed: 2026-06-08
---

# Phase 8 Plan 01: Segments Data Layer Summary

**Alembic c001/c002 migrations applied (segments.type+conditions, eval_events table), Segment ORM/schema extended with type/conditions/flag_count, list_segments() returns (Segment, int) tuples via LEFT JOIN subquery**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-08T13:00:00Z
- **Completed:** 2026-06-08T13:12:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Two Alembic migrations created and applied: c001 adds type/conditions to segments; c002 creates eval_events with indexes
- Segment ORM extended with type + conditions mapped columns; EvalEvent ORM model added for Plan 03
- SegmentCreate accepts rule_based type with conditions; SegmentResponse coerces NULL type to 'manual' and provides flag_count
- list_segments() refactored to return (Segment, flag_count) tuples via LEFT JOIN subquery eliminating N+1
- 34 tests pass including 6 new tests covering round-trip validation and backward-compat NULL coercion

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic migrations c001 + c002** - `24d33da` (feat)
2. **Task 2 RED: Failing tests for type/conditions/EvalEvent** - `fcf125a` (test)
3. **Task 2 GREEN: Extend ORM, schemas, service** - `4a79d4f` (feat)

_Note: TDD task 2 has two commits (test RED then feat GREEN)_

## Files Created/Modified

- `backend/alembic/versions/c001_expand_segments_type_conditions.py` - Adds nullable type (VARCHAR 20) and conditions (TEXT) to segments table
- `backend/alembic/versions/c002_create_eval_events_table.py` - Creates eval_events table; indexes on tenant_id and flag_key
- `backend/app/domains/feature_flags/models.py` - Segment: +type, +conditions columns; new EvalEvent model
- `backend/app/domains/feature_flags/schemas.py` - SegmentCreate: +type, +conditions; SegmentResponse: +type, +conditions, +flag_count with NULL coercion validator
- `backend/app/domains/feature_flags/service.py` - list_segments() returns tuples; create_segment() persists type+conditions
- `backend/tests/test_feature_flags_domain.py` - 6 new tests for Phase 08-01 behavior

## Decisions Made

- No `server_default` on `segments.type` — service layer treats NULL as 'manual'; avoids MySQL 5.6 ADD COLUMN table rewrite pitfall documented in RESEARCH.md Pitfall 5
- `list_segments()` returns `(Segment, int)` tuples rather than bare ORM objects — router update with `flag_count` population deferred to Plan 02 where segment router is reworked; TODO comment added in service
- `EvalEvent` model added now even though it is only used in Plan 03+ bulk-insert path — required for importability by later plans without model changes mid-phase
- `create_segment()` refactored from `model_dump()` dict-explosion pattern to explicit field assignment — avoids passing `type`/`conditions` through Pydantic's list serialization unexpectedly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - migrations applied cleanly, all 34 tests pass on first GREEN run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `alembic current` shows c002 (head) — Plan 02 can proceed immediately
- `segments` table has `type` and `conditions` columns; `eval_events` table exists with correct indexes
- Plan 02 (segments router) must unpack `(segment, flag_count)` tuples from `list_segments()` — TODO comment in service.py marks the exact location
- Plan 03 (SDK evaluator) can import `EvalEvent` from models without further model changes

---
*Phase: 08-advanced-segments-sdk-backend*
*Completed: 2026-06-08*
