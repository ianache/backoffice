# Project Research Summary

**Project:** BackOffice Multi-Tenant Platform - MVP2 (v1.1)
**Domain:** Multi-tenant SaaS BackOffice with Micro-Frontend Architecture and Feature Flag SDK
**Researched:** 2026-06-07
**Confidence:** HIGH

## Executive Summary

MVP2 is an architectural upgrade and capability expansion on top of a fully delivered v1.0 platform. The four capability areas - Module Federation micro-frontend migration, Products entity promotion, Advanced (rule-based) Segments, and a Feature Flag SDK - are deeply interdependent and must be sequenced correctly: the Products entity must exist before the SDK bootstrap can scope-resolve flags per product; the Shell must federate successfully before any domain MUI can be developed; rule-based segments must land before the SDK bootstrap payload can inline them. All four areas build on verified, in-repo foundations (Vue 3 + Pinia, FastAPI + SQLAlchemy, existing evaluate_flag() engine, Keycloak PKCE), so the stack additions are surgical rather than replacement-level.

The recommended approach is a strict backend-first, frontend-last phase order. The backend DB schema changes (Products tables, Segment type/rules columns) must be deployed as three separate, non-destructive Alembic migrations to protect MySQL 5.6 data. The SDK backend endpoints compose entirely from existing list_flags() and evaluate_flag() functions - no new evaluation logic is needed. The Module Federation Shell cutover is the highest-risk step and should be deferred until backend and BFF routes are stable so the MUIs have real data from day one.

The dominant risk is the Pinia singleton split in Module Federation: if singleton: true + requiredVersion is not set identically across all four vite.config.ts files (Shell + 3 remotes), auth state silently breaks in every remote without a console error. The second structural risk is collapsing the Products JSON-to-relational migration into a single Alembic revision, which on MySQL 5.6 (no transactional DDL) risks irreversible data loss. Both risks have clear prevention checklists and must be verified at the phase boundary before moving on.
---

## Key Findings

### Recommended Stack

The existing stack (Vue 3 + Pinia, Vite 5, Node.js BFF, FastAPI 0.115.5, SQLAlchemy async, Keycloak PKCE, MySQL 5.6) requires only four net-new additions. @originjs/vite-plugin-federation@1.4.1 is the correct Module Federation plugin - already scaffolded in microuis/mui-security and sufficient for a 3-remote closed monorepo. tsup@^8 builds the JS/TS SDK to dual ESM+CJS output with zero config. The Python SDK packages via pyproject.toml + hatchling per current PyPA recommendations, with websockets@16.0 as its async WS client. FastAPI built-in WebSocket support handles the server-side sync endpoint with no new dependencies.

Key version constraints: do not upgrade Vite past 5.x until @originjs/vite-plugin-federation confirms v6 support. The reconnecting-websocket npm package is abandoned (2020) - use an inline 30-line exponential-backoff class instead. Do not place @material/web or keycloak-js in the MF shared list without singleton: true.

**Core technologies (new additions only):**
- **@originjs/vite-plugin-federation@1.4.1**: Module Federation host + remote - already in use, well-understood config for this monorepo
- **tsup@^8**: SDK JS/TS bundler - zero-config dual ESM+CJS output, 6M weekly downloads
- **websockets@16.0,<17**: Python SDK async WS client - asyncio-native, integrates with FastAPI/Uvicorn event loop
- **hatchling + pyproject.toml**: Python SDK packaging - PyPA official recommendation, replaces legacy setup.py
- **FastAPI built-in WebSocket**: Server-side WS sync endpoint - no new dependency; @app.websocket + Starlette handles it

### Expected Features

The feature set spans four tightly coupled categories. All P1 items must ship together for the SDK to be functional end-to-end.

**Must have - MUI Architecture (P1):**
- Shell owns single Keycloak init + shared Pinia singleton (remotes read auth state via useAuthStore(), never init their own)
- Lazy-loaded remote routes registered via loadMicroUIRoutes() called before app.mount()
- Remote failure does not crash Shell (defineAsyncComponent with errorComponent)
- vite build --watch dev workflow (not vite dev) documented in CONTRIBUTING.md

**Must have - Products (P1):**
- Products catalog CRUD for PlatformAdmin
- Tenant product subscription via tenant_products join table
- Inactive product deactivates all product-scoped flag evaluations
- Three-revision Alembic migration (expand then backfill then contract)

**Must have - Advanced Segments (P1):**
- type field (manual or rule_based) + rules TEXT column on segments table (additive migration, server default manual)
- Rule-based segment editor reusing existing RuleCard.vue and useRuleSimulator.ts
- flag_count on segment response for orphan detection; UI badge for flag_count === 0

**Must have - SDK (P1):**
- Bootstrap endpoint (GET /api/v1/sdk/bootstrap) returning pre-scope-resolved flag configs with inlined segment rules
- JS/TS client: initialize(), synchronous local evaluate() (<1ms), WS invalidation with exponential backoff, telemetry batch (100 events or 60s + random jitter)
- Python server SDK: async initialize() + async evaluate() via asyncio
- WebSocket sync channel with first-message auth pattern (no JWT in query param)

**Should have - add after P1 validation (P2):**
- SDK API key management UI (generate/revoke per tenant+product)
- Product dashboard: flag count + active tenant count
- CI/CD version sync endpoint for products

**Defer (v2+):**
- Company-level scope in SDK bootstrap (4th hierarchy level)
- Percentage rollout in SDK (rollout field stored, eval deferred to v2)
- Segment preview (estimated user reach - requires external user attribute store)
- SSE as WebSocket alternative for SDK sync
### Architecture Approach

The architecture follows a strict layered micro-frontend pattern: Shell (auth + layout + router only) hosts three federated remote SPAs via @originjs/vite-plugin-federation. The Shell creates the single Pinia instance and Axios interceptor at boot; remotes consume both as federation-shared singletons. All domain business logic migrates out of the Shell into respective MUI packages. The backend adds a new products/ domain, a ws_hub.py singleton for WebSocket connection management, and SDK router endpoints that compose from existing list_flags() and evaluate_flag() without modifying their signatures.

**Major components:**
1. **Portal Shell** - Keycloak PKCE init, Pinia + Axios singleton provision, layout chrome, dynamic route registration from remotes; owns Dashboard, Login, Unauthorized views only
2. **mui-security / mui-tenants / mui-feature-flags** - federated remote SPAs; each exposes ./routes; consumes Shell Pinia and Axios
3. **BFF (Node.js)** - adds /products and /sdk/* proxy routes; adds ws: true WebSocket proxy for SDK sync channel
4. **Backend - products domain** - new products, tenant_products, flag_products tables; product CRUD and tenant subscription service
5. **Backend - SDK router + ws_hub** - bootstrap, remote eval, eval-events endpoints; ConnectionManager in-process singleton for WebSocket broadcast per tenant
6. **SDK JS/TS** - FeatureFlagClient with in-memory Map cache, local evaluator (port of evaluate_flag()), inline WS reconnect, telemetry queue
7. **SDK Python** - async FeatureFlagClient using httpx + websockets@16

### Critical Pitfalls

1. **Pinia singleton splits silently** - singleton: true + requiredVersion missing from any vite.config.ts causes useAuthStore() to return empty state in remotes; every BFF call fails 401 with no console error. Prevention: identical shared block in all 4 configs; pre-build pnpm ls check.

2. **MySQL 5.6 migration data loss** - combined expand+backfill+drop migration destroys tenants.products data if backfill fails (no transactional DDL). Prevention: three separate Alembic revisions; defensive guard for null/empty/json-null string in backfill.

3. **WS JWT auth loop** - browser WebSocket cannot send Authorization header; after token expiry, reconnect loop fails permanently. Prevention: first-message auth pattern; SDK tokenProvider callback; server re-validates on every reconnect.

4. **MUI route registration race** - hard refresh on /flags or /tenants redirects to /unauthorized if loadMicroUIRoutes() not awaited before app.mount(). Prevention: await in main.ts; timeout + fallback route if remote unreachable in 3s.

5. **DB calls inside evaluate_flag() break SDK local eval** - adding AsyncSession parameter for segment lookups destroys the <1ms guarantee. Prevention: SDK bootstrap pre-serializes full segment rules; local evaluator is DB-free; unit test asserts zero DB calls in eval path.

6. **Telemetry thundering herd** - fixed 60s flush interval causes all SDK instances to flush simultaneously post-deployment, exhausting asyncmy pool (default size 5). Prevention: Math.random() * 30000 jitter; bulk INSERT; pool_size=10, max_overflow=20 in database.py.

---
## Implications for Roadmap

Based on the strict dependency chain (Products before SDK, Segments before SDK bootstrap, Shell before MUIs) and MySQL 5.6 data-safety requirements, the following 7-phase structure is recommended.

### Phase 1: Backend - Products Domain + DB Migration
**Rationale:** Products is the upstream dependency for SDK bootstrap scoping and MUI product selectors. Alembic revision 002 (additive only) is safe to deploy while v1.0 still runs.
**Delivers:** domains/products/ (models, schemas, service, router), products + tenant_products + flag_products tables, Products CRUD endpoints, tenant product subscription endpoint.
**Addresses:** Products table stakes - catalog CRUD, tenant subscription, inactive product deactivation.
**Avoids:** Pitfall 2 - this revision is expand-only; backfill and drop are separate phases.

### Phase 2: Backend - Advanced Segments + SDK Endpoints + WebSocket Hub
**Rationale:** Additive segment columns are safe to deploy without breaking existing responses. SDK endpoints compose from existing functions. Entire phase is backend-only.
**Delivers:** segments.type + segments.rules columns, evaluate_segment(), SDK router (/sdk/bootstrap, /sdk/evaluate, /sdk/eval-events), ws_hub.py ConnectionManager, FastAPI WebSocket endpoint at /ws/flags/{tenant_id}, flag save path hooked to manager.broadcast().
**Addresses:** Advanced segment table stakes, SDK backend P1, WS invalidation.
**Avoids:** Pitfall 5 (segment rules embedded in bootstrap payload); Pitfall 6 (bulk insert, pool_size configured here).

### Phase 3: BFF - Products and SDK Routes
**Rationale:** Pure proxy additions following established requireAuth + http-proxy-middleware pattern. Can only be built after Phase 1 and 2 backend endpoints exist.
**Delivers:** bff/src/routes/products.ts, bff/src/routes/sdk.ts (HTTP + ws: true WebSocket proxy), mounted in bff/src/index.ts.
**Addresses:** BFF integration completeness for SDK and Products.

### Phase 4: Shell Cutover - Module Federation Host Config
**Rationale:** Highest-risk step, deferred until backend and BFF are stable. Shell refactoring is isolated: remove domain views, configure federation host, implement loadMicroUIRoutes().
**Delivers:** Shell vite.config.ts with federation host config (shared singletons), federation.ts plugin, refactored router/index.ts, domain views deleted, pnpm-workspace.yaml updated, CONTRIBUTING.md dev workflow (vite build --watch).
**Addresses:** MUI architecture table stakes - single Keycloak init, shared Pinia, remote failure boundary.
**Avoids:** Pitfall 1 (Pinia singleton - verified at this phase); Pitfall 4 (route registration race - awaited before mount).

### Phase 5: mui-tenants - Tenants Migration + Products UI
**Rationale:** Simplest domain. Ideal first remote to prove the federation pattern works end-to-end with real data. Products UI lives here.
**Delivers:** microuis/mui-tenants/ package, migrated TenantsView + tenant components, new ProductsView (catalog CRUD + tenant subscription), vite.config.ts remote federation config.
**Addresses:** Products UI, tenant product subscription workflow.

### Phase 6: mui-security - Users Migration
**Rationale:** Independent of Products. Lower priority since v1.0 user management was fully functional. Can proceed in parallel with Phase 5 if bandwidth allows.
**Delivers:** microuis/mui-security/ source files (stub package already exists), migrated UsersView + user drawer + components, vite.config.ts remote federation config.
**Addresses:** MUI migration completeness for the security domain.

### Phase 7: mui-feature-flags - Flags Migration + Advanced Segments UI + SDK Packages
**Rationale:** Highest complexity. Requires Phase 2 (backend), Phase 4 (Shell), and Phase 3 (BFF) all stable.
**Delivers:** microuis/mui-feature-flags/ package, migrated FlagsView + RuleBuilderView, new SegmentsView (type toggle, rule editor via RuleCard.vue, orphan detection badge), sdk/sdk-js package (tsup), sdk/sdk-python package (hatchling).
**Addresses:** All remaining P1 SDK features, rule-based segment UI, orphan detection, telemetry.
**Avoids:** Pitfall 3 (WS first-message auth, tokenProvider callback); Pitfall 6 (jitter on flush interval).

### Phase Ordering Rationale

- Backend-before-frontend is mandatory: SDK bootstrap requires products table; segment rules must be in DB before bootstrap can embed them; BFF proxy must point to live backend endpoints.
- Shell cutover (Phase 4) is deferred to the middle because it is the highest-risk step - building with real backend data means MUIs can be verified end-to-end immediately.
- Products migration safety drives Phase 1 scope: expand-only Alembic revision is deploy-safe; backfill script and drop revision are handled across Phase 1-2 boundary with verification gates.
- mui-tenants before mui-feature-flags: lower complexity, proves federation wiring before the most complex MUI is built.

### Research Flags

Phases likely needing deeper research or validation during planning:
- **Phase 4 (Shell Cutover):** Module Federation shared config edge cases, especially pinia-plugin-persistedstate singleton behavior and CORS in dev mode. Well-documented in PITFALLS.md but nuanced enough to warrant a focused validation step before execution.
- **Phase 7 (SDK WS auth):** First-message auth pattern over a BFF WebSocket proxy (ws: true) with Keycloak token refresh has not been E2E tested in this stack. Needs a spike/integration test before full implementation.

Phases with standard patterns (skip additional research):
- **Phase 1 (Products domain):** Follows the established domains/<name>/ pattern - same as tenants/users built in v1.0.
- **Phase 2 (SDK endpoints):** Composes from existing list_flags() + evaluate_flag(); pattern fully specified in ARCHITECTURE.md Pattern 6.
- **Phase 3 (BFF routes):** Standard http-proxy-middleware proxy - identical to all existing BFF routes.
- **Phase 6 (mui-security):** No new features; pure migration of existing, well-understood views.

---
## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All additions verified via official docs (PyPA, FastAPI, tsup); @originjs/vite-plugin-federation confirmed via in-repo scaffold; version constraints grounded in real issues |
| Features | HIGH | Derived from in-repo code inspection (service.py, auth.ts, existing router patterns) + PRD_MVP2.md; competitor analysis validates SDK design decisions |
| Architecture | HIGH | Based on direct codebase inspection of all relevant files; patterns are extensions of proven v1.0 patterns |
| Pitfalls | HIGH | 7 critical pitfalls each grounded in specific file/line in codebase + external verified issues; recovery strategies are concrete |

**Overall confidence:** HIGH

### Gaps to Address

- **SDK API key management:** v1.1 uses a shared secret from env for SDK auth. The gap to per-tenant API key management (sdk_keys table, key rotation UI) is deferred to P2 and will need a dedicated research pass before implementation.
- **alembic.ini presence:** Project has no checked-in alembic.ini. Must be created and committed before Phase 1 migrations can run. Confirm location and asyncio mode setting before Phase 1 begins.
- **SDK telemetry data model:** Before Phase 7, decide whether sdk_events goes to a DB table (queryable for a dashboard) or a log file (simpler). This choice affects Phase 2 schema.
- **WebSocket BFF proxy validation:** http-proxy-middleware ws: true behavior with Keycloak JWT token refresh in a long-lived WS connection has not been integration-tested. Flag for a spike task at the start of Phase 7.

---

## Sources

### Primary (HIGH confidence)
- backend/app/domains/feature_flags/service.py - evaluate_flag(), _evaluate_rule(), OPERATORS dispatch; SDK eval port source of truth
- portal/src/stores/auth.ts - Keycloak token management, MUI auth sharing strategy
- portal/src/router/index.ts - existing lazy-load pattern for MUI route registration
- portal/src/services/api.ts - Axios interceptor singleton; federation shared pattern
- docs/micro_ui_proposal.md - existing architectural proposal confirming federation config choices
- microuis/mui-security/package.json - confirms @originjs/vite-plugin-federation@1.4.1 already in use
- PRD_MVP2.md - SDK spec, bootstrap URL, ICD endpoints, telemetry parameters
- https://fastapi.tiangolo.com/advanced/websockets/ - ConnectionManager broadcast pattern
- https://packaging.python.org/en/latest/guides/writing-pyproject-toml/ - PyPA hatchling recommendation
- https://tsup.egoist.dev/ - dual ESM+CJS output, tsup@^8
- https://pypi.org/project/websockets/ - v16.0, asyncio implementation

### Secondary (MEDIUM confidence)
- https://github.com/originjs/vite-plugin-federation - Vite 5 issues, version history, maintenance status
- https://module-federation.io/guide/basic/vite - @module-federation/vite docs (evaluated and rejected)
- https://github.com/vuejs/pinia/discussions/1968 - getActivePinia error and singleton fix
- https://that.guru/blog/zero-downtime-upgrades-with-alembic-and-sqlalchemy/ - three-revision expand-contract pattern
- VWO FullStack + Optimizely event batching docs - 100-event/60s dual trigger pattern validation
- PostHog GitHub issue #32447 - WS cache invalidation confirms SSE/WS pattern

### Tertiary (references for edge cases)
- https://github.com/module-federation/core/issues/4078 - singleton version postfix bug
- https://websockets.readthedocs.io/en/stable/topics/authentication.html - token passing strategies; basis for first-message auth recommendation
- https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules - competitor evaluation order reference

---
*Research completed: 2026-06-07*
*Ready for roadmap: yes*
