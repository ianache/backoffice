# Phase 2: Tenant Management - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning

<domain>
## Phase Boundary

PlatformAdmin can manage the full tenant lifecycle — create, configure, filter, suspend, and associate products. This introduces the Python backend service, the app database, and the first admin UI beyond the login screen. Tenant-level user management is Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Database
- MySQL 5.6 as the application database (separate from Keycloak's Postgres)
- Alembic for all schema migrations — no raw DDL outside of migration files
- SQLAlchemy models define the schema; Alembic autogenerates migration scripts

### Python Backend
- Framework: FastAPI with async SQLAlchemy (AsyncSession + asyncmy driver for MySQL 5.6)
- Structure: router-per-domain — each domain (tenants, products) gets its own router module
- Lives at `backend/` at monorepo root, parallel to `bff/` and `portal/`
- First domain introduced in this phase: `tenants` router

### BFF Integration Pattern
- Vue portal calls BFF only — BFF proxies all tenant requests to Python backend
- BFF uses `http-proxy-middleware` for proxying (minimal code, handles streaming)
- BFF authenticates with Python backend via `X-Internal-Secret` header (shared secret in env)
- BFF forwards `X-User-Sub` and `X-User-Roles` headers so Python backend knows the acting user
- Python backend does not validate Keycloak JWTs directly

### Tenant List UI
- Data table with rows: one row per tenant
- Columns: Name, Status (color-coded badge), Country, Products (comma-separated or count), Created, Actions
- Actions column: Edit, Suspend/Unsuspend, Delete
- Search and filter in a horizontal top bar above the table: text search input + Status filter dropdown + Country filter dropdown
- Sorting on table columns

### Tenant Create/Edit UI
- Side drawer (slide-over from right) — tenant list stays visible in background
- Drawer has 2 tabs:
  - **General**: name, country, default_language, default_currency, default_units, status
  - **Whitelabel**: logo URL, primary/secondary/accent colors, font family + weight, domain
- Same drawer used for both create and edit; tab selection persists within a session

### Whitelabel Configuration
- Logo: external URL input only — no file upload in Phase 2
- Colors: free hex input with color picker for primary, secondary, and accent brand colors
- Typography: font family name text input (e.g., "Inter", "Roboto") + weight selection (regular, medium, bold)
- Domain: plain text input for custom domain string
- All whitelabel fields stored as columns/JSON in the tenants table

### Product Association (TNNT-05)
- Claude's Discretion: how products are represented in Phase 2 (enum vs products table)
- The association UI (enable/disable products per tenant) should be minimal — a simple checklist or toggle list within the General tab or as a third drawer tab

### Claude's Discretion
- Exact color picker component library choice for the whitelabel form
- Pagination vs infinite scroll for the tenant table (choose what fits the table component)
- Confirmation dialog design for suspend and delete actions
- Error state and empty state illustrations/copy
- Docker Compose additions for MySQL 5.6 service

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `portal/src/services/api.ts`: Axios instance with Bearer token interceptor and 401→login redirect — tenant API calls should use this same instance
- `portal/src/stores/auth.ts`: Pinia store with `hasRole()` helper — use to gate PlatformAdmin-only actions in the UI
- `bff/src/middleware/auth.ts`: `requireAuth` middleware — all new BFF tenant routes use this
- `bff/src/middleware/roles.ts`: `requireRole` middleware pattern — wrap tenant routes with `requireRole('PlatformAdmin')`

### Established Patterns
- BFF is the single API gateway — portal never calls backend services directly
- Pinia store per domain (auth store exists) — create a `tenants` store with the same composable pattern
- Axios service in `portal/src/services/` — create `tenants.ts` service alongside `api.ts`
- BFF routes in `bff/src/routes/` — create `tenants.ts` route file parallel to `auth.ts`

### Integration Points
- Portal router (`portal/src/router/`): add `/tenants` route, guarded by `requireAuth` + `hasRole('PlatformAdmin')`
- BFF index (`bff/src/index.ts`): mount `app.use('/tenants', tenantsRouter)` alongside `/auth`
- docker-compose.yml: add MySQL 5.6 service for the app database
- `.env` / `.env.example`: add `MYSQL_*` and `BACKEND_URL` and `INTERNAL_SECRET` env vars

</code_context>

<specifics>
## Specific Ideas

- BFF proxy pattern should mirror how auth routes work: `requireAuth` → `requireRole` → forward to Python backend
- MySQL 5.6 compatibility matters for Alembic — use `mysql+asyncmy` dialect and avoid MySQL 8-only syntax in migrations
- The side drawer pattern should feel like modern admin tools (Linear, Vercel team settings) — not a modal

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-tenant-management*
*Context gathered: 2026-06-06*
