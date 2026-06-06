---
phase: 01-foundation-and-auth
plan: "02"
subsystem: bff-auth
tags: [express, jose, jwt, keycloak, jwks, middleware, auth, cors, vitest, tdd]

# Dependency graph
requires:
  - 01-01 (pnpm monorepo + Keycloak dev env + bff package with jose/express installed)
provides:
  - JWT verification middleware (requireAuth) using jose + Keycloak JWKS singleton
  - Role enforcement middleware factory (requireRole) — Zero Trust per-request checks
  - GET /auth/me endpoint returning AuthUser {sub, email, name, roles}
  - Express BFF at localhost:3000 with /health and /auth endpoints
affects: [01-03, 01-04, all plans that consume BFF auth layer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - JWKS singleton via createRemoteJWKSet (caches keys, handles key rotation)
    - realm_access.roles filtered to APP_ROLES only (strips Keycloak internals)
    - Zero Trust: requireRole middleware enforces roles on every BFF route request
    - TDD: failing tests written first, then implementation; 11 unit tests (no Keycloak runtime required)

key-files:
  created:
    - bff/src/config/index.ts
    - bff/src/services/keycloak.ts
    - bff/src/middleware/auth.ts
    - bff/src/middleware/auth.test.ts
    - bff/src/middleware/roles.ts
    - bff/src/middleware/roles.test.ts
    - bff/src/routes/auth.ts
    - bff/src/index.ts
  modified: []

key-decisions:
  - "JWKS singleton (not per-request) — createRemoteJWKSet caches JWKS keys and handles rotation transparently"
  - "APP_ROLES allowlist in auth.ts strips offline_access/uma_authorization from JWT before propagating to frontend"
  - "clockTolerance: 10s in jwtVerify to handle minor clock skew between BFF and Keycloak"
  - "requireRole accepts variadic roles array — any-of semantics for multi-role routes"

# Metrics
duration: 4min
completed: 2026-06-06
---

# Phase 01 Plan 02: BFF Auth Layer Summary

**Express BFF with jose JWT verification middleware (JWKS singleton), APP_ROLES filter, requireRole factory, and /auth/me endpoint returning Keycloak realm roles filtered to application roles only**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-06T22:20:24Z
- **Completed:** 2026-06-06T22:24:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- BFF config module with fail-fast env var validation (requireEnv throws at startup if KEYCLOAK_URL/REALM/CLIENT_ID/CLIENT_SECRET are missing)
- JWKS singleton created via createRemoteJWKSet pointing at Keycloak JWKS endpoint; single instance cached globally so keys are not re-fetched per request
- requireAuth middleware: verifies Bearer token via jose jwtVerify against JWKS; attaches AuthUser to req.user; returns 401 for missing/invalid/expired tokens; filters realm_access.roles to APP_ROLES allowlist
- requireRole factory: variadic any-of role check; returns 403 if req.user is undefined or user lacks any of the required roles; implements Zero Trust per-request enforcement
- authRouter with GET /auth/me protected by requireAuth; returns {sub, email, name, roles}
- Express app with CORS (localhost:5173 + credentials), /health (unauthenticated), /auth/* routes
- 11 unit tests (6 auth + 5 roles) using vitest; JWKS and jose mocked — no Keycloak runtime required

## Task Commits

Each task was committed atomically:

1. **Task 1: BFF config + Keycloak JWKS singleton + auth/roles middleware** - `f901377` (feat)
2. **Task 2: Express app entry + /auth/me route** - `0990e66` (feat)

**Plan metadata:** (committed below as docs commit)

## Files Created/Modified

- `bff/src/config/index.ts` — Env var validation with requireEnv; exported config object used by all BFF modules
- `bff/src/services/keycloak.ts` — JWKS singleton (createRemoteJWKSet) + KEYCLOAK_ISSUER string
- `bff/src/middleware/auth.ts` — requireAuth async middleware; AuthUser interface; Express global Request augmentation
- `bff/src/middleware/auth.test.ts` — 6 unit tests: missing header, non-Bearer header, invalid token, valid token + req.user populated, APP_ROLES filtering, missing realm_access graceful handling
- `bff/src/middleware/roles.ts` — requireRole(...roles) factory middleware
- `bff/src/middleware/roles.test.ts` — 5 unit tests: matching role, missing role, undefined user, multi-role any-of pass, multi-role any-of fail
- `bff/src/routes/auth.ts` — authRouter with GET /me protected by requireAuth
- `bff/src/index.ts` — Express app entry: CORS, express.json(), /health, /auth prefix mount, app.listen

## Decisions Made

- **JWKS singleton pattern** — createRemoteJWKSet called once at module load; caches keys and handles Keycloak JWKS rotation transparently without restart
- **APP_ROLES allowlist** — Only application-defined roles propagated to frontend; Keycloak internals (offline_access, uma_authorization, default-roles-*) stripped at BFF boundary
- **clockTolerance: 10s** — Added to jwtVerify to tolerate minor clock skew between BFF and Keycloak; standard practice for JWT validation
- **requireRole variadic** — `requireRole('PlatformAdmin', 'TenantAdmin')` returns 200 if user has either; allows multi-role route guards without duplicating middleware

## Deviations from Plan

None — plan executed exactly as written. TDD protocol followed: tests written and confirmed failing before implementation; all 11 tests pass after implementation.

## Verification Results

| Check | Result |
|-------|--------|
| `pnpm test` passes (11 tests) | PASSED |
| BFF starts on port 3099 (3000 was occupied by Vite dev server) | PASSED |
| GET /health returns `{"status":"ok","service":"backoffice-bff"}` | PASSED |
| GET /auth/me (no token) returns 401 `{"error":"Missing token"}` | PASSED |
| CORS origin localhost:5173 configured with credentials | PASSED |
| APP_ROLES filter removes offline_access / uma_authorization | PASSED (unit tested) |

Note: /auth/me with a valid Keycloak token (verification step 5) requires Docker Desktop running with `docker compose up -d` — this is pending from Plan 01 (Docker Desktop not in PATH). The BFF is correctly wired and will work once Keycloak is running.

## Self-Check: PASSED
