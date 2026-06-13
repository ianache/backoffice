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

### 🚧 v1.1 MVP2 (Phases 7-14)

**Milestone Goal:** Refactorizar el portal en arquitectura Shell + Micro-UIs y entregar Productos, Segmentos Avanzados y Feature Flag SDK como entidades y capacidades de primer nivel.

- [x] **Phase 7: Products Domain** — Backend + DB: products catalog CRUD, tenant subscriptions, safe 3-step Alembic migration (completed 2026-06-08)
 (completed 2026-06-09)
- [x] **Phase 9: Shell Cutover** — Portal refactored to Module Federation host; shared Pinia/Axios singletons; lazy remote route registration (completed 2026-06-09)
- 🚧 **Phase 10: mui-tenants + mui-security** — Domain MUIs migrated; gap closure plans in progress (3/6 plans complete)
- [x] **Phase 11: mui-feature-flags + SDK Clients** — Feature flags MUI migrated; Segments UI with orphan detection; JS/TS + Python SDK packages (completed 2026-06-10)
- [x] **Phase 12: Dogfooding Feature Flags** — Portal gated by its own flags (product `backoffice`): bo.feature, bo.feature.create, bo.feature.update (completed 2026-06-11)
- [x] **Phase 13: Simulator Test Contexts** — Persistent per-flag test contexts in Live Simulator + toggle to use the logged-in user's real context (completed 2026-06-11)
- [x] **Phase 14: Flag Scope Targeting + List-Valued Rules** — Combobox de producto/tenant/company según scope del flag (persistido y aplicado por el SDK) + values de Rule como lista separada por coma para atributos lista (ej. roles) (completed 2026-06-12)
- [x] **Phase 15: AND Rule Combination Semantics + Flags Page Filters** — Multi-rule evaluation combina con AND: el flag/segment evalúa true solo si TODAS las reglas individuales matchean, false en caso contrario; paridad en los 4 evaluadores (backend, sdk-js, sdk-python, useRuleSimulator); OR y grupos de reglas diferidos a un release futuro. Además, filtros en la página `/flags`: Status, Tags, Complexity, Environment y target de scope (Products, Tenants o Global) (completed 2026-06-12)

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
- [x] 07-01-PLAN.md — Products domain foundation: ORM models, Pydantic schemas, Alembic env.py registration
- [x] 07-02-PLAN.md — Products CRUD service, router (POST/GET/PATCH), main.py registration
- [x] 07-03-PLAN.md — Alembic 3-step migration: expand, backfill, cleanup revisions
- [x] 07-04-PLAN.md — Tenant subscription endpoints + flag-product association endpoints

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
**Plans**: 4 plans

Plans:
- [x] 08-01-PLAN.md — Alembic migrations (segments + eval_events) + Segment ORM/schema/service extension
- [x] 08-02-PLAN.md — Segments router + portal UI (SegmentsView, SegmentForm, SegmentTable, nav)
- [x] 08-03-PLAN.md — SDK infrastructure (ConnectionManager, config, pool) + HTTP endpoints (bootstrap/evaluate/eval-events)
- [x] 08-04-PLAN.md — WebSocket endpoint + flag broadcast hooks + BFF proxy

### Phase 9: Shell Cutover
**Goal**: The portal is refactored into a lightweight Shell that owns only Keycloak PKCE init, layout chrome, and async remote route registration; domain views are removed from the Shell; Vue, Pinia, Vue Router and Axios are exposed as shared federation singletons so remote MUIs never instantiate duplicate stores.
**Depends on**: Phase 8
**Requirements**: MUI-01, MUI-02, MUI-03
**Success Criteria** (what must be TRUE):
  1. Hard refresh on any deep route (e.g., `/flags`, `/tenants/123`) resolves correctly; `loadMicroUIRoutes()` is awaited before `app.mount()` so no race condition redirects to `/unauthorized`
  2. Vue, Pinia, Vue Router and Axios each appear exactly once in the browser's loaded modules when the Shell boots with all remotes connected (verifiable via browser devtools network tab or `__webpack_modules__` / `__federation__` internals)
  3. If a remote MUI is unreachable at boot, the Shell still mounts and shows an error boundary component in place of that domain's routes — the rest of the portal remains functional
**Plans**: 4 plans

Plans:
- [x] 09-01-PLAN.md — Shell federation host: install @originjs/vite-plugin-federation, vite.config.ts with shared singletons, RemoteErrorBoundary component
- [x] 09-02-PLAN.md — Router refactor + domain cleanup: loadMicroUIRoutes(), main.ts ordering, delete domain views/stores/components/services
- [x] 09-03-PLAN.md — mui-stub remote: scaffold minimal stub MUI, build remoteEntry.js to prove federation loop
- [ ] 09-04-PLAN.md — E2E verification: hard refresh, singleton deduplication, error boundary (checkpoint:human-verify)

### Phase 10: mui-tenants + mui-security
**Goal**: Tenant management and user management views are extracted as independent federated remote applications that consume Shell-provided singletons; the Products UI (catalog CRUD and tenant subscription) lives in mui-tenants; BFF proxy routes for products and SDK are added.
**Depends on**: Phase 9
**Requirements**: MUI-04, MUI-05
**Success Criteria** (what must be TRUE):
  1. mui-tenants exposes `./routes`; all tenant CRUD flows (create, edit, suspend, delete, whitelabel) work end-to-end including Products subscription tab — data comes from live backend, no mocks
  2. mui-security exposes `./routes`; all user management flows (create, edit, activate, deactivate, reset MFA, audit log) work end-to-end inside the federated remote
  3. Auth state (user identity, roles, JWT token) is shared from Shell Pinia store in both MUIs — no 401 errors from BFF when navigating between tenant and security views
  4. BFF exposes `/products` proxy route and `/sdk/*` HTTP + WebSocket proxy routes (`ws: true`) pointing to the backend endpoints from Phase 7 and Phase 8
**Plans**: 6 plans

Plans:
- [x] 10-01-PLAN.md — Phase 10 scaffolding: mui-tenants, mui-security, and Shell UI component sharing
- [x] 10-02-PLAN.md — Tenant Domain migration: restore view/store/service/components to mui-tenants
- [x] 10-03-PLAN.md — Security Domain migration: restore view/store/service/components to mui-security
- [ ] 10-04-PLAN.md — Gap closure: Shell REMOTE_MANIFEST activation + preview port fixes (wave 1)
- [ ] 10-05-PLAN.md — Gap closure: BFF /products proxy route + SDK WebSocket proxy (ws: true) (wave 1)
- [ ] 10-06-PLAN.md — Gap closure: TenantForm live products integration via /products endpoint (wave 2)

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
**Plans**: 10 plans

Plans:
- [ ] 11-01-PLAN.md - Backend: add greaterThan/lessThan operators to feature flag evaluation engine (canonical OPERATORS table)
- [ ] 11-02-PLAN.md - Scaffold mui-feature-flags federated MUI (Vite Module Federation, package.json, tsconfig)
- [ ] 11-03-PLAN.md - Port flags list, FlagDrawer, services/store into mui-feature-flags
- [ ] 11-04-PLAN.md - Port rule builder + live simulator (useRuleSimulator.ts) with greaterThan/lessThan support
- [ ] 11-05-PLAN.md - Port SegmentsView/SegmentTable/SegmentForm/SegmentPicker with orphan detection and rule-based segment editing via RuleCard
- [ ] 11-06-PLAN.md - Backend bootstrap inlines manual segment members[] + sdk_key query-param auth fallback; scaffold sdk/sdk-js package; port evaluator.ts (7-operator engine)
- [ ] 11-07-PLAN.md - sdk-js FeatureFlagClient: initialize()/evaluate() (sync, <1ms, cache-only)/evaluateRemote() (async fallback) + public entrypoint
- [ ] 11-08-PLAN.md - sdk-js WebSocket reconnect (inline exponential backoff) + telemetry batching (dual trigger + jitter + sendBeacon)
- [ ] 11-09-PLAN.md - sdk-python core: pyproject.toml scaffold, evaluator.py (7-operator engine), async FeatureFlagClient (initialize/evaluate/evaluate_remote)
- [ ] 11-10-PLAN.md - sdk-python WebSocket reconnect (asyncio + websockets, exponential backoff + jitter, flag_updated cache invalidation)

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
| 7. Products Domain | 4/4 | Complete   | 2026-06-08 | - |
| 8. Advanced Segments + SDK Backend | 4/4 | Complete   | 2026-06-09 | - |
| 9. Shell Cutover | v1.1 | 4/4 | Complete | 2026-06-09 |
| 10. mui-tenants + mui-security | 6/6 | Complete    | 2026-06-09 | - |
| 11. mui-feature-flags + SDK Clients | 10/10 | Complete    | 2026-06-10 | - |
| 12. Dogfooding Feature Flags | v1.1 | 3/3 | Complete | 2026-06-11 |

### Phase 12: Dogfooding Feature Flags

**Goal**: La plataforma consume sus propios feature flags (producto id `backoffice`) para controlar su UI: `bo.feature` muestra/oculta la opción de menú "Feature Flags" en el Shell; `bo.feature.create` muestra/oculta el botón "Create Flag" de la página /flags y la acción "Clone" en la tabla de flags; `bo.feature.update` muestra/oculta el ícono de edición (lápiz) en la tabla de flags. La evaluación usa el SDK propio (`@backoffice/sdk-js` de la Fase 11) o el endpoint de bootstrap del BFF, con fail-safe: si el flag no existe o la evaluación falla, la UI se comporta según un default seguro documentado.
**Requirements**: TBD (derive at plan time: DOGF-01 menu gating, DOGF-02 create/clone gating, DOGF-03 edit gating)
**Depends on:** Phase 11
**Plans:** 3 plans

Plans:
- [x] 12-01-PLAN.md — useBoFlags composable + SDK workspace dep + Module Federation expose + env vars + Shell init
- [x] 12-02-PLAN.md — UI gating: MainLayout nav + FlagsView Create + FlagTable Edit/Clone with v-if bindings
- [x] 12-03-PLAN.md — Unit tests for fail-open behavior + planning docs update

### Phase 13: Simulator Test Contexts

**Goal**: El "Test Context" del Live Simulator en el Rule Builder deja de ser efímero: (1) al editarlo se puede **guardar en base de datos asociado al flag/regla** como ejemplo de prueba persistente, recuperado automáticamente al reabrir el editor (sirve para futuros ajustes de la regla); (2) un **Toggle "usar mi contexto real"** reemplaza el ejemplo por los valores reales de las propiedades del usuario logeado (sub, roles, tenant_id, etc.) para validar la regla contra el caso real, no solo contra ejemplos sintéticos. Aplica tanto al Rule Builder de flags como a la edición de segmentos rule-based (RuleSimulator es compartido).
**Requirements**: SIM-01, SIM-02, SIM-03, SIM-04
**Depends on:** Phase 12
**Plans:** 4/4 plans complete

Plans:
- [ ] 13-01-PLAN.md — Backend: Alembic migration d002 (test_context column on feature_flags + segments) + schema/service changes
- [ ] 13-02-PLAN.md — Shell: useUserContext composable (sub/email/roles/tenant_id/product_id) exposed via Module Federation
- [ ] 13-03-PLAN.md — RuleSimulator.vue: mode/testContext props, save-test-context emit, real-context toggle
- [ ] 13-04-PLAN.md — Wire RuleBuilderView.vue + SegmentForm.vue/SegmentsView.vue to persist and recover test_context

### Phase 14: Flag Scope Targeting + List-Valued Rules

**Goal**: Los feature flags con scope no-global apuntan a una entidad concreta y las reglas soportan listas de valores: (1) **Scope targeting** — al crear/editar un feature flag, cuando el `scope` seleccionado sea `product`, `tenant` o `company`, el formulario muestra un combobox para elegir el producto/tenant/company específico al que aplica el flag; la selección se **almacena en backend** (target del scope) y el **SDK** (bootstrap + evaluación local sdk-js/sdk-python + `POST /sdk/evaluate`) activa o desactiva el flag según el scope+target definidos — un flag scoped a `product=X` no se activa para `product=Y`. (2) **List-valued rule values** — en el editor de Rules del Rule Builder, cuando el `attribute` del contexto sea una lista (ej. `roles`), el `value` de la Rule acepta una **lista de valores separados por coma** (ej. `PlatformAdmin, TenantOwner`) que hace match si **cualquiera** de los valores aplica — evitando crear una regla por cada valor específico. El operador de evaluación correspondiente debe existir con paridad en backend OPERATORS, sdk-js evaluator, sdk-python evaluator y useRuleSimulator.ts.
**Requirements**: TBD (derive at plan time: TGT-01 combobox por scope, TGT-02 persistencia del target, TGT-03 enforcement en SDK/bootstrap/evaluate, LST-01 value como lista separada por coma con match any, LST-02 paridad del operador en los 4 evaluadores)
**Depends on:** Phase 13
**Plans:** 6/6 plans complete

Plans:
- [ ] 14-01-PLAN.md — Companies backend domain (models/schemas/service/router) + Alembic d003 + BFF /companies proxy
- [ ] 14-02-PLAN.md — Backend flag target validation (FlagCreate/FlagUpdate) + bootstrap per-scope dispatch + /sdk/evaluate fix
- [ ] 14-03-PLAN.md — anyOf operator in backend/sdk-js/sdk-python + SDK company-scope guard in local evaluators
- [ ] 14-04-PLAN.md — anyOf UI: useRuleSimulator parity + RuleCard comma-input/mini-chips + RuleSimulator Matched Rule chips
- [ ] 14-05-PLAN.md — FlagForm scope-target comboboxes (tenants/products/companies lookups, validation, mutual exclusivity)
- [ ] 14-06-PLAN.md — Companies UI in mui-tenants (/companies view+table+drawer+store+service) + Shell nav button

### Phase 15: AND Rule Combination Semantics + Flags Page Filters

**Goal:** (1) Multi-rule evaluation combines with AND — a flag whose rules combine with AND evaluates true only when ALL individual rules match, false otherwise, with parity across the 4 evaluators (backend, sdk-js, sdk-python, useRuleSimulator) — implemented as opt-in flag-level `rule_combination_mode` ('first_match' legacy default | 'and'); segment conditions keep OR semantics; OR operator and rule groups deferred to a future release. (2) The `/flags` page gains client-side filters: Status, Tags, Complexity (stored `complex` boolean), Environment, and scope target (Products / Tenants / Companies / Global).
**Requirements**: AND-01, AND-02, FLT-01, FLT-02, FLT-03, FLT-04, FLT-05 (assigned at plan time — registration gap vs REQUIREMENTS.md noted in phase deferred-items.md, same as Phase 14)
**Depends on:** Phase 14
**Plans:** 4/4 plans complete

Plans:
- [ ] 15-01-PLAN.md — Backend AND mode: d004 migration + rule_combination_mode column/schemas + evaluate_flag AND branch + bootstrap field
- [ ] 15-02-PLAN.md — sdk-js + sdk-python AND-mode parity in local evaluators (TDD)
- [ ] 15-03-PLAN.md — useRuleSimulator AND mode + RuleSimulator per-rule pass/fail UI + RuleBuilderView mode selector/persistence
- [ ] 15-04-PLAN.md — /flags client-side filters (useFlagFilters composable + FlagsView filter bar) + visual checkpoint

### Phase 16: MVP2 Auditoria (Audit Log Timeline + Diff Viewer)

**Goal:** Implement the unified Audit Log per PRD_MVP3 §6 — an immutable `audit_logs` table (id, created_at, tenant_id, user_id/email, action_type, environment, target_type, target_id, payload_before/after JSON, client_ip, user_agent) populated by existing write paths (flags, segments, tenants, whitelabel, users), exposed via `GET /bff/audit-logs` (filters: environment, action_type, user_id, date range, pagination) and `GET /bff/audit-logs/{id}/diff`, with a frontend Activity Timeline view + "View Diff" modal highlighting JSON additions/removals/modifications (green/red/yellow) per the `audit-log_activity-timeline.html` mockup.
**Requirements**: AUD-01, AUD-02, AUD-03, AUD-04, AUD-05, AUD-06 (assigned at plan time — registration gap vs REQUIREMENTS.md noted in phase deferred-items.md, same as Phases 14/15)
**Depends on:** Phase 15
**Plans:** 5/5 plans complete

Plans:
- [ ] 16-01-PLAN.md — `audit` domain: AuditLog model/schemas/e001 migration, write_audit_log/list_audit_logs/compute_diff service, GET /audit-logs + GET /audit-logs/{id}/diff router, BFF audit.ts proxy (TDD)
- [ ] 16-02-PLAN.md — Instrument feature_flags + segments write paths (create/update/enable/disable/delete) to emit audit_logs entries, BFF flags.ts X-User-Email
- [ ] 16-03-PLAN.md — Instrument users/tenants/companies write paths (create/update/enable/disable/reset-mfa/delete) to emit audit_logs entries, BFF companies.ts X-User-Email
- [ ] 16-04-PLAN.md — Frontend Activity Timeline (AuditLogView.vue) + color-coded DiffModal in mui-tenants, /audit-log route, MainLayout sidebar wiring
- [ ] 16-05-PLAN.md — Gap closure: align AuditLogDiff type/DiffModal.vue to flat backend diff shape (AUD-03/AUD-06) + bff tenants.ts X-User-Email forwarding

### Phase 17: Observabilidad SLA SLO

**Goal:** Implement the Observability dashboard per PRD_MVP3 §4 — a `service_health_samples` table populated by a non-blocking Health Checker Engine polling internal components (FastAPI core, BFF, PostgreSQL, Keycloak, WebSocket gateway) every 15s, tracking SLIs (uptime, p95/p99 latency, error rate against the <1ms local / <50ms remote evaluation SLOs), exposed via `GET /bff/health/services` and `GET /bff/observability/metrics` (query params: tenant_id, range=24h/7d/30d), with a frontend dashboard showing current status, trends, and SLO breach indicators.
**Requirements**: TBD — derive OBS-01..OBS-0x at plan time from PRD_MVP3 §4, §8.1, §9 (SERVICE_HEALTH_SAMPLES table)
**Depends on:** Phase 16
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 17 to break down)

### Phase 18: Telemetry Ingestion SDK Eval Events

**Goal:** Implement the SDK eval-events ingestion pipeline per PRD_MVP3 §5, §8.2 — `POST /api/v1/sdk/eval-events` accepts batched aggregated evaluation counts (tenant_id, product_id, environment, timestamp, evaluations[{flag_key, value, hits}]) and responds `202 Accepted` in <10ms via an async buffer/queue; a background aggregator consolidates raw events into `sdk_eval_events_aggregated` (hourly buckets per tenant/product/environment/flag_key/value) and prunes old detail rows. SDKs (sdk-js/sdk-python) batch every 60s or 100 events. Frontend surfaces per-flag hit statistics. Must not degrade or block flag evaluation if ingestion is down (resilience per §10.2).
**Requirements**: TBD — derive TEL-01..TEL-0x at plan time from PRD_MVP3 §5, §8.2, §9 (SDK_EVAL_EVENTS_AGGREGATED table)
**Depends on:** Phase 17
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 18 to break down)

### Phase 19: Redis PubSub WS Scaling and Webhook Alerts

**Goal:** Implement distributed cache invalidation and proactive alerting per PRD_MVP3 §7, §8.1, §9 — when a flag changes, FastAPI publishes `{tenant_id, product_id, environment}` to a Redis Pub/Sub channel (`flag-updates`); every backend instance subscribed to that channel notifies its locally-connected SDK WebSocket clients (`{"event": "invalidate"}`) so they refetch bootstrap, enabling horizontal scaling of stateless FastAPI instances. Also implement `webhook_alert_configs` (tenant_id, url, secret_token, enabled_events, active) with CRUD via `POST/GET /bff/observability/webhooks`, and an Alert Manager that fires webhook (Slack/Teams) + email notifications on service degradation or SLO breaches detected by Phase 17's health checker.
**Requirements**: TBD — derive RTS-01..RTS-0x at plan time from PRD_MVP3 §7, §8.1, §9 (WEBHOOK_ALERT_CONFIGS table)
**Depends on:** Phase 18
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 19 to break down)

### Phase 20: Localization White Label Engine

**Goal:** Implement the multi-language White Labeling Engine end to end — a `localized_labels` table (tenant_id, company_id nullable, product_id nullable, namespace, locale, label_key, label_value, version) resolved via 3-level inheritance (Tenant → Company → Product, "override by proximity") with an in-memory cache; a `namespaces` table (eager/lazy strategy, admin-creatable) and `missing_label_reports` table; SDK two-phase hydration (`/labels/bootstrap` eager namespaces <100ms, `/labels/prefetch` lazy namespaces) plus hot-reload invalidation via the existing `ConnectionManager`/`/ws/flags/{tenant_id}` WebSocket (`INVALIDATE_NAMESPACE` broadcast); a new sdk-js `LabelClient` + `$t` Vue plugin (interpolation, missing-key reporting, reactive cache); a new Keycloak `UXWriter` role with a value-only label-edit endpoint and optimistic concurrency (409 + PRD §9.2 PI-02 message); audit logging for all namespace/label CRUD; RF-07 export (JSON + CSV) for the active Workspace Context; and a new admin micro-UI `mui-labeling` (port 5179) implementing RF-01..05 and RF-08 per `docs/prd_namespaces_keys_management.md` and the HTML prototype.
**Requirements**: LBL-01 (localized_labels table), LBL-02 (namespaces table), LBL-03 (resolve_labels 3-level inheritance), LBL-04 (in-memory cache + invalidation), LBL-05 (SDK /labels/bootstrap), LBL-06 (SDK /labels/prefetch), LBL-07 (WS INVALIDATE_NAMESPACE broadcast), LBL-08 (sdk-js LabelClient + $t plugin), LBL-09 (namespace/key CRUD + role/scope auth), LBL-10 (UXWriter role + value-only PATCH), LBL-11 (optimistic concurrency 409 PI-02), LBL-12 (audit logging), LBL-13 (missing_label_reports + RF-06 diagnostics), LBL-14 (RF-07 export JSON/CSV), LBL-15 (mui-labeling admin UI RF-01..05,08), LBL-16 (seed common namespace for existing tenant/company)
**Depends on:** Phase 19
**Plans:** 6/9 plans executed

Plans:
- [x] 20-01-PLAN.md — Backend labels domain models/schemas/migrations + g002 seed migration + UXWriter Keycloak role (LBL-01, LBL-02, LBL-16)
- [x] 20-02-PLAN.md — resolve_labels() inheritance resolver + in-memory cache + namespace/label CRUD + missing-label report upsert (LBL-03, LBL-04, LBL-13)
- [x] 20-03-PLAN.md — Admin labels router: namespace/label CRUD, UXWriter value endpoint, audit logging, 409 concurrency, missing-reports listing (LBL-09, LBL-10, LBL-11, LBL-12)
- [x] 20-04-PLAN.md — SDK /labels/bootstrap + /labels/prefetch + POST /labels/missing + INVALIDATE_NAMESPACE WS broadcast (LBL-05, LBL-06, LBL-07)
- [x] 20-05-PLAN.md — BFF bff/src/routes/labels.ts admin proxy route (supports LBL-10/LBL-09 plumbing)
- [ ] 20-06-PLAN.md — sdk-js LabelClient + createLabelPlugin ($t) + reactive cache + WS hot-reload (LBL-08)
- [ ] 20-07-PLAN.md — mui-labeling scaffold + LabelingView grid + WorkspaceContextSelector (RF-01) + NamespaceSidebar (RF-02) + KeysMatrix (RF-03) (LBL-15)
- [ ] 20-08-PLAN.md — TranslationDrawer (RF-04/RF-05) + AddKeyModal + ImportExportModal (RF-07) + DiagnosticsModal (RF-06) + dark mode (RF-08) (LBL-14, LBL-15)
- [x] 20-09-PLAN.md — Backend RF-07 export endpoint: export_namespace_json/csv + GET /labels/export (LBL-14)
