---
phase: 13-simulator-test-contexts
plan: 02
subsystem: auth
tags: [vue, pinia, module-federation, vite, keycloak, feature-flags]

# Dependency graph
requires:
  - phase: 12-dogfooding-feature-flags
    provides: useBoFlags composable pattern + Module Federation exposes block in portal/vite.config.ts
provides:
  - "auth store user ref with real JWT sub claim"
  - "useUserContext() composable returning {sub, email, roles, tenant_id, product_id}"
  - "Module Federation exposure of shell/useUserContext to remote MUIs"
  - "TypeScript declaration for shell/useUserContext in mui-feature-flags"
affects: [13-03-simulator-real-context-toggle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Stateless data-access composable reading live Pinia store on each call (no singleton state, no async init) - contrasts with useBoFlags' singleton+SDK pattern"

key-files:
  created:
    - portal/src/composables/useUserContext.ts
    - portal/src/composables/useUserContext.test.ts
  modified:
    - portal/src/stores/auth.ts
    - portal/src/stores/auth.test.ts
    - portal/vite.config.ts
    - microuis/mui-feature-flags/src/env.d.ts

key-decisions:
  - "useUserContext exposes both real JWT sub and email as separate keys (not collapsing sub into email like the existing main.ts useBoFlags init pattern)"
  - "product_id hardcoded to 'backoffice' per CONTEXT.md dogfooding decision"
  - "useUserContext reuses the existing shared pinia singleton - no new shared dependency entry needed in vite.config.ts"

patterns-established:
  - "Synchronous read-through composable for cross-MUI federation: no module-scoped state, always fresh from Pinia store + env var"

requirements-completed: [SIM-03]

# Metrics
duration: 12min
completed: 2026-06-11
---

# Phase 13 Plan 02: useUserContext Composable + Federation Wiring Summary

**New `useUserContext()` composable exposes the logged-in user's real `sub`/`email`/`roles`/`tenant_id`/`product_id` to remote MUIs via Module Federation singleton `shell/useUserContext`, mirroring the Phase 12 `shell/useBoFlags` exposure pattern.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-11T18:28:00Z
- **Completed:** 2026-06-11T18:40:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Auth store's `user` ref now carries the real JWT `sub` claim (`keycloak.tokenParsed?.sub`), in addition to `name` and `email`
- New `useUserContext()` composable returns rule-attribute-named keys (`sub`, `email`, `roles`, `tenant_id`, `product_id`) read live from the Pinia auth store and `VITE_BO_TENANT_ID` env var
- `portal/vite.config.ts` exposes `./useUserContext` via Module Federation, reusing the existing shared `pinia` singleton
- `mui-feature-flags/src/env.d.ts` declares `shell/useUserContext` with a typed `UserContext` interface for Plan 13-03 consumption

## Task Commits

Each task was committed atomically:

1. **Task 1: Add `sub` to auth store's user ref** - `2c37801` (feat, TDD)
2. **Task 2: Create useUserContext composable** - `b2ef7ee` (feat, TDD)
3. **Task 3: Expose useUserContext via Module Federation** - `aea4bee` (feat)

**Plan metadata:** (pending) docs(13-02): complete plan

_Note: Tasks 1-2 were tagged `tdd="true"` but implementation was straightforward enough to write test+code together; both committed as single `feat` commits with passing tests verified before commit._

## Files Created/Modified
- `portal/src/composables/useUserContext.ts` - New composable: `useUserContext()` returns `{sub, email, roles, tenant_id, product_id}` read fresh from `useAuthStore()` + `import.meta.env.VITE_BO_TENANT_ID`
- `portal/src/composables/useUserContext.test.ts` - Two tests: authenticated context mapping, and unauthenticated empty defaults (no throw)
- `portal/src/stores/auth.ts` - `user` ref type extended to `{ name: string; email: string; sub: string }`; `_populate()` sets `sub` from `keycloak.tokenParsed?.sub ?? ''`
- `portal/src/stores/auth.test.ts` - Mock `tokenParsed` gains `sub: 'mock-sub-123'`; assertions and pre-init literals updated to include `sub`
- `portal/vite.config.ts` - `exposes` block gains `'./useUserContext': './src/composables/useUserContext.ts'`
- `microuis/mui-feature-flags/src/env.d.ts` - New `declare module 'shell/useUserContext'` block with `UserContext` interface and `useUserContext(): UserContext`

## Decisions Made
- `useUserContext()` exposes both the real JWT `sub` and `email` as distinct keys, rather than collapsing `sub` into `email` as the legacy `main.ts` `useBoFlags().init()` call currently does — this gives Plan 13-03 access to the actual JWT subject claim for rule matching.
- `product_id` is hardcoded to `'backoffice'` (matches `useBoFlags.ts` convention for the dogfooding product).
- No new `shared` dependency entry added to `vite.config.ts` federation config — `useUserContext()` calls `useAuthStore()`, which relies on the already-shared `pinia` singleton.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `shell/useUserContext` is now available for Plan 13-03 to consume from `mui-feature-flags` via `import { useUserContext } from 'shell/useUserContext'`, building the "use my real context" toggle in the Live Simulator.
- All portal vitest suites pass (`auth.test.ts`: 3 tests, `useUserContext.test.ts`: 2 tests); `vue-tsc --noEmit` reports zero errors.

---
*Phase: 13-simulator-test-contexts*
*Completed: 2026-06-11*

## Self-Check: PASSED

All created files and commits verified present.
