# Roadmap: BackOffice Multi-Tenant Platform

## Milestones

- ✅ **v1.0 BackOffice MVP** — Phases 1-6 (shipped 2026-06-08)
- 🚧 **v1.1 MVP2** — Phases 7-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 BackOffice MVP (Phases 1-6) — SHIPPED 2026-06-08</summary>

- [x] Phase 1: Foundation & Auth (4/4 plans) — completed 2026-06-07
- [x] Phase 2: Tenant Management (4/4 plans) — completed 2026-06-07
- [x] Phase 2.1: UI System & Brand Alignment (1/1 plan) — completed 2026-06-07
- [x] Phase 3: User Management (6/6 plans) — completed 2026-06-07
- [x] Phase 4: Feature Flags (7/7 plans) — completed 2026-06-07
- [x] Phase 5: Rule Builder (3/3 plans) — completed 2026-06-08
- [x] Phase 6: Stitch UI Implementation (4/4 plans) — completed 2026-06-06

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 MVP2 (Phases 7-11)

**Milestone Goal:** Refactorizar el portal en arquitectura Shell + Micro-UIs y entregar Productos, Segmentos Avanzados y Feature Flag SDK como entidades y capacidades de primer nivel.

- [ ] **Phase 7: Products Domain** — Backend + DB: products catalog CRUD, tenant subscriptions, safe 3-step Alembic migration
- [ ] **Phase 8: Advanced Segments + SDK Backend** — Backend: rule-based segments, SDK endpoints (bootstrap/evaluate/eval-events/WebSocket)
- [ ] **Phase 9: Shell Cutover** — Portal refactored to Module Federation host; shared Pinia/Axios singletons; lazy remote route registration
- [ ] **Phase 10: mui-tenants + mui-security** — Domain MUIs migrated as federated remotes; Products UI in mui-tenants
- [ ] **Phase 11: mui-feature-flags + SDK Clients** — Feature flags MUI migrated; Segments UI with orphan detection; JS/TS + Python SDK packages

## Phase Details

### Phase 7: Products Domain
**Goal**: PlatformAdmin can manage the products catalog and TenantOwners can subscribe products to their tenants; feature flags can be associated to products; the underlying relational schema is migrated safely without data loss on MySQL 5.6.
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: PROD-01, PROD-02, PROD-03, PROD-04, PROD-05, PROD-06
**Success Criteria** (what must be TRUE):
  1. PlatformAdmin can create a product with alphanumeric id, name, description, status and labels, and the product appears in the catalog list filterable by status and label
  2. PlatformAdmin can edit product metadata and toggle active/inactive; inactive product is visually indicated in the catalog
  3. TenantOwner can subscribe and unsubscribe products for their tenant from the tenant management UI; subscribed products appear in the tenant detail view
  4. A feature flag can be associated to one or more products via `flag_products` relational table; existing product associations from the legacy JSON field are preserved after migration
  5. Three separate Alembic revisions (expand, backfill, cleanup) can each be applied and rolled back independently without destroying existing tenant or flag data
**Plans**: 4 plans

Plans:
- [ ] 07-01-PLAN.md — Products domain foundation: ORM models, Pydantic schemas, Alembic env.py registration
- [ ] 07-02-PLAN.md — Products CRUD service, router (POST/GET/PATCH), main.py registration
- [ ] 07-03-PLAN.md — Alembic 3-step migration: expand, backfill, cleanup revisions
- [ ] 07-04-PLAN.md — Tenant subscription endpoints + flag-product association endpoints

### Phase 8: Advanced Segments + SDK Backend
**Goal**: Segments support rule-based dynamic conditions using the existing evaluation engine; SDK backend endpoints expose a consolidated flag bootstrap, remote evaluation, telemetry ingestion, and real-time WebSocket invalidation — all composing from existing `list_flags()` and `evaluate_flag()` without changes to their signatures.
**Depends on**: Phase 7
**Requirements**: SEG-01, SEG-02, SEG-03, SEG-04, SEG-05, SDK-01, SDK-02, SDK-03, SDK-04
**Success Criteria** (what must be TRUE):
  1. A segment can be created with `type: manual` (existing behavior unchanged) or `type: rule_based`; rule-based segments store conditions in the same JSON format as feature flag rules
  2. `GET /api/v1/sdk/bootstrap?tenant_id=X&product_id=Y&environment=Z` returns a single JSON payload containing pre-resolved flag configs with inlined segment rules, usable without further DB calls at evaluation time
  3. `POST /api/v1/sdk/evaluate` accepts a flag key and user context object and returns the evaluated boolean value; delegates to existing `evaluate_flag()` without code duplication
  4. `POST /api/v1/sdk/eval-events` accepts a batch of evaluation events and persists them; bulk INSERT is used to avoid N+1 writes; pool_size and max_overflow are configured to handle concurrent SDK instances
  5. A WebSocket connection to `/ws/flags/{tenant_id}` receives a `{type:"flag_updated", flag_key}` message within 500ms of any flag save for that tenant; first-message auth pattern is used (no JWT in query param or Depends())
**Plans**: TBD

### Phase 9: Shell Cutover
**Goal**: The portal is refactored into a lightweight Shell that owns only Keycloak PKCE init, layout chrome, and async remote route registration; domain views are removed from the Shell; Vue, Pinia, Vue Router and Axios are exposed as shared federation singletons so remote MUIs never instantiate duplicate stores.
**Depends on**: Phase 8
**Requirements**: MUI-01, MUI-02, MUI-03
**Success Criteria** (what must be TRUE):
  1. Hard refresh on any deep route (e.g., `/flags`, `/tenants/123`) resolves correctly; `loadMicroUIRoutes()` is awaited before `app.mount()` so no race condition redirects to `/unauthorized`
  2. Vue, Pinia, Vue Router and Axios each appear exactly once in the browser's loaded modules when the Shell boots with all remotes connected (verifiable via browser devtools network tab or `__webpack_modules__` / `__federation__` internals)
  3. If a remote MUI is unreachable at boot, the Shell still mounts and shows an error boundary component in place of that domain's routes — the rest of the portal remains functional
**Plans**: TBD

### Phase 10: mui-tenants + mui-security
**Goal**: Tenant management and user management views are extracted as independent federated remote applications that consume Shell-provided singletons; the Products UI (catalog CRUD and tenant subscription) lives in mui-tenants; BFF proxy routes for products and SDK are added.
**Depends on**: Phase 9
**Requirements**: MUI-04, MUI-05
**Success Criteria** (what must be TRUE):
  1. mui-tenants exposes `./routes`; all tenant CRUD flows (create, edit, suspend, delete, whitelabel) work end-to-end including Products subscription tab — data comes from live backend, no mocks
  2. mui-security exposes `./routes`; all user management flows (create, edit, activate, deactivate, reset MFA, audit log) work end-to-end inside the federated remote
  3. Auth state (user identity, roles, JWT token) is shared from Shell Pinia store in both MUIs — no 401 errors from BFF when navigating between tenant and security views
  4. BFF exposes `/products` proxy route and `/sdk/*` HTTP + WebSocket proxy routes (`ws: true`) pointing to the backend endpoints from Phase 7 and Phase 8
**Plans**: TBD

### Phase 11: mui-feature-flags + SDK Clients
**Goal**: Feature flags, rule builder, live simulator and segments are extracted into a federated MUI; segments UI adds rule-based editing (reusing RuleCard.vue) and visual orphan detection; the JS/TS and Python SDK client packages are published from the monorepo with local evaluation, WebSocket sync, and telemetry batching.
**Depends on**: Phase 10
**Requirements**: MUI-06, SDK-05, SDK-06, SDK-07, SDK-08, SDK-09, SDK-10, SDK-11, SDK-12
**Success Criteria** (what must be TRUE):
  1. mui-feature-flags exposes `./routes`; all feature flag flows (create/edit flag, rule builder with drag-and-drop, live simulator) work end-to-end inside the federated remote
  2. The segments list shows a reference count badge on each segment; segments with zero active flag references display an orphan visual indicator; the rule-based segment editor uses `RuleCard.vue` without a separate editor component
  3. `sdk/sdk-js` initializes with a single `initialize({tenantId, productId, environment})` call, evaluates flags synchronously from in-memory cache in under 1ms (measurable in unit tests with `performance.now()`), and recovers from cache-miss via remote evaluate fallback
  4. `sdk/sdk-js` maintains a WebSocket connection with exponential-backoff reconnect (inline, no external library); cache is invalidated on `flag_updated` message; telemetry flushes on dual trigger (100 events OR 60s) with random jitter at startup; `navigator.sendBeacon()` is used for flush on `beforeunload`
  5. `sdk/sdk-python` initializes asynchronously via `async initialize()`, evaluates flags locally from cache, reconnects WebSocket with exponential-backoff + jitter — all async via asyncio compatible with FastAPI/Uvicorn event loop
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 8 → 9 → 10 → 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Auth | v1.0 | 4/4 | Complete | 2026-06-07 |
| 2. Tenant Management | v1.0 | 4/4 | Complete | 2026-06-07 |
| 2.1. UI System & Brand Alignment | v1.0 | 1/1 | Complete | 2026-06-07 |
| 3. User Management | v1.0 | 6/6 | Complete | 2026-06-07 |
| 4. Feature Flags | v1.0 | 7/7 | Complete | 2026-06-07 |
| 5. Rule Builder | v1.0 | 3/3 | Complete | 2026-06-08 |
| 6. Stitch UI Implementation | v1.0 | 4/4 | Complete | 2026-06-06 |
| 7. Products Domain | v1.1 | 0/4 | Planning complete | - |
| 8. Advanced Segments + SDK Backend | v1.1 | 0/TBD | Not started | - |
| 9. Shell Cutover | v1.1 | 0/TBD | Not started | - |
| 10. mui-tenants + mui-security | v1.1 | 0/TBD | Not started | - |
| 11. mui-feature-flags + SDK Clients | v1.1 | 0/TBD | Not started | - |
