---
phase: 05-rule-builder
plan: "03"
subsystem: ui
tags: [vue3, typescript, tailwind, vuedraggable, router, feature-flags, rule-builder]

# Dependency graph
requires:
  - phase: 05-01
    provides: useRuleSimulator composable, ChipTagInput component, vuedraggable@next installed
  - phase: 05-02
    provides: RuleCard component, RuleSimulator component

provides:
  - RuleBuilderView.vue — full-page rule editor at /flags/:id/rules with draggable canvas + simulator grid
  - /flags/:id/rules route (name: rule-builder) in router/index.ts
  - FlagDrawer Edit Rules button navigating to rule-builder route
  - FlagForm rules JSON textarea removed; replaced with read-only label

affects:
  - Phase 06 (any future phase using FlagForm will find rules field gone from payload)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "splice-in-place pattern: localRules.splice(index, 1, updated) avoids vuedraggable reactivity pitfall vs full array replacement"
    - "_id strip before PATCH: localRules.map(({ _id, ...r }) => r) cleanly removes internal tracking field before API call"
    - "auto-set complex: rules.length > 0 auto-sets complex=true when rules exist — no manual toggle needed"
    - "emit-close-then-navigate pattern in FlagDrawer: emit('close') before router.push prevents drawer state leak"

key-files:
  created:
    - portal/src/views/RuleBuilderView.vue
  modified:
    - portal/src/router/index.ts
    - portal/src/components/flags/FlagDrawer.vue
    - portal/src/components/flags/FlagForm.vue

key-decisions:
  - "RuleBuilderView uses splice(index, 1, updated) not full array replacement — vuedraggable tracks items by reference, replacement triggers unnecessary drag state reset"
  - "complex auto-derived from rules.length > 0 in saveChanges — user never needs to toggle the complex checkbox manually in RuleBuilderView"
  - "Edit Rules button placed in drawer footer (not header) — footer is the action zone per existing drawer UX pattern; v-if flag.id guards creation mode"
  - "FlagForm.rules field removed entirely from emitted FlagPayload — rules are now exclusively owned by RuleBuilderView PATCH flow"

patterns-established:
  - "Full-page route for complex feature editing: /flags/:id/rules separates complex multi-field editing from drawer-based quick edits"
  - "Ownership split: FlagDrawer owns name/scope/metadata, RuleBuilderView owns rules/rollout — clean separation of concern"

requirements-completed: [RULE-01, RULE-02, RULE-03]

# Metrics
duration: ~10min
completed: 2026-06-08
---

# Phase 05 Plan 03: RuleBuilderView Assembly Summary

**Full-page rule editor at /flags/:id/rules assembled with vuedraggable canvas (drag/add/delete/reorder), rollout slider, live RuleSimulator sidebar, and FlagDrawer navigation — TypeScript build clean and E2E human verification approved**

## Performance

- **Duration:** ~15 min (including E2E human checkpoint)
- **Started:** 2026-06-08T02:31:20Z
- **Completed:** 2026-06-08 (E2E approved)
- **Tasks:** 2 (1 auto + 1 human-verify — both complete)
- **Files modified:** 4

## Accomplishments

- Created RuleBuilderView.vue — 12-column grid layout (8 cols canvas, 4 cols simulator), vuedraggable with drag handle class, rollout range slider, AND connector between cards, empty state, save/cancel navigation wired to flags store updateFlag()
- Added /flags/:id/rules route to router/index.ts with rule-builder name and same role guards as /flags
- Added openRuleBuilder() to FlagDrawer.vue — emits close then router.push to rule-builder; "Edit Rules" button shown only when editing existing flag (v-if props.flag?.id)
- Cleaned up FlagForm.vue — removed rulesRaw ref, JSON textarea, JSON.parse validation, rules field from FlagPayload; replaced with read-only informational label pointing to Rule Builder
- E2E human verification passed: navigation from FlagDrawer, draggable cards, chip input for in/notIn, live simulator, save/cancel all confirmed working

## Task Commits

Each task was committed atomically:

1. **Task 1: Create RuleBuilderView and wire router + FlagDrawer + FlagForm** - `9c467a9` (feat)
2. **Task 2: E2E human verification checkpoint** - `fcb6338` (docs — checkpoint approved)

**Plan metadata:** `8badec5` (docs: complete plan — initial checkpoint commit)

## Files Created/Modified

- `portal/src/views/RuleBuilderView.vue` — full-page rule editor; imports draggable, RuleCard, RuleSimulator; owns localRules + localRollout state; splice-based updateRule/deleteRule; saveChanges strips _id before PATCH
- `portal/src/router/index.ts` — added /flags/:id/rules route with name rule-builder
- `portal/src/components/flags/FlagDrawer.vue` — added useRouter import, openRuleBuilder function, Edit Rules button in footer
- `portal/src/components/flags/FlagForm.vue` — removed rulesRaw ref, JSON validation, rules from payload; added read-only label

## Decisions Made

- **splice-in-place for updateRule:** `localRules.splice(index, 1, updated)` used instead of `localRules.value[index] = updated`. vuedraggable tracks drag state by object reference — full assignment can confuse the drag item tracking. Splice avoids the pitfall.
- **complex auto-derived:** `complex: rules.length > 0` computed automatically in saveChanges — keeps UI clean; the checkbox in FlagForm still works for metadata but RuleBuilderView always sets the authoritative value.
- **Edit Rules in footer not header:** The drawer footer is the established action zone (Cancel / Save Changes). Adding Edit Rules as a third action button there follows the existing UX pattern without restructuring the drawer header layout.
- **rules removed from FlagPayload in FlagForm:** This is a breaking change to the payload shape — intentional. FlagDrawer's handleSave no longer writes rules; the PATCH from RuleBuilderView is the only rules write path. Prevents double-write race conditions.

## Deviations from Plan

None - plan executed exactly as written. TypeScript build passed on first attempt.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Rule Builder is feature-complete — E2E human verification approved
- RULE-01 (navigate to rule builder), RULE-02 (drag/add/delete rules), RULE-03 (live simulator) all verified E2E
- Phase 05-rule-builder fully delivered; no blockers for subsequent phases

---
*Phase: 05-rule-builder*
*Completed: 2026-06-08*
