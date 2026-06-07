---
phase: 03-user-management
plan: "02"
subsystem: api
tags: [keycloak, bff, proxy, rbac, service-account, typescript]

# Dependency graph
requires:
  - phase: 01-foundation-and-auth
    provides: BFF auth middleware (requireAuth, requireRole), config pattern, JWT verification
  - phase: 02-tenant-management
    provides: Tenant proxy route pattern (tenantsRouter) to mirror exactly
provides:
  - BFF /users/* proxy route guarded by TenantAdmin/TenantOwner roles
  - Keycloak admin service account token cache (module-level singleton)
  - kcAdminFetch helper for admin API calls
  - config.keycloakAdmin extension for service account credentials
affects: [03-user-management, backend-users-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-level singleton token cache with 30s pre-expiry refresh
    - Native Node 18+ fetch for Keycloak token acquisition (no node-fetch)
    - BFF proxy route pattern mirrored from tenantsRouter

key-files:
  created:
    - bff/src/services/keycloak-admin.ts
    - bff/src/routes/users.ts
  modified:
    - bff/src/config/index.ts
    - bff/src/index.ts
    - bff/.env.example

key-decisions:
  - "req.user in auth.ts has no tenantId/attributes — X-User-Tenant-Id will be empty until Keycloak protocol mapper for tenant_id attribute is added"
  - "Native fetch (Node 18+) used in keycloak-admin.ts — no additional HTTP library dependency needed"

patterns-established:
  - "Service account token cache: module-level variables _adminToken/_tokenExpiry, refreshed only when < 30s remain"
  - "kcAdminFetch: wraps token acquisition + base URL construction for admin API calls"

requirements-completed:
  - USER-01
  - USER-02
  - USER-03
  - USER-04
  - USER-05

# Metrics
duration: 2min
completed: 2026-06-07
---

# Phase 03 Plan 02: BFF User Management Layer Summary

**BFF /users proxy route with TenantAdmin/TenantOwner RBAC guard, module-level Keycloak admin token cache, and X-User-Tenant-Id header injection (pending Keycloak protocol mapper)**

## Performance

- **Duration:** ~2 min (implementation) + human checkpoint
- **Started:** 2026-06-07T10:54:06Z
- **Completed:** 2026-06-07
- **Tasks:** 3 of 3 (all complete including human checkpoint)
- **Files modified:** 5

## Accomplishments

- Extended BFF config with `keycloakAdmin.clientId` and `keycloakAdmin.clientSecret` (KEYCLOAK_ADMIN_CLIENT_ID / KEYCLOAK_ADMIN_CLIENT_SECRET)
- Created singleton token cache service (`keycloak-admin.ts`) exporting `getAdminToken` and `kcAdminFetch` using native Node 18+ fetch
- Created `/users` proxy route guarded by `requireRole('TenantAdmin', 'TenantOwner')` with X-User-Sub, X-User-Roles, X-User-Tenant-Id header injection
- Mounted `usersRouter` at `/users` in `index.ts` following the established tenantsRouter pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend BFF config with Keycloak admin credentials** - `282567d` (feat)
2. **Task 2: Keycloak Admin token service + users proxy route + mount** - `7960b8c` (feat)
3. **Task 3: Checkpoint — provision backoffice-admin-svc Keycloak client** - COMPLETE (human action)

## Files Created/Modified

- `bff/src/config/index.ts` - Added `keycloakAdmin` block with `clientId` and `clientSecret`
- `bff/.env.example` - Added `KEYCLOAK_ADMIN_CLIENT_ID` and `KEYCLOAK_ADMIN_CLIENT_SECRET` placeholder entries
- `bff/src/services/keycloak-admin.ts` - NEW: module-level singleton token cache, exports `getAdminToken` and `kcAdminFetch`
- `bff/src/routes/users.ts` - NEW: Express router with `requireAuth + requireRole(TenantAdmin, TenantOwner)` + proxy to backend
- `bff/src/index.ts` - Added `usersRouter` import and `app.use('/users', usersRouter)` mount

## Decisions Made

- `req.user` in `auth.ts` (`AuthUser` interface) exposes only `{ sub, email, name, roles }` — no `tenantId` or `attributes`. The `X-User-Tenant-Id` header will be empty string until a Keycloak protocol mapper is configured to embed the tenant_id attribute into JWT claims. This is an expected deferral noted with a comment in the route.
- Native `fetch` (Node 18+ built-in) used in `keycloak-admin.ts` — consistent with project's no-extra-dependencies approach, no node-fetch or axios added.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Auth Gates

**Checkpoint Task 3: Keycloak Service Account Provisioning**
- **Task:** Provision `backoffice-admin-svc` client in QA Keycloak
- **What was needed:** Keycloak Admin Console access to create confidential client with service account enabled; assign `manage-users`, `view-users`, `view-realm` roles from `realm-management` client
- **Outcome:** COMPLETE — client created, secret copied, bff/.env updated with `KEYCLOAK_ADMIN_CLIENT_ID=backoffice-admin-svc` and `KEYCLOAK_ADMIN_CLIENT_SECRET`

## Next Phase Readiness

- BFF layer fully complete with service account provisioned
- Backend `/users` routes implemented in plan 03-01 — integration ready
- Future: Keycloak protocol mapper for `tenant_id` attribute needed to populate `X-User-Tenant-Id` header

---
*Phase: 03-user-management*
*Completed: 2026-06-07*
