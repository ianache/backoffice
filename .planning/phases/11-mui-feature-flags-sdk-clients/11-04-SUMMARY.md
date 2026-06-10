---
phase: 11-mui-feature-flags-sdk-clients
plan: 04
subsystem: ui
tags: [vue, vitest, tailwind, drag-and-drop, vuedraggable, feature-flags, rule-builder]

# Dependency graph
requires:
  - phase: 11-mui-feature-flags-sdk-clients
    provides: "Plan 01 backend OPERATORS table with greaterThan/lessThan (float() coercion); Plan 02 buildable mui-feature-flags remote scaffold; Plan 03 services/flags.ts (RuleSchema), stores/flags.ts (useFeatureFlagsStore), ChipTagInput.vue"
provides:
  - "useRuleSimulator.ts composable with 7-entry OPERATORS table (equals, in, notIn, contains, regex, greaterThan, lessThan) and exported evaluateRule for unit testing"
  - "RuleCard.vue with mode?: 'flag'|'segment' prop — 'segment' mode hides Result column, ready for Plan 05 segment rule editor reuse"
  - "RuleSimulator.vue live JSON-context evaluator with Passing/Failing/No match pill badges"
  - "RuleBuilderView.vue Stitch two-column rule builder (canvas + simulator) with drag-and-drop reordering"
affects: [11-05-segments, 11-06-sdk-js, 11-07-sdk-js]

# Tech tracking
tech-stack:
  added: ["vitest@^1.6.0 (devDependency, mirrors portal's version, zero-config test runner)"]
  patterns:
    - "useRuleSimulator OPERATORS table is the canonical TS reference for greaterThan/lessThan — Number() coercion mirrors backend service.py float() coercion, both fail-closed via existing try/catch on NaN comparisons"
    - "RuleCard mode prop ('flag'|'segment', default 'flag') controls 4-col vs 3-col grid and Result column visibility — shared component pattern for Plan 05 SEG-03"
    - "Stitch rule-block accent: border-l-4 border-l-primary-container on bg-surface-container-lowest cards"

key-files:
  created:
    - microuis/mui-feature-flags/src/composables/useRuleSimulator.ts
    - microuis/mui-feature-flags/src/composables/useRuleSimulator.test.ts
    - microuis/mui-feature-flags/src/components/flags/RuleCard.vue
    - microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue
  modified:
    - microuis/mui-feature-flags/src/views/RuleBuilderView.vue
    - microuis/mui-feature-flags/package.json
    - pnpm-lock.yaml

key-decisions:
  - "evaluateRule() exported from useRuleSimulator.ts (was previously a private function in v1.0) to enable direct vitest unit testing without mounting Vue reactivity"
  - "vitest@^1.6.0 added as devDependency matching portal's pinned version, with 'test': 'vitest run' script — zero extra config file needed (vite.config.ts test defaults sufficient)"
  - "RuleSimulator.vue badge restyled from v1.0's tertiary-container pill to Stitch's bg-green-100/text-green-700 uppercase label style"

patterns-established:
  - "Operator-table parity pattern: any future operator added to backend service.py OPERATORS must be mirrored in useRuleSimulator.ts OPERATORS with equivalent coercion + fail-closed semantics, verified via paired vitest fixtures"

requirements-completed: [MUI-06, SDK-06]

# Metrics
duration: ~10min
completed: 2026-06-10
---

# Phase 11 Plan 04: Rule Builder + Live Simulator (greaterThan/lessThan, mode prop) Summary

**Ported and restyled the rule builder (`RuleBuilderView.vue`, `RuleCard.vue`, `RuleSimulator.vue`, `useRuleSimulator.ts`) to `mui-feature-flags` with a 7-operator evaluator (adding `greaterThan`/`lessThan` via `Number()` coercion matching the backend's `float()` coercion), a `mode: 'flag'|'segment'` prop on `RuleCard`, and a Stitch two-column canvas+simulator layout with drag-and-drop reordering.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-10T01:43:00Z
- **Completed:** 2026-06-10T01:53:00Z
- **Tasks:** 2
- **Files modified:** 7 (4 created, 3 modified)

## Accomplishments
- `useRuleSimulator.ts` OPERATORS table extended to 7 entries (equals, in, notIn, contains, regex, greaterThan, lessThan); `evaluateRule` exported and unit-tested with 6 fixtures mirroring Plan 01's backend test cases — all pass
- `RuleCard.vue` operator dropdown extended to 7 options; new `mode?: 'flag'|'segment'` prop (default `'flag'`) toggles 4-col/3-col grid and hides the Result toggle in `'segment'` mode for Plan 05 reuse
- `RuleCard.vue` restyled with Stitch's `border-l-4 border-l-primary-container` accent on the rule-block container, drag-handle preserved
- `RuleSimulator.vue` ported with live JSON-context evaluation; "Passing"/"Failing"/"No match" badges restyled to Stitch's `bg-green-100 text-green-700` uppercase label style
- `RuleBuilderView.vue` rebuilt as a Stitch two-column layout (`col-span-8` canvas + `col-span-4` simulator) with dotted-grid canvas background, environment tab indicators (Production/Staging/Development with colored status dots), AND-connector pills, rollout slider, and `vuedraggable` drag-and-drop reordering
- `vitest@^1.6.0` added to `mui-feature-flags`; `pnpm run test` and `pnpm run build` both pass

## Task Commits

1. **Task 1: Port useRuleSimulator.ts and RuleCard.vue with greaterThan/lessThan operators + mode prop** - `f7f7090` (feat)
2. **Task 2: Port RuleSimulator.vue and restyle RuleBuilderView.vue to Stitch two-column layout** - `18fff52` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` - OPERATORS table with 7 entries (added greaterThan/lessThan via Number() coercion), evaluateRule exported
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.test.ts` - 6 vitest cases covering greaterThan/lessThan including numeric-string coercion and fail-closed NaN behavior
- `microuis/mui-feature-flags/src/components/flags/RuleCard.vue` - 7-operator dropdown, `mode?: 'flag'|'segment'` prop, Stitch border-l-4 accent
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` - Live simulator panel with Stitch-styled Passing/Failing badge
- `microuis/mui-feature-flags/src/views/RuleBuilderView.vue` - Stitch two-column rule builder (canvas + simulator), drag-and-drop, environment tabs, save/cancel via shell/StitchButton
- `microuis/mui-feature-flags/package.json` - Added `vitest` devDependency and `test` script
- `pnpm-lock.yaml` - Updated for vitest dependency

## Decisions Made
- Exported `evaluateRule` from `useRuleSimulator.ts` (private in v1.0) to allow direct unit testing without Vue component mounting
- Added `vitest@^1.6.0` matching portal's pinned version; no separate vitest config file needed — defaults sufficient for a single composable test
- `RuleSimulator.vue` result badge restyled to Stitch's `bg-green-100 text-green-700 uppercase` pill (replacing v1.0's `tertiary-container` pill) per `design/stitch/design-builder-feature-flags-rules.html`

## Deviations from Plan

None - plan executed exactly as written. `services/flags.ts`, `stores/flags.ts`, and `ChipTagInput.vue` (created concurrently by Plan 03 in the same wave) were available by the time `RuleCard.vue` and `RuleBuilderView.vue` were written, so all cross-file imports resolved cleanly on first build.

## Issues Encountered

Wave 2 concurrency: Plans 03 and 04 ran in parallel and both modified files under `microuis/mui-feature-flags/`. Verified via `git status --short` before each commit that only this plan's files (`RuleCard.vue`, `RuleSimulator.vue`, `RuleBuilderView.vue`, `composables/`, `package.json`, `pnpm-lock.yaml`) were staged — Plan 03's concurrently-created files (`ChipTagInput.vue`, `FlagForm.vue`, `FlagTable.vue`, `FlagsView.vue` changes) and unrelated `portal/*` changes from other in-flight work were left untouched.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `RuleCard.vue` with `mode="segment"` is ready for Plan 05 (segments) to reuse for SEG-03 rule-based segment editing
- `useRuleSimulator.ts` OPERATORS table is the canonical TS reference for Plans 06/07 (sdk-js) to mirror for client-side flag evaluation
- `/flags/:id/rules` route renders the full two-column rule builder; `pnpm --filter @backoffice/mui-feature-flags build` and `test` both succeed

---
*Phase: 11-mui-feature-flags-sdk-clients*
*Completed: 2026-06-10*

## Self-Check: PASSED

All 6 created/modified files verified present on disk. Both task commit hashes (f7f7090, 18fff52) verified present in git history.
