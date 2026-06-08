---
phase: 05-rule-builder
plan: "01"
subsystem: ui
tags: [vue3, typescript, vuedraggable, composable, feature-flags]

# Dependency graph
requires:
  - phase: 04-feature-flags
    provides: RuleSchema interface in flags.ts; _evaluate_rule() / evaluate_flag() in service.py

provides:
  - vuedraggable@next installed in portal (SortableJS Vue 3 wrapper for drag-and-drop)
  - useRuleSimulator composable — reactive TypeScript port of Python evaluation engine
  - ChipTagInput component — chip-tag input for in/notIn operator array values

affects:
  - 05-02 (RuleCard uses ChipTagInput + useRuleSimulator)
  - 05-03 (RuleBuilderView uses vuedraggable + useRuleSimulator)

# Tech tracking
tech-stack:
  added: [vuedraggable@next (^4.1.0)]
  patterns:
    - watchEffect for auto-tracking reactive deps (not watch with deep:true)
    - Operator dispatch table (Record<string, fn>) mirrors backend OPERATORS dict pattern
    - v-model chip input pattern (modelValue + update:modelValue emit)

key-files:
  created:
    - portal/src/composables/useRuleSimulator.ts
    - portal/src/components/flags/ChipTagInput.vue
  modified:
    - portal/package.json

key-decisions:
  - "useRuleSimulator uses watchEffect (not watch+deep) — auto-tracks rules and contextJson refs without explicit dep list"
  - "OPERATORS record in TS uses Array.isArray guard for in/notIn — matches Python isinstance(expected, list) check"
  - "regex operator wraps new RegExp() in try/catch returning false — safe against malformed patterns"

patterns-established:
  - "Composable pattern: accept Readonly<Ref<T>> for input arrays, return plain Refs for reactive output"
  - "Chip-tag v-model: addChip deduplicates, removeChip emits filtered array — no mutation of prop"

requirements-completed: [RULE-01, RULE-03]

# Metrics
duration: 8min
completed: 2026-06-07
---

# Phase 05 Plan 01: Rule Builder Foundations Summary

**vuedraggable@next installed, TypeScript OPERATORS evaluation engine composable and chip-tag input component built as Wave 1 foundations for the visual rule builder**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-07T18:21:50Z
- **Completed:** 2026-06-07T18:29:40Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Installed vuedraggable@next (SortableJS Vue 3 wrapper) as new portal dependency
- Created useRuleSimulator.ts — direct TypeScript port of Python _evaluate_rule() with all 5 operators (equals, in, notIn, contains, regex) using watchEffect for zero-config reactivity
- Created ChipTagInput.vue — chip-tag input supporting Enter and comma delimiters, add deduplication, and v-model pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Install vuedraggable@next and create useRuleSimulator composable** - `79cfd66` (feat)
2. **Task 2: Create ChipTagInput component** - `3385de4` (feat)

**Plan metadata:** (included in final docs commit)

## Files Created/Modified

- `portal/src/composables/useRuleSimulator.ts` — OPERATORS dispatch table + evaluateRule + useRuleSimulator composable; watchEffect-based reactive evaluation
- `portal/src/components/flags/ChipTagInput.vue` — chip-tag input for array operator values; modelValue/update:modelValue v-model
- `portal/package.json` — vuedraggable@next ^4.1.0 added to dependencies

## Decisions Made

- useRuleSimulator uses `watchEffect` (not `watch` with `{ deep: true }`) — auto-tracks accessed reactive deps without explicit dep list, cleaner for multi-ref scenarios
- OPERATORS `in`/`notIn` use `Array.isArray(expected)` guard to mirror Python `isinstance(expected, list)` semantics — returns false if value is not an array
- `regex` operator wraps `new RegExp()` in try/catch returning false on invalid patterns — safe against user-entered malformed regex

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed invalid Vue keydown modifier syntax**
- **Found during:** Task 2 (ChipTagInput)
- **Issue:** `@keydown.exact.prevent.capture.key=","` generated TS1003 Identifier expected — invalid Vue template syntax
- **Fix:** Removed the invalid modifier line; `@keydown.comma.prevent="addChip"` alone correctly handles comma key
- **Files modified:** portal/src/components/flags/ChipTagInput.vue
- **Verification:** TypeScript build passes clean after fix
- **Committed in:** 3385de4 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in generated template syntax)
**Impact on plan:** Minor fix, no scope creep. Comma add-chip still works as specified.

## Issues Encountered

None beyond the auto-fixed template syntax error above.

## Next Phase Readiness

- Wave 2 (05-02: RuleCard) can import ChipTagInput and useRuleSimulator immediately
- Wave 2 (05-03: RuleBuilderView) can import vuedraggable and useRuleSimulator
- Both foundations TypeScript-clean and build-verified

---
*Phase: 05-rule-builder*
*Completed: 2026-06-07*
