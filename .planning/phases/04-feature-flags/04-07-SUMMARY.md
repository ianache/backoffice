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
  - FlagDrawer.vue that fetches segments on open and persists segment links (add + remove) after save
  - flags.ts with addSegmentToFlag(), removeSegmentFromFlag(), and getSegmentsByFlag() API functions
  - backend DELETE /flags/{flag_id}/segments/{segment_id} endpoint + remove_segment_from_flag() service
  - FLAG-06 end-to-end: UI segment selection wired to backend flag-segment link endpoints, human-verified

affects: [phase-05-rule-builder, portal-flags-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FlagDrawer owns the full save flow (store calls + segment linking) — emits @saved(flag) instead of @save(payload)
    - selectedSegmentIds exposed from FlagForm via defineExpose for parent (FlagDrawer) to read after handleSave
    - Capture mutable refs before first await in async handlers to avoid race conditions after reactivity resets
    - Diff-based segment sync (toAdd/toRemove) rather than naive add-only loop — correct for edit mode

key-files:
  created: []
  modified:
    - portal/src/services/flags.ts
    - portal/src/components/flags/FlagForm.vue
    - portal/src/components/flags/FlagDrawer.vue
    - portal/src/views/FlagsView.vue
    - backend/app/domains/feature_flags/service.py
    - backend/app/domains/feature_flags/router.py
    - backend/tests/test_feature_flags_domain.py

key-decisions:
  - "FlagDrawer takes ownership of save flow — calls flagsStore.createFlag/updateFlag then addSegmentToFlag/removeSegmentFromFlag per diff, emits @saved(flag) on success. FlagsView shows toast only."
  - "selectedSegmentIds is read from flagFormRef.value?.selectedSegmentIds before the first await (not after) — prevents race condition where props.flag update resets the ref mid-save"
  - "Diff logic (toAdd/toRemove) replaces naive add-only loop — supports segment removal from flags starting Phase 4 (not deferred to Phase 5 as originally planned)"
  - "PlatformAdmin and ProductManager bypass tenant_id filter in list_flags — global roles should see all flags across tenants"

patterns-established:
  - "Drawer-owns-save pattern: complex drawers call store + side-effects internally, parent view only shows toast and closes"
  - "defineExpose for partial exposure: FlagForm exposes both handleSave (callable by parent) and selectedSegmentIds (readable by parent after save)"
  - "Capture-before-await pattern: snapshot reactive refs to local const before any async call to prevent reactivity teardown mid-handler"

requirements-completed: [FLAG-06]

# Metrics
duration: ~30min total (2min task 1 auto + checkpoint + bug fixes during human-verify + task 2 commit)
completed: 2026-06-07
---

# Phase 04 Plan 07: FLAG-06 Portal Wiring Summary

**SegmentPicker wired into FlagForm + FlagDrawer — segment selection (add + remove) persists to backend on save; FLAG-06 human-verified end-to-end**

## Performance

- **Duration:** ~30 min total (Task 1 auto, checkpoint pause, bug fixes during human verification, Task 2 commit)
- **Started:** 2026-06-07
- **Completed:** 2026-06-07
- **Tasks:** 2/2 (both complete)
- **Files modified:** 7

## Accomplishments

- Added `addSegmentToFlag()`, `removeSegmentFromFlag()`, and `getSegmentsByFlag()` to portal/src/services/flags.ts
- FlagForm.vue renders Segments section above Rules with SegmentPicker multi-select; exposes `selectedSegmentIds` via defineExpose; watches `linkedSegmentIds` prop for async arrival
- FlagDrawer.vue fetches segments list + linked segment IDs on drawer open; captures segment state before any await; applies diff logic (toAdd/toRemove) after flag save
- FlagsView adapted to @saved event — FlagDrawer now owns the complete save flow
- Backend: `remove_segment_from_flag()` service function added to service.py
- Backend: `DELETE /flags/{flag_id}/segments/{segment_id}` endpoint added to router.py (204 No Content)
- Backend: PlatformAdmin/ProductManager bypass tenant_id filter in `list_flags` — global roles see all flags
- Tests: `_get_scope_filter` unit tests + `list_flags` router tenant bypass integration test added
- Human verification approved: Segments section visible in FlagForm, POST /flags/{id}/segments returns 201, segments pre-selected on re-open

## Task Commits

Each task was committed atomically:

1. **Task 1: Add segment API functions + wire SegmentPicker into FlagForm + FlagDrawer** — `151618c` (feat)
2. **Task 2: Fix segment sync bugs — capture before await, diff logic, remove endpoint** — `8d164ee` (feat)

## Files Created/Modified

- `portal/src/services/flags.ts` — Added addSegmentToFlag(), removeSegmentFromFlag(), getSegmentsByFlag() exports
- `portal/src/components/flags/FlagForm.vue` — Added SegmentPicker import, segments/linkedSegmentIds props, Segments section in template, selectedSegmentIds exposed, async watch on linkedSegmentIds
- `portal/src/components/flags/FlagDrawer.vue` — Full save-flow ownership: fetchSegments on open, capture-before-await, diff-based segment sync (toAdd/toRemove), @saved emit
- `portal/src/views/FlagsView.vue` — Adapted to @saved handler; FlagPayload import removed (no longer needed in view)
- `backend/app/domains/feature_flags/service.py` — Added remove_segment_from_flag() async function
- `backend/app/domains/feature_flags/router.py` — Added DELETE /{flag_id}/segments/{segment_id} endpoint; PlatformAdmin/ProductManager tenant_id bypass in list_flags
- `backend/tests/test_feature_flags_domain.py` — Added _get_scope_filter tests + list_flags router tenant bypass test

## Decisions Made

- FlagDrawer takes ownership of the complete save flow rather than delegating to FlagsView — cleaner because segment linking is an implementation detail of the drawer
- `selectedSegmentIds` is captured as a local const before the first `await` in handleSave — prevents race condition where store update changes `props.flag`, which triggers the watch in FlagForm to reset the ref
- Segment removal from flag implemented in Phase 4 (not deferred to Phase 5) — required for correct edit-mode behavior when user unchecks a segment
- Diff logic (toAdd/toRemove) is the correct general pattern for managing many-to-many UI associations

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Refactor] FlagsView @save → @saved handler pattern**
- **Found during:** Task 1
- **Issue:** Plan described FlagDrawer emitting @saved(FeatureFlag), but FlagsView had @save(FlagPayload) with its own store calls — these would conflict (double create/update)
- **Fix:** Refactored FlagsView handleSave → handleSaved; removed FlagPayload import; changed @save → @saved in template; FlagDrawer now handles store calls exclusively
- **Files modified:** portal/src/views/FlagsView.vue
- **Committed in:** 151618c

**2. [Rule 1 - Bug] Race condition: selectedSegmentIds reset before read in handleSave**
- **Found during:** Task 2 human verification
- **Issue:** `flagFormRef.value?.selectedSegmentIds` was read AFTER `await flagsStore.updateFlag()` — the store update changes `props.flag`, which triggers FlagForm's watch to reset `selectedSegmentIds.value = []`, so the read always returned an empty array
- **Fix:** Capture `selectedIds = [...(flagFormRef.value?.selectedSegmentIds ?? [])]` and `previousIds = [...linkedSegmentIds.value]` before any await call
- **Files modified:** portal/src/components/flags/FlagDrawer.vue
- **Committed in:** 8d164ee

**3. [Rule 1 - Bug] Async prop arrival: linkedSegmentIds not reactive in FlagForm**
- **Found during:** Task 2 human verification
- **Issue:** `linkedSegmentIds` prop arrived after initial render (FlagDrawer fetches them async), but FlagForm only set `selectedSegmentIds` in the `watch(() => props.flag, ...)` handler — linkedSegmentIds was not watched independently
- **Fix:** Added a separate `watch(() => props.linkedSegmentIds, ...)` in FlagForm to sync selectedSegmentIds when the prop updates asynchronously
- **Files modified:** portal/src/components/flags/FlagForm.vue
- **Committed in:** 8d164ee

**4. [Rule 2 - Missing Functionality] Segment removal not implemented (was deferred in plan)**
- **Found during:** Task 2 human verification
- **Issue:** Plan deferred segment removal to Phase 5, but without it, editing a flag and unchecking a segment had no effect — a correctness requirement for edit mode
- **Fix:** Added `remove_segment_from_flag()` backend service, `DELETE /flags/{flag_id}/segments/{segment_id}` endpoint, `removeSegmentFromFlag()` frontend service, and diff logic in FlagDrawer
- **Files modified:** backend/app/domains/feature_flags/service.py, router.py, portal/src/services/flags.ts, FlagDrawer.vue
- **Committed in:** 8d164ee

**5. [Rule 2 - Missing Functionality] PlatformAdmin sees no flags (tenant filter too strict)**
- **Found during:** Task 2 human verification
- **Issue:** list_flags was scoping by tenant_id for all roles — PlatformAdmin with no tenant_id in JWT could see no flags at all
- **Fix:** Added role check in router: if PlatformAdmin or ProductManager, set tenant_id = None to bypass tenant filter
- **Files modified:** backend/app/domains/feature_flags/router.py
- **Committed in:** 8d164ee

---

**Total deviations:** 5 (1 refactor + 2 bugs + 2 missing functionality — all auto-fixed per Rules 1-2)
**Impact on plan:** All were correctness requirements. The plan described the happy-path wiring; verification exposed edge cases that had to be fixed for the feature to work correctly.

## Self-Check

- `portal/src/components/flags/FlagForm.vue` — modified in 151618c, 8d164ee
- `portal/src/components/flags/FlagDrawer.vue` — modified in 151618c, 8d164ee
- `portal/src/services/flags.ts` — modified in 151618c, 8d164ee
- `backend/app/domains/feature_flags/service.py` — modified in 8d164ee
- `backend/app/domains/feature_flags/router.py` — modified in 8d164ee
- Commits 151618c and 8d164ee both present in git log

## Self-Check: PASSED

## Next Phase Readiness

- FLAG-06 fully complete: SegmentPicker visible in FlagForm, segment links saved (201) and removed (204) correctly, segments pre-selected on re-open
- Phase 4 feature flags are complete end-to-end: evaluation engine, CRUD UI, segment management, segment-to-flag association
- Phase 5 (Rule Builder) can build on top: FlagForm already has the segment pattern; rule editing can follow the same drawer-owns-save pattern

---
*Phase: 04-feature-flags*
*Completed: 2026-06-07*
