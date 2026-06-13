---
phase: 21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini
plan: "02"
subsystem: ui
tags: [vue, typescript, vitest, html]
requires:
  - phase: 21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini
    provides: Eager login namespace seed migration
provides:
  - Pre-auth localization runtime
  - Singleton LabelClient wrapper useLoginLabels
  - Fallback-aware translation plugin with 1-second mount deadline
  - Center-spinner accessible HTML loader
affects: [21-03]
tech-stack:
  added: []
  patterns: [Singleton composable for eager pre-auth namespace resolution]
key-files:
  created:
    - portal/src/composables/useLoginLabels.ts
    - portal/src/composables/useLoginLabels.test.ts
  modified:
    - sdk/sdk-js/src/labels.ts
    - sdk/sdk-js/tests/labels.test.ts
    - portal/src/main.ts
    - portal/index.html
    - portal/src/env.d.ts
key-decisions:
  - "Raced the label initialization promise against a 1-second deadline and resolved it fail-open using catalog fallbacks to avoid blocking authentication UI in case of BFF/SDK failures."
patterns-established:
  - "Getter-based lazy singleton references for third-party client wrappers inside Vue composables."
requirements-completed: [LOGIN-LBL-02, LOGIN-LBL-03, LOGIN-LBL-04, LOGIN-LBL-06, LOGIN-LBL-07, LOGIN-LBL-08]
duration: 25min
completed: 2026-06-13
---

# Phase 21 Plan 02: Pre-auth LabelClient runtime Summary

**Pre-auth LabelClient runtime with 1-second mount deadline, fallback resolver, neutral CSS spinner, and comprehensive unit test coverage implemented and verified**

## Performance

- **Duration:** 25 min
- **Started:** 2026-06-13T23:28:40Z
- **Completed:** 2026-06-13T23:32:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Extended the SDK `createLabelPlugin` factory with an optional `fallbackResolver` callback to intercept cache-miss `[sys.key]` translations.
- Built the `useLoginLabels` singleton composable featuring case-insensitive browser locale mapping, a bounded 1-second startup wait, and local catalog fallbacks.
- Wired up `useLoginLabels` asynchronously inside `portal/src/main.ts` prior to authentication checks.
- Created a neutral, full-viewport CSS spinner inside `portal/index.html` with `aria-label="Loading login"`.
- Wrote 7 comprehensive unit tests in `useLoginLabels.test.ts` verifying deadline, locale detection, fallback resolution, and late success rendering.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend the SDK Vue plugin with an optional fallback resolver** - `44afa78` (feat)
2. **Task 2: Implement the singleton login-label runtime and unit tests** - `60d617d` (feat)
3. **Task 3: Wire pre-auth label startup and the neutral pre-mount loader** - `140817f` (feat)

## Files Created/Modified
- `portal/src/composables/useLoginLabels.ts` - Singleton login-label composable
- `portal/src/composables/useLoginLabels.test.ts` - Unit test suite for login-label composable
- `sdk/sdk-js/src/labels.ts` - Extended Vue plugin with optional fallback resolver
- `sdk/sdk-js/tests/labels.test.ts` - Vitest assertions for plugin resolver behavior
- `portal/src/main.ts` - Application entrypoint loading labels asynchronously
- `portal/index.html` - Neutral pre-mount CSS loader
- `portal/src/env.d.ts` - Type declarations for VITE_BO_* environment keys

## Decisions Made
- Raced the label initialization promise against a 1-second deadline and resolved it fail-open using catalog fallbacks to avoid blocking authentication UI in case of BFF/SDK failures.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- TypeScript error TS1016 (required parameter following optional parameter) was resolved by changing `variables?` to `variables: Record<string, unknown> | undefined` in `fallbackResolver` signature.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pre-auth localization runtime completes and builds successfully.
- Ready for plan 21-03: LoginView localization.

---
*Phase: 21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini*
*Completed: 2026-06-13*
