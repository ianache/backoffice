---
phase: 14-flag-scope-targeting-list-valued-rules
plan: 02
subsystem: api
tags: [fastapi, pydantic, sqlalchemy, feature-flags, sdk]

# Dependency graph
requires:
  - phase: 14-flag-scope-targeting-list-valued-rules
    provides: phase context and research (CONTEXT.md, locked decisions on company-target/legacy behavior)
provides:
  - FlagCreate model_validator enforcing non-global flags carry their scope's target column at create time
  - FlagUpdate gains scope/tenant_id/product_id/company_id fields for retrofitting targets onto legacy flags
  - router._validate_update_target() — merged-state validation on PATCH, only when scope/target fields touched
  - bootstrap_flags() per-scope target dispatch (_flag_matches_target) fixing the company-scope exclusion gap
  - bootstrap entries carry tenant_id/product_id/company_id for SDK-side enforcement
  - /sdk/evaluate fetches flags unfiltered, letting evaluate_flag()'s existing per-scope candidate matching resolve product/company-scoped flags
affects: [14-03 (sdk-js/sdk-python target enforcement using bootstrap target fields)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Merged-state validation in router layer (not schema) for PATCH endpoints where partial updates must skip validation unless specific fields are touched"
    - "Per-scope dispatch function (_flag_matches_target) replacing scope-blind OR-clause filters"

key-files:
  created: []
  modified:
    - backend/app/domains/feature_flags/schemas.py
    - backend/app/domains/feature_flags/router.py
    - backend/app/domains/sdk/service.py
    - backend/app/domains/sdk/router.py
    - backend/tests/test_feature_flags_router.py
    - backend/tests/test_sdk_bootstrap.py

key-decisions:
  - "FlagUpdate has NO model_validator — partial updates (e.g. toggling enabled) must not trip scope/target validation; validation happens in router._validate_update_target() on merged state only when scope/tenant_id/product_id/company_id are present in the PATCH payload"
  - "Scope change via PATCH clears the two non-matching target columns (mutual exclusivity) by rebuilding the payload via FlagUpdate(**validated_dict) so exclude_unset persists the forced Nones"
  - "company-scope bootstrap inclusion: company target is per-user context (checked by evaluate_flag's company_id match), NOT per-SDK-client — bootstrap includes company-scoped flags unless the flag also carries a tenant_id that mismatches the requesting tenant"
  - "/sdk/evaluate now calls list_flags(db) unfiltered (no tenant_id pre-filter) — evaluate_flag() already does per-scope candidate matching against context, so the previous tenant-only filter was incorrectly starving product/company-scoped flags (tenant_id NULL)"

patterns-established:
  - "_validate_update_target(flag, update_data) helper pattern: check target_keys.intersection(update_data) first to skip validation entirely for legacy edits"

requirements-completed: [TGT-02, TGT-03]

# Metrics
duration: 18min
completed: 2026-06-12
---

# Phase 14 Plan 02: Backend Flag Scope Targeting Enforcement Summary

**Server-side validation that non-global flags carry their target (create+update via Pydantic model_validator + router merged-state check), bootstrap_flags() per-scope dispatch fixing the company-scope exclusion gap, and /sdk/evaluate unfiltered-fetch fix so evaluate_flag's existing candidate matching can resolve product/company-scoped flags.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-06-11T23:52:00Z
- **Completed:** 2026-06-12T00:10:38Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- FlagCreate now rejects non-global scopes without their required target column (422 via Pydantic ValidationError)
- FlagUpdate can retrofit scope/tenant_id/product_id/company_id onto legacy flags; PATCH validates merged state only when scope/target fields are touched, leaving legacy no-target edits (e.g. toggling `enabled`) completely unaffected
- bootstrap_flags() replaced its scope-blind OR-clause filter with `_flag_matches_target()` per-scope dispatch — company-scoped flags (tenant_id=None) are now included in bootstrap, and entries carry tenant_id/product_id/company_id for SDK-side enforcement
- /sdk/evaluate fetches flags unfiltered (`list_flags(db)`), removing the tenant-only pre-filter that previously starved product/company-scoped flags out of remote evaluation — evaluate_flag()'s existing candidate matching now reaches all four scopes

## Task Commits

Each task was committed atomically:

1. **Task 1: FlagCreate/FlagUpdate target validation + update merged-state enforcement** - `f6dee94` (feat)
2. **Task 2: bootstrap_flags() per-scope dispatch + target fields in entries** - `c207292` (feat)
3. **Task 3: /sdk/evaluate fetch-unfiltered fix** - `ce323f7` (fix)

**Plan metadata:** (this commit)

_Note: All three tasks followed TDD (RED -> GREEN) within a single commit each — failing tests were written first, then implementation, then verified green before committing._

## Files Created/Modified
- `backend/app/domains/feature_flags/schemas.py` - FlagCreate gains validate_scope_target model_validator; FlagUpdate gains scope/tenant_id/product_id/company_id fields with no validator
- `backend/app/domains/feature_flags/router.py` - new `_validate_update_target()` helper + `_TARGET_FIELD_BY_SCOPE` map; update_flag endpoint checks permission for new scope on scope-change and validates merged state before persisting
- `backend/app/domains/sdk/service.py` - new `_flag_matches_target()` per-scope dispatch function; bootstrap_flags() filter replaced; entries gain tenant_id/product_id/company_id keys
- `backend/app/domains/sdk/router.py` - evaluate() calls `list_flags(db)` unfiltered with explanatory comment
- `backend/tests/test_feature_flags_router.py` - TestFlagCreateScopeTargetValidation, TestFlagUpdateScopeTargetFields, TestValidateUpdateTarget (9 new tests)
- `backend/tests/test_sdk_bootstrap.py` - make_flag extended with tenant_id/company_id kwargs; TestBootstrapTargetFiltering (9 tests), TestSdkEvaluateScoping (3 tests)

## Decisions Made
- See `key-decisions` in frontmatter. Summary: validation lives in the router for PATCH (not the schema) to preserve legacy partial-update behavior; bootstrap's company-scope inclusion treats company_id as a per-user-context check (deferred to evaluate_flag), not a per-SDK-client filter; /sdk/evaluate now relies entirely on evaluate_flag's existing scope+target candidate matching rather than a pre-filter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] make_flag test helper rules='[]' string vs list mismatch**
- **Found during:** Task 3 (writing TestSdkEvaluateScoping tests)
- **Issue:** Initial test drafts passed `rules='[]'` (a JSON string) to `make_flag(rules=...)`, but the helper does `json.dumps(rules) if rules is not None else '[]'`, which would have double-encoded the string into `'"[]"'`
- **Fix:** Changed all three new test calls to pass `rules=[]` (an actual empty list) so `json.dumps([])` produces `'[]'` correctly
- **Files modified:** backend/tests/test_sdk_bootstrap.py
- **Verification:** Tests pass with correct rules JSON
- **Committed in:** ce323f7 (Task 3 commit)

**2. [Rule 1 - Bug] TestSdkEvaluateScoping fake_list_flags initially didn't exercise the starvation bug**
- **Found during:** Task 3 (RED phase verification)
- **Issue:** The plan's described fake `fake_list_flags(db, tenant_id=None): return flags` ignores `tenant_id` entirely, so the test passed even before the fix (the bug it's meant to catch — list_flags' tenant filter starving product/company-scoped flags — was never exercised since payload.user had no tenant_id, making `list_flags(db, tenant_id=None)` a no-op filter in both old and new code)
- **Fix:** Made `fake_list_flags` replicate the real list_flags() tenant filter (`scope=='global' or tenant_id matches`) when `tenant_id` is truthy, and added `tenant_id: 't1'` to the test payload.user dicts so the pre-fix code path actually excludes the product/company flags (tenant_id=None), giving a true RED before the router fix
- **Files modified:** backend/tests/test_sdk_bootstrap.py
- **Verification:** Confirmed RED (2 of 3 new tests failed) before router.py change, GREEN (all 3 pass) after
- **Committed in:** ce323f7 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - test-correctness bugs found while writing TDD tests, no production code impact beyond the planned fix)
**Impact on plan:** Both fixes were within the test files for Task 3 and made the TDD RED/GREEN cycle meaningful. No scope creep — production code matches the plan's `<action>` exactly.

## Issues Encountered
- `backend/app/domains/sdk/service.py` had a pre-existing uncommitted manual fix to `bootstrap_flags()` (unfiltered list_flags() fetch + scope-aware post-filter) noted in the executor's important_note. Built Task 2 on top of it as instructed — the pre-existing diff (unfiltered fetch comment + structure) is included in commit c207292 alongside the new `_flag_matches_target()` dispatch, which is the same concern this plan formalizes.
- `backend/tests/test_feature_flags_eval.py` had 3 pre-existing failures (anyOf operator tests, out of scope for this plan — belongs to a concurrent 14-01/14-04 plan) at the start of execution. By the time Task 2 completed, these had been resolved by concurrent work in the same repo (other plan executors running in parallel on phase 14). Full suite is green (148 passed) as of the final commit; no action was needed from this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend enforcement layer (TGT-02, TGT-03) is complete: create/update validation, bootstrap per-scope dispatch with target fields, and /sdk/evaluate unfiltered fetch.
- Plan 14-03 (SDK clients) can now consume `tenant_id`/`product_id`/`company_id` from bootstrap entries to enforce scope+target client-side.
- Full backend test suite green (148 passed).

---
*Phase: 14-flag-scope-targeting-list-valued-rules*
*Completed: 2026-06-12*

## Self-Check: PASSED

- FOUND: .planning/phases/14-flag-scope-targeting-list-valued-rules/14-02-SUMMARY.md
- FOUND: f6dee94 (Task 1 commit)
- FOUND: c207292 (Task 2 commit)
- FOUND: ce323f7 (Task 3 commit)
