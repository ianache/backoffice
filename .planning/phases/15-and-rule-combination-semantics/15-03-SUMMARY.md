---
phase: 15-and-rule-combination-semantics
plan: 03
subsystem: ui
tags: [vue3, composable, mui-feature-flags, rule-simulator, and-mode, vitest]

# Dependency graph
requires:
  - phase: 15-and-rule-combination-semantics
    provides: "15-01 rule_combination_mode field on FlagResponse/FlagUpdate (backend canonical AND spec)"
provides:
  - "useRuleSimulator AND mode: ruleResults[] (per-rule pass/fail, both modes) + overallResult (AND truth table)"
  - "RuleSimulator.vue combinationMode prop with per-rule pass/fail list + overall Passing/Failing badge in AND mode"
  - "RuleBuilderView.vue Match selector (First matching rule / All rules AND) persisted via rule_combination_mode"
  - "services/flags.ts rule_combination_mode on FeatureFlag and FlagPayload"
affects: [15-04-mui-feature-flags-flags-view-filters]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useRuleSimulator 3rd param `mode: Readonly<Ref<string>>` defaults to ref('first_match') — preserves existing 2-arg call sites byte-for-byte"
    - "RuleSimulator.vue effectiveMode computed (props.combinationMode ?? 'first_match') feeds both the badge and the composable mode param"
    - "AND-mode per-rule list uses inline Tailwind (check_circle/cancel + text-green-700/text-error) — no new scoped styles, 14-04 precedent"

key-files:
  created: []
  modified:
    - microuis/mui-feature-flags/src/composables/useRuleSimulator.ts
    - microuis/mui-feature-flags/src/composables/useRuleSimulator.test.ts
    - microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue
    - microuis/mui-feature-flags/src/views/RuleBuilderView.vue
    - microuis/mui-feature-flags/src/services/flags.ts

key-decisions:
  - "overallResult computed inside the existing watchEffect after ruleResults — AND: ruleList.length ? ruleResults.every(Boolean) : null; first_match: mirrors matchedResult (including null on no-match)"
  - "matchedIndex/matchedResult remain first_match-only and are always null in AND mode, per locked interface contract"
  - "RuleSimulator badge unified to bind on overallResult in both modes since overallResult === matchedResult in first_match mode — avoids duplicating badge logic"
  - "Connector label between RuleCards reads 'ELSE IF' in first_match mode (was hardcoded 'AND') and 'AND' only in AND mode — prevents first_match chains from misreading as AND"

patterns-established:
  - "Simulator AND-mode body replaces 'Matched Rule' panel with 'Rules (ALL must match)' per-rule list, gated on effectiveMode !== 'and' vs else"

requirements-completed: [AND-01, AND-02]

# Metrics
duration: 9min
completed: 2026-06-12
---

# Phase 15 Plan 03: Rule Simulator AND Mode + Rule Builder Match Selector Summary

**useRuleSimulator gained a 3rd `mode` param exposing `ruleResults[]`/`overallResult` with AND truth-table semantics; RuleSimulator.vue renders per-rule pass/fail rows + overall badge in AND mode; RuleBuilderView.vue adds a "Match: First rule / All rules (AND)" selector persisted via PATCH `rule_combination_mode`.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-06-12T13:28:00Z
- **Completed:** 2026-06-12T13:34:30Z
- **Tasks:** 3 completed
- **Files modified:** 5

## Accomplishments
- `useRuleSimulator` now computes `ruleResults[]` (per-rule `evaluateRule` outcome) in both modes and `overallResult` per the locked AND spec (all rules must pass; empty rules => null; per-rule `result` ignored in AND mode)
- Live Simulator shows a "Rules (ALL must match)" list with check_circle/cancel icons and a "Not all rules match" hint in AND mode, while first_match keeps the original "Matched Rule" panel byte-identical
- Header badge (Passing/Failing/No match) now driven by `overallResult` in both modes
- Rule Builder has a "Match" selector (native `<select>`) below the Rollout bar; defaults to `first_match` for legacy flags, reflects `and` for AND flags, and round-trips through `saveChanges()` -> PATCH `rule_combination_mode`
- AND/ELSE IF connector label between rule cards now reflects the active mode
- `FeatureFlag.rule_combination_mode: string` and `FlagPayload.rule_combination_mode?: string` added to `services/flags.ts`

## Task Commits

Each task was committed atomically:

1. **Task 1: useRuleSimulator AND mode + ruleResults/overallResult** - `d49ef39` (test, RED), `7602aef` (feat, GREEN)
2. **Task 2: RuleSimulator.vue per-rule pass/fail + overall badge** - `0dab542` (feat)
3. **Task 3: RuleBuilderView mode selector + persistence + service types** - `81a07ed` (feat)

**Plan metadata:** (this commit) `docs(15-03): complete rule simulator AND mode + rule builder match selector plan`

## Files Created/Modified
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` - new 3rd `mode` param (default `ref('first_match')`), `ruleResults`/`overallResult` refs computed in the existing `watchEffect`; `evaluateRule`/`OPERATORS` untouched
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.test.ts` - new `describe('useRuleSimulator — AND combination mode')` (7 cases: and-all-match, and-one-fails, and-result-ignored, and-empty-rules, and-invalid-context, first_match-default, first_match-no-match)
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` - new `combinationMode` prop, `effectiveMode` computed, badge bound to `overallResult`, AND-mode per-rule list (check_circle/cancel), first_match "Matched Rule" panel preserved
- `microuis/mui-feature-flags/src/views/RuleBuilderView.vue` - `localMode` ref + onMounted init from `flag.rule_combination_mode`, Match selector bar, dynamic AND/ELSE IF connector, `rule_combination_mode` in `saveChanges()` payload, `:combination-mode="localMode"` on `RuleSimulator`
- `microuis/mui-feature-flags/src/services/flags.ts` - `rule_combination_mode: string` on `FeatureFlag`, `rule_combination_mode?: string` on `FlagPayload`

## Decisions Made
- `overallResult` computed inside the existing `watchEffect`, after `ruleResults`: AND mode = `ruleList.length ? ruleResults.every(Boolean) : null`; first_match mode mirrors `matchedResult` (already null on no-match), preserving existing badge/null-state behavior with zero special-casing
- `matchedIndex`/`matchedResult` stay `null` in AND mode per the locked interface — no repurposing for AND bookkeeping
- RuleSimulator badge unified on `overallResult` for both modes (no separate AND-only badge branch) since `overallResult === matchedResult` in first_match mode
- Connector label switched from hardcoded "AND" to `localMode === 'and' ? 'AND' : 'ELSE IF'` so first_match rule chains no longer visually imply AND semantics

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All 46 tests pass (39 pre-existing + 7 new), `pnpm build` green after each UI task.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- AND-01 4-evaluator parity complete (backend Plan 15-01, sdk-js/sdk-python Plan 15-02, useRuleSimulator this plan)
- AND-02 UI half complete: Rule Builder can opt a flag into AND mode and the Live Simulator correctly visualizes per-rule + overall AND results; legacy first_match UX unchanged
- Mode round-trip (UI -> PATCH -> FlagResponse -> UI) relies on backend Plan 15-01's `rule_combination_mode` normalization, already applied to dev DB via d004
- `microuis/mui-feature-flags/src/views/FlagsView.vue` (modified by 15-04) was not touched by this plan — no conflict with the committed filter-bar state

---
*Phase: 15-and-rule-combination-semantics*
*Completed: 2026-06-12*

## Self-Check: PASSED

All created files and task commits verified present.
