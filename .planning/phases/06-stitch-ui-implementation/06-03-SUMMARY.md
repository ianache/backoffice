---
phase: 06-stitch-ui-implementation
plan: "03"
subsystem: ui

tags: [vue, material-web, stitch, login, playwright, visual-regression]

requires:
  - phase: 06-02
    provides: AuthLayout.vue and StitchButton/StitchTextField components used in LoginView
provides:
  - Stitch-styled Login page (LoginView.vue) with email/password form using Material Web components
  - Visual regression test suite for Login page (light, dark, and error states)
affects: [06-04, testing, ui]

tech-stack:
  added: []
  patterns:
    - "Custom login form using Keycloak Resource Owner Password Grant for credential-based auth"
    - "Visual regression baseline with Playwright toHaveScreenshot across light/dark themes"

key-files:
  created:
    - portal/tests/visual/login.spec.ts
    - portal/tests/visual/login.spec.ts-snapshots/login-light-chromium-win32.png
    - portal/tests/visual/login.spec.ts-snapshots/login-dark-chromium-win32.png
    - portal/tests/visual/login.spec.ts-snapshots/login-error-chromium-win32.png
  modified:
    - portal/src/views/LoginView.vue
    - portal/src/stores/auth.ts

key-decisions:
  - "Custom Vue login form uses Keycloak ROPC grant (token endpoint) instead of redirect-based login — enables portal-native UX while preserving Keycloak auth"
  - "Visual regression baselines captured for light mode, dark mode, and error state — maxDiffPixelRatio 0.1 tolerance"

patterns-established:
  - "StitchTextField + StitchButton are the standard input/action primitives for all portal forms"
  - "Error display uses bg-error-container / text-on-error-container tokens with md-icon for inline errors"

requirements-completed: [UI-03]

duration: 20min
completed: 2026-06-06
---

# Phase 06 Plan 03: Stitch Login Page Summary

**Stitch-styled login form with md-outlined-text-field / md-filled-button components, Keycloak ROPC credential flow, and Playwright visual baselines for light, dark, and error states**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-06T21:45:00Z
- **Completed:** 2026-06-06T22:10:00Z
- **Tasks:** 2
- **Files modified:** 4 (LoginView.vue, auth.ts, login.spec.ts + 3 snapshots)

## Accomplishments

- Redesigned LoginView.vue using StitchTextField and StitchButton, replacing ad-hoc HTML inputs
- Added `loginWithCredentials` to the auth store via Keycloak ROPC token endpoint for form-based auth
- Created Playwright visual regression tests for Login covering light mode, dark mode, and error state — all 3 tests pass

## Task Commits

1. **Task 1: Redesign LoginView.vue** - `ef12cf9` (feat)
2. **Task 2: Add visual regression tests for Login** - `a0e8fe8` (test)

## Files Created/Modified

- `portal/src/views/LoginView.vue` — Stitch-styled login form with StitchTextField, StitchButton, error display, loading state
- `portal/src/stores/auth.ts` — Added `loginWithCredentials` using Keycloak ROPC grant (token endpoint)
- `portal/tests/visual/login.spec.ts` — Playwright visual tests: light mode, dark mode, error state
- `portal/tests/visual/login.spec.ts-snapshots/login-light-chromium-win32.png` — baseline light mode
- `portal/tests/visual/login.spec.ts-snapshots/login-dark-chromium-win32.png` — baseline dark mode
- `portal/tests/visual/login.spec.ts-snapshots/login-error-chromium-win32.png` — baseline error state

## Decisions Made

- Used Keycloak ROPC (Resource Owner Password Grant) for custom form-based login rather than Keycloak-hosted login page — preserves portal theming while reusing the existing QA Keycloak server
- Visual snapshot tolerance set to `maxDiffPixelRatio: 0.1` to allow minor rendering differences across test runs without false failures

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Task 2 test file (`login.spec.ts`) was created in a prior partial run but not committed; the dark mode snapshot existed as well. Completed the test run to generate missing light and error snapshots, then committed all four files together.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Login page is complete and visually tested; ready for 06-04 (internal pages / navigation shell)
- Visual baseline snapshots are committed — future UI changes will flag regressions automatically

---
*Phase: 06-stitch-ui-implementation*
*Completed: 2026-06-06*
