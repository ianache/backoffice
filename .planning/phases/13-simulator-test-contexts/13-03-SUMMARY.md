---
phase: 13-simulator-test-contexts
plan: 03
subsystem: ui
tags: [vue, vitest, feature-flags, rule-simulator, module-federation]

# Dependency graph
requires:
  - phase: 13-simulator-test-contexts
    provides: "shell/useUserContext composable + Module Federation wiring (Plan 13-02), test_context column on flags/segments (Plan 13-01)"
provides:
  - "RuleSimulator.vue extended with testContext/mode props, save-test-context emit, and a real-context toggle"
  - "flags.ts service types (FeatureFlag, FlagPayload, Segment, SegmentPayload) extended with test_context"
affects: ["13-04 (RuleBuilderView + SegmentForm wiring of save-test-context and testContext prop)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RuleSimulator stays prop/emit-driven and mode-agnostic — parent components own persistence (save-test-context emit) and initial testContext value"
    - "Real-context toggle swaps contextJson.value directly, relying on existing useRuleSimulator watchEffect for re-evaluation — no new evaluation logic"

key-files:
  created: []
  modified:
    - microuis/mui-feature-flags/src/services/flags.ts
    - microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue
    - microuis/mui-feature-flags/src/composables/useRuleSimulator.test.ts

key-decisions:
  - "Real-context mapping uses useUserContext()'s exact key names (sub, email, roles, tenant_id, product_id) with no renaming — matches Phase 12 dogfooding rule attribute names (e.g. tenant_id)"
  - "contextJson initialization uses props.testContext || PLACEHOLDER_CONTEXT (truthy check) so empty-string saved contexts also fall back to the synthetic placeholder"

patterns-established:
  - "Save Test Context button is purely an emit — no internal saved/error UI state; parent (Plan 13-04) owns toast/error feedback"

requirements-completed: [SIM-02, SIM-03]

# Metrics
duration: 8min
completed: 2026-06-11
---

# Phase 13 Plan 03: RuleSimulator Live Test Context + Real-Context Toggle Summary

**RuleSimulator.vue extended with persistent testContext/mode props, a JSON-validity-gated "Save Test Context" emit, and a "Use my real context" toggle backed by shell/useUserContext that live re-evaluates PASSING/FAILING via the existing watchEffect**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-11T18:39:00Z
- **Completed:** 2026-06-11T18:47:38Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- `flags.ts` types (`FeatureFlag`, `FlagPayload`, `Segment`, `SegmentPayload`) now carry `test_context` for round-tripping the saved simulator context to/from the backend
- `RuleSimulator.vue` accepts `testContext`/`mode` props, initializes `contextJson` from a saved context (falling back to the existing synthetic placeholder), and exposes a "Save Test Context" button gated on JSON validity that emits `save-test-context`
- "Use my real context" checkbox toggle (default OFF, never persisted) swaps `contextJson` for the logged-in user's real attributes via `shell/useUserContext`, makes the textarea read-only, and restores any unsaved edits on toggle-off — PASSING/FAILING + Matched Rule recompute live with zero new evaluation logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend flags.ts service types with test_context** - `44c8566` (feat)
2. **Task 2: RuleSimulator.vue — props, save-test-context emit, JSON-valid save button** - `c0f837e` (feat)
3. **Task 3: Real-context toggle — useUserContext integration + live re-evaluation** - `9c6ae3a` (feat)

_TDD note: Tasks 2 and 3 were implemented directly with verification via vitest/vue-tsc rather than separate RED/GREEN commits, since the underlying evaluation logic (`evaluateRule`/`useRuleSimulator`) was explicitly marked "do not modify" — only new documentation/regression tests were added in Task 3 alongside the component change, all passing on first run._

## Files Created/Modified
- `microuis/mui-feature-flags/src/services/flags.ts` - Added `test_context: string | null` (response) / `test_context?: string` (payload) to FeatureFlag, FlagPayload, Segment, SegmentPayload
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` - Added `mode`/`testContext` props, `save-test-context` emit, "Save Test Context" button, "Use my real context" toggle with readonly textarea and contextJson swap/restore logic
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.test.ts` - Added "real user context shape (Phase 13)" describe block with 2 new tests (8 total, all passing)

## Decisions Made
- Real-context key mapping is a direct 1:1 of `useUserContext()`'s shape (`sub`, `email`, `roles`, `tenant_id`, `product_id`) — no renaming to `id`/`role`, matching existing rule attribute names from Phase 12 dogfooding
- `contextJson` falls back to the placeholder via `||` (not `??`) so an empty-string saved `test_context` also falls back, per plan guidance

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `RuleSimulator.vue` is ready to be mounted with `:test-context` and `mode="segment"` from `SegmentForm.vue`, and `:test-context`/`@save-test-context` from `RuleBuilderView.vue`, in Plan 13-04
- `flags.ts` `update()`/`updateSegment()` already accept `Partial<FlagPayload>`/`Partial<SegmentPayload>`, so `{ test_context: '...' }` payloads work without further service changes
- All vitest tests pass (8/8); `vue-tsc --noEmit` compiles cleanly

---
*Phase: 13-simulator-test-contexts*
*Completed: 2026-06-11*

## Self-Check: PASSED

All created/modified files and task commits verified present.
