---
phase: 15-and-rule-combination-semantics
plan: 02
subsystem: sdk
tags: [feature-flags, evaluator, sdk-js, sdk-python, vitest, pytest, and-mode]

# Dependency graph
requires:
  - phase: 15-and-rule-combination-semantics
    provides: "rule_combination_mode bootstrap entry field (Plan 15-01, backend evaluate_flag AND branch)"
provides:
  - "sdk-js evaluateFlag AND combination mode (FlagEntry.rule_combination_mode)"
  - "sdk-python evaluate_flag AND combination mode (entry['rule_combination_mode'])"
affects: [15-03-useRuleSimulator, 15-04-mui-feature-flags]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "mode = entry.rule_combination_mode ?? 'first_match' / entry.get('rule_combination_mode') or 'first_match' resolution, checked after the company-scope guard and before the first-match loop in both SDK local evaluators"

key-files:
  created: []
  modified:
    - sdk/sdk-js/src/evaluator.ts
    - sdk/sdk-js/src/types.ts
    - sdk/sdk-js/tests/evaluator.test.ts
    - sdk/sdk-python/src/backoffice_sdk/evaluator.py
    - sdk/sdk-python/tests/test_evaluator.py

key-decisions:
  - "Both SDK evaluators branch on rule_combination_mode immediately after the company-scope guard and before the existing rules loop, mirroring the backend (Plan 15-01) placement exactly"
  - "AND mode with non-empty rules is strict-false: any rule failure returns false immediately without consulting segments or default_val, per the locked interfaces spec"
  - "AND mode with empty rules falls through unchanged to the legacy segment/default_val path (vacuous AND, zero regression for no-rules entries)"

patterns-established:
  - "FlagEntry.rule_combination_mode?: string | null (sdk-js) / entry.get('rule_combination_mode') (sdk-python) — optional/missing-key safe so legacy cached bootstrap payloads continue to type-check and evaluate identically"

requirements-completed: [AND-01]

# Metrics
duration: 12min
completed: 2026-06-12
---

# Phase 15 Plan 02: SDK Local Evaluator AND Combination Mode Summary

**Ported the backend's AND rule-combination semantics to both sdk-js (`evaluateFlag`) and sdk-python (`evaluate_flag`) local evaluators — identical strict-false "all rules must match" behavior, with legacy first-match payloads unaffected.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-12T06:58:00Z (approx)
- **Completed:** 2026-06-12T12:03:38Z
- **Tasks:** 2 completed
- **Files modified:** 5

## Accomplishments
- sdk-js `FlagEntry` gained optional `rule_combination_mode?: string | null`, and `evaluateFlag` now branches into an AND path (`entry.rules.every(...)`) before the legacy first-match loop
- sdk-python `evaluate_flag` gained the identical branch (`all(evaluate_rule(rule, user) for rule in rules)`) at the same position relative to the company-scope guard
- 8 new AND-mode test cases added to each SDK's evaluator test suite, covering all-match, partial-fail (strict-false with segments/default_val present), per-rule `result` being inert, vacuous-AND fall-through (empty rules), legacy/`first_match` parity, and fail-closed missing-attribute behavior
- Full pre-existing evaluator suites remain green and unmodified (sdk-js: 48/48 passing including 8 new; sdk-python: 79/79 passing including 8 new)
- TypeScript typecheck clean (`tsc --noEmit`)

## Task Commits

Each task was committed atomically (TDD RED -> GREEN):

1. **Task 1: sdk-js AND mode (types + evaluator + tests)**
   - `7c8c512` test(15-02): add failing tests for AND combination mode in sdk-js evaluator
   - `493e9c1` feat(15-02): add AND combination mode to sdk-js evaluator
2. **Task 2: sdk-python AND mode (evaluator + tests)**
   - `789acc0` test(15-02): add failing tests for AND combination mode in sdk-python evaluator
   - `36c72e0` feat(15-02): add AND combination mode to sdk-python evaluator

_Note: TDD tasks produced 2 commits each (test -> feat); no refactor commit needed._

## Files Created/Modified
- `sdk/sdk-js/src/types.ts` - Added `rule_combination_mode?: string | null` to `FlagEntry`
- `sdk/sdk-js/src/evaluator.ts` - Added AND-mode branch in `evaluateFlag` (after company guard, before rules loop); updated doc comment to document both modes
- `sdk/sdk-js/tests/evaluator.test.ts` - New `describe('rule_combination_mode AND (AND-01)')` block with 8 cases
- `sdk/sdk-python/src/backoffice_sdk/evaluator.py` - Added identical AND-mode branch in `evaluate_flag`; updated docstring
- `sdk/sdk-python/tests/test_evaluator.py` - New `TestAndCombinationMode` class with 8 cases mirroring the sdk-js suite

## Decisions Made
- Mode resolution placement and strict-false/vacuous-AND semantics follow the locked `<interfaces>` spec from the plan verbatim (identical to backend Plan 15-01) — no deviations needed.
- Kept the diff minimal in sdk-python: introduced a local `rules = entry.get('rules', [])` variable reused by both the AND branch and the legacy loop, avoiding a duplicate `entry.get('rules', [])` call.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- AND-01 evaluator parity now complete for 3 of 4 evaluators (backend Plan 15-01, sdk-js, sdk-python). Plan 15-03 (useRuleSimulator) is the final evaluator to port for full 4-way parity.
- `rule_combination_mode` is now consumed correctly by both SDK clients when bootstrap entries (from Plan 15-01) include the field; legacy cached payloads without the key continue to evaluate byte-identically.
- No blockers for Plan 15-03 or 15-04.

---
*Phase: 15-and-rule-combination-semantics*
*Completed: 2026-06-12*

## Self-Check: PASSED

All claimed files and commits verified present.
