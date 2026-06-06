---
phase: 01-foundation-and-auth
plan: "01"
subsystem: infra
tags: [pnpm, monorepo, keycloak, docker, postgresql, vue3, pinia, express, jose, keycloak-js]

# Dependency graph
requires: []
provides:
  - pnpm monorepo workspace with bff, portal, microuis/mui-security packages
  - Docker Compose environment (Keycloak 26.0.5 + PostgreSQL 16)
  - Keycloak backoffice realm with 9 roles and seed PlatformAdmin user
  - Environment variable templates for all three packages
affects: [01-02, 01-03, 01-04, all subsequent plans in phase 01]

# Tech tracking
tech-stack:
  added: [pnpm@11.5.2, express@4.22.2, jose@5.10.0, keycloak-js@26.2.4, vue@3.5.35, pinia@2.3.1, vue-router@4.6.4, pinia-plugin-persistedstate@4.7.1, vite@5.4.21, typescript@5.9.3, tsx@4.22.4, axios@1.17.0]
  patterns:
    - pnpm workspaces monorepo (bff + portal + microuis/*)
    - Keycloak realm-export.json auto-import via volume mount on start-dev

key-files:
  created:
    - pnpm-workspace.yaml
    - package.json
    - pnpm-lock.yaml
    - bff/package.json
    - bff/tsconfig.json
    - portal/package.json
    - portal/tsconfig.json
    - microuis/mui-security/package.json
    - microuis/mui-security/tsconfig.json
    - docker-compose.yml
    - keycloak/realm-export.json
    - .gitignore
    - .env.example
    - bff/.env.example
    - portal/.env.example
  modified: []

key-decisions:
  - "pnpm workspaces selected for monorepo (bff, portal, microuis/*) with single root install"
  - "Keycloak realm roles (not client roles) used for PlatformAdmin et al. — realm_access.roles simplifies JWT extraction on BFF"
  - "lightweightAccessTokenEnabled=false on both clients prevents silent role stripping (Keycloak 24+ pitfall)"
  - "backoffice-bff client secret hardcoded in realm-export for dev convenience; must be rotated in production"
  - "pnpm build scripts for esbuild and vue-demi approved in pnpm-workspace.yaml (required for Vite/Vue)"

patterns-established:
  - "Monorepo: pnpm workspaces with three top-level packages; run pnpm install at root"
  - "Keycloak dev: start-dev --import-realm reads from /opt/keycloak/data/import volume mount"
  - "Env vars: .env.example committed; actual .env files excluded via .gitignore"

requirements-completed: [AUTH-01]

# Metrics
duration: 7min
completed: 2026-06-06
---

# Phase 01 Plan 01: Monorepo Bootstrap & Keycloak Dev Environment Summary

**pnpm monorepo with bff/portal/mui-security packages and Keycloak 26.0.5 Docker dev environment pre-configured with backoffice realm, 9 realm roles, PKCE frontend client, and seed PlatformAdmin user**

## Performance

- **Duration:** 7 min
- **Started:** 2026-06-06T22:10:20Z
- **Completed:** 2026-06-06T22:17:01Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- pnpm monorepo initialized with three workspace packages (@backoffice/bff, @backoffice/portal, @backoffice/mui-security); all 216 packages installed successfully
- Docker Compose file created for Keycloak 26.0.5 + PostgreSQL 16 with realm auto-import via volume mount; realm-export.json defines the complete backoffice realm
- Keycloak realm configured with 9 realm roles, backoffice-frontend (public PKCE) and backoffice-bff (confidential) clients, seed user admin@backoffice.dev / Admin1234! with PlatformAdmin role assigned
- Environment variable templates documented for root, bff, and portal packages; .gitignore prevents .env files from being committed

## Task Commits

Each task was committed atomically:

1. **Task 1: Initialize pnpm monorepo workspace with three packages** - `ea622ba` (chore)
2. **Task 2: Docker Compose + Keycloak realm with seed PlatformAdmin user** - `5ec2779` (chore)

**Plan metadata:** (committed below as docs commit)

## Files Created/Modified
- `package.json` - Root monorepo package (name: backoffice-platform, dev/build/test/lint workspace scripts)
- `pnpm-workspace.yaml` - Workspace definition (bff, portal, microuis/*) + approved build scripts for esbuild/vue-demi
- `pnpm-lock.yaml` - Lockfile from successful pnpm install (287 packages resolved)
- `bff/package.json` - @backoffice/bff: express, jose, cors, dotenv + tsx/typescript dev deps
- `bff/tsconfig.json` - TypeScript config: ESNext module, bundler resolution, strict mode
- `portal/package.json` - @backoffice/portal: Vue 3, Pinia, keycloak-js, vue-router, axios, pinia-plugin-persistedstate
- `portal/tsconfig.json` - Vue tsconfig with @/* path alias
- `microuis/mui-security/package.json` - @backoffice/mui-security: auth micro-frontend (Vite library mode)
- `microuis/mui-security/tsconfig.json` - Same as portal tsconfig
- `docker-compose.yml` - Keycloak 26.0.5 + PostgreSQL 16 with realm volume mount and healthcheck
- `keycloak/realm-export.json` - Complete backoffice realm: 9 roles, 2 clients, 1 seed user
- `.gitignore` - Excludes node_modules/, dist/, .env, *.local
- `.env.example` - Root env (Keycloak admin credentials)
- `bff/.env.example` - BFF env (PORT, KEYCLOAK_URL, REALM, CLIENT_ID, CLIENT_SECRET, FRONTEND_URL)
- `portal/.env.example` - Portal env (VITE_KEYCLOAK_URL, REALM, CLIENT_ID, VITE_BFF_URL)

## Decisions Made
- **pnpm workspaces** selected for monorepo management with single `pnpm install` at root
- **Realm roles** (not client roles) used for all application roles — `realm_access.roles` is simpler to extract in BFF JWT validation and consistent across clients
- **`lightweightAccessTokenEnabled: false`** explicitly set on both Keycloak clients to prevent the Keycloak 24+ silent role stripping pitfall documented in RESEARCH.md
- **Hardcoded BFF client secret** (`backoffice-bff-secret`) in realm-export for dev convenience — must be rotated in production via Keycloak admin
- **esbuild and vue-demi build scripts approved** in pnpm-workspace.yaml (pnpm 11.x security policy requires explicit approval)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Approved pnpm build scripts for esbuild and vue-demi**
- **Found during:** Task 1 (pnpm install)
- **Issue:** pnpm 11.x security policy requires explicit approval of packages with install scripts. esbuild (needed by Vite) and vue-demi (needed by Pinia) were blocked, causing install failure with exit code 1
- **Fix:** Added `allowBuilds: { esbuild: true, vue-demi: true }` to pnpm-workspace.yaml (pnpm auto-added the `allowBuilds` section with placeholders; we set both to true)
- **Files modified:** pnpm-workspace.yaml
- **Verification:** Re-ran `pnpm install` — completed successfully with all 216 packages added
- **Committed in:** ea622ba (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for pnpm 11.x compatibility. No scope creep. pnpm-workspace.yaml is a valid location for build script allowlist per pnpm documentation.

## Issues Encountered

**Docker Desktop not available in PATH:** The Task 2 automated verification (`docker compose up -d` + curl check) could not be executed because Docker Desktop is installed but not running and `docker` is not in PATH in this shell session. All Docker/Keycloak files are correctly created and committed. The user must start Docker Desktop and run `docker compose up -d` manually to complete the runtime verification.

See **User Setup Required** section below.

## User Setup Required

To complete the Task 2 verification and confirm Keycloak is working:

1. **Start Docker Desktop** (from Windows Start menu — "Docker Desktop")
2. Once Docker is running, open a terminal in the project root and run:
   ```bash
   docker compose up -d
   ```
3. Wait ~30 seconds for Keycloak to start, then verify:
   ```bash
   curl http://localhost:8080/realms/backoffice/.well-known/openid-configuration
   ```
   Expected: JSON with `"issuer":"http://localhost:8080/realms/backoffice"`
4. Verify JWKS endpoint (needed by BFF in Plan 02):
   ```bash
   curl http://localhost:8080/realms/backoffice/protocol/openid-connect/certs
   ```
   Expected: JSON with `keys` array

**Keycloak Admin UI:** http://localhost:8080 — login with `admin` / `admin`

**Seed user:** `admin@backoffice.dev` / `Admin1234!` — should have PlatformAdmin role in backoffice realm

## Next Phase Readiness

**Ready for Plan 02 (BFF auth endpoints) when:**
- Docker Desktop is running with `docker compose up -d`
- Keycloak OIDC discovery endpoint responds at http://localhost:8080/realms/backoffice/.well-known/openid-configuration
- The JWKS endpoint is live at http://localhost:8080/realms/backoffice/protocol/openid-connect/certs

**Plan 02 dependencies satisfied:**
- `bff/` package with express, jose, cors, dotenv installed
- `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET` documented in `bff/.env.example`
- Keycloak realm configured with backoffice-bff confidential client (secret: `backoffice-bff-secret`)

---
*Phase: 01-foundation-and-auth*
*Completed: 2026-06-06*

## Self-Check: PASSED
