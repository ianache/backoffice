---
phase: 05-rule-builder
plan: "02"
subsystem: ui
tags: [vue3, typescript, tailwind, composable, drag-handle, feature-flags, rule-builder]

# Dependency graph
requires:
  - phase: 05-01
    provides: useRuleSimulator composable, ChipTagInput component, vuedraggable@next

provides:
  - RuleCard component — stateless logic block card (attribute/operator/value/result fields + drag handle)
  - RuleSimulator component — right-sidebar live evaluation panel consuming useRuleSimulator

affects:
  - 05-03 (RuleBuilderView imports RuleCard + RuleSimulator for the full interactive view)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Stateless card pattern: parent holds array, child emits update/delete — no internal mutable state
    - Operator family coercion: isArrayOperator guard converts scalar<->array on operator change
    - computed<RuleSchema[]>() + Readonly<Ref> cast pattern to satisfy composable signature without deep-readonly mismatch
    - group-hover Tailwind pattern for drag handle reveal on card hover

key-files:
  created:
    - portal/src/components/flags/RuleCard.vue
    - portal/src/components/flags/RuleSimulator.vue
  modified: []

key-decisions:
  - "RuleCard uses scoped form-label/form-input styles (not global) — matches project CSS token pattern from FlagForm.vue"
  - "RuleSimulator uses strippedRules computed<RuleSchema[]>() + Readonly<Ref> cast — avoids Vue readonly() deep-readonly mismatch with composable Readonly<Ref<RuleSchema[]>> signature"
  - "onOperatorChange coerces value: scalar->array for in/notIn, array->comma-string for scalar ops — preserves user data across operator switches"

patterns-established:
  - "Stateless card emit pattern: emit('update', { ...props.rule, field: newValue }) — parent is source of truth"
  - "Readonly<Ref> cast workaround: computed<T[]>() as unknown as Readonly<Ref<T[]>> — safe for composables that only read, never write"

requirements-completed: [RULE-01, RULE-02, RULE-03]

# Metrics
duration: ~3min
completed: 2026-06-08
---

# Phase 05 Plan 02: RuleCard + RuleSimulator Summary

**RuleCard stateless card with drag handle, 4 interactive fields, operator type coercion, and ChipTagInput integration; RuleSimulator live evaluation sidebar wired to useRuleSimulator composable — both TypeScript-clean**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-08T02:26:26Z
- **Completed:** 2026-06-08T02:28:48Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created RuleCard.vue — stateless logic block card emitting update/delete; 4-column grid (attribute/operator/value/result); drag-handle div for vuedraggable integration; ChipTagInput conditional on in/notIn operators; onOperatorChange() coerces value between scalar string and string[] when switching operator families; scoped form-label/form-input CSS using design tokens
- Created RuleSimulator.vue — right-sidebar panel owning contextJson ref; strippedRules computed removes _id before passing to useRuleSimulator; result badge (Passing/Failing/No match) in header; matched rule highlight panel; contextError inline display

## Task Commits

Each task was committed atomically:

1. **Task 1: Create RuleCard component** - `793b79a` (feat)
2. **Task 2: Create RuleSimulator sidebar component** - `d4f8229` (feat)

**Plan metadata:** (included in final docs commit)

## Files Created/Modified

- `portal/src/components/flags/RuleCard.vue` — stateless card; drag-handle; 4-field grid; ChipTagInput v-if isArrayOperator; onOperatorChange value coercion; scoped CSS tokens
- `portal/src/components/flags/RuleSimulator.vue` — contextJson textarea; useRuleSimulator wired via computed+cast; matchedIndex highlight; contextError display

## Decisions Made

- **Scoped form styles in RuleCard:** `.form-input`/`.form-label` are scoped to FlagForm.vue (not global), so RuleCard defines its own scoped equivalents using the same CSS variable tokens. This keeps the styling consistent without creating global pollution.
- **Readonly<Ref> cast for RuleSimulator:** `computed<RuleSchema[]>()` produces a `ComputedRef<RuleSchema[]>`. Wrapping with Vue's `readonly()` creates a deep-readonly type that TypeScript rejects as `Readonly<Ref<RuleSchema[]>>` (the composable signature). Solution: cast via `as unknown as Readonly<Ref<RuleSchema[]>>`. Safe because `useRuleSimulator` only reads `rules.value` — never writes it.
- **onOperatorChange coercion logic:** When switching TO in/notIn: wrap current value in array (or empty array). When switching AWAY: join array with ', '. This preserves user-entered data across operator family switches instead of resetting to empty.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Readonly<Ref> deep-readonly TypeScript mismatch in RuleSimulator**
- **Found during:** Task 2 build verification
- **Issue:** `readonly(strippedRules)` from Vue creates `Readonly<Ref<readonly RuleSchema[]>>` (deep-readonly array), which TypeScript rejects as `Readonly<Ref<RuleSchema[]>>` (mutable array). TS error: "readonly type cannot be assigned to mutable type"
- **Fix:** Removed `readonly()` import; used `strippedRules as unknown as Readonly<Ref<RuleSchema[]>>` cast. Safe because `useRuleSimulator` only reads `.value`, never mutates the array.
- **Files modified:** portal/src/components/flags/RuleSimulator.vue
- **Verification:** `pnpm build` EXIT_CODE: 0 after fix
- **Committed in:** d4f8229 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - TypeScript deep-readonly type mismatch)
**Impact on plan:** Minor fix, no scope creep. Plan's `readonly(strippedRules)` pattern works at runtime but requires a cast to satisfy vue-tsc strict type checking.

## Issues Encountered

None beyond the auto-fixed TypeScript mismatch above.

## Next Phase Readiness

- Wave 3 (05-03: RuleBuilderView) can import RuleCard and RuleSimulator immediately
- RuleCard exports: `update` (RuleSchema & { _id }) and `delete` events
- RuleSimulator accepts: `rules: (RuleSchema & { _id: string })[]` prop
- Both components TypeScript-clean and build-verified

---
*Phase: 05-rule-builder*
*Completed: 2026-06-08*
