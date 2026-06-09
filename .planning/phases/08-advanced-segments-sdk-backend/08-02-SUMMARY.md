---
phase: 08-advanced-segments-sdk-backend
plan: "02"
subsystem: ui
tags: [vue, typescript, fastapi, segments, feature-flags, rule-based]

# Dependency graph
requires:
  - phase: 08-01
    provides: list_segments() returning (Segment, int) tuples; Segment model with type/conditions columns; SegmentResponse with flag_count

provides:
  - /segments portal page with CRUD (create/edit/delete)
  - SegmentTable.vue with flag_count badges and amber Orphan chips
  - SegmentForm.vue with RuleCard-based condition builder for rule_based type
  - PATCH /flags/segments/{id} backend endpoint + update_segment() service
  - /segments router route guarded by PlatformAdmin/TenantAdmin/TenantOwner/ProductManager
  - Segments sidebar nav item in MainLayout after Feature Flags

affects:
  - 08-03 (SDK backend references segments for bootstrap endpoint)
  - any future phase using segments portal UI

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "inline form panel pattern (showForm ref toggles SegmentForm inline above table)"
    - "RuleCard reuse in SegmentForm — same component as FlagRuleBuilder used in /flags/:id/rules"
    - "hover-reveal action buttons in table rows (group/group-hover opacity)"

key-files:
  created:
    - portal/src/components/flags/SegmentTable.vue
    - portal/src/components/flags/SegmentForm.vue
    - portal/src/views/SegmentsView.vue
  modified:
    - backend/app/domains/feature_flags/router.py
    - backend/app/domains/feature_flags/service.py
    - portal/src/services/flags.ts
    - portal/src/router/index.ts
    - portal/src/components/layout/MainLayout.vue

key-decisions:
  - "update_segment() uses SegmentCreate schema (full replacement) not a partial update schema — keeps service simple for Phase 8 scope"
  - "Segments nav item uses v-if with same role check as Feature Flags (PlatformAdmin|TenantAdmin|TenantOwner|ProductManager)"
  - "SegmentForm emits full SegmentPayload on save and strips _id from RuleCard conditions before emit"

patterns-established:
  - "Flag-count badge: rounded-full bg-primary-container text-on-primary-container px-2 py-0.5 text-xs"
  - "Orphan chip: bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 rounded-full px-2 py-0.5 text-xs"
  - "Inline form panel: v-if showForm above table card, form emits save/cancel to parent view"

requirements-completed:
  - SEG-01
  - SEG-02
  - SEG-03
  - SEG-04
  - SEG-05

# Metrics
duration: 25min
completed: 2026-06-08
---

# Phase 08 Plan 02: Segments UI — Summary

**Segment portal page with flag_count badges, amber Orphan chips, and inline RuleCard-based condition builder for rule_based segment creation**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-06-08
- **Completed:** 2026-06-08
- **Tasks:** 2 of 2 auto tasks complete (checkpoint pending human verification)
- **Files modified:** 7

## Accomplishments

- Backend segments list endpoint updated to unpack (Segment, int) tuples and inject flag_count into SegmentResponse
- Added update_segment() service function and PATCH /flags/segments/{id} router endpoint
- Extended Segment TypeScript interface with type, conditions, flag_count fields; added updateSegment/deleteSegment to flags.ts
- SegmentTable.vue: flag_count badge on every row, amber Orphan chip when flag_count === 0, type badge (blue rule_based / grey manual), hover-reveal edit/delete buttons
- SegmentForm.vue: type toggle between manual (UUID textarea) and rule_based (RuleCard condition list with + Add Condition); defineExpose({ reset }) for parent
- SegmentsView.vue: full CRUD page wiring listSegments/createSegment/updateSegment/deleteSegment with toast feedback
- /segments route added to router with same auth+role meta as /flags
- Segments sidebar nav item added in MainLayout after Feature Flags with group icon

## Task Commits

1. **Task 1: Update segments router + extend flags.ts + build SegmentTable and SegmentForm** - `c63e671` (feat)
2. **Task 2: Build SegmentsView + wire router route + add sidebar nav item** - `9029f32` (feat)

## Files Created/Modified

- `backend/app/domains/feature_flags/router.py` - Unpack (Segment, flag_count) tuples in list handler; add PATCH update endpoint
- `backend/app/domains/feature_flags/service.py` - Add update_segment() function
- `portal/src/services/flags.ts` - Extended Segment interface + updateSegment/deleteSegment functions
- `portal/src/components/flags/SegmentTable.vue` - Table with flag_count badge, orphan chip, type badge, hover actions
- `portal/src/components/flags/SegmentForm.vue` - Inline form with RuleCard conditions or UUID textarea by type
- `portal/src/views/SegmentsView.vue` - Full segments page with CRUD wiring and toast feedback
- `portal/src/router/index.ts` - /segments route with requiresAuth + roles meta
- `portal/src/components/layout/MainLayout.vue` - Segments nav item after Feature Flags

## Decisions Made

- update_segment() uses SegmentCreate schema (full replacement) for simplicity — avoids a partial SegmentUpdate schema in Phase 8 scope
- Segments nav item uses same role condition as Feature Flags (PlatformAdmin|TenantAdmin|TenantOwner|ProductManager)
- SegmentForm emits full SegmentPayload on save and strips internal _id from RuleCard conditions before emit

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added update_segment() service function and PATCH endpoint**
- **Found during:** Task 1 (router update)
- **Issue:** Plan specified updateSegment() in flags.ts calling PATCH /flags/segments/{id}, but no PATCH endpoint or update_segment() service function existed
- **Fix:** Added update_segment() to service.py and @segments_router.patch("/{segment_id}") endpoint in router.py
- **Files modified:** backend/app/domains/feature_flags/service.py, backend/app/domains/feature_flags/router.py
- **Verification:** 34 backend tests pass; TypeScript compilation clean
- **Committed in:** c63e671 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical endpoint)
**Impact on plan:** Required for edit functionality to work. No scope creep.

## Issues Encountered

None — plan executed smoothly. Backend tests all pass (34/34). TypeScript compilation clean.

## Next Phase Readiness

- Checkpoint: human must verify /segments page at http://localhost:5173/segments
- After checkpoint approval: Phase 08-02 complete, ready for Phase 08-04 (SDK JS frontend)
- /flags page unaffected (no regression from router.py changes)

---
*Phase: 08-advanced-segments-sdk-backend*
*Completed: 2026-06-08*
