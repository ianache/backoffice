---
phase: 01-foundation-and-auth
plan: "03"
subsystem: auth
tags: [vue3, keycloak-js, pinia, pinia-plugin-persistedstate, axios, vue-router, vite, typescript, oidc]

requires:
  - phase: 01-01
    provides: Keycloak realm/client configured, pnpm monorepo workspace, portal package.json with dependencies installed
  - phase: 01-02
    provides: BFF /auth/me endpoint and JWT middleware that portal will call via api.ts

provides:
  - keycloak-js singleton with check-sso OIDC flow (portal/src/plugins/keycloak.ts)
  - Pinia auth store with init(), login(), logout(), hasRole() and sessionStorage persistence (portal/src/stores/auth.ts)
  - Axios API service with automatic token refresh interceptor (portal/src/services/api.ts)
  - Vue Router with beforeEach auth guard enforcing requiresAuth and roles route meta (portal/src/router/index.ts)
  - Silent check-sso iframe page (portal/public/silent-check-sso.html)
  - Three portal views: LoginView, UnauthorizedView, DashboardView
  - main.ts wired with await authStore.init() before app.mount() preventing auth race condition

affects: [02-tenant-management, 03-feature-flags, 04-microfrontend]

tech-stack:
  added: [keycloak-js@26, pinia@2, pinia-plugin-persistedstate@4, axios@1, vue-router@4, vite@5, @vitejs/plugin-vue]
  patterns:
    - check-sso onLoad (not login-required) for non-forced redirect behavior
    - await authStore.init() before app.mount() — prevents unauthenticated content flash
    - sessionStorage persistence (not localStorage) for XSS mitigation
    - Keycloak singleton pattern — single instance shared across plugins, stores, services
    - return-value navigation guards (not next() callback) for Vue Router 4

key-files:
  created:
    - portal/src/plugins/keycloak.ts
    - portal/src/stores/auth.ts
    - portal/src/services/api.ts
    - portal/src/router/index.ts
    - portal/src/views/LoginView.vue
    - portal/src/views/UnauthorizedView.vue
    - portal/src/views/DashboardView.vue
    - portal/src/App.vue
    - portal/src/main.ts
    - portal/src/env.d.ts
    - portal/public/silent-check-sso.html
    - portal/vite.config.ts
  modified: []

key-decisions:
  - "pick (not paths) for pinia-plugin-persistedstate v4 — API changed from v3; pick selects state keys to persist"
  - "env.d.ts with vite/client and pinia-plugin-persistedstate triple-slash references to activate import.meta.env types and persist option type augmentation"
  - "sessionStorage over localStorage for auth token persistence — XSS risk mitigation per RESEARCH.md anti-patterns"

patterns-established:
  - "Auth store init pattern: await authStore.init() in main.ts before app.mount() prevents auth guard race conditions"
  - "Keycloak singleton: single keycloak instance imported by stores/auth.ts and services/api.ts — never create multiple instances"
  - "Token refresh: 30s interval in auth store + updateToken(30) interceptor in api.ts ensure tokens stay fresh"
  - "Role guard: router beforeEach checks meta.roles array with some() — user needs at least one matching role"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03]

duration: 4min
completed: 2026-06-06
---

# Phase 01 Plan 03: Vue Portal Auth Shell Summary

**Vue 3 portal with Keycloak OIDC check-sso flow, Pinia auth store persisted to sessionStorage, Axios token-refresh interceptor, and Vue Router role guards protecting /dashboard**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-06T22:26:17Z
- **Completed:** 2026-06-06T22:30:08Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Keycloak OIDC integration using check-sso (not login-required) so public routes don't force redirect
- Pinia auth store with token/user/roles persisted to sessionStorage and 30-second refresh interval preventing mid-session expiry
- Axios API service with request interceptor calling updateToken(30) and response interceptor redirecting 401s to Keycloak login
- Vue Router beforeEach guard: unauthenticated users on requiresAuth routes trigger keycloak.login(), role mismatches redirect to /unauthorized
- main.ts wires await authStore.init() before app.mount() eliminating auth-state race condition on page load

## Task Commits

1. **Task 1: Keycloak plugin, Pinia auth store, and Axios API service** - `00a3a85` (feat)
2. **Task 2: Vue Router guards, views, and main.ts wiring** - `b0e9034` (feat)

**Plan metadata:** _(to be added in final commit)_

## Files Created/Modified

- `portal/src/plugins/keycloak.ts` - Keycloak singleton reading VITE_* env vars
- `portal/src/stores/auth.ts` - Auth store: isAuthenticated, token, user, roles, isLoading + init/login/logout/hasRole
- `portal/src/services/api.ts` - Axios instance: token refresh request interceptor + 401 response redirector
- `portal/src/router/index.ts` - Vue Router with 4 routes and beforeEach auth+role guard
- `portal/src/views/LoginView.vue` - Auto-calls authStore.login() on mount if not authenticated
- `portal/src/views/UnauthorizedView.vue` - Access denied page with user info and logout button
- `portal/src/views/DashboardView.vue` - Dashboard showing user email, name, and roles
- `portal/src/App.vue` - Root shell with router-view only
- `portal/src/main.ts` - App entry: Pinia + persistedstate + router + await authStore.init() before mount
- `portal/src/env.d.ts` - Triple-slash refs for vite/client and pinia-plugin-persistedstate types
- `portal/public/silent-check-sso.html` - Required iframe page for keycloak-js check-sso
- `portal/vite.config.ts` - Vite config with @vitejs/plugin-vue and @/* alias

## Decisions Made

- **pick not paths** for pinia-plugin-persistedstate v4: the API changed from v3; `paths` is a v3 option, `pick` is the v4 equivalent. Discovered during TypeScript type check.
- **env.d.ts triple-slash references**: `@vue/tsconfig/tsconfig.dom.json` sets `"types": []` (intentionally empty), so `import.meta.env` and `persist` plugin types require explicit references in env.d.ts.
- **sessionStorage over localStorage**: Per RESEARCH.md anti-patterns — localStorage survives browser close and is accessible to any JS on the page, making it higher XSS risk for auth tokens.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pinia-plugin-persistedstate v4 API: paths -> pick**
- **Found during:** Task 1 (auth store creation)
- **Issue:** Plan specified `paths: [...]` in persist config but pinia-plugin-persistedstate v4 renamed this property to `pick`. TypeScript error: `'paths' does not exist in type 'PersistenceOptions'`
- **Fix:** Changed `paths` to `pick` in the persist configuration of auth.ts
- **Files modified:** `portal/src/stores/auth.ts`
- **Verification:** `vue-tsc --noEmit` passes with no errors
- **Committed in:** `00a3a85` (Task 1 commit)

**2. [Rule 3 - Blocking] Added env.d.ts for import.meta.env and persist type augmentation**
- **Found during:** Task 1 (TypeScript type check)
- **Issue:** `@vue/tsconfig/tsconfig.dom.json` sets `"types": []`, so `import.meta.env` (vite/client) and `persist` option (pinia-plugin-persistedstate module augmentation) are not recognized — TypeScript errors on all three files using VITE_* env vars
- **Fix:** Created `portal/src/env.d.ts` with `/// <reference types="vite/client" />` and `/// <reference types="pinia-plugin-persistedstate" />`
- **Files modified:** `portal/src/env.d.ts` (created)
- **Verification:** `vue-tsc --noEmit` passes cleanly after adding env.d.ts
- **Committed in:** `00a3a85` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 API version mismatch, 1 blocking type reference)
**Impact on plan:** Both fixes necessary for TypeScript correctness. No scope creep. env.d.ts is standard Vite project practice.

## Issues Encountered

- TypeScript errors on first `vue-tsc` run due to (a) pinia-plugin-persistedstate v4 API change and (b) missing type references. Both resolved in Task 1 before commit.

## User Setup Required

None — `.env` already exists with correct values from plan 01-01. To verify full auth flow, Docker Desktop must be running with `docker compose up -d` (Keycloak at localhost:8080).

## Next Phase Readiness

- Portal runs at localhost:5173 with full OIDC login flow ready
- Auth store provides isAuthenticated, roles, and hasRole() for all future views
- api.ts is the single Axios instance all BFF calls must use — pattern established
- Router pattern established: add `meta: { requiresAuth: true, roles: ['PlatformAdmin'] }` to any protected route
- Blocker: Keycloak runtime requires Docker Desktop running — deferred to user

---
*Phase: 01-foundation-and-auth*
*Completed: 2026-06-06*
