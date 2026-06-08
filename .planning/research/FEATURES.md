# Feature Research

**Domain:** BackOffice Multi-Tenant Platform — MVP2 new capabilities
**Researched:** 2026-06-07
**Confidence:** HIGH (architecture derived from verified in-repo patterns + industry SDK standards)

---

## Feature Landscape

### Categories

This research covers four distinct capability areas. Each is analysed independently because they have different complexity profiles and different dependencies on v1.0 code.

| Category | Description |
|----------|-------------|
| **MUI Architecture** | Refactor monolithic portal into Shell + 3 federated Micro-UIs |
| **Products** | New first-class relational entity with catalog CRUD and tenant subscriptions |
| **Advanced Segments** | Extend existing segment model with rule-based (dynamic) type + orphan detection |
| **Feature Flag SDK** | JS/TS client + Python server SDKs with local eval, WebSocket sync, telemetry |

---

## Category A: Micro-UI (Module Federation) Architecture

### Table Stakes — MUI Architecture

Features users (developers consuming the MUIs) expect. Missing these breaks the shell.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Shell owns auth — single Keycloak init | One login, all MUIs; duplicated Keycloak instances cause token conflicts | MEDIUM | Shell's `authStore` already exists in `portal/src/stores/auth.ts`; must be shared as singleton via `shared: ['pinia']` in federation config |
| Shared Pinia instance (singleton) | Remote MUIs must read `authStore.token` and `authStore.roles`; two Pinia instances = two stores = stale data | HIGH | `vite-plugin-federation` `shared` array must mark `pinia` as `singleton: true`; Shell exposes the pinia instance, remotes import and `useStore()` in the same pinia context |
| Lazy-loaded MUI routes in Shell router | Shell router `() => import(remote/View)` — loads only when user navigates there | MEDIUM | `vue-router` already has lazy import pattern in `portal/src/router/index.ts`; federation adds async remote component resolution on top |
| Auth token propagated to remote API calls | MUI components call BFF endpoints; need `Authorization: Bearer <token>` | MEDIUM | Axios interceptor in `portal/src/services/api.ts` already injects token; if remotes share the same `api.ts` instance (via `shared`), they inherit the interceptor automatically |
| Remote failure does not crash Shell | If `mui-feature-flags` fails to load, dashboard still renders | HIGH | Wrap dynamic remote imports in `defineAsyncComponent` with `errorComponent` and `loadingComponent`; standard Vue 3 pattern |
| Base URL and environment config injected by Shell | MUI builds need to know BFF URL, Keycloak URL at runtime | MEDIUM | Pass via exposed Shell config object or env variables baked into remote builds at CI time; env vars shared via federation `shared` global is simpler |

### Differentiators — MUI Architecture

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Independent MUI deployability | `mui-feature-flags` deploys without rebuilding Shell | HIGH | Each MUI is a separate Vite build with its own `package.json`; Shell loads it from a URL; requires separate dev server ports per MUI |
| MUI route manifest registered dynamically | Shell nav rail items are driven by what each MUI exposes; adding a new MUI auto-adds nav entries | HIGH | Requires a `navigationStore` in Shell where each MUI registers itself on mount; v1.1 scope is 3 fixed MUIs so this can be simplified to static route config initially |
| Shell layout components shared to remotes | `MainLayout.vue`, `ConfirmDialog.vue`, `StitchButton.vue` exposed from Shell | MEDIUM | Reduces bundle duplication; remotes use Shell's design system rather than bundling their own copy |

### Anti-Features — MUI Architecture

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Each MUI installs its own Vue + Pinia | Seems safer for isolation | Two Vue instances = duplicate reactivity engine + Pinia context mismatch; `useAuthStore()` in remote returns a different store instance than Shell's | Mark `vue` and `pinia` as `singleton: true` in `shared` — they must be the same instance |
| Shared state via custom events (window.postMessage / CustomEvent) | Avoids federation complexity | Bypasses TypeScript types, loses reactivity, introduces message serialization bugs; much harder to debug than shared Pinia | Share the Pinia store directly via federation `shared` config |
| Shell re-evaluates auth on every MUI navigation | "Belt and suspenders" safety | Causes visible loading flickers; Keycloak PKCE init is not instant; token is already live in `authStore.token` | Use token refresh interval (already in `authStore` at 30s) — no re-init needed |
| Monorepo with shared packages for everything | Cleaner code reuse | Adds build tooling complexity (turborepo/nx) for v1.1 scope; 3 MUIs is manageable with per-project builds | Simple multi-project structure: `portal/` (Shell), `mui-security/`, `mui-tenants/`, `mui-feature-flags/`; shared types via published npm package if needed later |

### Expected User-Facing Behaviors — MUI Architecture

1. **Shell bootstrap**: User lands at `portal`, Keycloak PKCE runs once, `authStore` populates token + roles. Nav rail renders role-filtered items.
2. **MUI lazy load**: User clicks "Feature Flags" nav item. Shell router resolves `() => defineAsyncComponent(() => import('mf:mui-feature-flags/FlagsView'))`. Remote JS bundle loads from MUI dev server (dev) or CDN URL (prod). `FlagsView` mounts within Shell's `<RouterView>`.
3. **Auth token in MUI API calls**: `FlagsView` calls `GET /bff/flags/`. Axios instance (shared from Shell) injects `Authorization: Bearer <token>` from `authStore.token`. BFF validates. Response renders.
4. **MUI error boundary**: Network error loading `mui-tenants` bundle. Shell renders `<ErrorComponent>` ("Module unavailable") without crashing. Other nav items still work.
5. **Token refresh mid-session**: Shell's 30s interval refreshes Keycloak token. `authStore.token` updates. Next API call in any MUI picks up the new token via the shared Axios interceptor — no MUI-side token management needed.

---

## Category B: Products

### Table Stakes — Products

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Products catalog CRUD (PlatformAdmin) | Without a catalog, subscriptions have nothing to subscribe to | MEDIUM | New `products` table; follows exact same pattern as `tenants` CRUD (Phase 2). 3 new backend files (models, schemas, service), 1 BFF route, 1 portal view |
| Tenant product subscription (TenantOwner) | TenantOwner needs to enable/disable products for their tenant | MEDIUM | `tenant_products` join table; `POST /bff/tenant/{id}/products` as per ICD §19.1; role guard: TenantOwner only |
| Product status (active/inactive) propagates | Inactive product's flags should not evaluate as active | MEDIUM | Evaluation engine must check `product.status` when resolving product-scoped flags; existing `evaluate_flag()` in `service.py` needs product status lookup |
| Labels/tags for filtering | Admin users expect to filter large product catalogs | LOW | Labels stored as TEXT JSON (established MySQL 5.6 pattern); filter in `list_products()` via `LIKE` or Python-side filtering |
| Product visible in feature flag scope picker | When creating a flag with `scope=product`, the product must be selectable | LOW | Reuse `SegmentPicker.vue` pattern — a `ProductPicker.vue` fetches `GET /bff/products` and renders a searchable list |

### Differentiators — Products

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Flag-Product many-to-many (`flag_products` table) | Cross-product flags (e.g., `maintenance-mode` shared across suites) | MEDIUM | New `flag_products` join table; adds complexity to flag creation form (multi-select product picker vs single product_id) |
| Product dashboard: flag count + active tenant count | Gives PlatformAdmin visibility into product impact before deactivation | MEDIUM | Requires COUNT subqueries against `flag_products` and `tenant_products`; can be added to `GET /products/{id}` response |
| CI/CD version sync endpoint (`PUT /products/{id}/version`) | Products update their build metadata without BackOffice login | MEDIUM | Simple PATCH endpoint; requires service account auth (existing BFF internal secret pattern works) |

### Anti-Features — Products

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Per-product Keycloak realm or client | "Real" product isolation | Massive Keycloak ops complexity; not in scope | Keep multi-tenant logical isolation with `product_id` scoping — already validated in v1.0 |
| Product versioning / changelog | Audit trail of product config changes | Scope creep for v1.1; the existing audit log already captures all write operations | Use the existing `audit_log` pattern; add product-specific audit entries at service layer |
| Hierarchical product categories / sub-products | Enterprise catalog organization | Premature for MVP2 scope; no requirement | Flat product list with labels provides sufficient filtering for v1.1 |

### Expected User-Facing Behaviors — Products

1. **PlatformAdmin creates product**: Fills name, description, labels. `POST /bff/products`. Product appears in catalog with `status: active`.
2. **PlatformAdmin deactivates product**: Toggles product `status=inactive`. Confirmation dialog (reuse `ConfirmDialog.vue`). All product-scoped flags for that product now evaluate as `false` regardless of their own `enabled` state.
3. **TenantOwner subscribes**: Goes to tenant detail, sees product catalog, selects products to subscribe. `POST /bff/tenant/{id}/products`. Subscribed products appear in tenant's product list.
4. **ProductManager creates flag for product**: In flag creation form, `scope=product` reveals a product picker. ProductManager selects their product. Flag created with `product_id` set.

---

## Category C: Advanced Segments (Rule-Based + Orphan Detection)

### How Rule-Based Segments Work vs Manual Segments

This is the core design question. The evaluation difference is critical:

**Manual segment (v1.0, already built):**
- Storage: `members TEXT` — a JSON array of user UUIDs in the `segments` table
- Evaluation at flag-check time: `service.py` lines 89-93 — checks `user_id in segment_members[winner.id]`; segment members are pre-expanded into the evaluation context
- Runtime cost: O(n) membership check against a static list loaded at query time
- Mutability: Members are managed explicitly (add/remove UUID)

**Rule-based segment (v1.1, new):**
- Storage: `rules TEXT` — same JSON rule format as `feature_flags.rules` in the `segments` table
- Evaluation at flag-check time: When the flag evaluation engine encounters a linked segment, instead of checking `user_id in members`, it runs `_evaluate_rule(segment_rule, user_context)` for each rule in the segment
- Runtime cost: Same O(n rules) as flag rule evaluation — cheap because the evaluation engine is already in memory
- Key insight: Rule-based segments reuse the IDENTICAL operator dispatch dict (`OPERATORS` in `service.py`) as flag rules. No new evaluation code. Only the data model (adding `type` and `rules` to `segments`) and the evaluation call site (expand segment → run rules instead of membership check) need to change.
- Mutability: Rules are edited in the Rule Builder UI (already built in Phase 5)

**Evaluation flow comparison at flag-check time:**

```
Flag evaluation request arrives with context:
  { tenant_id, product_id, user: { id, country, ltv, ... } }

1. Find most-specific flag candidate (existing evaluate_flag logic — unchanged)
2. Evaluate inline flag rules (existing _evaluate_rule loop — unchanged)
3. If no inline rule matched, check linked segments:

   Manual segment path (v1.0):
     for segment in flag.linked_segments:
       if user.id in segment.members:  # O(n) list search
         return True

   Rule-based segment path (NEW):
     for segment in flag.linked_segments:
       if segment.type == 'manual':
         if user.id in segment.members: return True
       elif segment.type == 'rule_based':
         for rule in segment.rules:    # reuse _evaluate_rule
           if _evaluate_rule(rule, user): return True
```

The rule-based path is additive — it does not replace or break the manual path. The v1.0 `service.py` evaluation already handles segments via `context['segment_members']`; v1.1 needs to extend how that context dict is populated to also include rule-based resolution.

### Table Stakes — Advanced Segments

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Segment type field (`manual` or `rule_based`) | Without type discrimination, the UI cannot know which editor to show | LOW | One Alembic migration: `ALTER TABLE segments ADD COLUMN type VARCHAR(20) DEFAULT 'manual'` + `ADD COLUMN rules TEXT NULL` |
| Rule-based segment editor (Rule Builder reuse) | Users expect to define segment rules visually (Rule Builder already exists) | MEDIUM | Reuse `RuleCard.vue`, `ChipTagInput.vue`, `useRuleSimulator.ts` in the segment editing drawer; no new rule editor needed |
| Segment flag-reference count in dashboard | Admin must see how many flags use each segment before deleting it | MEDIUM | New `GET /flags/segments/{id}/usage` endpoint or augment `SegmentResponse` with `flag_count: int` via COUNT JOIN on `flag_segments`; already has the join table |
| Orphan detection (flag_count == 0) | Without this, old unused segments accumulate silently | LOW | CSS badge/chip in segment list: `v-if="segment.flag_count === 0"` renders an "Orphan" warning chip; data comes from the flag_count field above |

### Differentiators — Advanced Segments

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Segment preview (how many users match) | Shows estimated reach before activating — reduces surprise in production | HIGH | Requires hitting a dedicated endpoint with a sample of user contexts or a DB query against user attribute data; deferred to v1.2 unless user store already exists |
| Segment-level Rule Builder with live simulator | Same simulator UX for segments as for flags — zero learning curve | MEDIUM | Reuse `RuleSimulator.vue` composable in `SegmentDrawer`; already works for flag rules, works identically for segment rules |
| Orphan segment cleanup action | "Delete all orphans" bulk action | LOW | Simple filtered DELETE — low complexity once orphan flag_count logic is in place |

### Anti-Features — Advanced Segments

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Segment inheritance / nesting (segment of segments) | Flexible audience composition | Exponential evaluation complexity; circular reference risk; not standard in flag platforms | Flat segments only; users can create a new combined segment with all rules |
| Real-time segment membership count from production telemetry | Show "123 users in segment right now" | Requires streaming aggregation pipeline; out of scope | Show flag_count (how many flags reference the segment) instead — that is actionable data |
| Automatic segment deduplication | Merge segments with identical rules | Implicit side effects are dangerous in production flag systems | Manual management with orphan detection is sufficient |

### Expected User-Facing Behaviors — Advanced Segments

1. **Create rule-based segment**: Segment creation drawer shows a `type` toggle (Manual / Rule-Based). Selecting Rule-Based reveals the rule card editor (same `RuleCard.vue` components). User defines `country == 'PE' AND ltv > 500`. Saves. Segment stored with `type='rule_based'` and `rules=[{attribute:'country', operator:'equals', value:'PE'}, ...]`.
2. **Attach segment to flag**: In `FlagDrawer`, `SegmentPicker.vue` shows both manual and rule-based segments. User selects the rule-based segment. It is linked via `flag_segments` join table (unchanged).
3. **Flag evaluation with rule-based segment**: SDK or remote eval endpoint receives `{user: {id: 'u1', country: 'PE', ltv: 600}}`. Inline flag rules do not match. Engine checks linked segments. Finds the rule-based segment. Evaluates `country == 'PE'` → true. Flag returns `true`.
4. **Orphan detection**: Segment dashboard shows a table with a `flag_count` column. Rows where `flag_count == 0` display an amber "Orphan" badge. Optional "Delete" action removes safely.

---

## Category D: Feature Flag SDK

### Bootstrap Contract

The SDK bootstrap is the handshake between SDK init and the backend. Industry standard (verified via Unleash, PostHog, FeatBit patterns):

**Request**: `GET /api/v1/sdk/bootstrap?tenant_id=X&product_id=Y&environment=production`
- Authenticated via SDK API key (not user JWT) in `Authorization: Bearer <sdk_key>` header
- `sdk_key` is a machine credential scoped to a tenant+product+env, separate from user JWTs

**Response payload**:
```json
{
  "flags": [
    {
      "key": "show-new-dashboard",
      "enabled": true,
      "default_value": false,
      "rules": [
        {"attribute": "country", "operator": "in", "value": ["PE", "AR"], "result": true}
      ],
      "segments": [
        {"id": 5, "type": "rule_based", "rules": [...]}
      ],
      "rollout": 100,
      "scope": "product"
    }
  ],
  "timestamp": "2026-06-07T12:00:00Z",
  "version": "v1.1.0"
}
```

Key design decisions embedded in the contract:
- **Flags are pre-resolved to the right scope**: The backend runs the scope-hierarchy resolution at bootstrap time, so the SDK receives only the flags applicable to the tenant+product. The SDK does NOT re-run scope resolution — it only runs rule evaluation.
- **Rules are embedded inline**: SDK evaluates locally without additional DB calls. This is what enables `<1ms` evaluation.
- **Segments are inlined** (their rules embedded in the flag payload): SDK does not need to fetch segments separately. Rule-based segment evaluation is identical to flag rule evaluation.

### Local Evaluation Algorithm

The SDK's local evaluator is a verbatim TypeScript/Python port of `evaluate_flag()` from `backend/app/domains/feature_flags/service.py` (already verified in-repo). The algorithm:

1. Look up flag by `key` in the in-memory cache (Map/dict keyed by flag key)
2. If not found → return `false` (safe default)
3. If `flag.enabled === false` → return `false`
4. Iterate `flag.rules` in order (first-match-wins)
5. For each rule, evaluate `_evaluate_rule(rule, userContext)` using OPERATORS dispatch
6. If a rule matches → return `rule.result`
7. If no rule matched → check linked segments (if `flag.segments` is present in bootstrap payload)
8. For each segment: if `type=manual`, check `userContext.id in segment.members`; if `type=rule_based`, run segment rules through `_evaluate_rule`
9. If no segment matched → return `bool(flag.default_value)`

Evaluation is synchronous, ~10-20 operations per flag. Well under `<1ms` for any reasonable flag count.

### WebSocket Invalidation Protocol

Industry-standard pattern (verified from PostHog issue #32447, Unleash SSE docs, FeatBit SDK):

**Connection**: `WS /api/v1/sdk/ws?tenant_id=X&product_id=Y&token=<sdk_key>`

**Server-to-client invalidation message**:
```json
{"type": "flag_updated", "flag_key": "show-new-dashboard", "version": 42}
```
or for full refresh:
```json
{"type": "bootstrap_refresh", "reason": "bulk_edit"}
```

**SDK reaction on receiving `flag_updated`**:
1. Remove the named flag from local cache
2. Issue `GET /api/v1/sdk/bootstrap?tenant_id=X&product_id=Y` (optionally with `?keys=show-new-dashboard` for partial refresh)
3. Merge received flags into local cache
4. Fire `onFlagUpdate` callback if registered

**SDK reconnect strategy**: Exponential backoff starting at 1s, cap at 60s. On reconnect, SDK re-fetches full bootstrap to avoid stale-while-disconnected state. This is the standard pattern used by all major SDKs.

**SSE as alternative**: Simpler (unidirectional, auto-reconnect built into browser), no WS library needed. For v1.1 scope a single WS channel per SDK instance is acceptable; SSE can be substituted with identical message semantics.

### Telemetry Batching

Industry standard pattern (verified from VWO FullStack, Optimizely event-batching, OpenTelemetry BatchSpanProcessor):

- **Buffer**: SDK maintains an in-memory queue of `EvalEvent` objects
- **EvalEvent schema**: `{flag_key, result, context_hash, timestamp_ms}`
- **Flush triggers**: (a) 100 events accumulated OR (b) 60 seconds elapsed since last flush — whichever comes first
- **Flush call**: `POST /api/v1/sdk/eval-events` with body `{events: EvalEvent[], sdk_version, tenant_id, product_id}`
- **Flush on unload**: `window.addEventListener('beforeunload', () => sdk.flush())` for JS SDK — ensures events are sent on page close (use `sendBeacon` for non-blocking send)
- **Backend behavior**: Endpoint is fire-and-forget from SDK perspective (no response payload needed beyond 202 Accepted); backend queues for async processing

### Table Stakes — SDK

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Bootstrap endpoint (`GET /api/v1/sdk/bootstrap`) | Without bootstrap, SDK cannot do local eval — every call would be remote | HIGH | New FastAPI endpoint; reuses `evaluate_flag` logic from `service.py`; joins `flag_products` + `flag_segments` to build the payload; depends on Products entity being built first |
| JS/TS client `initialize()` method with local cache | SDK consumers expect `await client.initialize()` → subsequent `evaluate()` are sync | MEDIUM | In-memory `Map<string, FlagDefinition>` populated from bootstrap response |
| Python server SDK async eval | Python microservices consume flags too; must be non-blocking | MEDIUM | `asyncio` + `httpx` for bootstrap fetch; in-memory `dict`; same evaluation algorithm as JS |
| Remote eval fallback (`POST /api/v1/sdk/evaluate`) | Needed when context contains sensitive data that should not be sent to client | MEDIUM | New FastAPI endpoint; receives `{flag_key, context}`, runs `evaluate_flag()` server-side, returns `{result: bool}` |
| WebSocket gateway for cache invalidation | Without this, SDK caches go stale; developers then force page reloads | HIGH | `websockets` library in FastAPI (`WebSocket` endpoint at `/api/v1/sdk/ws`); broadcast to all connected SDK clients when any flag is updated |

### Differentiators — SDK

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| SDK triggers broadcast on BackOffice save | When ProductManager clicks "Save" in Rule Builder, all SDK clients refresh within <100ms | HIGH | BackOffice save path (`PATCH /flags/{id}`) must trigger WS broadcast; requires a connection registry (in-memory dict of `tenant_id → [websocket, ...]`) in FastAPI |
| `onReady` + `onFlagUpdate` callback API | SDK consumers can react to changes without polling | LOW | Once WS invalidation is built, callbacks are a simple event emitter wrapper |
| SDK API key management in BackOffice | PlatformAdmin generates per-tenant SDK keys | HIGH | New `sdk_keys` table; out of scope for v1.1 alpha — use shared secret from env for first release |

### Anti-Features — SDK

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| SDK evaluating full scope hierarchy (Company > Product > Tenant > Global) | "Complete parity with server" | Client has no DB access; client should receive a pre-resolved flag list for its scope from bootstrap | Bootstrap endpoint does the scope resolution server-side; client only does rule eval |
| SDK storing evaluated results in localStorage | "Persist cache across page loads" | Stale flags from previous session can cause unexpected behavior in production; security risk if flag data contains sensitive targeting info | Bootstrap is fast (<50ms); re-fetch on init is acceptable; optionally support sessionStorage with explicit TTL |
| SDK exposing raw rules to browser | Transparency for debugging | Exposes business targeting logic (competitor intelligence risk) | Rule evaluation happens in SDK memory; expose only result + (optionally) which rule index matched via debug mode |

### Expected User-Facing Behaviors — SDK

1. **JS SDK init**: App calls `await client.initialize()`. SDK GETs bootstrap. In-memory Map populated with N flag definitions. `isReady = true`. All subsequent `client.evaluate('flag-key', ctx)` calls return synchronously in <1ms.
2. **Rule-based eval in browser**: User has `{country: 'PE', ltv: 650}`. SDK runs operator dispatch against flag rules in Map. Returns `true`. No network call made.
3. **Flag update in BackOffice**: ProductManager changes a flag rule in Rule Builder and clicks Save. Backend sends WS message `{type:'flag_updated', flag_key:'premium-feature'}` to all SDK clients registered for that tenant+product. Each SDK client re-fetches bootstrap and updates its Map. Apps using the flag see updated behavior on next `evaluate()` call — no page reload.
4. **Telemetry**: After 100 flag evaluations, SDK sends batched POST to `/api/v1/sdk/eval-events`. Backend receives and stores for dashboard consumption. SDK clears buffer and resets 60s timer.
5. **Python server SDK**: FastAPI microservice wraps SDK in startup lifecycle: `await sdk.initialize()` on lifespan start. Endpoints call `await sdk.evaluate_async('flag-key', context)` — returns from cache in <1ms. WS sync runs as background task.

---

## Feature Dependencies

```
Products entity
    └──required by──> SDK bootstrap endpoint
                          (bootstrap joins flag_products to scope-resolve per product)

Segments type discrimination (manual|rule_based)
    └──required by──> SDK bootstrap payload
                          (segment rules must be embedded in bootstrap response)

Existing evaluate_flag() in service.py (v1.0)
    └──extended by──> Rule-based segment evaluation
    └──ported to──>   JS SDK local evaluator
    └──ported to──>   Python SDK local evaluator

Existing Rule Builder UI (v1.0 Phase 5)
    └──reused by──> Rule-based segment editor
                     (same RuleCard.vue, same operators)

Existing SegmentPicker.vue (v1.0)
    └──extended by──> Segment type badge display

Existing BackOffice PATCH /flags/{id} endpoint (v1.0)
    └──triggers──> WebSocket broadcast to SDK clients

MUI Shell (must be built first)
    └──required by──> All 3 remote MUIs
                          (remotes depend on Shell's Pinia instance + Axios interceptor)
```

### Dependency Notes

- **SDK bootstrap requires Products entity**: The bootstrap endpoint scopes flag resolution to `tenant_id + product_id`. If the `products` table does not exist, the bootstrap cannot validate that the product is subscribed by the tenant. Products must be built before SDK endpoints.
- **Rule-based segments require the existing evaluation engine**: The extension is additive (~20 lines in `service.py`) not a rewrite. The v1.0 evaluation engine is the foundation.
- **MUI Shell must be built before MUI remotes**: The Shell provides the Pinia instance and Axios interceptor that remotes depend on. Remote builds will fail to load auth state if Shell is not ready.
- **WebSocket broadcast requires flag save path changes**: The `PATCH /flags/{id}` endpoint in `router.py` must be modified to broadcast to a WS connection registry after a successful save. This is a surgical change to existing code.

---

## MVP Definition

### Launch With (v1.1)

- [ ] MUI Shell: auth, layout, shared Pinia instance, lazy route loading for 3 remotes
- [ ] mui-security: users view extracted as remote MUI
- [ ] mui-tenants: tenants view extracted as remote MUI
- [ ] mui-feature-flags: flags + rule builder + segments view extracted as remote MUI
- [ ] Products catalog CRUD (PlatformAdmin)
- [ ] Tenant product subscription (TenantOwner)
- [ ] Segment `type` field + rule-based segment CRUD (Alembic migration + service extension)
- [ ] Orphan detection: `flag_count` on segment, UI badge for `flag_count === 0`
- [ ] SDK backend: bootstrap endpoint, remote eval endpoint, eval-events ingestion
- [ ] SDK JS/TS client: `initialize()`, local `evaluate()`, WS invalidation, telemetry batch
- [ ] SDK Python server: async `initialize()`, async `evaluate()`, WS sync background task

### Add After Validation (v1.1.x)

- [ ] SDK API key management UI (generate/revoke keys per tenant+product) — currently uses shared secret
- [ ] Segment preview (estimated user count matching rules) — requires user attribute data store
- [ ] Product dashboard: flag count + active tenant count detail view
- [ ] CI/CD version sync endpoint for products

### Future Consideration (v2+)

- [ ] Company-level scope in SDK bootstrap (4th hierarchy level)
- [ ] Percentage rollout in SDK (deterministic hashing) — field stored in v1.0, evaluation deferred to v2
- [ ] Per-environment rule sets in segments (rules differ between prod/staging)
- [ ] SSE as alternative to WebSocket for SDK sync (simpler reconnect semantics)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| MUI Shell + 3 remotes (clean cutover) | HIGH | HIGH | P1 |
| SDK bootstrap + local eval | HIGH | HIGH | P1 |
| Products CRUD + tenant subscription | HIGH | MEDIUM | P1 |
| Rule-based segments | HIGH | MEDIUM | P1 |
| Orphan detection | MEDIUM | LOW | P1 |
| WebSocket flag invalidation | HIGH | HIGH | P1 |
| Telemetry batch endpoint | MEDIUM | LOW | P1 |
| Python server SDK | MEDIUM | MEDIUM | P1 |
| SDK API key management | MEDIUM | HIGH | P2 |
| Product dashboard detail | LOW | MEDIUM | P2 |
| Segment preview (reach estimate) | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Required for MVP2 to be functional
- P2: Add when P1 is stable
- P3: Defer to v1.2+

---

## Competitor Feature Analysis

Reference platforms analyzed for behavioral patterns (not as adoption targets — this project uses custom evaluators):

| Feature | Unleash | PostHog | LaunchDarkly | Our Approach |
|---------|---------|---------|--------------|--------------|
| Bootstrap payload | `/api/client/features` returns all toggle definitions | `/decide/` endpoint returns pre-evaluated booleans per user | `/sdk/latest-all` returns all flags + rules | Our `/sdk/bootstrap` returns pre-scope-resolved flags with rules inlined — richer than pre-evaluated, lighter than full admin API |
| Local evaluation | Server-side SDK only; client SDK gets pre-evaluated values | Client SDK gets pre-evaluated values (no local rule eval) | Client SDK gets pre-evaluated values | We support true local rule evaluation in client SDK — differentiator |
| WS invalidation | SSE streaming (`/api/client/stream`) | Polling (500ms) or SSE | Streaming (`/sdk/eval/stream`) | WebSocket with `flag_updated` message; compatible behavior to SSE |
| Telemetry | `/api/client/metrics` every 15s | `/e/` event endpoint with 1000-event buffer | `/api/events/bulk` | Our 60s/100-event pattern matches industry middle ground |
| Segments | Rule-based segments standard | Cohort-based (rule + static) | Rule-based + percentage | Manual + rule-based with same operator set as flags — consistent UX |

---

## Sources

- `backend/app/domains/feature_flags/service.py` — existing `evaluate_flag()` and `_evaluate_rule()` source of truth for SDK port (HIGH confidence, verified in-repo)
- `portal/src/stores/auth.ts` — Keycloak token management pattern; MUI auth sharing strategy (HIGH confidence, verified in-repo)
- `portal/src/router/index.ts` — existing lazy-load pattern for MUI route registration (HIGH confidence, verified in-repo)
- `portal/src/services/flags.ts` — existing Segment interface (type field missing — confirms schema extension needed) (HIGH confidence, verified in-repo)
- `PRD_MVP2.md` §17 — SDK specification, bootstrap URL, telemetry batching parameters (HIGH confidence, project requirement)
- `vite-plugin-federation` GitHub README — `shared: { pinia: { singleton: true } }` pattern (MEDIUM confidence, WebSearch verified)
- Unleash SDK docs — bootstrap payload format `client/features`, local eval architecture (MEDIUM confidence, WebSearch)
- PostHog GitHub issue #32447 — WS cache invalidation discussion confirms SSE/WS pattern (MEDIUM confidence, WebSearch)
- VWO FullStack event batching docs — `eventsPerRequest: 100`, `requestTimeInterval: 60_000` (MEDIUM confidence, WebSearch verified)
- Optimizely event batching docs — confirms 100-event/time-based dual trigger pattern (MEDIUM confidence, WebSearch)

---

*Feature research for: BackOffice Multi-Tenant Platform MVP2*
*Researched: 2026-06-07*
