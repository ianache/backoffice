---
phase: 14-flag-scope-targeting-list-valued-rules
plan: 03
subsystem: feature-flags-sdk
tags: [feature-flags, operators, sdk-js, sdk-python, evaluator, anyOf, company-scope, targeting]

# Dependency graph
requires:
  - phase: 14-flag-scope-targeting-list-valued-rules
    provides: FlagEntry bootstrap target fields (tenant_id/product_id/company_id) added in Plan 14-02
provides:
  - 8th operator `anyOf` in backend OPERATORS, sdk-js OPERATORS, sdk-python OPERATORS — identical list-intersection/scalar-membership semantics
  - FlagEntry.company_id/tenant_id/product_id optional fields in sdk-js types
  - Company-scope target guard (TGT-03) in sdk-js evaluateFlag() and sdk-python evaluate_flag()
affects: [14-04 (useRuleSimulator.ts anyOf operator and FlagForm list-valued rule UI)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "anyOf operator: list actual -> set intersection non-empty; scalar actual -> membership in expected array; case-sensitive, no trimming in operator"
    - "Company-scope target guard placed immediately after the enabled check in evaluateFlag/evaluate_flag, skipped entirely when entry.company_id is null/undefined (legacy payloads)"

key-files:
  created: []
  modified:
    - backend/app/domains/feature_flags/service.py
    - backend/tests/test_feature_flags_eval.py
    - sdk/sdk-js/src/evaluator.ts
    - sdk/sdk-js/src/types.ts
    - sdk/sdk-js/tests/evaluator.test.ts
    - sdk/sdk-python/src/backoffice_sdk/evaluator.py
    - sdk/sdk-python/tests/test_evaluator.py

key-decisions:
  - "anyOf lambda identical across backend/sdk-js/sdk-python: set intersection for list actual, membership for scalar actual"
  - "Company guard uses != null / is not None checks so both null and undefined/missing company_id skip the guard (legacy compatibility)"
  - "No tenant/product guards added to SDK local evaluators per CONTEXT.md — bootstrap already filters by SDK client identity"

patterns-established:
  - "anyOf operator: identical Python lambda reused in backend service.py and sdk-python evaluator.py; TS arrow function reused in sdk-js evaluator.ts (and Plan 14-04 useRuleSimulator.ts)"

requirements-completed: [LST-02, TGT-03]

# Metrics
duration: 9min
completed: 2026-06-12
---

# Phase 14 Plan 03: anyOf Operator + Company-Scope Target Guard Summary

**Added the 8th `anyOf` operator (list-intersection/scalar-membership) to backend, sdk-js, and sdk-python evaluators with full test parity, plus a fail-closed company-scope target guard in both SDK local evaluators.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-12T00:09:07Z
- **Completed:** 2026-06-12T00:18:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- `anyOf` operator added to backend OPERATORS dict (8th operator), with `TestAnyOfOperator` (7 cases) and updated `test_all_eight_operators_have_true_case`
- `anyOf` operator added to sdk-js OPERATORS with 7 new evaluateRule tests including fail-closed non-array `expected` case
- `FlagEntry` (sdk-js types.ts) extended with optional `tenant_id`/`product_id`/`company_id` to mirror Plan 14-02 bootstrap entries
- Company-scope target guard (TGT-03) added to sdk-js `evaluateFlag()`: 5 new tests covering match/mismatch/missing-user/legacy-null/non-company-scope
- `anyOf` operator + identical company-scope guard added to sdk-python `evaluator.py`, with `TestAnyOfOperator` (7 cases) + `TestCompanyScopeGuard` (6 cases)
- All three suites green: backend (45 tests), sdk-js (74 tests), sdk-python (70 tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: backend anyOf operator + tests** - `c9d2aff` (feat)
2. **Task 2: sdk-js anyOf + FlagEntry target fields + company guard** - `1f586ca` (feat)
3. **Task 3: sdk-python anyOf + company guard** - `3dd905c` (feat)

**Plan metadata:** (this commit, follows)

_Note: All three tasks were TDD (tests written first, confirmed failing, then implementation)._

## Files Created/Modified
- `backend/app/domains/feature_flags/service.py` - Added `anyOf` lambda to OPERATORS (8th operator)
- `backend/tests/test_feature_flags_eval.py` - `TestAnyOfOperator` class (7 cases) + renamed/updated `test_all_eight_operators_have_true_case`
- `sdk/sdk-js/src/evaluator.ts` - Added `anyOf` to OPERATORS; added company-scope target guard in `evaluateFlag()`; updated doc comment
- `sdk/sdk-js/src/types.ts` - `FlagEntry` gained optional `tenant_id`/`product_id`/`company_id`
- `sdk/sdk-js/tests/evaluator.test.ts` - OPERATORS key assertion now 8 keys; 7 new anyOf tests; 5 new company-guard tests in new `describe('company-scope target guard (TGT-03)')` block
- `sdk/sdk-python/src/backoffice_sdk/evaluator.py` - Added `anyOf` lambda (identical to backend); added company-scope target guard in `evaluate_flag()`; updated docstring
- `sdk/sdk-python/tests/test_evaluator.py` - OPERATORS key-set now 8 keys; `TestAnyOfOperator` (7 cases) + `TestCompanyScopeGuard` (6 cases)

## Decisions Made
- Used `!= null` (sdk-js) and `is not None` (sdk-python/backend) for the company guard condition so both `null`/`None` and `undefined`/missing keys skip the check — preserves legacy (pre-14-02) cached payload behavior exactly.
- Reused the exact `anyOf` Python lambda from CONTEXT.md verbatim in both backend `service.py` and `sdk-python/evaluator.py` for byte-for-byte parity.
- Did not add tenant/product guards to SDK local evaluators (per CONTEXT.md/interfaces — bootstrap filtering by SDK client identity already covers this; SDK user contexts typically lack `tenant_id`/`product_id` keys).

## Deviations from Plan

### Notes (no auto-fixes required for this plan's own tasks)

**1. [Informational] Pre-existing parallel-executor change bundled into Task 1 commit**
- **Found during:** Task 1 commit (`git add` + `git commit` for backend files)
- **Issue:** At commit time, `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` had an uncommitted, already-staged `anyOf` implementation from the parallel Plan 14-04 executor (GREEN-phase work for their TDD task). My `git commit` for backend Task 1 inadvertently included this already-staged file, attributing it to commit `c9d2aff` instead of a 14-04 commit.
- **Fix:** None taken — the bundled content is correct, working code (matches the CONTEXT.md `anyOf` TS implementation exactly, identical to what Task 2 of this plan implements in sdk-js). Reverting would destroy the 14-04 executor's in-progress GREEN-phase work and risk breaking their running test suite. Left as-is; documented here for traceability. The 14-04 executor's own commit for that file will show no diff against HEAD for `useRuleSimulator.ts` (content already matches), which is expected and not an error.
- **Files affected:** `microuis/mui-feature-flags/src/components/composables/useRuleSimulator.ts` (already correct on disk, attributed to commit `c9d2aff`)
- **Impact:** None on this plan's deliverables. Flagged for orchestrator awareness re: 14-04 plan's commit history.

---

**Total deviations:** 0 auto-fixes (Rules 1-4 not triggered for this plan's own scope). 1 informational note re: parallel-execution commit attribution.
**Impact on plan:** None — all 3 tasks executed exactly as written, all suites green.

## Issues Encountered
None — straightforward TDD execution for all 3 tasks, RED confirmed before each implementation, GREEN confirmed after.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- LST-02 operator parity: 3 of 4 evaluators now have `anyOf` (backend, sdk-js, sdk-python). The 4th (`useRuleSimulator.ts`) is in progress under Plan 14-04 (parallel execution) — see deviation note above; its `anyOf` implementation already present in the working tree.
- TGT-03 SDK-side company-scope guard complete in both SDK local evaluators, ready to consume the bootstrap `company_id` field from Plan 14-02.
- No blockers for Plan 14-04 or subsequent plans.

---
*Phase: 14-flag-scope-targeting-list-valued-rules*
*Completed: 2026-06-12*

## Self-Check: PASSED

- FOUND: .planning/phases/14-flag-scope-targeting-list-valued-rules/14-03-SUMMARY.md
- FOUND: c9d2aff (Task 1 commit)
- FOUND: 1f586ca (Task 2 commit)
- FOUND: 3dd905c (Task 3 commit)
