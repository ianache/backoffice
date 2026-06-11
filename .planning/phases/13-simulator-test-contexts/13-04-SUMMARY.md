---
phase: 13-simulator-test-contexts
plan: 04
subsystem: ui
tags: [vue, feature-flags, segments, rule-simulator, test-context]

# Dependency graph
requires:
  - phase: 13-simulator-test-contexts
    provides: "Plan 13-01 backend test_context fields on Flag/Segment + PATCH support; Plan 13-03 RuleSimulator.vue with mode/testContext props and save-test-context emit"
provides:
  - "RuleBuilderView.vue passes flag.test_context to RuleSimulator and persists @save-test-context via store.updateFlag (independent of Save Changes)"
  - "SegmentForm.vue mounts RuleSimulator mode=segment for rule_based segments only, with shared buildPayload() helper for save and save-test-context"
  - "SegmentsView.vue handles @save-test-context via updateSegment(), syncs editingSegment with response, keeps form open"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "buildPayload() helper shared between handleSubmit and handleSaveTestContext to avoid duplicating SegmentPayload construction"
    - "save-test-context as a separate emit/PATCH path independent from the main Save action, to avoid wiping unrelated form state"

key-files:
  created: []
  modified:
    - microuis/mui-feature-flags/src/views/RuleBuilderView.vue
    - microuis/mui-feature-flags/src/components/flags/SegmentForm.vue
    - microuis/mui-feature-flags/src/views/SegmentsView.vue

key-decisions:
  - "RuleBuilderView's handleSaveTestContext omits an isSavingTestContext loading flag (RuleSimulator has no loading-state prop) — kept simple per plan's optional-polish note"
  - "SegmentsView.handleSaveTestContext reassigns editingSegment to the updateSegment() response so SegmentForm's :segment prop reflects the persisted test_context without remounting"

patterns-established:
  - "Segment full-replacement PATCH always goes through buildPayload() to guarantee name/conditions/members/type are included alongside test_context"

requirements-completed: [SIM-01, SIM-02, SIM-04]

# Metrics
duration: 8min
completed: 2026-06-11
---

# Phase 13 Plan 04: Wire RuleSimulator test_context into Rule Builder and Segments Summary

**Connected the persistent Live Simulator (Plan 13-03) to real flag and segment data via PATCH /flags/{id} and PATCH /flags/segments/{id}, with full-payload safety for segment saves.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-11T18:53:00Z
- **Completed:** 2026-06-11T19:01:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Rule Builder's Live Simulator now shows the flag's saved `test_context` (or placeholder) and persists edits via a dedicated "Save Test Context" path, separate from the main Save Changes button
- Rule-based segment editor now mounts the Live Simulator (manual segments do not), pre-populated with `segment.test_context`
- Segment "Save Test Context" sends the full current segment payload (name/description/type/members/conditions + test_context) to avoid the full-replacement PATCH wiping fields

## Task Commits

Each task was committed atomically:

1. **Task 1: RuleBuilderView.vue — pass test_context, handle save-test-context** - `6f7ea8d` (feat)
2. **Task 2: SegmentForm.vue — mount RuleSimulator for rule_based segments, emit save-test-context** - `4388d1d` (feat)
3. **Task 3: SegmentsView.vue — handle save-test-context from SegmentForm** - `f4b3fce` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `microuis/mui-feature-flags/src/views/RuleBuilderView.vue` - imports shell/toastStore, mounts RuleSimulator with mode="flag" and :test-context="flag?.test_context", adds handleSaveTestContext() PATCHing test_context via store.updateFlag with toast feedback
- `microuis/mui-feature-flags/src/components/flags/SegmentForm.vue` - imports RuleSimulator, adds 'save-test-context' emit, extracts buildPayload() helper used by both handleSubmit and new handleSaveTestContext, mounts RuleSimulator mode="segment" inside the existing rule_based template block
- `microuis/mui-feature-flags/src/views/SegmentsView.vue` - adds handleSaveTestContext() that PATCHes via updateSegment(), reassigns editingSegment to the response, refreshes segments list, shows toast, and wires @save-test-context on SegmentForm

## Decisions Made
- Omitted an `isSavingTestContext` loading ref in RuleBuilderView since RuleSimulator (Plan 13-03) exposes no loading-state prop — kept the save handler minimal per the plan's "include only if trivial" guidance
- In SegmentsView, `editingSegment.value` is reassigned to the `updateSegment()` response (not just refreshed via `loadSegments()`) so the `:segment` prop passed to SegmentForm immediately reflects the persisted `test_context` without remounting the form

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three SIM-01/SIM-02/SIM-04 UI wiring tasks complete; `vue-tsc --noEmit` and `vitest run` pass with no regressions
- Manual end-to-end verification (save/reload persistence, real-context toggle, manual-segment no-simulator check, segment field-preservation regression) requires a running dev stack and is documented in the plan's `<verification>` section for follow-up manual QA
- This was the final plan (4/4) of Phase 13 (Simulator Test Contexts) and the final phase of milestone v1.1 MVP2

---
*Phase: 13-simulator-test-contexts*
*Completed: 2026-06-11*

## Self-Check: PASSED

- FOUND: .planning/phases/13-simulator-test-contexts/13-04-SUMMARY.md
- FOUND: 6f7ea8d (Task 1 commit)
- FOUND: 4388d1d (Task 2 commit)
- FOUND: f4b3fce (Task 3 commit)
