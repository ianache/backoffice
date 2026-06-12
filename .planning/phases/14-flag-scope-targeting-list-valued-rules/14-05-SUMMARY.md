---
phase: 14-flag-scope-targeting-list-valued-rules
plan: 05
subsystem: ui
tags: [vue, vitest, feature-flags, scope-targeting, federation]

# Dependency graph
requires:
  - phase: 14-flag-scope-targeting-list-valued-rules
    provides: "Companies BFF route (/companies) and backend scope-target validation from 14-01/14-02"
provides:
  - "FlagForm.vue conditional product/tenant/company comboboxes with Name (id) labels"
  - "lookups.ts: listProductsLookup/listCompaniesLookup/listTenantsLookup via shell/api"
  - "flagFormModel.ts pure helpers: validateFlagTarget + buildTargetFields"
  - "FlagPayload widened to accept explicit null for tenant_id/product_id/company_id"
affects: [14-06, sdk-bootstrap-enforcement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-function form helpers (flagFormModel.ts) extracted from Vue SFC for unit testing without mounting"
    - "Lazy per-scope catalog fetch with loaded/loading flags, triggered on scope watch + edit-mode initial load"
    - "403 fallback for PlatformAdmin-only BFF routes via useUserContext() single-option catalog"

key-files:
  created:
    - microuis/mui-feature-flags/src/services/lookups.ts
    - microuis/mui-feature-flags/src/components/flags/flagFormModel.ts
    - microuis/mui-feature-flags/src/components/flags/flagFormModel.test.ts
  modified:
    - microuis/mui-feature-flags/src/services/flags.ts
    - microuis/mui-feature-flags/src/components/flags/FlagForm.vue

key-decisions:
  - "validateFlagTarget/buildTargetFields kept dependency-free (no Vue) for direct vitest unit testing"
  - "Tenant lookup wrapped in try/catch — on error, falls back to useUserContext().tenant_id as a single 'My tenant' option"
  - "Scope-switch watcher clears all three target refs unconditionally when oldScope !== newScope (locked behavior per CONTEXT.md)"

patterns-established:
  - "FlagPayload target fields use string | null (not optional-only) so PATCH can explicitly clear stale columns"

requirements-completed: [TGT-01, TGT-02]

# Metrics
duration: 12min
completed: 2026-06-11
---

# Phase 14 Plan 05: FlagForm Scope-Target Comboboxes Summary

**Conditional product/tenant/company comboboxes in FlagForm.vue fed by new lookups.ts services (BFF /products, /tenants, /companies), with required-target validation, scope-switch clearing, and mutual-exclusivity payload (explicit nulls) — verified end-to-end against the live backend (422 without target, 201 with).**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-11T19:14:00Z
- **Completed:** 2026-06-11T19:19:00Z
- **Tasks:** 3
- **Files modified:** 5 (2 created source, 1 created test, 2 modified)

## Accomplishments
- New `lookups.ts` service exposes `listProductsLookup`/`listCompaniesLookup`/`listTenantsLookup`, mapping BFF responses to `{id, name}` LookupOption with `{items}`-wrapper tolerance
- New `flagFormModel.ts` provides pure `validateFlagTarget` (required-target-per-scope) and `buildTargetFields` (mutual-exclusivity nulls), both fully unit-tested (9 tests, no Vue mounting)
- `FlagForm.vue` gained conditional Product/Tenant/Company comboboxes with "Name (id)" / "Name (#id)" labels, active-only catalogs, empty-state hints, lazy per-scope fetch (including edit-mode pre-load), scope-switch clearing of all three target refs, and inline validation error
- `FlagPayload` (`flags.ts`) widened to `tenant_id?/product_id?/company_id?: string | null` so PATCH explicitly clears stale target columns
- End-to-end contract verified against the running backend: `POST /flags/` with `scope:"product"` and no `product_id` → 422 (14-02 validator); with `product_id:"backoffice"` → 201 with payload shape `{tenant_id: null, product_id: "backoffice", company_id: null}` matching `buildTargetFields` output exactly; smoke flag deleted afterwards (204)

## Task Commits

Each task was committed atomically:

1. **Task 1: lookups service + flagFormModel pure helpers + tests** - `f08fd24` (feat)
2. **Task 2: FlagForm.vue comboboxes + validation + scope-switch clearing** - `ad2fac0` (feat)
3. **Task 3: end-to-end wiring check against live backend** - no file changes (verification-only, no commit)

**Plan metadata:** (this commit)

_Note: TDD task 1 ran RED (test written against non-existent module, confirmed failure) then GREEN (implementation added, 9/9 tests pass) in the same commit since both files were new — no separate test-only commit was meaningful._

## Files Created/Modified
- `microuis/mui-feature-flags/src/services/lookups.ts` - listProductsLookup/listCompaniesLookup/listTenantsLookup via shell/api
- `microuis/mui-feature-flags/src/components/flags/flagFormModel.ts` - validateFlagTarget + buildTargetFields pure helpers
- `microuis/mui-feature-flags/src/components/flags/flagFormModel.test.ts` - 9 unit tests covering all 4 scopes for both helpers
- `microuis/mui-feature-flags/src/services/flags.ts` - FlagPayload tenant_id/product_id/company_id widened to `string | null`
- `microuis/mui-feature-flags/src/components/flags/FlagForm.vue` - target refs, option lists, ensureCatalogLoaded(), scope watcher, validate()/handleSave() wiring, 3 conditional combobox template blocks

## Decisions Made
- Kept `flagFormModel.ts` as pure TypeScript (no Vue imports) per plan spec — enables direct vitest testing and matches the `evaluateRule()` precedent from 11-04
- Tenant catalog fetch uses try/catch with `useUserContext()` fallback rather than checking roles client-side, since the 403 boundary is enforced server-side and is the simplest signal
- Used `sel.productId || null` (falsy-coalesce) in `buildTargetFields` rather than ternary on empty-string check — equivalent but more concise; empty string and undefined both map to null

## Deviations from Plan

None - plan executed exactly as written. Task 3's integration check passed cleanly on the first attempt against the live backend with zero contract mismatches, so no FlagForm.vue fixes were needed.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- TGT-01/TGT-02 UI half complete: FlagForm now persists exactly one scope target with explicit nulls for the other two, matching the 14-02 backend validator contract
- Companies catalog admin UI (mui-tenants `/companies`) is being delivered in parallel by 14-06; FlagForm's `listCompaniesLookup()` will start returning real data once that BFF route + seed data exist (BFF route already live per 14-01)
- No blockers for SDK bootstrap/evaluation enforcement work (covered by 14-03, already complete)

---
*Phase: 14-flag-scope-targeting-list-valued-rules*
*Completed: 2026-06-11*

## Self-Check: PASSED

All created files found on disk; both task commits (f08fd24, ad2fac0) verified in git log.
