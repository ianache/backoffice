---
phase: 21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini
plan: "03"
subsystem: ui
tags: [vue, typescript, playwright, vitest]
requires:
  - phase: 21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini
    provides: Pre-auth localization runtime
provides:
  - Localized login authentication panel UI
  - Stable authentication error code contract
  - Playwright visual and usability regression coverage
affects: []
tech-stack:
  added: []
  patterns: [Stable internal error code mapping to localization keys]
key-files:
  created: []
  modified:
    - portal/src/views/LoginView.vue
    - portal/src/stores/auth.ts
    - portal/src/stores/auth.test.ts
    - portal/tests/visual/login.spec.ts
    - portal/vite.config.ts
    - portal/src/env.d.ts
key-decisions:
  - "Mapped Keycloak authentication failures to stable internal codes (e.g. AUTH_ERR_INVALID_CREDENTIALS) in the Pinia store, translating them to localized label keys in the component to prevent diagnostic detail leakage."
  - "Utilized Playwright's toHaveJSProperty to inspect reactive properties bound by Vue 3 directly on Material Web Components instead of searching for HTML attributes."
requirements-completed: [LOGIN-LBL-04, LOGIN-LBL-05, LOGIN-LBL-06, LOGIN-LBL-07, LOGIN-LBL-08]
duration: 35min
completed: 2026-06-13
---

# Phase 21 Plan 03: Localization UI Integration Summary

**Localized login view UI, stable error-code mappings, and comprehensive browser E2E test coverage for Spanish/English/fallback/hydration states implemented and verified.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-06-13T23:35:00Z
- **Completed:** 2026-06-13T23:42:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- **Localized UI Elements:** Swapped left auth-panel hardcoded English copy in `LoginView.vue` for `$t('login.<key>')` bindings while keeping fixed logo texts and the entire right-side preview stable.
- **Stable Error Mapping:** Updated `portal/src/stores/auth.ts` to return stable codes (`AUTH_ERR_INVALID_CREDENTIALS` / `AUTH_ERR_FAILED_AFTER_EXCHANGE`) and mapped them in `LoginView.vue` to appropriate label keys, preventing diagnostic details from leaking to the user.
- **E2E Visual Test Suites:** Restructured Playwright E2E tests in `portal/tests/visual/login.spec.ts` to mock the bootstrap API, asserting locale detection (`es_PE`), fallback resolution (English when bootstrap fails), late hydration (retains typed user credentials during lazy updates), and theme snapshots.
- **Vitest Exclusion:** Configured Vitest in `portal/vite.config.ts` to exclude files in `tests/visual/**` so Playwright tests are not incorrectly executed as Vitest unit tests.
- **TypeScript Augmentation:** Extended `portal/src/env.d.ts` with global property definitions for `$t` to ensure clean TypeScript builds (`vue-tsc`).

## Task Commits

1. **Task 1: Swapped left-panel copy with $t bindings and stable auth codes** - `771fc1d` (feat)
2. **Task 2: Restructured E2E test coverage using toHaveJSProperty and mode builds** - `4a59d9c` (test)
3. **Task 3: Added Vitest exclusions and TypeScript definitions** - `3c93ee5` (refactor)

## Files Created/Modified
- `portal/src/views/LoginView.vue` - Implemented localized bindings and error-code lookups.
- `portal/src/stores/auth.ts` - Refactored to return stable login error codes.
- `portal/src/stores/auth.test.ts` - Verified auth store error throwing logic.
- `portal/tests/visual/login.spec.ts` - Added E2E tests for locale fallback, Spanish detection, and late hydration.
- `portal/vite.config.ts` - Excluded E2E tests from unit test runs.
- `portal/src/env.d.ts` - Registered global `$t` typings.

## Decisions Made
- Extracted type augmentation for Vue's global properties to avoid compilation errors and maintain typescript build integrity.
- Used `--mode playwright` when building for E2E tests to correctly bake `VITE_E2E_SKIP_AUTH=true` into the test distribution, preventing unwanted external auth redirects.

## Deviations from Plan
None.

## Issues Encountered
- **TypeScript TS2339:** Resolved compiler error by properly augmenting the `@vue/runtime-core` (and `vue`) module declarations in `env.d.ts`.
- **Vitest running Playwright specs:** Solved by adding a custom `exclude` glob in the Vite configuration.
- **Redirection loop during E2E:** Solved by executing `vite build --mode playwright` so the preview server references the correct auth-skip bundle.

## User Setup Required
None.

## Next Phase Readiness
- All unit, backend integration, and visual E2E tests are 100% green.
- Phase 21 execution is complete.

---
*Phase: 21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini*
*Completed: 2026-06-13*
