# Phase 20: Localization White Label Engine - Research

**Researched:** 2026-06-13
**Domain:** Multi-tenant label/translation engine (backend domain + BFF + Vue SDK + admin micro-UI)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### MVP Scope Slice
- Single Phase 20, broken into multiple plans/waves by the planner — covers engine + admin UI + SDK together.
- Admin UI must-have RFs for v1: RF-01 (Workspace Context Selector), RF-02 (Namespace sidebar + CRUD), RF-03 (Key matrix + filters), RF-04 (Key editor + parameter validation), RF-05 (Inheritance tree + restore override), RF-08 (Dark mode).
- Vue 3 `$t` plugin + missing-key reporting is added to the existing `sdk/sdk-js` package (new "labels" module alongside the flag evaluator) — not a separate package, not portal-only.
- Hot-reload (WS `INVALIDATE_NAMESPACE`) is IN SCOPE for v1. Reuse the existing in-process `ConnectionManager` + per-tenant WebSocket pattern (`backend/app/ws/connection_manager.py`, `backend/app/domains/sdk/ws_router.py`) — do NOT wait for Phase 19's Redis pub/sub.

#### Locales & Seed Content
- v1 supports exactly two locales: `es_PE` and `en_US` (matches design doc examples).
- Seed the `common` namespace (eager-load) with realistic nav/button labels (e.g., `btn_aceptar`/`btn_cancelar`) for an existing tenant, PLUS 1-2 company-level overrides to demonstrate the inheritance cascade in the UI.
- Seed data targets EXISTING tenant/company/product records already in the dev DB (from Phases 2 and 7) — do not fabricate a new demo hierarchy.
- Namespaces are fully admin-creatable from day one (RF-02: create via modal with id/strategy/description, unique-ID validation) — no hardcoded namespace list. `common` is seeded as starter data but the create flow works identically for new namespaces.

#### Roles & Permissions
- Add a new Keycloak role `UXWriter`. Backend enforces that `UXWriter` can only update `label_value` on existing keys (no namespace CRUD, no key/structure creation) — matches PRD §4 row exactly.
- For PlatformAdmin / TenantAdmin (TenantOwner) / ProductManager, mirror the existing scope-checking pattern from `backend/app/domains/feature_flags/router.py` (the `allowed_scopes` / role-based authorization helper) applied to namespaces and labels endpoints.
- "Their own" tenant/company/product for non-PlatformAdmin roles comes from Keycloak token claims, same as the existing tenants/feature_flags domains — restricts Workspace Context Selector options accordingly.

#### Diagnostics & Import/Export (RF-06 / RF-07)
- RF-06 (Missing Keys panel) ships in v1 via a SELF-CONTAINED `missing_label_reports`-style table/endpoint — independent of Phase 18's telemetry pipeline (which has 0 plans / not built).
- Miss trigger: the SDK `$t` plugin calls `reportMissingLabel(namespace, key)` (per design doc §5A), which posts to a BFF/backend endpoint. Repeated misses increment a hit counter; panel shows namespace, missing key, hits, last reported (per PRD RF-06).
- `quickCreateMissing()` flow (pre-fill create-key form from a missing-key row) is part of RF-06 v1.
- RF-07 v1 = EXPORT ONLY (JSON for SDK bootstrap shape + CSV for translators), for the active Workspace Context. Import (drag-and-drop, overwrite/skip conflict resolution) is DEFERRED to a follow-up.

### Claude's Discretion
- Exact `localized_labels` schema details beyond what's specified (indexes, version field type) — follow PRD §7 (optimistic concurrency via `version`) and existing model conventions (MySQL 5.6-safe TEXT for JSON-ish fields like `params`).
- Cache implementation details (in-memory vs Redis-backed per design doc §3) — design doc shows Redis; confirm what's already available in this environment and adapt accordingly.
- Exact shape of the `missing_label_reports` table and dedup/hit-counting mechanism.
- Micro-UI module name/location and Shell nav placement for the new admin module — follow the `mui-feature-flags`/`mui-tenants` Module Federation pattern.
- BFF route naming/structure for labels endpoints — follow `bff/src/routes/flags.ts` / `tenants.ts` conventions.

### Deferred Ideas (OUT OF SCOPE)
- RF-07 Import (drag-and-drop JSON/CSV upload with overwrite/skip conflict resolution) — follow-up phase once export is proven.
- Flutter `LabelEngine` (offline-capable SDK with shared_preferences) from design doc §5B — no Flutter codebase exists in this project; out of scope unless a Flutter client is introduced later.
- Full integration of missing-key diagnostics with Phase 18's telemetry/aggregation pipeline — v1 uses a self-contained log; unify with Phase 18 once that pipeline is built.
- Redis-backed distributed cache + Redis pub/sub for hot-reload (Phase 19 scope) — v1 hot-reload uses the existing in-process WS pattern; multi-instance scaling remains Phase 19's concern.
</user_constraints>

## Summary

Phase 20 is the largest single phase in the project: a new `localized_labels` domain (models/schemas/service/router) mirroring `feature_flags` scoping conventions, plus a `namespaces` table, a `missing_label_reports` table, a BFF resolver layer with in-memory caching, two new SDK bootstrap-style endpoints (`/labels/bootstrap`, `/labels/prefetch`), WS `INVALIDATE_NAMESPACE` broadcast reusing the existing `ConnectionManager`, a new "labels" module in `sdk/sdk-js` (Vue 3 `$t` plugin + `reportMissingLabel`), a new BFF route (`labels.ts`), and a new admin micro-UI (`mui-labeling` or similar) built against the existing HTML prototype.

**Critical environment finding:** There is **no Redis** anywhere in this codebase — not in `backend/requirements.txt`, not in `docker-compose.yml`, no `redis`/`aioredis` import anywhere except as prose in the design docs. The design doc's `resolve_labels()` Python snippet using `redis.Redis(...)` is illustrative/conceptual only. **Recommendation: implement an in-process dict-based cache** (module-level or `app.state`-attached `dict[str, dict]`) keyed by `f"{tenant_id}:{company_id}:{product_id}:{namespace}:{locale}"`, invalidated synchronously on label CRUD (matching the existing in-memory `ConnectionManager` philosophy — "Redis upgrade path: replace cache body, public interface stays the same" comment pattern already used in `connection_manager.py`).

**Primary recommendation:** Build this phase as a close structural mirror of `feature_flags` (models/schemas/service/router + scope/role auth helper) plus `audit`(write_audit_log integration) plus `sdk`(bootstrap/ws_router pattern), reusing every existing convention rather than introducing new patterns. The admin micro-UI is a near-literal Vue port of the provided HTML prototype's DOM structure and state machine.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|---------------|
| FastAPI | 0.115.5 (pinned, requirements.txt) | Backend domain router (`localized_labels`, `namespaces`, `missing_label_reports`) | Already the project's framework; no new dependency needed |
| SQLAlchemy 2.0 (async) | 2.0.35 | ORM models for new tables | Matches `feature_flags/models.py` `Mapped[...]` style |
| Alembic | 1.13.3 | New migration(s) for `localized_labels`, `namespaces`, `missing_label_reports`, plus seed data via `INSERT IGNORE` | Same 3-step expand/backfill/cleanup convention is NOT needed here (net-new tables, no backfill from existing column) — single additive migration like `e001_create_audit_logs_table.py`, plus optional data-seed migration following `b002_backfill_tenant_subscriptions.py`'s `SELECT ... FROM tenants/companies/products` + `INSERT IGNORE` pattern |
| Vue 3 + Pinia + Vue Router | workspace-pinned | New micro-UI `mui-labeling` (or similar name) | Mirrors `mui-feature-flags` exactly |
| @originjs/vite-plugin-federation | 1.4.1 | Module Federation for new micro-UI | Already scaffolded pattern — do not upgrade beyond Vite 5.x per STATE.md decision |
| TypeScript | workspace-pinned | `sdk/sdk-js` new `labels.ts`/`i18n.ts` module | Matches existing evaluator/telemetry/websocket modules |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Express + http-proxy-middleware | bff workspace-pinned | New `bff/src/routes/labels.ts` | Proxy admin CRUD + SDK bootstrap/prefetch/WS to backend, mirroring `flags.ts` (admin) and `sdk.ts` (SDK passthrough) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Redis-backed cache (design doc §3) | In-process Python dict cache | No Redis client/service exists in this repo (verified absent from requirements.txt and docker-compose.yml). In-memory cache matches the existing `ConnectionManager` "Redis upgrade path" pattern; correct for single-instance MVP2. Document the upgrade path in code comments exactly as `connection_manager.py` does. |
| Separate `sdk-i18n` package | New module inside `sdk/sdk-js` | CONTEXT.md locks this — extend existing package, follow `evaluator.ts`/`telemetry.ts` file-per-concern convention |
| SSE for hot-reload | WebSocket via existing `ConnectionManager`/`ws_flags_endpoint` | CONTEXT.md locks this — design doc offers SSE OR WS; the codebase already has a working in-process per-tenant WS broadcast mechanism used by `flag_updated`; reuse it for `INVALIDATE_NAMESPACE` with a new message `type` |

**Installation:**
No new pip/npm packages required for the in-memory-cache + existing-WS approach. If a future phase adds Redis, `redis.asyncio` (redis-py ≥4.2, which ships native asyncio support) would be the standard choice — but NOT needed for Phase 20.

## Architecture Patterns

### Recommended Project Structure

```
backend/app/domains/labels/                    # NEW domain (mirrors feature_flags/)
├── __init__.py
├── models.py        # Namespace, LocalizedLabel, MissingLabelReport
├── schemas.py        # NamespaceCreate/Response, LabelCreate/Update/Response, MissingLabelReportResponse
├── service.py        # CRUD + resolve_labels() (inheritance) + cache + bootstrap/prefetch helpers
└── router.py          # /labels/namespaces, /labels/keys, /labels/missing, scope/role auth (UXWriter etc.)

backend/app/domains/sdk/
├── router.py          # ADD: /labels/bootstrap, /labels/prefetch endpoints (alongside existing /bootstrap, /evaluate)
└── ws_router.py        # Existing ws_flags_endpoint already broadcasts JSON — INVALIDATE_NAMESPACE reuses same channel/manager

backend/alembic/versions/
├── gXXX_create_localized_labels_tables.py   # namespaces, localized_labels, missing_label_reports (additive)
└── gXXX_seed_common_namespace_labels.py     # INSERT IGNORE seed data targeting real tenant_id=5 (or discovered at migration time)

sdk/sdk-js/src/
├── labels.ts          # NEW: LabelClient / $t plugin core, interpolation, reportMissingLabel
├── index.ts           # export new labels module alongside existing exports
└── types.ts           # ADD: LabelBootstrapResponse, LabelNamespace types

bff/src/routes/
└── labels.ts          # NEW: mirrors flags.ts (admin CRUD, role-gated) + sdk.ts pattern (bootstrap/prefetch/ws passthrough)

microuis/mui-labeling/                          # NEW micro-UI (name: Claude's discretion — "mui-labeling" recommended)
├── vite.config.ts     # Module Federation, port 5179 (next available), shared vue/pinia/vue-router/axios singletons
├── src/
│   ├── routes.ts        # /labels route, roles: PlatformAdmin|TenantAdmin|TenantOwner|ProductManager|UXWriter
│   ├── views/LabelingView.vue   # 12-col grid: NamespaceSidebar | KeysMatrix | TranslationDrawer
│   ├── components/
│   │   ├── NamespaceSidebar.vue
│   │   ├── KeysMatrix.vue
│   │   ├── TranslationDrawer.vue       # inheritance tree (RF-05), restore action
│   │   ├── AddNamespaceModal.vue
│   │   ├── AddKeyModal.vue
│   │   ├── ImportExportModal.vue       # export-only per CONTEXT.md
│   │   └── DiagnosticsModal.vue        # RF-06 missing keys panel
│   └── services/labelsApi.ts

portal/src/components/layout/MainLayout.vue     # Replace disabled "WhiteLabels" placeholder button with active nav entry
portal/src/router/index.ts                      # ADD REMOTE_MANIFEST entry + importRemote case for mui-labeling
```

### Pattern 1: Domain CRUD mirrors `feature_flags`
**What:** `Namespace` and `LocalizedLabel` models use the same nullable scoping columns (`tenant_id`, `company_id`, `product_id` — all `String(100)`/`String(50)`, nullable, indexed, no FK) as `FeatureFlag`. `version: Mapped[int] = mapped_column(Integer, server_default='1', nullable=False)` with manual increment-on-update (optimistic concurrency check in service layer — compare client-sent `version` against current row, raise 409 on mismatch).
**When to use:** All `localized_labels` CRUD operations.
**Example:**
```python
# Source: backend/app/domains/feature_flags/models.py (existing pattern)
class LocalizedLabel(Base):
    __tablename__ = "localized_labels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    namespace: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    label_key: Mapped[str] = mapped_column(String(150), nullable=False)
    label_value: Mapped[str] = mapped_column(Text, nullable=False)
    label_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # LABEL|PLACEHOLDER|VALIDATION|TOOLTIP
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as TEXT — MySQL 5.6 safe, e.g. '["min"]'
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, server_default='1', nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
    # UNIQUE KEY on (tenant_id, company_id, product_id, namespace, locale, label_key) at migration level
```
Note: design doc's SQL DDL uses `id VARCHAR(36)` (UUID) — but every existing table in this codebase (`feature_flags`, `segments`, `audit_logs`, `products`... except user-defined slugs) uses autoincrement `Integer` PK. **Recommend `Integer` autoincrement** for consistency; the design doc's UUID choice is illustrative, not binding (CONTEXT.md gives schema details as Claude's discretion).

### Pattern 2: Role/scope authorization — extend `_get_scope_filter`/`_check_scope_permission`
**What:** `feature_flags/router.py` has `_get_scope_filter(roles)` and `_check_scope_permission(scope, roles, action)`. For labels, the "scope" concept maps to **which hierarchy level a label row targets** (tenant-only vs company-override vs product-override), derived from whether `company_id`/`product_id` are set on the row, NOT a `scope` enum column (design doc schema has no `scope` column — presence/absence of `company_id`/`product_id` IS the scope).
**When to use:** New `_check_label_permission(label_row_or_payload, roles, action)` helper in `labels/router.py`.
**Example:**
```python
# Adapted from feature_flags/router.py _check_scope_permission
def _check_label_permission(company_id, product_id, roles, action, allow_uxwriter_value_only=False):
    is_platform_admin = 'PlatformAdmin' in roles
    is_tenant_admin = bool({'TenantAdmin', 'TenantOwner'}.intersection(roles))
    is_product_manager = 'ProductManager' in roles
    is_ux_writer = 'UXWriter' in roles

    if is_platform_admin:
        return  # full access

    if action == 'update_value' and is_ux_writer:
        return  # UXWriter: label_value-only edits, any level — enforced by NOT exposing
                # namespace/key/structure fields in the UXWriter-callable schema

    if product_id is not None:
        if not (is_tenant_admin or is_product_manager):
            raise HTTPException(403, "Only TenantAdmin/TenantOwner or ProductManager can manage product-level label overrides")
    elif company_id is not None:
        if not is_tenant_admin:
            raise HTTPException(403, "Only TenantAdmin/TenantOwner can manage company-level label overrides")
    else:  # tenant-level (base)
        if not is_tenant_admin:
            raise HTTPException(403, "Only TenantAdmin/TenantOwner can manage tenant-level labels")
```
**UXWriter enforcement detail (PRD §4 + CONTEXT.md):** UXWriter has "Solo Lectura de la estructura; no crea claves nuevas sin autorización" + "Editar valores de traducción (`label_value`) en locales activos." Implement via a **separate, narrow endpoint** `PATCH /labels/keys/{id}/value` accepting only `{label_value, locale, version}` — UXWriter is allowed on THIS endpoint only. The general `PATCH /labels/keys/{id}` (full structure edit) and namespace/key CRUD endpoints reject UXWriter entirely (read-only).

### Pattern 3: `resolve_labels()` — inheritance resolution + in-memory cache
**What:** Service-layer function implementing "override by proximity": fetch tenant-level rows (company_id=NULL, product_id=NULL), then company-level (company_id=X, product_id=NULL), then product-level (company_id=X, product_id=Y) for the given namespace+locale, merge with `dict.update()` in that order (product wins).
**When to use:** Called by `/labels/bootstrap`, `/labels/prefetch`, and any "preview resolved value" admin UI feature (RF-05 inheritance tree).
**Example:**
```python
# Source: docs/white_labeling_engine_design.md §3, adapted — Redis replaced with module-level dict
_label_cache: dict[str, dict[str, str]] = {}  # module-level; "Redis upgrade path: replace dict ops with redis calls"

async def resolve_labels(db, tenant_id, company_id, product_id, namespace, locale) -> dict[str, str]:
    cache_key = f"{tenant_id}:{company_id}:{product_id}:{namespace}:{locale}"
    if cache_key in _label_cache:
        return _label_cache[cache_key]

    tenant_labels = await _fetch_labels(db, tenant_id, None, None, namespace, locale)
    company_labels = await _fetch_labels(db, tenant_id, company_id, None, namespace, locale) if company_id else {}
    product_labels = await _fetch_labels(db, tenant_id, company_id, product_id, namespace, locale) if product_id else {}

    resolved = {**tenant_labels, **company_labels, **product_labels}
    _label_cache[cache_key] = resolved
    return resolved

def invalidate_namespace_cache(tenant_id, namespace=None):
    """Called after any CREATE/UPDATE/DELETE on localized_labels. namespace=None clears all for tenant."""
    keys_to_remove = [k for k in _label_cache if k.startswith(f"{tenant_id}:") and (namespace is None or k.endswith(f":{namespace}:es_PE") or k.endswith(f":{namespace}:en_US"))]
    for k in keys_to_remove:
        del _label_cache[k]
```
**Caveat for tests:** A module-level dict is global mutable state — same caveat as any singleton cache. For pytest isolation, expose a `clear_cache()` test helper (like `connection_manager`'s per-test manager instances aren't needed since `_label_cache` is simple to `.clear()` in fixtures).

### Pattern 4: WS `INVALIDATE_NAMESPACE` broadcast — extend existing `flag_updated` channel
**What:** `ConnectionManager.broadcast(tenant_id, message)` already sends arbitrary JSON dicts to all WS clients registered for a tenant. Reuse the SAME `/ws/flags/{tenant_id}` endpoint and `ConnectionManager` instance — add a new message `type`.
**When to use:** After any label CRUD that changes `label_value`, call:
```python
manager = request.app.state.ws_manager
await manager.broadcast(label.tenant_id, {
    "type": "INVALIDATE_NAMESPACE",
    "namespace": label.namespace,
})
```
**Important:** Despite the design doc's separate `/labels/events` WS endpoint mockup, CONTEXT.md locks reuse of the EXISTING `ws_flags_endpoint`/`/ws/flags/{tenant_id}` — do NOT create a second WS route. The sdk-js `ReconnectingSocket.onMessage` callback in `client.ts` already has a dispatcher (`if (msg?.type === 'flag_updated') ...`); add an `else if (msg?.type === 'INVALIDATE_NAMESPACE')` branch — likely in the new `labels.ts` module's own listener registered on the same socket, OR `client.ts` needs a generic message-type registry if `FeatureFlagClient` and a new `LabelClient` both need the same socket. **Open question** — see Open Questions.

### Pattern 5: Bootstrap/prefetch endpoints mirror `sdk/router.py`
**What:** `GET /api/v1/sdk/bootstrap` already exists for flags (query params `tenant_id`, `product_id`, `environment`, `Depends(verify_sdk_secret)`). Add sibling endpoints:
```python
@router.get("/labels/bootstrap")
async def labels_bootstrap(
    tenant_id: str = Query(...), company_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None), locale: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Eager namespaces only (namespace.strategy == 'eager', e.g. 'common'). Target <100ms."""
    ...

@router.get("/labels/prefetch")
async def labels_prefetch(
    tenant_id: str = Query(...), company_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None), locale: str = Query(...),
    namespaces: str = Query(...),  # comma-separated
    db: AsyncSession = Depends(get_db),
):
    """Lazy namespaces requested by client (page_*/form_*)."""
    ...
```
Both live in `backend/app/domains/sdk/router.py` (same `verify_sdk_secret` dependency, same router prefix `/api/v1/sdk`), calling `labels.service.resolve_labels()` per requested namespace.

### Pattern 6: Audit logging — every label CRUD writes to `audit_log`
**What:** Mirror `feature_flags/router.py`'s `_audit_request_meta()` + `audit_service.write_audit_log(db, AuditLogCreate(...))` calls on create/update/delete. New `ActionType` constants needed: `CREATE_LABEL`, `UPDATE_LABEL`, `DELETE_LABEL` (and optionally `CREATE_NAMESPACE`/`UPDATE_NAMESPACE`/`DELETE_NAMESPACE`), `target_type="LOCALIZED_LABEL"` / `"NAMESPACE"`.
**Example:** Add to `backend/app/domains/audit/schemas.py::ActionType`:
```python
CREATE_LABEL = "CREATE_LABEL"
UPDATE_LABEL = "UPDATE_LABEL"
DELETE_LABEL = "DELETE_LABEL"
CREATE_NAMESPACE = "CREATE_NAMESPACE"
UPDATE_NAMESPACE = "UPDATE_NAMESPACE"
DELETE_NAMESPACE = "DELETE_NAMESPACE"
```
`payload_before`/`payload_after` are the full `LabelResponse.model_dump(mode='json')` — matches `FlagResponse` pattern exactly (16-02 precedent: "fetch existing ... before mutation to capture non-trivial payload_before diff").

### Pattern 7: Vue 3 `$t` plugin in sdk-js — new `labels.ts`
**What:** Design doc §5A's `LabelPlugin` is a starting point but needs adaptation: (1) it currently mutates `app.config.globalProperties.$t` directly with a module-level `ref` — for `sdk/sdk-js` (a framework-agnostic-ish package that already exports `FeatureFlagClient`), create a `LabelClient` class analogous to `FeatureFlagClient` (own cache, own bootstrap/prefetch fetch, own `reportMissingLabel`), and a SEPARATE thin Vue plugin factory `createLabelPlugin(client)` that wires `$t` to `client.translate()`.
**When to use:** `sdk/sdk-js/src/labels.ts` (core, framework-agnostic) + small Vue-plugin export (could live in same file or `labels-vue.ts` — Vue is a `peerDependency`/shared singleton already, so importing `type { App } from 'vue'` for the plugin type is fine).
**Example:**
```typescript
// sdk/sdk-js/src/labels.ts — core client (framework-agnostic)
export interface LabelClientOptions {
  tenantId: string; companyId?: string; productId?: string;
  locale: 'es_PE' | 'en_US'; apiBaseUrl: string; sdkKey: string;
}

export class LabelClient {
  private cache: Record<string, Record<string, string>> = {}  // namespace -> {key: value}
  private loadedNamespaces = new Set<string>()

  constructor(private opts: LabelClientOptions) {}

  async initialize(): Promise<void> {
    // GET /labels/bootstrap?tenant_id=...&locale=... -> { namespaces: { common: {...} } }
    const res = await fetch(this._url('/labels/bootstrap'), { headers: this._headers() })
    const data = await res.json()
    this.cache = data.namespaces
    Object.keys(this.cache).forEach(ns => this.loadedNamespaces.add(ns))
  }

  async prefetch(namespaces: string[]): Promise<void> {
    const missing = namespaces.filter(ns => !this.loadedNamespaces.has(ns))
    if (missing.length === 0) return
    const res = await fetch(this._url(`/labels/prefetch?namespaces=${missing.join(',')}`), { headers: this._headers() })
    const data = await res.json()
    Object.assign(this.cache, data.namespaces)
    missing.forEach(ns => this.loadedNamespaces.add(ns))
  }

  translate(path: string, variables?: Record<string, unknown>): string {
    const [namespace, key] = path.split('.')
    const label = this.cache[namespace]?.[key]
    if (label === undefined) {
      this.reportMissingLabel(namespace, key)
      return `[sys.${key}]`
    }
    if (!variables) return label
    return Object.entries(variables).reduce(
      (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
      label,
    )
  }

  invalidateNamespace(namespace: string): void {
    delete this.cache[namespace]
    this.loadedNamespaces.delete(namespace)
    // background reload
    void this.prefetch([namespace])
  }

  reportMissingLabel(namespace: string, key: string): void {
    void fetch(this._url('/labels/missing'), {
      method: 'POST',
      headers: { ...this._headers(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ namespace, label_key: key }),
    }).catch(() => {})  // best-effort, like TelemetryBatcher
  }

  private _url(path: string) { return `${this.opts.apiBaseUrl}${path}` }
  private _headers() { return { Authorization: `Bearer ${this.opts.sdkKey}` } }
}

// Vue plugin factory
import type { App } from 'vue'
export function createLabelPlugin(client: LabelClient) {
  return {
    install(app: App) {
      app.config.globalProperties.$t = (path: string, vars?: Record<string, unknown>) =>
        client.translate(path, vars)
    },
  }
}
```
**Reactivity note:** `app.config.globalProperties.$t` is NOT reactive by itself — when `invalidateNamespace()` reloads a namespace, components using `$t` in templates won't auto re-render unless the cache is a `reactive()`/`ref()` object AND `$t` reads through it inside a render (Vue's template compiler tracks `this.$t(...)` calls as part of the render function, so IF `this.cache` is reactive and `translate()` reads `this.cache[ns][key]`, re-renders WILL be triggered — Options/Composition API global properties ARE tracked when they read reactive state during render). **Recommendation:** make `LabelClient.cache` a `reactive()` object (from `vue`) instead of a plain object — this gives "free" reactivity to `$t` calls in templates without extra plumbing, matching the design doc's `ref<Record<...>>` intent but at the class-property level.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| WebSocket reconnect/backoff for labels WS | New reconnect class | `ReconnectingSocket` (sdk-js, already exists) | Same connection serves both `flag_updated` and `INVALIDATE_NAMESPACE` — one socket, two message types, dispatched by `type` field |
| Distributed cache for label resolution | Redis client/setup | Module-level Python dict + `app.state` if per-instance isolation needed | No Redis infra exists; adding it is out of scope for this phase per CONTEXT.md |
| CSV export | Manual string-building with custom escaping | Python stdlib `csv` module (`csv.writer` with `io.StringIO`) | Handles quoting/escaping of label values containing commas/newlines correctly |
| Optimistic concurrency | Custom timestamp comparison | Integer `version` column, increment on update, compare client-sent `version` to current — 409 on mismatch | Matches PRD §7 and design doc schema exactly; simple equality check, no extra libs |
| Fuzzy search (RF-03 `#globalSearch`) | New fuzzy-match library | Simple case-insensitive substring match on `label_key` + both locale values (as in the HTML prototype's `renderKeys()`) | Prototype's matching is already substring-based; no need for Fuse.js etc. for this scale |

**Key insight:** Every "hard" piece of this phase (WS reconnect, scoping/role auth, audit trail, MySQL 5.6-safe JSON-as-TEXT, Module Federation micro-UI) already has a working reference implementation elsewhere in this codebase. The work is replication + adaptation, not invention.

## Common Pitfalls

### Pitfall 1: Assuming Redis is available because the design doc shows it
**What goes wrong:** A plan task tries `pip install redis` / adds `redis` to `docker-compose.yml` / imports `redis.asyncio`, expanding scope beyond CONTEXT.md's locked decision.
**Why it happens:** `docs/white_labeling_engine_design.md` §3 explicitly shows `import redis` and `cache_client.setex(...)`.
**How to avoid:** Treat the design doc's Redis usage as architectural illustration only. Verified: `backend/requirements.txt` has no redis client; `docker-compose.yml` has no redis service. Implement the in-memory dict cache described in Pattern 3.
**Warning signs:** Any task description mentioning "Redis setup" or "redis-py" should be flagged for re-scoping.

### Pitfall 2: Schema mismatch — design doc uses `id VARCHAR(36)` (UUID), codebase convention is `Integer` autoincrement
**What goes wrong:** Following the design doc's literal `CREATE TABLE` DDL produces a UUID PK inconsistent with `feature_flags.id`, `segments.id`, `audit_logs.id`, etc.
**Why it happens:** The design doc is a generic enterprise reference, not tailored to this codebase's conventions.
**How to avoid:** Use `Integer` autoincrement PK per CONTEXT.md's "Claude's Discretion" grant on schema details + existing model conventions.
**Warning signs:** Migration file defines `sa.Column('id', sa.String(36), ...)` for `localized_labels` — should be `sa.Integer()` with `autoincrement=True`.

### Pitfall 3: UXWriter scope creep — accidentally allowing namespace/key structure mutation
**What goes wrong:** A single generic `PATCH /labels/keys/{id}` endpoint accepts the full `LabelUpdate` schema (including `namespace`, `label_key`, `params`, `label_type`) and is role-gated only on "any authenticated user with a labels role" — UXWriter could then rename keys or change namespaces.
**Why it happens:** Reusing one PATCH endpoint for both admin structure-edits and UX-writer value-edits is simpler to build but violates PRD §4's row for UX Writer ("Solo Lectura de la estructura").
**How to avoid:** Two endpoints (or one endpoint with a schema discriminated by role): `PATCH /labels/keys/{id}` (PlatformAdmin/TenantAdmin/ProductManager — full `LabelUpdate`) vs `PATCH /labels/keys/{id}/value` (adds UXWriter — only `label_value`, `locale`, `version` fields accepted).
**Warning signs:** `LabelUpdate` Pydantic schema has no narrower sibling; router has a single PATCH handler checking only `'UXWriter' in roles or ...`.

### Pitfall 4: Seed data targeting fabricated tenant/company/product IDs
**What goes wrong:** Seed migration inserts rows with `tenant_id='corp_acme'`, `company_id='comp_subway'` etc. (the PRD/HTML prototype's example IDs) — these do NOT exist in the actual dev MySQL DB, so the admin UI's Workspace Context Selector shows a tenant with zero real data, or worse, FK-less orphan rows that look fine but never appear in the Tenant/Company dropdowns (which are populated from `tenants`/`companies` tables).
**Why it happens:** The HTML prototype and PRD use illustrative IDs (`corp_acme`, `comp_subway`, `prod_banking_app`) that were never created in this project's actual data.
**How to avoid:** Follow `b002_backfill_tenant_subscriptions.py`'s pattern — at migration time, `SELECT id FROM tenants LIMIT 1` (or target the known dogfooding tenant, `tenant_id=5`, used in `portal/.env` as `VITE_BO_TENANT_ID=5`) and `SELECT id FROM companies WHERE tenant_id=:tid LIMIT 1` / `SELECT id FROM products LIMIT 1`, then `INSERT IGNORE` `localized_labels` rows referencing those real IDs. If no company exists for that tenant, the company-level override seed (CONTEXT.md's "1-2 company-level overrides") should be skipped gracefully (`IF row exists` guard) rather than failing the migration — OR create one company row as part of the seed if companies table is empty (acceptable since CONTEXT.md says "don't fabricate a new demo hierarchy" but a single company row for an EXISTING tenant, if zero exist, is a gray area — prefer querying first and falling back to a minimal real-tenant-scoped company creation only if absolutely none exist).
**Warning signs:** Seed migration has hardcoded string literals like `'corp_acme'`, `'comp_subway'`, `'prod_banking_app'` instead of `SELECT`-derived variables.

### Pitfall 5: `$t` global property not reactive — hot-reload doesn't update the UI
**What goes wrong:** TC-06 / PI-01 verification scenario ("Modificar el texto ... la interfaz se refresca automáticamente") fails because `invalidateNamespace()` updates a plain JS object, but Vue components using `{{ $t('common.btn_accept') }}` in templates don't re-render.
**Why it happens:** `app.config.globalProperties.$t` is a function; Vue's reactivity system only re-renders when REACTIVE STATE read during the previous render changes. If `$t`'s implementation reads from a plain (non-reactive) object, mutating that object doesn't trigger anything.
**How to avoid:** Back `LabelClient.cache` with `reactive()` (from `'vue'`) so that `translate()`'s property reads are tracked by the active render effect. Confirmed Vue 3 behavior: global properties read inside `<template>` expressions DO participate in the component's render-effect dependency tracking, as long as the underlying data is reactive.
**Warning signs:** `cache: Record<string, Record<string,string>> = {}` (plain object) in `LabelClient`; no `reactive()`/`ref()` import from `'vue'` in `labels.ts`.

### Pitfall 6: Forgetting `X-User-Email`/`X-User-Sub` header forwarding in new BFF route
**What goes wrong:** Audit log entries for label CRUD have `user_id=''`/`user_email=None`, breaking the audit trail (recently fixed in 16-05 for tenants.ts).
**Why it happens:** Easy to copy an older BFF route file (e.g., `sdk.ts`, which intentionally has NO auth headers) instead of `flags.ts`/`tenants.ts` (which DO forward `X-User-Sub`/`X-User-Roles`/`X-User-Tenant-Id`/`X-User-Email`).
**How to avoid:** New `bff/src/routes/labels.ts` ADMIN endpoints must use the `flags.ts` template (with `requireAuth`, `requireRole(...)`, and all four `X-User-*` headers). Only the SDK bootstrap/prefetch/missing-report endpoints (if proxied via `/labels/...` SDK paths) should follow `sdk.ts`'s no-Keycloak-auth pattern — likely cleanest to put SDK-facing label endpoints under the EXISTING `sdk.ts` proxy (since it already rewrites to `/api/v1/sdk/...` and handles WS), and admin CRUD under the new `labels.ts`.
**Warning signs:** `labels.ts` proxyReq doesn't set `X-User-Email`; audit_log rows for `CREATE_LABEL`/`UPDATE_LABEL` have empty `user_email`.

### Pitfall 7: MySQL 5.6 JSON column pitfalls for `params`
**What goes wrong:** Using `sa.JSON()` type for the `params` column (interpolation variable names) fails on MySQL 5.6 (no native JSON type) or silently works in SQLite tests but fails in MySQL 5.6 CI/prod.
**Why it happens:** SQLAlchemy's `JSON` type maps to `JSON` column type which MySQL 5.6 doesn't support (added in 5.7.8).
**How to avoid:** `params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)` storing JSON-serialized array string (e.g. `'["min"]'`), deserialized in `LabelResponse` via the same `model_validator(mode='before')` pattern as `FlagResponse.rules`/`SegmentResponse.conditions`.
**Warning signs:** `sa.Column('params', sa.JSON(), ...)` in the migration file.

## Code Examples

### CSV Export (RF-07, export-only)
```python
# Source: Python stdlib csv module — no external dependency
import csv
import io

def export_namespace_csv(labels: list[LocalizedLabelRow]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['namespace', 'label_key', 'es_PE', 'en_US', 'level'])
    for row in labels:
        writer.writerow([row.namespace, row.label_key, row.es_pe_value, row.en_us_value, row.override_level])
    return output.getvalue()
```

### Parameter validation (RF-04 — `{min}` must appear in all locale values if defined)
```python
import re

def validate_label_params(params: list[str], es_value: str, en_value: str) -> None:
    """Raises ValueError if any declared param placeholder is missing from either locale's value."""
    for param in params:
        placeholder = f"{{{param}}}"
        if placeholder not in es_value or placeholder not in en_value:
            raise ValueError(f"Missing variable {placeholder} in one or more locale translations")
```
(Matches PRD RF-04's regex-validation requirement and TC-02's expected error.)

### Optimistic concurrency check (PRD §7, PI-02)
```python
async def update_label_value(db, label_id: int, new_value: str, locale: str, client_version: int):
    label = await get_label(db, label_id)
    if label is None:
        raise HTTPException(404, "Label not found")
    if label.version != client_version:
        raise HTTPException(409, detail="La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios.")
    label.label_value = new_value
    label.version += 1
    await db.commit()
    return label
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---------------|-------------------|---------------|--------|
| Design doc's Redis-based `resolve_labels()` | In-memory dict cache, same function signature | This phase (CONTEXT.md decision) | Cache invalidation is synchronous Python dict ops, no network round-trip; upgrade to Redis later is a drop-in replacement of cache internals only |
| Design doc's separate `/labels/events` WS endpoint | Reuse `/ws/flags/{tenant_id}` with new `type: "INVALIDATE_NAMESPACE"` message | This phase (CONTEXT.md decision) | One WS connection per SDK client serves both flag updates and label invalidation — sdk-js `ReconnectingSocket.onMessage` callback needs a message-type dispatcher shared across `FeatureFlagClient` and `LabelClient` (open question below) |

**Deprecated/outdated:**
- Flutter `LabelEngine` (design doc §5B) — no Flutter client exists; entire section is non-applicable to this project.

<phase_requirements>
## Phase Requirements

No formal `LBL-XX` IDs exist yet in `.planning/REQUIREMENTS.md` — CONTEXT.md and ROADMAP.md direct the planner to derive them from the design doc (§1-7, TC-01..TC-06) and PRD (RF-01..RF-08, narrowed per CONTEXT.md). Proposed requirement IDs for the planner to adopt (derived from source documents, cross-referenced against CONTEXT.md scope decisions):

| Proposed ID | Description | Source | Research Support |
|----|-------------|--------|-------------------|
| LBL-01 | `localized_labels` table with tenant/company/product nullable scoping, namespace, locale, label_key, label_value, version, params (TEXT JSON) | design doc §1, PRD §7 | Pattern 1 (models.py mirror), Pitfall 2 (Integer PK), Pitfall 7 (TEXT not JSON) |
| LBL-02 | `namespaces` table with id, strategy (eager/lazy), description | design doc §2, PRD RF-02 | Pattern 1; RF-02 admin-creatable namespace CRUD |
| LBL-03 | `resolve_labels()` 3-level inheritance resolution ("override by proximity": Tenant → Company → Product) | design doc §1, §3; PRD §2.1 | Pattern 3 |
| LBL-04 | In-memory cache for resolved label sets, invalidated on label CRUD | design doc §3 (adapted — no Redis) | Pattern 3, Pitfall 1 |
| LBL-05 | `GET /api/v1/sdk/labels/bootstrap` — eager namespaces (`common`), <100ms target | design doc §4, TC-01..TC-03 | Pattern 5 |
| LBL-06 | `GET /api/v1/sdk/labels/prefetch?namespaces=...` — lazy namespace loading | design doc §4 | Pattern 5 |
| LBL-07 | WS `INVALIDATE_NAMESPACE` broadcast on label_value update, via existing `ConnectionManager`/`ws_flags_endpoint` | design doc §6, PRD §6.1, TC-06, PI-01 | Pattern 4 |
| LBL-08 | sdk-js `LabelClient` + `$t` Vue plugin: cache, `translate()` with `{var}` interpolation, `reportMissingLabel()` | design doc §5A | Pattern 7, Pitfall 5 |
| LBL-09 | Namespace/key CRUD endpoints with role/scope authorization (PlatformAdmin/TenantAdmin/TenantOwner/ProductManager) | PRD §4, RF-02/03/04 | Pattern 2 |
| LBL-10 | New Keycloak role `UXWriter`; `PATCH /labels/keys/{id}/value` restricted to label_value-only edits | PRD §4, CONTEXT.md | Pattern 2, Pitfall 3 |
| LBL-11 | Optimistic concurrency via `version` field; 409 + PRD §9.2 PI-02 toast message on conflict | PRD §7, §9.2 | Code Examples (concurrency check) |
| LBL-12 | Audit logging for all `localized_labels`/`namespaces` CRUD (entity_type, before/after) | PRD §7; Phase 16 pattern | Pattern 6 |
| LBL-13 | `missing_label_reports` table + `POST /labels/missing` ingestion + RF-06 diagnostics panel + `quickCreateMissing()` | PRD RF-06, CONTEXT.md | New table — Claude's discretion on exact shape |
| LBL-14 | RF-07 export-only: JSON (SDK bootstrap shape) + CSV (translator) for active Workspace Context | PRD RF-07, CONTEXT.md | Code Examples (CSV export) |
| LBL-15 | Admin micro-UI `mui-labeling`: RF-01 (Workspace Context Selector), RF-02 (Namespace sidebar+CRUD), RF-03 (Key matrix+filters), RF-04 (Key editor+param validation), RF-05 (Inheritance tree+restore), RF-08 (Dark mode) | PRD RF-01..05,08; HTML prototype | Recommended Project Structure; HTML prototype is near-literal DOM reference |
| LBL-16 | Seed `common` namespace (eager) for an existing tenant + 1-2 company-level overrides, targeting real Phase 2/7 tenant/company/product IDs | CONTEXT.md | Pitfall 4 (b002 migration pattern, `VITE_BO_TENANT_ID=5`) |

**Verification scenarios from design doc §7 map to these requirements:**
- TC-01 (no overrides → tenant value) → LBL-03
- TC-02 (company override) → LBL-03, LBL-16
- TC-03 (product override) → LBL-03
- TC-04 (missing key fallback `[sys.key]`) → LBL-08
- TC-05 (interpolation) → LBL-08
- TC-06 (WS invalidation + reload) → LBL-07, LBL-08

**PRD §9 verification scenarios map to:**
- TC-01 (create namespace) → LBL-02, LBL-15
- TC-02 (param validation error) → LBL-09 (validation logic), LBL-15
- TC-03 (cascade view read-only) → LBL-15 (RF-05)
- TC-04 (create override) → LBL-09, LBL-15
- TC-05 (restore/delete override) → LBL-09, LBL-15 (RF-05 restore action)
- TC-06 (missing key → quickCreateMissing) → LBL-13, LBL-15
- PI-01 (WS invalidation + bootstrap refetch, <200ms) → LBL-07, LBL-04
- PI-02 (concurrency conflict toast) → LBL-11
</phase_requirements>

## Open Questions

1. **How does `ReconnectingSocket`/`FeatureFlagClient`'s single WS connection serve both `flag_updated` and `INVALIDATE_NAMESPACE` if `LabelClient` is a separate class from `FeatureFlagClient`?**
   - What we know: `client.ts`'s `ReconnectingSocket` constructor takes one `onMessage` callback; `FeatureFlagClient.initialize()` creates the socket and wires `onMessage` to its own `invalidate(flag_key)`. The same backend `ws_flags_endpoint`/`ConnectionManager` channel will now also emit `INVALIDATE_NAMESPACE` messages.
   - What's unclear: Whether `LabelClient` should (a) share `FeatureFlagClient`'s socket instance (requires `FeatureFlagClient` to expose a message-type registry / event-emitter so `LabelClient` can subscribe to `INVALIDATE_NAMESPACE` without `FeatureFlagClient` knowing about labels), or (b) open its OWN `ReconnectingSocket` to the same `/ws/flags/{tenant_id}` endpoint (simplest, but means 2 WS connections per page if both SDKs are active — acceptable for MVP since `ConnectionManager` has no connection limit), or (c) `LabelClient` is only usable in apps that already have a `FeatureFlagClient` and receives invalidation via a callback injected at construction.
   - Recommendation: Option (b) — `LabelClient` opens its own `ReconnectingSocket` to `/ws/flags/{tenant_id}` (same backend endpoint, same SDK-key auth) and filters for `INVALIDATE_NAMESPACE` messages, ignoring `flag_updated`. Simplest, fully decoupled, matches "new labels module alongside the flag evaluator" (CONTEXT.md) without requiring changes to `FeatureFlagClient`. Two WS connections to the same backend endpoint from one browser tab is a known-acceptable MVP tradeoff (the backend `ConnectionManager` already supports multiple connections per tenant in a `set`).

2. **Exact `missing_label_reports` table shape and dedup key.**
   - What we know: PRD RF-06 columns are Namespace, Clave Faltante (label_key), Hits, Último Reporte. CONTEXT.md says "self-contained" and "Claude's discretion."
   - What's unclear: Unique constraint for dedup — likely `(tenant_id, company_id, product_id, namespace, label_key)` so hits increment on the SAME row regardless of WHO requested it, vs per-locale tracking.
   - Recommendation: `UNIQUE KEY (tenant_id, namespace, label_key, locale)`, with `hits: Integer` incremented via `UPDATE ... SET hits = hits + 1, last_reported_at = NOW() ON DUPLICATE KEY UPDATE` (MySQL upsert) or SELECT-then-UPDATE/INSERT in the service layer (simpler, avoids raw SQL). A row is deleted (or marked resolved) when a matching `localized_labels` row is created for that `(namespace, label_key)` — satisfies "Las alertas se limpian automáticamente cuando la clave se añade a la base de datos" (PRD RF-06 footer note).

3. **Where do `/labels/bootstrap`, `/labels/prefetch`, `/labels/missing` live in the backend router tree — `sdk/router.py` (SDK-key auth) or `labels/router.py` (internal-secret auth)?**
   - What we know: `sdk/router.py` uses `Depends(verify_sdk_secret)` (Bearer SDK key, used by browser/mobile clients). `labels/router.py` (new domain, admin CRUD) would use `Depends(verify_internal_secret)` (BFF-only, like `feature_flags/router.py`).
   - What's unclear: `/labels/bootstrap`/`/labels/prefetch`/`/labels/missing` are CLIENT-facing (called by `sdk-js`'s `LabelClient`, same actor as `FeatureFlagClient.initialize()`), so they belong under `sdk/router.py` with `verify_sdk_secret` — confirmed by design doc's framing ("SDK del BFF"). The admin CRUD (`namespaces`, `localized_labels` keys, `missing_label_reports` listing for the diagnostics panel) belongs in the new `labels/router.py` with `verify_internal_secret` (BFF-proxied, Keycloak-role-gated).
   - Recommendation: Split as described — `backend/app/domains/sdk/router.py` gets `/labels/bootstrap`, `/labels/prefetch`, `POST /labels/missing` (report a miss — SDK-key auth, public-ish). `backend/app/domains/labels/router.py` gets admin CRUD + `GET /labels/missing` (list reports for diagnostics panel — internal-secret auth). Both routers' label endpoints would collide on path prefix `/labels/missing` (POST vs GET) — FastAPI allows this since they're different HTTP methods on potentially different `APIRouter` prefixes (`/api/v1/sdk/labels/missing` vs `/labels/missing` — actually distinct full paths since `sdk_router` has prefix `/api/v1/sdk` and the new labels router would need its own prefix like `/labels`). No actual collision; just naming awareness for the planner.

4. **Micro-UI name and port.**
   - What we know: Existing ports: mui-security=5174, mui-stub=5175, mui-tenants=5176, (5177 unaccounted — possibly reserved/skipped), mui-feature-flags=5178.
   - What's unclear: Exact next free port and final module name (`mui-labeling` vs `mui-localization` vs `mui-i18n`).
   - Recommendation: `mui-labeling`, port 5179. Verify 5177 isn't used by checking all `vite.config.ts` `preview.port` values at plan time — if 5177 is free, the planner may choose to fill that gap instead, but 5179 is safe regardless.

5. **Does `companies` table have ANY rows in the dev DB for the dogfooding tenant (`tenant_id=5`)?**
   - What we know: `VITE_BO_TENANT_ID=5` is the real dogfooding tenant ID (portal `.env`). No seed migration creates `companies` rows — they're created via the Phase 14 UI (`mui-tenants` companies CRUD) ad-hoc during dev/testing.
   - What's unclear: Whether tenant 5 currently has any company rows to use for the "1-2 company-level overrides" seed requirement (LBL-16).
   - Recommendation: The seed migration (LBL-16) MUST query `SELECT id FROM companies WHERE tenant_id = :tid LIMIT 1` at migration runtime (not hardcode) and conditionally seed the company-level override ONLY if a row exists; if none exists, seed only the tenant-level `common` namespace labels and add a code comment noting the company-override seed is skipped. This keeps the migration idempotent and safe across different dev DB states, satisfying CONTEXT.md's "don't fabricate a new demo hierarchy" while still demonstrating the cascade when data permits.

## Validation Architecture

> `.planning/config.json` was not found in this read pass — assuming `workflow.nyquist_validation` may be enabled; the planner should verify `.planning/config.json` directly. Section included for completeness; trim if `nyquist_validation` is `false`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.3 + pytest-asyncio 0.24.0 (backend); vitest ^1.6.0/^2.1.0 (sdk-js, mui-*) |
| Config file | `backend/pytest.ini` or `pyproject.toml` (verify at plan time); `sdk/sdk-js/vitest.config.ts` |
| Quick run command | `cd backend && python -m pytest tests/test_labels_*.py -x` |
| Full suite command | `cd backend && python -m pytest` ; `cd sdk/sdk-js && npm test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| LBL-01 | `localized_labels` model + migration creates table with correct columns | unit/migration | `pytest backend/tests/test_labels_models.py -x` | ❌ Wave 0 |
| LBL-03 | `resolve_labels()` correctly applies override-by-proximity for TC-01..TC-03 | unit | `pytest backend/tests/test_labels_resolve.py -x` | ❌ Wave 0 |
| LBL-04 | Cache invalidation removes stale resolved-set on label update | unit | `pytest backend/tests/test_labels_resolve.py::test_cache_invalidation -x` | ❌ Wave 0 |
| LBL-05/06 | `/labels/bootstrap` and `/labels/prefetch` return correct namespace shapes | integration | `pytest backend/tests/test_labels_sdk_router.py -x` | ❌ Wave 0 |
| LBL-07 | Label update broadcasts `INVALIDATE_NAMESPACE` via `ConnectionManager` | unit | `pytest backend/tests/test_labels_router.py::test_ws_broadcast -x` | ❌ Wave 0 |
| LBL-08 | sdk-js `LabelClient.translate()` interpolation + missing-key fallback (TC-04, TC-05) | unit | `cd sdk/sdk-js && npx vitest run src/labels.test.ts` | ❌ Wave 0 |
| LBL-09/10 | Role/scope authorization incl. UXWriter value-only restriction | unit | `pytest backend/tests/test_labels_router.py::test_role_permissions -x` | ❌ Wave 0 |
| LBL-11 | Version conflict returns 409 with PRD §9.2 message (PI-02) | unit | `pytest backend/tests/test_labels_router.py::test_optimistic_concurrency -x` | ❌ Wave 0 |
| LBL-12 | CRUD writes audit_log rows with entity_type=localized_label | unit | `pytest backend/tests/test_labels_router.py::test_audit_logging -x` | ❌ Wave 0 |
| LBL-13 | Missing-key report increments hits, `quickCreateMissing` data shape | unit | `pytest backend/tests/test_labels_missing.py -x` | ❌ Wave 0 |
| LBL-14 | JSON/CSV export shape correctness | unit | `pytest backend/tests/test_labels_export.py -x` | ❌ Wave 0 |
| LBL-15 | Admin UI renders namespace list, key matrix, drawer — RF-01..05,08 | manual/E2E | manual UAT against running dev stack (per `verify` skill) | ❌ Wave 0 (no E2E harness for new micro-UI yet) |
| LBL-16 | Seed migration produces queryable `common` namespace rows for real tenant | manual/migration | `alembic upgrade head` then `SELECT * FROM localized_labels` | N/A (migration, not unit test) |

### Sampling Rate
- **Per task commit:** targeted `pytest backend/tests/test_labels_*.py -x` for backend tasks; `npx vitest run src/labels.test.ts` for sdk-js tasks
- **Per wave merge:** `cd backend && python -m pytest` (full backend suite) + `cd sdk/sdk-js && npm test`
- **Phase gate:** Full backend + sdk-js suites green, plus manual UAT walkthrough of TC-01..TC-06 (design doc) and PRD TC-01..TC-06 + PI-01/PI-02 before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_labels_models.py` — model/migration smoke test
- [ ] `backend/tests/test_labels_resolve.py` — `resolve_labels()` inheritance + cache unit tests (covers TC-01..TC-03 from design doc)
- [ ] `backend/tests/test_labels_router.py` — CRUD, role/scope auth, UXWriter restriction, optimistic concurrency, audit logging, WS broadcast
- [ ] `backend/tests/test_labels_sdk_router.py` — `/labels/bootstrap`, `/labels/prefetch` endpoint tests
- [ ] `backend/tests/test_labels_missing.py` — missing-label-report ingestion/dedup
- [ ] `backend/tests/test_labels_export.py` — JSON/CSV export shape
- [ ] `sdk/sdk-js/src/labels.test.ts` — `LabelClient.translate()` interpolation (TC-05), missing-key fallback (TC-04), `invalidateNamespace()` reactivity
- [ ] No E2E harness exists for new `mui-labeling` micro-UI — RF-01..05/08 verification is manual UAT only for v1 (consistent with how `mui-feature-flags`/`mui-tenants` were verified)

## PRD4_MVP4.md Cross-Reference

A separate document `PRD4_MVP4.md` (root) describes an overlapping "Feature Flags + Remote Config" platform on a NestJS/normalized-schema stack, sharing the same UX/UI reference (`design/stitch/labeling - namespaces_keys_management.html`). User directed: ignore its stack/schema for Phase 20, but review it for applicable ideas. Findings:

### Confirms existing recommendations (no change needed)
- PRD4's `sdk/` file layout splits `feature-flags/` and `labeling/` into separate modules with a shared `client.ts` facade — matches Pattern 7's plan to add `sdk/sdk-js/src/labels.ts` alongside the existing evaluator, confirming the chosen structure.
- PRD4's separate `namespaces` table (vs inlining namespace metadata into the label table) matches LBL-02's already-planned `Namespace` model — Phase 20's 2-table design (`namespaces` + `localized_labels`) is directionally aligned, just simpler than PRD4's 3-table split (`namespaces`/`ui_labels`/`ui_label_translations`).
- PRD4's <1ms BFF resolution target is trivially met by the in-memory dict cache (Pattern 3) — no architecture change needed to satisfy this if adopted as a non-functional target.

### Low-risk enhancement within Claude's discretion (optional, LBL-05/06)
- **Namespace hash/ETag for `NOT_MODIFIED` responses**: PRD4's bootstrap contract sends `cached_namespaces: {ns: hash}` and returns `status: "NOT_MODIFIED"` with empty `data` when unchanged. This is a payload-size optimization compatible with the single-`localized_labels`-table design — compute a hash (e.g., `md5` of the resolved dict) per `resolve_labels()` call, compare against client-sent hash. Does not require schema changes. The planner MAY include this in LBL-05/06 as a stretch goal; not required for v1 (CONTEXT.md doesn't mandate it).

### New capabilities — flagged as deferred (out of CONTEXT.md scope, do not add to LBL-01..16)
- **Role-based `targeting_rules` on label translations** (PRD4 §2/§4: per-translation JSON rules like `{"role": "VIP_CUSTOMER"}` that override the resolved value based on user profile). This is a genuinely new capability beyond "override by proximity" (Tenant→Company→Product) — CONTEXT.md and the PRD namespaces_keys_management.md scope don't include per-role label targeting. Note for future roadmap consideration; NOT part of Phase 20.
- **SWR client persistence (IndexedDB for web)**: PRD4 §5 describes local-disk cache + stale-while-revalidate for the SDK. CONTEXT.md locked sdk-js scope to `$t` plugin + interpolation + missing-key reporting (in-memory `reactive()` cache per Pattern 7), with no offline-persistence requirement. Could be a natural follow-up to LBL-08 but would expand its scope — flagged, not added.
- **`KILL_SWITCH` flag message type**: belongs to feature_flags domain, not labels — not applicable to Phase 20.

### Not applicable / conflicts (do not adopt)
- **ContextGuard / Sealed Context Token (`X-Context-Token` JWT)**: PRD4's NestJS auth model conflicts with this codebase's existing pattern (Keycloak token → BFF forwards `X-User-Sub`/`X-User-Roles`/`X-User-Tenant-Id`/`X-User-Email` headers, verified internal-secret on backend). CONTEXT.md already locks "Keycloak token claims" for scoping (Roles & Permissions section) — do not introduce a second auth scheme for labels.
- **Normalized 3-table schema** (`ui_labels` + `ui_label_translations` split): would require restructuring Pattern 1/LBL-01 (single `localized_labels` row per locale). CONTEXT.md gives schema details as Claude's discretion but the 2-table design (Pattern 1 + LBL-02) is simpler and sufficient for the locked v1 scope (es_PE/en_US, no per-role targeting). Not adopted.

## Sources

### Primary (HIGH confidence)
- `docs/white_labeling_engine_design.md` — full read, §1-7
- `docs/prd_namespaces_keys_management.md` — full read, §1-9
- `design/stitch/labeling - namespaces_keys_management.html` — full read (DOM structure, state machine, RF-01..08 implementation reference)
- `backend/app/domains/feature_flags/{models,router,schemas}.py` — scoping columns, role/scope auth helper, audit integration pattern (read in full)
- `backend/app/domains/audit/{service,schemas}.py` — `write_audit_log`, `ActionType`, `AuditLogCreate` (read in full)
- `backend/app/domains/sdk/{router,ws_router}.py` + `backend/app/ws/connection_manager.py` — bootstrap pattern, WS first-message auth, broadcast mechanism (read in full)
- `backend/app/config.py`, `backend/requirements.txt`, `docker-compose.yml` — confirmed NO Redis client/service present
- `sdk/sdk-js/src/{client,websocket,telemetry,index}.ts` — `FeatureFlagClient`, `ReconnectingSocket`, `TelemetryBatcher` patterns (read in full)
- `bff/src/routes/{flags,sdk}.ts` — admin proxy (role-gated, X-User-* headers) vs SDK proxy (no Keycloak auth) patterns (read in full)
- `microuis/mui-feature-flags/{vite.config.ts,src/routes.ts}` — Module Federation port/shared-deps convention
- `backend/alembic/versions/{e001_create_audit_logs_table,b002_backfill_tenant_subscriptions}.py` — additive migration convention + `INSERT IGNORE` seed-from-existing-data pattern
- `portal/src/router/index.ts`, `portal/src/main.ts`, `portal/.env` — REMOTE_MANIFEST registration, `VITE_BO_TENANT_ID=5` real dogfooding tenant ID
- `portal/src/components/layout/MainLayout.vue` — existing disabled "WhiteLabels" nav placeholder (natural insertion point)
- `keycloak/realm-export.json` — confirmed existing realm roles (PlatformAdmin, TenantOwner, TenantAdmin, TenantViewer, ProductManager, ProductDeveloper, ProductQA) — `UXWriter` does not yet exist, needs to be added
- `.planning/{CONTEXT.md, STATE.md, REQUIREMENTS.md, ROADMAP.md}` for Phase 20 — full read

### Secondary (MEDIUM confidence)
- Vue 3 global property reactivity behavior (Pitfall 5 / `reactive()` recommendation) — based on documented Vue 3 reactivity model (render-effect dependency tracking applies to any reactive object read during render, including via `globalProperties`); not verified against Context7/official Vue docs in this pass — recommend the implementing plan spike-test this specific pattern (`reactive()` object behind `$t`) early since it's load-bearing for TC-06/PI-01.

### Tertiary (LOW confidence)
- None — no unverified WebSearch findings used; all findings grounded in direct repo inspection.

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — no new dependencies; entirely composed of already-pinned libraries and existing internal patterns.
- Architecture: HIGH — every pattern has a direct, read, working reference implementation in this codebase (feature_flags, audit, sdk, connection_manager, sdk-js, bff routes, mui-feature-flags).
- Pitfalls: HIGH for environment facts (Redis absence, MySQL 5.6 JSON, real tenant ID) — verified via direct file reads. MEDIUM for the Vue reactivity recommendation (Pitfall 5) — sound from Vue 3 reactivity model but not Context7-verified.

**Research date:** 2026-06-13
**Valid until:** 30 days (stable internal codebase; no fast-moving external dependencies introduced)
