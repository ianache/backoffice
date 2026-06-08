# Architecture Research

**Domain:** Multi-tenant BackOffice — MVP2 Micro-Frontend Architecture
**Researched:** 2026-06-07
**Confidence:** HIGH (based on direct codebase inspection + verified patterns)

---

## Standard Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Browser (Single Origin)                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │             Portal Shell (Host — Vue 3, Port 5173)                   │   │
│  │  Keycloak init · Pinia · Axios interceptor · Layout · Router        │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │   │
│  │  │ mui-security  │  │ mui-tenants  │  │   mui-feature-flags     │   │   │
│  │  │  :5174        │  │   :5175      │  │       :5176             │   │   │
│  │  │ (remote)      │  │  (remote)    │  │      (remote)           │   │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────┘   │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                                │ Bearer JWT (axios interceptor)              │
└────────────────────────────────┼───────────────────────────────────────────┘
                                  │
┌────────────────────────────────▼───────────────────────────────────────────┐
│                    BFF — Node.js / Express (Port 3000)                      │
│  requireAuth (jose JWKS) · requireRole · http-proxy-middleware              │
│  X-Internal-Secret · X-User-Roles · X-User-Sub · X-User-Tenant-Id          │
└────────────┬─────────────────────────────────────────────────┬─────────────┘
             │ HTTP (internal secret)                          │ Admin REST
┌────────────▼──────────────────────────┐         ┌───────────▼──────────────┐
│  FastAPI Backend — Python (Port 8000) │         │  Keycloak IdP             │
│  SQLAlchemy async + Alembic           │         │  realm: Apps              │
│  Domains: tenants / users / flags     │         │  PKCE + ROPC              │
│  MySQL 5.6 (TEXT for JSON fields)     │         └──────────────────────────┘
└───────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| Portal Shell | Auth lifecycle, Layout, Router, shared Pinia/Axios | Vue 3 + Keycloak-JS + Pinia |
| mui-security | Users CRUD, role assignment, MFA reset | Remote Vue 3 SPA |
| mui-tenants | Tenant CRUD + product subscriptions | Remote Vue 3 SPA |
| mui-feature-flags | Flags, rule builder, segments, SDK UI | Remote Vue 3 SPA |
| BFF | JWT validation, role enforcement, proxy to backend | Express + jose + http-proxy-middleware |
| Backend | Domain logic, DB, Keycloak admin calls | FastAPI + SQLAlchemy + Alembic |
| Keycloak | Token issuance, realm roles, PKCE/ROPC | External IdP |

---

## Recommended Project Structure

### Monorepo Changes Required for MVP2

The root `package.json` has no `workspaces` field yet (only scripts). Add workspaces and two new packages:

```
backoffice-platform/              # root — pnpm workspaces
├── package.json                  # ADD: "workspaces": ["portal","bff","microuis/*"]
├── portal/                       # MODIFY: shell cutover (remove domain views)
│   ├── src/
│   │   ├── main.ts               # unchanged — Pinia + Keycloak init here
│   │   ├── plugins/
│   │   │   ├── keycloak.ts       # unchanged
│   │   │   └── federation.ts     # NEW: loadMicroUIRoutes() helper
│   │   ├── stores/
│   │   │   ├── auth.ts           # unchanged — shared via federation
│   │   │   ├── toast.ts          # unchanged — shared via federation
│   │   │   └── ui.ts             # unchanged — shared via federation
│   │   ├── views/
│   │   │   ├── DashboardView.vue # keep — shell owns Dashboard
│   │   │   ├── LoginView.vue     # keep — shell owns auth
│   │   │   └── UnauthorizedView.vue # keep
│   │   ├── components/layout/    # keep — shell owns chrome
│   │   └── router/
│   │       └── index.ts          # MODIFY: addRoute() from remotes
│   └── vite.config.ts            # MODIFY: add federation() host config
│
├── bff/                          # MODIFY: add /products and /sdk routes
│   └── src/
│       ├── routes/
│       │   ├── products.ts       # NEW
│       │   └── sdk.ts            # NEW: bootstrap, evaluate, eval-events
│       └── index.ts              # MODIFY: mount new routers
│
├── backend/                      # MODIFY: new domains + alembic migrations
│   └── app/
│       ├── domains/
│       │   ├── feature_flags/
│       │   │   ├── models.py     # MODIFY: Segment add type+rules cols
│       │   │   ├── schemas.py    # MODIFY: SegmentCreate/Response
│       │   │   ├── service.py    # MODIFY: rule-based segment eval
│       │   │   └── router.py     # MODIFY: segment PATCH endpoint + SDK routes
│       │   ├── products/         # NEW domain
│       │   │   ├── __init__.py
│       │   │   ├── models.py     # Product + TenantProduct + FlagProduct
│       │   │   ├── schemas.py
│       │   │   ├── service.py
│       │   │   └── router.py
│       │   └── tenants/
│       │       ├── models.py     # MODIFY: remove products JSON field
│       │       └── service.py    # MODIFY: product subscription via junction table
│       ├── services/
│       │   └── ws_hub.py         # NEW: WebSocket connection manager
│       ├── main.py               # MODIFY: include products_router + sdk_router + ws
│       └── alembic/versions/
│           └── 002_mvp2_*.py     # NEW migration
│
└── microuis/
    ├── mui-security/             # SCAFFOLD: migrate UsersView + UserDrawer here
    │   ├── src/
    │   │   ├── main.ts           # standalone dev entry (consumes shared pinia)
    │   │   ├── router/routes.ts  # EXPOSES via federation
    │   │   ├── views/UsersView.vue
    │   │   └── components/users/
    │   └── vite.config.ts        # federation remote config
    ├── mui-tenants/              # SCAFFOLD: migrate TenantsView + TenantDrawer here
    │   ├── src/
    │   │   ├── router/routes.ts  # EXPOSES via federation
    │   │   ├── views/
    │   │   │   ├── TenantsView.vue
    │   │   │   └── ProductsView.vue  # NEW
    │   │   └── components/
    │   │       ├── tenants/      # migrated from portal
    │   │       └── products/     # NEW
    │   └── vite.config.ts
    └── mui-feature-flags/        # SCAFFOLD: migrate FlagsView + RuleBuilderView here
        ├── src/
        │   ├── router/routes.ts  # EXPOSES via federation
        │   ├── views/
        │   │   ├── FlagsView.vue
        │   │   ├── RuleBuilderView.vue
        │   │   └── SegmentsView.vue  # NEW
        │   └── components/flags/  # migrated from portal
        └── vite.config.ts
```

### Structure Rationale

- **portal/ keeps auth + layout:** Keycloak and shared Pinia must live in the Shell because they must be initialized before any remote is loaded. Moving them to a remote would break the singleton guarantee.
- **microuis/ as workspace packages:** pnpm hoists `vue`, `pinia`, `axios`, `vue-router` to the root `node_modules`, making the `singleton: true` federation config reliable since the same physical module is resolved.
- **backend/domains/products/ as new domain:** Follows the established `domains/<name>/{models,schemas,service,router}` pattern. Do not merge into tenants domain — Products is an independent catalog entity.
- **ws_hub.py as a service:** WebSocket state (connected clients) must be a process-level singleton, not scoped to a request. A module-level `ConnectionManager` in `services/` fits the existing service layer pattern.

---

## Architectural Patterns

### Pattern 1: Module Federation Shared Singleton for Pinia + Keycloak

**What:** Shell creates Pinia instance and calls `app.use(pinia)` before any remote loads. Remotes list `pinia`, `vue`, `vue-router`, `axios` in `shared` with `singleton: true` and `requiredVersion`. Federation resolves to the Shell's already-running copy.

**When to use:** Any store defined in the Shell (auth, toast, ui) needs to be readable by MUI components without prop drilling or event buses.

**Trade-offs:** Remotes cannot call `createPinia()` themselves; they must call `useXxxStore()` directly, which works because Pinia is already active. Version mismatch between shell and remote `package.json` will silently load two instances — pin exact versions.

**Shell vite.config.ts (fragment):**
```typescript
federation({
  name: 'portal-shell',
  remotes: {
    mui_security:      'http://localhost:5174/assets/remoteEntry.js',
    mui_tenants:       'http://localhost:5175/assets/remoteEntry.js',
    mui_feature_flags: 'http://localhost:5176/assets/remoteEntry.js',
  },
  shared: {
    vue:        { singleton: true, requiredVersion: '^3.4.29' },
    'vue-router': { singleton: true, requiredVersion: '^4.4.0' },
    pinia:      { singleton: true, requiredVersion: '^2.2.2' },
    axios:      { singleton: true, requiredVersion: '^1.7.2' },
  },
})
```

**Remote vite.config.ts (fragment, same for all three MUIs):**
```typescript
federation({
  name: 'mui_security',
  filename: 'remoteEntry.js',
  exposes: { './routes': './src/router/routes.ts' },
  shared: {
    vue:        { singleton: true, requiredVersion: '^3.4.29' },
    'vue-router': { singleton: true, requiredVersion: '^4.4.0' },
    pinia:      { singleton: true, requiredVersion: '^2.2.2' },
    axios:      { singleton: true, requiredVersion: '^1.7.2' },
  },
})
```

### Pattern 2: Token Flow — Shell owns Keycloak, MUIs consume via shared Axios

**What:** `portal/src/services/api.ts` (the Axios instance with the Keycloak interceptor) is exposed as a federation shared module. Remotes import it instead of creating their own axios instances.

**Current state:** `api.ts` imports the `keycloak` singleton directly from `portal/src/plugins/keycloak.ts`. Since both `keycloak` and `api` live in the Shell and are in the shared list, remotes get the same instance.

**Token propagation path:**
```
keycloak.token (Shell)
    ↓ (axios request interceptor — updateToken(30) + Authorization header)
api.ts instance (shared singleton)
    ↓ (consumed by MUI components via import)
BFF requireAuth middleware (jose JWKS verification)
    ↓
X-User-Roles / X-User-Sub / X-User-Tenant-Id headers
    ↓
FastAPI backend verify_internal_secret + header-based RBAC
```

**When to use:** Every MUI that calls the BFF. Do not create new axios instances in remotes.

**Trade-offs:** `api.ts` must also be in `shared` config. This adds one more singleton to manage but avoids the alternative (window.postMessage token passing) which is fragile.

### Pattern 3: Dynamic Route Registration from Remotes

**What:** Shell router starts with only shell-owned routes (/, /login, /unauthorized, /dashboard). After Keycloak auth completes, `loadMicroUIRoutes()` dynamically imports `./routes` from each remote and calls `router.addRoute()`.

**When to use:** Clean cutover (all domain routes move to remotes). No co-existence of old portal routes and new remote routes.

**Shell router/index.ts changes:**
```typescript
export async function loadMicroUIRoutes(router: Router) {
  const remotes = [
    () => import('mui_security/routes'),
    () => import('mui_tenants/routes'),
    () => import('mui_feature_flags/routes'),
  ]
  for (const load of remotes) {
    try {
      const mod = await load()
      ;(mod.routes as RouteRecordRaw[]).forEach(r => router.addRoute(r))
    } catch (e) {
      console.warn('[Shell] Failed to load remote routes', e)
    }
  }
}
```

**Trade-offs:** Route guards (`requiresAuth`, `roles`) must still be applied in the shell's `beforeEach` — remotes declare route meta but the shell enforces it. This is correct: security lives in the shell.

### Pattern 4: Products Domain — Relational Migration from JSON field

**What:** `tenants.products` is currently a `JSON` column (SQLAlchemy `mapped_column(JSON)`). MVP2 promotes Products to a first-class `products` table with a `tenant_products` join table.

**Migration path (two-step, safe for MySQL 5.6):**

Step 1 — Additive migration (new tables, keep old column):
```python
# alembic/versions/002_add_products_tables.py
def upgrade():
    op.create_table('products',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('labels', sa.Text, nullable=True),   # JSON as TEXT — MySQL 5.6
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
    )
    op.create_table('tenant_products',
        sa.Column('tenant_id', sa.Integer, sa.ForeignKey('tenants.id'), primary_key=True),
        sa.Column('product_id', sa.String(50), sa.ForeignKey('products.id'), primary_key=True),
    )
    op.create_table('flag_products',
        sa.Column('flag_id', sa.Integer, sa.ForeignKey('feature_flags.id'), primary_key=True),
        sa.Column('product_id', sa.String(50), sa.ForeignKey('products.id'), primary_key=True),
    )
```

Step 2 — Data migration script (run once, outside Alembic):
```python
# scripts/migrate_tenant_products.py
# Read tenants.products JSON array → insert rows into tenant_products
# Run AFTER products catalog seeded, BEFORE deploying new BFF routes
```

Step 3 — Cleanup migration (separate version, deploy after verification):
```python
# alembic/versions/003_drop_tenants_products_json.py
def upgrade():
    op.drop_column('tenants', 'products')
```

**Why not one step:** MySQL 5.6 does not support transactional DDL. Combining table creation, data migration, and column drop in one migration risks data loss if the data step fails mid-way.

**tenants/models.py change:** Remove `products: Mapped[List[str]] = mapped_column(JSON, ...)`. Add relationship via `TenantProduct` model in `products/models.py`.

### Pattern 5: Advanced Segments — Additive Column Migration

**What:** `segments` table needs two new columns: `type VARCHAR(20)` (manual|rule_based) and `rules TEXT` (JSON array, same pattern as `feature_flags.rules`).

**Migration:**
```python
def upgrade():
    op.add_column('segments',
        sa.Column('type', sa.String(20), server_default='manual', nullable=False))
    op.add_column('segments',
        sa.Column('rules', sa.Text, nullable=True))
```

**service.py changes:** `_evaluate_rule()` already exists in `feature_flags/service.py`. For rule-based segment evaluation, import and reuse `_evaluate_rule` — do not duplicate. Create `evaluate_segment(segment, context) -> bool` in the same service file.

**schemas.py changes:** `SegmentCreate` adds `type: str = 'manual'` and `rules: List[RuleSchema] = []`. `SegmentResponse` adds same fields with the existing `model_validator` pattern for TEXT→list parsing.

### Pattern 6: SDK Bootstrap Endpoint — Composing Existing Evaluation Logic

**What:** `GET /api/v1/sdk/bootstrap?tenant_id=X&product_id=Y&environment=Z` returns a consolidated snapshot of all flags relevant to the given scope. The SDK caches this and evaluates locally.

**How it composes existing code:**

```
sdk/bootstrap (new FastAPI router)
    ↓
service.list_flags(db, scope_filter=['global','tenant','product'], tenant_id=X)
    ↓ (existing function, unchanged)
returns List[FeatureFlag]
    ↓
bootstrap serializes as {flag_key: {rules, default_val, rollout, segments}}
```

The bootstrap does NOT call `evaluate_flag()`. It returns raw flag configs. Evaluation happens client-side in the SDK using the same operator logic (ported to TypeScript in the JS SDK, already exists in `src/composables/useRuleSimulator.ts`).

**`POST /api/v1/sdk/evaluate`** — delegates to the existing `evaluate_flag()` function with the posted context. This is a thin wrapper:

```python
@sdk_router.post("/evaluate")
async def remote_evaluate(payload: EvaluateRequest, db: AsyncSession = Depends(get_db)):
    flags = await service.list_flags(db, tenant_id=payload.tenant_id)
    result = service.evaluate_flag(flags, payload.context)
    return {"result": result}
```

**`POST /api/v1/sdk/eval-events`** — append-only telemetry ingestion. Store in a new `sdk_events` table (id, flag_key, tenant_id, result, evaluated_at) or write to a log file in v1.1 for simplicity.

### Pattern 7: WebSocket Hub for Real-Time Cache Invalidation

**What:** When a flag is saved (POST/PATCH on `/flags`), the backend broadcasts an invalidation message to all connected SDK clients subscribed to that tenant.

**Implementation in `backend/app/services/ws_hub.py`:**

```python
from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, ws: WebSocket, tenant_id: str):
        await ws.accept()
        self._connections[tenant_id].append(ws)

    def disconnect(self, ws: WebSocket, tenant_id: str):
        self._connections[tenant_id].remove(ws)

    async def broadcast(self, tenant_id: str, message: dict):
        dead = []
        for ws in self._connections.get(tenant_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[tenant_id].remove(ws)

manager = ConnectionManager()  # module-level singleton
```

**WebSocket endpoint in `main.py` or `sdk/router.py`:**
```python
@app.websocket("/ws/flags/{tenant_id}")
async def ws_flags(websocket: WebSocket, tenant_id: str):
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
```

**Hook into flag mutations in `router.py`:**
```python
# After update_flag() succeeds:
await manager.broadcast(tenant_id, {"type": "flags:invalidate", "tenant_id": tenant_id})
```

**BFF WebSocket proxy:** The BFF currently only handles HTTP. For WebSocket, add a WS proxy route in `bff/src/routes/sdk.ts` using `http-proxy-middleware` with `ws: true`. The JWT validation still applies via the `?token=` query param pattern (standard for browser WebSocket since headers are not supported).

---

## Data Flow

### Request Flow — Shell to Backend

```
User action in MUI component
    ↓
import api from '@/services/api'  (shared singleton from Shell)
    ↓
axios interceptor: keycloak.updateToken(30) + Authorization: Bearer <jwt>
    ↓
BFF /tenants | /users | /flags | /products | /sdk/...
    ↓
requireAuth: jwtVerify(token, JWKS) → req.user = {sub, roles, tenantId}
requireRole: check roles array
    ↓
http-proxy-middleware → FastAPI backend
    + X-Internal-Secret
    + X-User-Roles
    + X-User-Sub
    + X-User-Tenant-Id
    ↓
FastAPI router: verify_internal_secret + header-based RBAC
    ↓
service layer: SQLAlchemy async queries
    ↓
MySQL 5.6
```

### State Management

```
Shell main.ts
    createPinia() + pinia.use(persistedstate)
    useAuthStore(pinia).init()  ← Keycloak PKCE
    app.use(pinia)
    loadMicroUIRoutes()         ← federation dynamic import
         ↓
MUI components
    useAuthStore()   ← reads Shell's Pinia (singleton via federation shared)
    useToastStore()  ← same
    useFlagsStore()  ← MUI-local store, defined in mui-feature-flags
```

### Key Data Flows

1. **Auth bootstrap:** `main.ts` calls `authStore.init()` before router mount → no flash of unauthenticated content. Remote routes load after auth resolves. This existing pattern is preserved unchanged.

2. **Products subscription:** `PUT /bff/tenants/:id/products` → BFF proxies to `PUT /tenants/:id/products` in backend → service deletes all rows in `tenant_products` for that tenant, inserts new set. Atomic replacement is simpler than diff-based sync for MVP2.

3. **SDK bootstrap flow:** SDK client calls `GET /bff/sdk/bootstrap?tenant_id&product_id&environment` → BFF proxies to backend (requires new BFF route with `requireAuth` + SDK client authentication) → backend calls `list_flags()` → serializes full flag config snapshot → SDK stores in memory.

4. **Flag save → WebSocket invalidation:** PATCH /flags/:id succeeds → router layer calls `manager.broadcast()` → connected SDK clients receive `{type: "flags:invalidate"}` → clients re-fetch bootstrap.

---

## Integration Points

### New vs Modified Files — Explicit List

#### Portal (Shell) — MODIFIED

| File | Change Type | What Changes |
|------|-------------|--------------|
| `portal/vite.config.ts` | Modify | Add `@originjs/vite-plugin-federation` host config |
| `portal/package.json` | Modify | Add `@originjs/vite-plugin-federation` dep |
| `portal/src/router/index.ts` | Modify | Remove domain routes; add `loadMicroUIRoutes()` |
| `portal/src/plugins/federation.ts` | New | `loadMicroUIRoutes()` helper function |
| `portal/src/components/layout/MainLayout.vue` | Modify | Remove domain-specific nav items; nav becomes driven by roles + registered routes |
| `portal/src/views/TenantsView.vue` | Delete | Moved to mui-tenants |
| `portal/src/views/UsersView.vue` | Delete | Moved to mui-security |
| `portal/src/views/FlagsView.vue` | Delete | Moved to mui-feature-flags |
| `portal/src/views/RuleBuilderView.vue` | Delete | Moved to mui-feature-flags |
| `portal/src/services/api.ts` | Modify | Add to federation `shared` list |

#### BFF — MODIFIED/NEW

| File | Change Type | What Changes |
|------|-------------|--------------|
| `bff/src/routes/products.ts` | New | CRUD proxy for `/products` |
| `bff/src/routes/sdk.ts` | New | Proxy for `/sdk/bootstrap`, `/sdk/evaluate`, `/sdk/eval-events` + WS proxy |
| `bff/src/index.ts` | Modify | Mount `productsRouter` and `sdkRouter` |

#### Backend — MODIFIED/NEW

| File | Change Type | What Changes |
|------|-------------|--------------|
| `backend/app/domains/products/` | New domain | models, schemas, service, router |
| `backend/app/domains/feature_flags/models.py` | Modify | Add `type` + `rules` cols to Segment |
| `backend/app/domains/feature_flags/schemas.py` | Modify | Update SegmentCreate/Response + new SegmentUpdate |
| `backend/app/domains/feature_flags/service.py` | Modify | Add rule-based segment eval + `_evaluate_segment()` |
| `backend/app/domains/feature_flags/router.py` | Modify | Add PATCH /segments/:id + SDK endpoints |
| `backend/app/domains/tenants/models.py` | Modify | Remove `products` JSON column (Step 3 migration only) |
| `backend/app/domains/tenants/service.py` | Modify | Replace JSON-based product list with junction table ops |
| `backend/app/services/ws_hub.py` | New | `ConnectionManager` singleton |
| `backend/app/main.py` | Modify | Include products_router, sdk router, WebSocket endpoint |
| `backend/alembic/versions/002_*.py` | New | Add products, tenant_products, flag_products tables |
| `backend/alembic/versions/003_*.py` | New | Add type+rules to segments; drop tenants.products (later) |

#### Micro-UIs — NEW PACKAGES

| Package | Scaffolding Needed | Core Files |
|---------|-------------------|------------|
| `microuis/mui-security` | Exists (stub) | `vite.config.ts` (add federation), `src/router/routes.ts`, migrate user views/components |
| `microuis/mui-tenants` | New | Full scaffold + migrate tenant views + new ProductsView |
| `microuis/mui-feature-flags` | New | Full scaffold + migrate flag views + new SegmentsView |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Keycloak | PKCE init in Shell `main.ts`; ROPC for test login; JWKS verification in BFF | Existing pattern, no changes for MVP2 |
| MySQL 5.6 | SQLAlchemy async + TEXT for JSON fields | No native JSON column type; maintain TEXT + json.dumps/loads pattern |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Shell ↔ MUI remotes | Vite Module Federation (runtime JS loading) | `shared: singleton` for vue/pinia/axios |
| Shell stores ↔ MUI components | Pinia singleton (same JS module instance) | MUIs call `useAuthStore()` directly |
| MUI components ↔ BFF | Shared Axios instance (Shell's `api.ts`) | Token injection via interceptor |
| BFF ↔ Backend | HTTP proxy with internal secret header | Existing pattern; extend for new routes |
| Backend flag mutations ↔ SDK clients | WebSocket broadcast | New: `ws_hub.ConnectionManager` |
| SDK clients ↔ Backend | WebSocket `/ws/flags/{tenant_id}` | BFF proxies with `ws: true` |

---

## Build Order for Phases

### Rationale

Dependencies flow strictly: DB schema → Backend domain → BFF routes → Shell/MUI integration. The Shell must be refactored before any MUI can work in federation mode. Products must be a DB entity before the MUIs can display them.

### Suggested Phase Order

**Phase 1 — Backend: Products domain + DB migration**
- Why first: Products table is a dependency for MUIs that need product selectors (mui-tenants, mui-feature-flags). Also unblocks BFF route work.
- Deliverables: `domains/products/`, Alembic migrations 002 (additive), products CRUD endpoints, tenant_products junction table. `tenants.products` JSON column kept for now (safe parallel operation).
- No frontend changes needed yet.

**Phase 2 — Backend: Advanced Segments + SDK endpoints + WebSocket hub**
- Why second: SDK endpoints reuse existing `list_flags()` and `evaluate_flag()` — safe to add without touching existing flag logic. Segment columns are additive (no breaking change to existing segment responses because `type` has a server default and `rules` is nullable).
- Deliverables: `segments.type` + `segments.rules` columns, `evaluate_segment()`, SDK router (`/sdk/bootstrap`, `/sdk/evaluate`, `/sdk/eval-events`), `ws_hub.py`, WebSocket endpoint.

**Phase 3 — BFF: New routes for Products and SDK**
- Why third: Can only be built after backend endpoints exist.
- Deliverables: `bff/src/routes/products.ts`, `bff/src/routes/sdk.ts` (HTTP + WS proxy), mount in `index.ts`.

**Phase 4 — Shell Cutover: Vite Module Federation host config**
- Why fourth: Shell refactoring is the highest-risk step. Do it after the backend and BFF are stable so the MUIs have real data to work with from day one.
- Deliverables: Shell `vite.config.ts` with federation host config, `federation.ts` plugin, `router/index.ts` changes, remove migrated views. Verify auth store singleton works end-to-end with at least one remote stub.

**Phase 5 — mui-tenants: Scaffold + migrate + Products UI**
- Why fifth: Simplest domain (PlatformAdmin only, no drag-and-drop). Good first remote to prove the federation pattern works.
- Deliverables: New `microuis/mui-tenants/` package, migrate `TenantsView` + tenant components, add `ProductsView` (CRUD catalog + tenant subscriptions).

**Phase 6 — mui-security: Scaffold + migrate**
- Why sixth: Users domain is independent of Products; can proceed in parallel with mui-tenants if bandwidth allows, but lower priority because v1.0 user management was fully functional.
- Deliverables: New `microuis/mui-security/` src files in the stub package, migrate `UsersView` + user components.

**Phase 7 — mui-feature-flags: Scaffold + migrate + Advanced Segments + SDK UI**
- Why last: Highest complexity (drag-and-drop rule builder, new segment type UI, SDK connection indicator). Depends on backend SDK endpoints (Phase 2) and the shell federation pattern being proven (Phase 4).
- Deliverables: New `microuis/mui-feature-flags/` package, migrate flags + rule builder + existing segments, add `SegmentsView` with type selector and rule-based editor, add SDK connection indicator in layout.

---

## Anti-Patterns

### Anti-Pattern 1: Initializing Keycloak in Each Remote

**What people do:** Add `keycloak.init()` to each MUI's `main.ts` for standalone dev convenience, then forget to strip it in production mode.

**Why it's wrong:** Two `keycloak.init()` calls on the same Keycloak instance throw: "A 'Keycloak' instance can only be initialized once." Even if guarded, two instances means two token refresh intervals and split auth state.

**Do this instead:** Shell always owns Keycloak init. For standalone remote dev, inject a mock auth store via `import.meta.env.VITE_STANDALONE_MODE === 'true'` that reads a token from `sessionStorage` (same mechanism as the existing `VITE_E2E_SKIP_AUTH` pattern).

### Anti-Pattern 2: Duplicating `api.ts` in Each Remote

**What people do:** Create `microuis/mui-security/src/services/api.ts` to avoid cross-package imports.

**Why it's wrong:** Creates a second Axios instance without the Keycloak interceptor. Requests go to BFF without a token. Also creates two instances of Axios even if the token is manually injected, defeating the singleton.

**Do this instead:** Expose `api.ts` from the Shell via federation `exposes` and add it to `shared`. Remotes `import api from 'portal-shell/api'` (one import, one instance).

### Anti-Pattern 3: Three-Step Products Migration Done as One Alembic Revision

**What people do:** Combine `CREATE TABLE products`, data copy from `tenants.products` JSON, and `DROP COLUMN tenants.products` in a single migration revision.

**Why it's wrong:** MySQL 5.6 has no transactional DDL. If the data copy fails mid-way, the column is already dropped. Recovery requires manual intervention. The existing codebase would also break immediately since the `Tenant` model still references `products`.

**Do this instead:** Three separate revisions across at least two deploys. Revision 002 adds the new tables. Data migration script runs separately. Revision 003 (scheduled cleanup, next sprint) drops the column after the new BFF routes are verified in production.

### Anti-Pattern 4: Putting Business Logic in the Shell

**What people do:** Add `ProductsView.vue` to the Shell because it's "quick" and the shell already has routing.

**Why it's wrong:** Defeats the entire point of the Shell cutover. The Shell would grow back into a monolith and each deploy would require building all domains together.

**Do this instead:** Shell only owns Dashboard, Login, Unauthorized, and the MainLayout chrome. Every domain view lives in its MUI. If a feature is truly cross-cutting (e.g., a global notification system), it stays in a Shell store, not a view.

### Anti-Pattern 5: WebSocket Authentication via URL Token Without Expiry Check

**What people do:** Pass `?token=<jwt>` in the WebSocket URL without checking token expiry on the server.

**Why it's wrong:** WebSocket connections can live for hours. A JWT passed at connection time could expire and the client would still receive flag updates. Malicious users could also replay an old token.

**Do this instead:** Backend WebSocket endpoint validates the JWT at connect time via `verify_internal_secret` equivalent (or passes through BFF which validates via jose). Additionally, send periodic ping/pong and close connections that stop responding. The SDK should reconnect and re-authenticate on disconnect.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k SDK clients | Single process WebSocket hub in FastAPI; in-memory connection list is fine |
| 1k-10k SDK clients | Add Redis Pub/Sub; `ConnectionManager.broadcast()` publishes to Redis instead of iterating local list; multiple FastAPI workers each subscribe |
| 10k+ SDK clients | Separate WebSocket gateway service; Server-Sent Events as simpler alternative to WS for one-way invalidation |

**First bottleneck for MVP2:** The WebSocket hub is in-process and does not survive horizontal scaling. This is acceptable for v1.1 with a single worker. Add Redis Pub/Sub before horizontal scaling.

**Second bottleneck:** SDK bootstrap endpoint hits the DB on every client initialization. Add an in-memory LRU cache (per tenant_id + environment) with TTL=60s in the backend before this becomes a problem.

---

## Sources

- Codebase direct inspection: `portal/src/main.ts`, `portal/src/plugins/keycloak.ts`, `portal/src/stores/auth.ts`, `portal/src/services/api.ts`, `backend/app/domains/feature_flags/service.py`, `backend/app/domains/feature_flags/models.py`, `backend/app/domains/tenants/models.py`, `bff/src/middleware/auth.ts`
- `docs/micro_ui_proposal.md` — existing architectural proposal with federation config examples (MEDIUM confidence, project-internal)
- [@originjs/vite-plugin-federation GitHub](https://github.com/originjs/vite-plugin-federation) — shared singleton pattern for Pinia (MEDIUM confidence, WebSearch verified)
- [Pinia with microfrontends discussion](https://github.com/vuejs/pinia/discussions/1968) — `getActivePinia` error cause and fix (MEDIUM confidence)
- [FastAPI WebSockets official docs](https://fastapi.tiangolo.com/advanced/websockets/) — ConnectionManager broadcast pattern (HIGH confidence)
- Alembic official docs — `op.add_column` with `sa.Text` for MySQL compatibility (HIGH confidence)
- PRD_MVP2.md — data model, ICD endpoints, feature requirements (HIGH confidence, project-internal)

---

*Architecture research for: BackOffice Multi-Tenant Platform MVP2*
*Researched: 2026-06-07*
