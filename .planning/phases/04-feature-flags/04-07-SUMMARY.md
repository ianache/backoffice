---
phase: 04-feature-flags
plan: "07"
subsystem: ui
tags: [vue, pinia, typescript, feature-flags, segments]

# Dependency graph
requires:
  - phase: 04-06
    provides: POST/GET /flags/{flag_id}/segments endpoints + evaluate_flag() segment membership

provides:
  - FlagForm.vue with Segments section using SegmentPicker multi-select
  - FlagDrawer.vue that fetches segments on open and persists segment links after save
  - flags.ts with addSegmentToFlag() and getSegmentsByFlag() API functions
  - FLAG-06 end-to-end: UI segments selection wired to backend flag-segment link endpoints

affects: [phase-05-rule-builder, portal-flags-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FlagDrawer owns the full save flow (store calls + segment linking) — emits @saved(flag) instead of @save(payload)
    - selectedSegmentIds exposed from FlagForm via defineExpose for parent (FlagDrawer) to read after handleSave

key-files:
  created: []
  modified:
    - portal/src/services/flags.ts
    - portal/src/components/flags/FlagForm.vue
    - portal/src/components/flags/FlagDrawer.vue
    - portal/src/views/FlagsView.vue

key-decisions:
  - "FlagDrawer takes ownership of save flow — calls flagsStore.createFlag/updateFlag then addSegmentToFlag per selected ID, emits @saved(flag) on success. FlagsView shows toast only."
  - "selectedSegmentIds is read from flagFormRef.value?.selectedSegmentIds after handleSave (not passed up via emit) — simpler than extra payload field since FlagPayload intentionally excludes segment_ids"
  - "Segment removal from a flag is deferred to Phase 5 (Rule Builder) — Phase 4 is addition-only"

patterns-established:
  - "Drawer-owns-save pattern: complex drawers call store + side-effects internally, parent view only shows toast and closes"
  - "defineExpose for partial exposure: FlagForm exposes both handleSave (callable by parent) and selectedSegmentIds (readable by parent after save)"

requirements-completed: [FLAG-06]

# Metrics
duration: 2min (task 1 only — paused at checkpoint:human-verify task 2)
completed: 2026-06-07
---

# Phase 04 Plan 07: FLAG-06 Portal Wiring Summary

**SegmentPicker wired into FlagForm + FlagDrawer — segment selection now persists to POST /flags/{id}/segments on save**

## Performance

- **Duration:** ~2 min (Task 1 auto-executed; paused at Task 2 checkpoint)
- **Started:** 2026-06-07T17:30:53Z
- **Completed:** 2026-06-07T17:33:07Z (checkpoint pause)
- **Tasks:** 1/2 (Task 2 is human-verify checkpoint)
- **Files modified:** 4

## Accomplishments
- Added `addSegmentToFlag()` and `getSegmentsByFlag()` to portal/src/services/flags.ts
- FlagForm.vue now renders a Segments section above Rules with SegmentPicker multi-select; exposes `selectedSegmentIds` via defineExpose
- FlagDrawer.vue fetches segments list + linked segment IDs on drawer open; calls addSegmentToFlag() for each selected segment after flag save
- FlagsView adapted to @saved event — FlagDrawer now owns the complete save flow

## Task Commits

Each task was committed atomically:

1. **Task 1: Add segment API functions + wire SegmentPicker into FlagForm + FlagDrawer** - `151618c` (feat)

## Files Created/Modified
- `portal/src/services/flags.ts` - Added addSegmentToFlag() and getSegmentsByFlag() exports
- `portal/src/components/flags/FlagForm.vue` - Added SegmentPicker import, segments/linkedSegmentIds props, Segments section in template, selectedSegmentIds exposed
- `portal/src/components/flags/FlagDrawer.vue` - Full save-flow ownership: fetchSegments on open, addSegmentToFlag after save, @saved emit instead of @save
- `portal/src/views/FlagsView.vue` - Adapted to @saved handler; FlagPayload import removed (no longer needed in view)

## Decisions Made
- FlagDrawer takes ownership of the complete save flow rather than delegating to FlagsView — cleaner because segment linking is an implementation detail of the drawer
- `selectedSegmentIds` is read via template ref after `handleSave()` rather than passed in the emit payload — keeps FlagPayload segment-free as designed in plan 04-05
- Segment removal from flag deferred to Phase 5 (only addition is supported in Phase 4)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Refactor] FlagsView @save → @saved handler pattern**
- **Found during:** Task 1
- **Issue:** Plan described FlagDrawer emitting @saved(FeatureFlag), but FlagsView had @save(FlagPayload) with its own store calls — these would conflict (double create/update)
- **Fix:** Refactored FlagsView handleSave → handleSaved; removed FlagPayload import; changed @save → @saved in template; FlagDrawer now handles store calls exclusively
- **Files modified:** portal/src/views/FlagsView.vue
- **Verification:** vue-tsc --noEmit passes cleanly
- **Committed in:** 151618c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (refactor to avoid double-save conflict)
**Impact on plan:** Necessary for correct behavior. FlagsView was calling createFlag/updateFlag AND FlagDrawer would call them again — this would double-create flags. Fixed by moving store ownership exclusively to FlagDrawer.

## Issues Encountered
- None beyond the deviation above.

## Next Phase Readiness
- Task 2 (human-verify) pending: user needs to verify Segments section appears in FlagForm UI and POST /flags/{id}/segments returns 201 in Network tab
- Once verified: FLAG-06 is complete end-to-end; Phase 4 fully done
- Phase 5 can build Rule Builder on top of the established foundation

---
*Phase: 04-feature-flags*
*Completed: 2026-06-07 (checkpoint pending human verification)*
