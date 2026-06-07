---
phase: 03-user-management
plan: "06"
subsystem: auth
tags: [keycloak, jwt, typescript, tenant-isolation, protocol-mapper]

# Dependency graph
requires:
  - phase: 03-user-management
    provides: BFF users router and auth middleware baseline from plans 01-05
provides:
  - BFF AuthUser.tenantId populated from Keycloak JWT tenant_id claim
  - Dev-mode warning when JWT tenant_id claim is absent
  - docs/KEYCLOAK_SETUP.md with step-by-step protocol mapper configuration
affects:
  - 04-feature-flags
  - Any phase that relies on correct tenant scoping via X-User-Tenant-Id

# Tech tracking
tech-stack:
  added: []
  patterns:
    - JWT claim extraction with multi-spelling fallback (tenant_id / tenantId)
    - Dev-mode console.warn as misconfiguration guard for missing JWT claims

key-files:
  created:
    - docs/KEYCLOAK_SETUP.md
  modified:
    - bff/src/middleware/auth.ts
    - bff/src/routes/users.ts

key-decisions:
  - "Dual claim name fallback: try payload['tenant_id'] then payload['tenantId'] — covers both Keycloak mapper emission styles"
  - "Dev-only console.warn (not production) when tenantId absent — surfaces misconfiguration at request time without spamming production logs"
  - "users.ts simplified to req.user?.tenantId without (req as any) cast — AuthUser interface now fully typed with tenantId"

patterns-established:
  - "Keycloak User Attribute protocol mapper must be configured on both backoffice-portal and backoffice-bff clients"
  - "New users get tenant_id stamped automatically by backend; existing users need manual attribute set in Keycloak"

requirements-completed:
  - USER-01

# Metrics
duration: 15min
completed: 2026-06-07
---

# Phase 03 Plan 06: Close Tenant Isolation Gap (X-User-Tenant-Id) Summary

**BFF auth middleware now extracts tenant_id from Keycloak JWT claims — AuthUser.tenantId typed and forwarded as X-User-Tenant-Id header with dev-mode misconfiguration guard**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-07T14:29:23Z
- **Completed:** 2026-06-07T14:44:00Z
- **Tasks:** 2 auto tasks complete, 1 human-verify checkpoint pending
- **Files modified:** 3 (docs/KEYCLOAK_SETUP.md created, auth.ts modified, users.ts modified)

## Accomplishments
- Created `docs/KEYCLOAK_SETUP.md` with complete step-by-step Keycloak protocol mapper configuration
- Added `tenantId?: string` to `AuthUser` interface — closes the type gap that forced `(req as any)` casts
- `requireAuth` middleware now extracts `tenant_id` (with `tenantId` fallback) from decoded JWT payload
- Dev-mode `console.warn` fires when claim is absent — misconfiguration caught at request time, not silently
- `users.ts` simplified: `req.user?.tenantId` used directly, no more unsafe `any` cast
- TypeScript compiles without errors across all BFF files

## Task Commits

Each task was committed atomically:

1. **Task 1: Document Keycloak protocol mapper setup** - `e9024b1` (docs)
2. **Task 2: Extend AuthUser with tenantId and extract claim in requireAuth** - `5bb525b` (feat)

**Checkpoint 3 (human-verify):** Awaiting Keycloak mapper configuration and runtime tenant isolation verification.

## Files Created/Modified
- `docs/KEYCLOAK_SETUP.md` - Step-by-step Keycloak protocol mapper setup, attribute setting for existing users, verification commands
- `bff/src/middleware/auth.ts` - AuthUser interface extended with tenantId; requireAuth extracts JWT claim with dev-mode warning
- `bff/src/routes/users.ts` - Simplified proxyReq handler — uses typed req.user?.tenantId, no more (req as any) cast

## Decisions Made
- Dual claim name fallback (`tenant_id` then `tenantId`) covers both Keycloak mapper emission styles without configuration assumption
- Dev-only warning (`NODE_ENV !== 'production'`) avoids production log spam while catching misconfiguration in dev/QA
- users.ts cleanup removes the `(req as any)` cast now that AuthUser is properly typed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — TypeScript compiled clean on first attempt. No type conflicts.

## User Setup Required

**Manual Keycloak configuration required before tenant isolation is fully functional.** See `docs/KEYCLOAK_SETUP.md`:
- Configure User Attribute protocol mapper on `backoffice-portal` and `backoffice-bff` clients in Keycloak Apps realm
- Set `tenant_id` attribute on existing test users (new invite-flow users get it automatically)
- Verify: BFF console should NOT print `[warn] X-User-Tenant-Id will be empty` after mapper is active

## Next Phase Readiness
- BFF code changes are complete and type-safe — ready for Phase 4 (Feature Flags) once human checkpoint is approved
- Keycloak protocol mapper must be provisioned before tenant isolation works at runtime
- Human checkpoint (Task 3) confirms mapper is active and cross-tenant isolation verified

---
*Phase: 03-user-management*
*Completed: 2026-06-07*
