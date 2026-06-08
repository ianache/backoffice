# Pitfalls Research

**Domain:** BackOffice MVP2 — Adding Module Federation, Feature Flag SDK, Dynamic Segments, and Products Migration to an existing Vue 3 + FastAPI + MySQL 5.6 system
**Researched:** 2026-06-07
**Confidence:** HIGH (codebase-grounded) / MEDIUM (WebSearch-verified patterns)

---

## Critical Pitfalls

### Pitfall 1: Pinia Singleton Breaks When `pinia` Is Not Pinned to `singleton: true` in All Remotes

**What goes wrong:**
Each Micro-UI remote that declares `pinia` in its `shared` array but does NOT set `singleton: true` and an exact `requiredVersion` will load its own private Pinia instance at runtime. The Shell creates one `pinia` instance and mounts `useAuthStore` on it. A remote that loaded a second Pinia instance calls `useAuthStore()` against that second instance and gets an empty, unpopulated store. `authStore.isAuthenticated` is `false`, `token` is `null`, and every BFF call fails with 401. This is silent — no console error until the first API call.

**Why it happens:**
`@originjs/vite-plugin-federation` resolves sharing by semver range. If `portal/package.json` has `pinia: ^2.2.2` and a remote has `pinia: ^2.3.0`, Module Federation treats them as incompatible under default settings and loads two copies. The same failure happens with `vue`, `vue-router`, `keycloak-js`, and `pinia-plugin-persistedstate`. The existing auth store (`stores/auth.ts`) uses `pinia-plugin-persistedstate` with `sessionStorage` — this plugin registration is attached to the Pinia instance created in `main.ts`. If a remote gets a second Pinia instance, the persist plugin is NOT registered on it, causing hydration to silently fail even if the singleton issue is later patched.

**How to avoid:**
Every package in `pnpm-workspace.yaml` must list the same exact version for all shared libraries. In every `vite.config.ts` (Shell and all remotes):
```typescript
shared: {
  'vue':                   { singleton: true, requiredVersion: '^3.4.29' },
  'vue-router':            { singleton: true, requiredVersion: '^4.4.0' },
  'pinia':                 { singleton: true, requiredVersion: '^2.2.2' },
  'pinia-plugin-persistedstate': { singleton: true, requiredVersion: '^4.1.1' },
  'keycloak-js':           { singleton: true, requiredVersion: '^26.0.5' },
  'axios':                 { singleton: true, requiredVersion: '^1.7.2' },
}
```
Pin exact workspace versions with pnpm `catalog:` or `workspace:*` protocol. Enforce with a pre-build check: `pnpm ls vue pinia keycloak-js` across all packages must show one resolved version. **Do not share `@material/web`** — it registers custom elements globally; sharing it is correct but adding `singleton: true` here is also required to avoid double-registration errors in the custom element registry.

**Warning signs:**
- `useAuthStore()` returns `isAuthenticated: false` inside a remote component while the Shell nav rail shows the user as logged in
- `pinia-plugin-persistedstate` warns: "store not found in storage" on first MUI route load
- Vue DevTools shows two separate Pinia trees
- `import.meta.env.MODE` shows `production` in dev MUI but `development` in Shell — indicates separate bundle boundaries loaded

**Phase to address:** Phase 1 (Shell + MUI scaffold). Must be verified before any domain logic is moved to remotes.

---

### Pitfall 2: HMR Completely Breaks in Dev Mode with `@originjs/vite-plugin-federation`

**What goes wrong:**
`@originjs/vite-plugin-federation` does NOT support Vite dev server HMR for remotes. During `vite dev`, the plugin serves a dev-mode bundle that cannot be hot-updated. Editing a Vue component inside `mui-feature-flags` in dev mode either causes a full page reload, hangs the HMR websocket, or silently serves the stale pre-built version of the remote. This wastes hours of debugging.

**Why it happens:**
Module Federation for Vite works by building remotes to disk (`vite build --watch`) and serving those static files. The `vite dev` pipeline for the host expects ESM live updates via the HMR WebSocket, but remotes are static bundles — they are not part of the host's Vite dev graph. `remoteHmr: true` in plugin v1.x is experimental and covers only specific topologies.

**How to avoid:**
Adopt the explicit dev workflow from day one:
1. Each remote runs `vite build --watch` (not `vite dev`)
2. The remote's built `dist/` is served by a static file server on its designated port
3. The Shell runs `vite dev` with the remotes pointing at `localhost:<port>/assets/remoteEntry.js`
4. Document this in `CONTRIBUTING.md` and add a root `dev` script in the workspace `package.json` that starts all `build --watch` processes in parallel

For the `VITE_E2E_SKIP_AUTH` pattern already in `portal/.env.playwright`, extend it to all remotes. Do not rely on `vite dev` for a remote.

**Warning signs:**
- Component edits in a remote take effect only after manually running `vite build` again
- HMR websocket disconnects reported in browser console after a remote edit
- Vue DevTools shows stale component trees

**Phase to address:** Phase 1 (Shell scaffold). Establish dev workflow before any work moves to remotes.

---

### Pitfall 3: MySQL 5.6 `JSON` Column Type in `tenants.products` Will Silently Corrupt on Migration to Relational Table

**What goes wrong:**
`backend/app/domains/tenants/models.py` uses `mapped_column(JSON, ...)` for the `products` field. SQLAlchemy's `JSON` type on MySQL 5.6 maps to the `JSON` DDL column type — which **does not exist in MySQL 5.6** (it was introduced in MySQL 5.7.8). MySQL 5.6 silently stores this as `LONGTEXT`. When you run the Alembic migration to add a `products` relational table and backfill data, if you run `op.drop_column('tenants', 'products')` in the same migration transaction as the backfill, any row where `products` is `NULL` or `'null'` (the string — a known SQLAlchemy JSON quirk on MySQL 5.6) will produce silent data loss: backfill skips it, drop removes it, and the tenant ends up with zero products.

**Why it happens:**
The expand-contract migration pattern requires three separate deployments: (1) add new table + populate it, (2) dual-write, (3) remove old column. Collapsing all three into one Alembic migration is the common mistake. Additionally, SQLAlchemy serializes `JSON` Python `None` as `'null'` (the JSON string) on older drivers, not SQL `NULL`. The backfill query `WHERE products IS NOT NULL` misses these rows.

**How to avoid:**
Three separate Alembic revisions, not one:
- **Revision A (expand):** Create `products` table and `tenant_product_subscriptions` join table. No data change.
- **Revision B (backfill):** Read all `tenants.products` TEXT values, `json.loads()` each (handle `'null'`, `''`, `None`), insert rows. Use batched UPDATE, not a single transaction for all rows.
- **Revision C (contract):** Drop `tenants.products` column. Only after the application code has been updated to not read it.

Backfill defensive read:
```python
raw = row.products
if not raw or raw == 'null':
    products_list = []
else:
    products_list = json.loads(raw)
```

**Warning signs:**
- Alembic `op.create_table` + `op.drop_column` in the same `upgrade()` function
- Backfill SELECT does not guard against `raw == 'null'`
- No test that runs the migration against a tenant with `products = '[]'` and `products = NULL`

**Phase to address:** Phase for Products entity promotion. Must have migration tests before running against production data.

---

### Pitfall 4: WebSocket JWT Auth Fails for Long-Lived SDK Connections Because the Browser WebSocket API Cannot Send `Authorization` Headers

**What goes wrong:**
The SDK's WebSocket sync connects to `wss://<bff>/ws?token=<jwt>`. The JWT issued at connect time has a 5-minute or 30-minute lifetime. After expiry, the server closes the connection (or continues accepting stale messages if the backend never re-validates). The SDK reconnects, but the token it re-uses from the in-memory cache is the same expired token — the SDK has no built-in token refresh for the reconnect handshake. The result is a permanent reconnect loop: every connection attempt immediately closes with 4001 Unauthorized.

**Why it happens:**
The existing `api.ts` interceptor (`keycloak.updateToken(30)`) works for HTTP because Axios fires before the request. WebSocket `new WebSocket(url)` is a single browser call — there is no interceptor hook. The token must be fresh **at the moment the URL is constructed**, but the SDK client is a JS library that will be used outside the portal (no Keycloak context), so `keycloak.updateToken()` is not available to the SDK.

**How to avoid:**
- The backend WS endpoint must accept the token as a first-message payload (not query param — query params appear in server logs, risking token exposure). Pattern: connect without auth, immediately send `{"type":"auth","token":"<jwt>"}`, server validates and either ACKs or closes with code 4001.
- The SDK must accept a `tokenProvider: () => Promise<string>` callback. The portal integration passes `() => keycloak.updateToken(30).then(() => keycloak.token)`. External SDK consumers pass their own refresh logic.
- The backend must re-validate the token on every reconnect (not just at initial handshake).
- Set WS ping/pong interval to 45s. If the Keycloak token TTL is 5min, the SDK should proactively refresh and re-auth via the in-band `auth` message before expiry, not wait for a 4001.

**Warning signs:**
- SDK connects and gets flag bootstrap successfully, but after ~5min flags stop updating
- Browser network tab shows WS connection closing with code 1006 (abnormal closure) every 5 minutes
- BFF logs show `Invalid token` errors followed immediately by new connections

**Phase to address:** Phase for Feature Flag SDK. Must be addressed before SDK WS implementation begins, not after.

---

### Pitfall 5: Telemetry Batching Creates a Thundering Herd When All SDK Instances Share the Same 60-Second Timer Boundary

**What goes wrong:**
If every SDK instance initializes at app startup and sets `setInterval(() => flush(), 60_000)`, all instances that started at roughly the same time (e.g., all users who loaded the app after a deployment) flush simultaneously. 50 SDK clients flushing 100 events each = 5,000 rows inserted to `eval_events` within the same second. MySQL 5.6 without connection pooling tuning will queue these inserts, causing latency spikes. After a deployment, this is guaranteed: all sessions start within a short window.

**Why it happens:**
Fixed-interval timers are synchronized by the deployment event. The same pattern causes problems in reconnect storms (all WS clients reconnect at `t+0`, `t+2`, `t+4` in lockstep). The current backend has no connection pool cap configured in `database.py` — `create_async_engine` uses a default pool size of 5, which will be exhausted immediately by a flush storm.

**How to avoid:**
- Add jitter to the flush interval: `const jitter = Math.random() * 30_000; setInterval(flush, 60_000 + jitter)`
- Cap max events per batch at 100 (already in requirements), but also enforce a maximum payload size (e.g., 50KB) to prevent a slow accumulator from sending a megabyte batch
- The backend `POST /api/v1/sdk/eval-events` endpoint must use bulk insert (`INSERT INTO ... VALUES (...),(...)`) not one `INSERT` per event. SQLAlchemy: use `db.execute(insert(EvalEvent), [row_dicts])`
- Configure `asyncmy` pool: `create_async_engine(..., pool_size=10, max_overflow=20)` — document this in `database.py` as a required production setting
- The BFF should validate and forward (not buffer) telemetry — do not add a second batching layer in Node.js

**Warning signs:**
- Database connection pool exhaustion errors in FastAPI logs (`TimeoutError: QueuePool limit of size 5 overflow 10 reached`) every 60 seconds after a deployment
- P99 latency spikes on `eval-events` endpoint every 60s visible in any APM tool
- `asyncpg` or `asyncmy` pool warnings about connection wait time

**Phase to address:** Phase for Feature Flag SDK backend endpoints. Jitter and bulk insert must be in the initial implementation, not added reactively.

---

### Pitfall 6: Dynamic Rule-Based Segment Evaluation Runs a Separate DB Query Per Flag Evaluation, Breaking the <1ms Local Eval Target

**What goes wrong:**
The current evaluation engine in `service.py` takes pre-loaded `segment_members: {flag_id: [user_ids]}` as part of the context dict. This works for static (manual) segments because the bootstrap endpoint can pre-load all segment memberships for a tenant once. Dynamic rule-based segments cannot be pre-loaded this way — their membership is computed at eval time from `Segment.rules` (a JSON-TEXT field, same pattern as flags). If the evaluation path calls `await db.execute(select(Segment).where(...))` for each segment referenced by a flag, a single flag evaluation for a user in 3 segments = 3 extra DB queries. For an SDK doing 100 local evaluations per request, this is unacceptable and violates the <1ms local eval constraint.

**Why it happens:**
It is tempting to add `async def _evaluate_segment_rules(segment_id, user, db)` inside the existing `evaluate_flag` function. This works in the admin portal (single flag eval, latency-tolerant) but is catastrophic in the SDK path where local eval is supposed to be DB-free.

**How to avoid:**
Maintain strict separation between the admin eval path (DB-aware) and the SDK eval path (in-memory only):
- The SDK bootstrap endpoint (`GET /api/v1/sdk/bootstrap`) must pre-serialize all rule-based segment definitions into the bootstrap payload, not just their `id`.
- The SDK in-memory evaluator receives the full segment rule graph and evaluates segments locally, the same way flags are evaluated: `_evaluate_rule(segment_rule, user_context)`.
- The `evaluate_flag` function signature change: instead of `segment_members: {flag_id: [user_ids]}`, accept `segments: {segment_id: SegmentDefinition}` where `SegmentDefinition` is either `{type: 'static', members: [...]}` or `{type: 'rule', rules: [...]}`. Evaluate inside `evaluate_flag` without DB access.
- The admin portal live simulator can use a separate endpoint that does DB-backed segment evaluation — that is acceptable since it is a UI operation.

**Warning signs:**
- `evaluate_flag()` function signature gains an `AsyncSession` parameter
- SDK bootstrap payload does not include segment `rules` field, only `id` and `name`
- E2E tests for SDK local eval use `await` inside the evaluation loop

**Phase to address:** Phase for Dynamic Segments. The data model change to `Segment` (adding `type` and `rules` TEXT field) must land before SDK bootstrap is implemented.

---

### Pitfall 7: Module Federation Routes Registered Asynchronously Race Against the Initial Navigation Guard

**What goes wrong:**
The current `router/index.ts` calls `router.beforeEach()` which guards every route. If the Shell mounts and `router.push('/flags')` fires (e.g., from a browser refresh) before `loadMicroUIRoutes()` completes the `import('mui_feature_flags/routes')` async call, Vue Router cannot find the `/flags` route (it was in the monolith, now it lives in the remote). The router fires the `beforeEach` guard for a route that does not yet exist and redirects to `/unauthorized` or falls through to a 404. This is a regression — it worked before MF migration because all routes were synchronously registered.

**Why it happens:**
The docs proposal (`docs/micro_ui_proposal.md`) calls `loadMicroUIRoutes()` but does not `await` it before `app.mount()`. The Shell's `main.ts` already uses a top-level `await` for `authStore.init()` — the same pattern must apply to route registration. But top-level `await` in module scope delays first paint, so the remote loading must be fast or deferred with a loading state.

**How to avoid:**
```typescript
// main.ts — await both auth AND route registration before mount
await authStore.init()
await loadMicroUIRoutes()  // must settle before mount
app.use(router)
app.mount('#app')
```
Add a timeout + fallback: if a remote fails to load within 3 seconds, register a fallback error route for its path rather than leaving the route undefined. This prevents an infinite loading state if a remote's CDN is down.

**Warning signs:**
- Browser refresh on `/flags` redirects to `/unauthorized` even when authenticated
- Vue Router warns "No match found for location with path /flags" in the console on hard reload
- E2E Playwright tests that navigate directly to a route path (not via the nav) fail intermittently

**Phase to address:** Phase 1 (Shell scaffold). Must be fixed in the initial routing implementation — do not move domain routes to remotes until this is confirmed working.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Share `keycloak-js` as a non-singleton in MF `shared` list | Remote can call `keycloak.token` directly | Two Keycloak adapters initialize simultaneously; double `init()` calls throw errors silently | Never — always singleton |
| Put WS token in URL query param `?token=` | Simple to implement | Token appears in Nginx/BFF access logs; token is exposed to `window.location` in iframes | Never in production |
| Single Alembic migration for expand + backfill + contract | One `alembic upgrade head` command | Rollback is destructive; if backfill fails mid-migration, the column is already dropped | Never — always three separate revisions |
| Fixed 60s telemetry flush with no jitter | Predictable behavior | Post-deployment thundering herd on eval-events endpoint | Never in SDK |
| Call `db.execute(select(Segment)...)` inside `evaluate_flag()` | Simplest code path | Turns O(1) local eval into O(n) DB queries; breaks SDK <1ms constraint | Only acceptable in admin portal live simulator, never in SDK eval path |
| Use `vite dev` for remotes during development | Familiar workflow | HMR silently serves stale remote build; debugging time lost | Never — use `vite build --watch` + static serve |
| Skip `requiredVersion` in MF `shared` config | Less config boilerplate | Minor semver mismatch loads two Vue instances; reactive system corruption at runtime | Never for `vue`, `pinia`, `vue-router` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Keycloak + Module Federation | Initialize `keycloak-js` in each remote independently | Shell owns the single `keycloak` instance; remotes access auth state via the shared `useAuthStore` Pinia store only. `keycloak` plugin (`plugins/keycloak.ts`) must NOT be imported in any remote. |
| BFF + WebSocket SDK | Proxy WS through the same Express BFF using `http-proxy-middleware` | WS upgrade requires explicit `ws: true` in proxy config. Without it, HTTP 101 upgrade is silently rejected. Alternatively, expose WS directly from FastAPI — the BFF does not need to proxy it for internal networks. |
| asyncmy + MySQL 5.6 + JSON TEXT | Use `mapped_column(JSON)` from SQLAlchemy (already present in `tenants/models.py`) | MySQL 5.6 does not have a native `JSON` DDL type. SQLAlchemy `JSON` falls back to `LONGTEXT` for storage but the Alembic `op.add_column(Column(JSON))` will emit `JSON` DDL which MySQL 5.6 accepts (it aliases to LONGTEXT) — but `op.create_index` on a JSON column will fail. Do not index JSON columns. Use TEXT explicit notation in migrations. |
| Alembic + asyncmy | Alembic runs synchronous DDL by default; asyncmy is async | Alembic requires the `--asyncio` option or `run_sync` wrapper pattern. Missing this causes `RuntimeError: greenlet_spawn has not been called`. The project has no `alembic.ini` checked in — ensure it is created before the products migration phase. |
| pinia-plugin-persistedstate + MF remotes | Remotes call `useStore()` before the persist plugin is registered | Persist plugin is registered on the Pinia instance in `portal/src/main.ts`. Since `pinia` is shared as singleton, remotes that call `useAuthStore()` after the Shell mounts will get the already-registered instance correctly. But if a remote tries to USE the store BEFORE the Shell's `main.ts` finishes (e.g., in a remote's `main.ts` that runs in isolation for testing), the persist plugin is absent. Solution: always call stores from Vue component lifecycle hooks or route guards, never at module import time. |
| FastAPI WebSocket + Keycloak JWT | Use `Depends(verify_internal_secret)` on WS endpoint | `Depends()` does not work on WebSocket handshake for header-based auth in FastAPI. Auth must happen inside the handler after connection, using first-message pattern. The existing `verify_internal_secret` dependency (used on all existing routes) cannot be reused as-is for WS. |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Segment membership loaded per-flag in SDK eval path | SDK local eval >1ms; DB connection pool exhaustion under load | Pre-serialize full segment graph in bootstrap payload; evaluate segments in-memory using same rule engine as flags | With any segment attached to any flag in the bootstrap |
| No bulk insert for telemetry events | `eval-events` endpoint slow at >10 concurrent SDK clients flushing | Use `db.execute(insert(EvalEvent), [dicts])` — one round trip for the batch | At ~5 SDK clients flushing simultaneously (default pool_size=5) |
| `@material/web` custom elements registered twice | `CustomElementRegistry: already defined "md-button"` error; component renders incorrectly | Mark `@material/web` as `singleton: true` in MF shared config OR do not share it (each remote bundles its own, but custom element registry is global — collision is inevitable without singleton) | First page that loads two remotes that both import `@material/web` |
| WS fan-out sends flag update to all tenant connections on every flag change | Under 100 concurrent tenants with frequent flag edits, WS broadcast CPU spikes | Filter WS broadcast by `tenant_id`: only send invalidation to connections whose tenant matches the changed flag's `tenant_id` | At >20 concurrent tenants with active SDK connections |
| All SDK instances start bootstrap fetch at app load simultaneously after deployment | BFF/backend `/sdk/bootstrap` endpoint receives N requests within 1 second of deployment | Add startup jitter: `setTimeout(bootstrap, Math.random() * 5000)`. Mark bootstrap response `Cache-Control: public, max-age=30` for CDN caching (flags change rarely) | At >50 active SDK users when a new deployment occurs |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| WS token passed in URL query string | Token in Nginx access logs, browser history, Referer header on link clicks | Use first-message auth pattern: connect → send `{"type":"auth","token":"<jwt>"}` → server validates → ACK or close 4001 |
| SDK telemetry endpoint unauthenticated (`POST /sdk/eval-events`) | Any caller can flood the eval_events table with garbage data | Require `X-SDK-Key` header (tenant-specific API key issued at tenant creation) — do not reuse Keycloak JWT for SDK since external SDK consumers won't have a user JWT |
| Rule-based segment `rules` TEXT field can contain `regex` operator with unbounded pattern | ReDoS (regex denial of service) if a TenantAdmin crafts a pathological regex | Apply the same `re.match` timeout wrapper used in `_evaluate_rule()` — add a `signal.alarm(1)` guard or compile regex with a timeout; reject patterns matching known catastrophic forms (nested quantifiers) |
| MF remote loaded from an external URL controlled by attacker | XSS via malicious remote entry | All remote URLs must be same-origin or same CDN with SRI hash verification. Never load `remoteEntry.js` from a user-configurable URL. Hardcode remote origins in Shell config. |
| SDK bootstrap exposes all flag rules including disabled flags | Information disclosure: attacker learns what features exist before they launch | Bootstrap endpoint filters: only return flags where `enabled=1` OR explicitly include disabled flags with a flag indicating they are disabled (so SDK can correctly eval to `false`). Do not return `rules` for disabled flags. |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Hard navigation to MUI route before remote loads shows blank screen | PlatformAdmin refreshes `/flags` and sees an empty page with no feedback | Add a Shell-level loading state that shows a centered spinner while `loadMicroUIRoutes()` is in flight; display an error with retry button if a remote fails to load |
| Light/Dark theme stored in `useUIStore` (persist: true) but remote components read `document.documentElement.getAttribute('data-theme')` directly | Theme switch in Shell does not update a remote component until full reload | Remotes must consume `useUIStore` (shared singleton) and react to `theme` reactively, never reading `data-theme` from DOM directly |
| Orphaned segment UI shows only a count but no list of affected flags | TenantAdmin cannot decide whether to delete or migrate the segment | The orphan detection query should return flag names, not just a count. The Pinia store should expose `orphanedSegments: Segment[]` with a `referencedByFlags: string[]` field |
| SDK bootstrap loading state not reflected in UI | User sees correct UI for 500ms then a flicker as flags load and hide/show features | SDK must expose a `ready` promise/event; consuming application must gate rendering behind `await sdk.ready()` |

---

## "Looks Done But Isn't" Checklist

- [ ] **Module Federation singleton config:** `shared` block in all `vite.config.ts` files (Shell + 3 remotes) includes `singleton: true` and `requiredVersion` for `vue`, `pinia`, `vue-router`, `pinia-plugin-persistedstate`, `keycloak-js`, `axios` — verify with `vite build` and check network tab for duplicate module loads
- [ ] **Products migration:** Three separate Alembic revisions exist (expand, backfill, contract) — verify with `alembic history` showing at least 3 new heads; backfill handles `'null'`, `''`, and SQL NULL for `tenants.products`
- [ ] **WS auth:** SDK does NOT pass JWT in query param — verify no `?token=` in WS URL in network tab; verify `auth` message sent as first payload after connect
- [ ] **Telemetry jitter:** SDK flush interval includes `Math.random() * 30_000` offset — verify in SDK source, not just in documentation
- [ ] **Dynamic segment bootstrap:** `GET /sdk/bootstrap` response includes `segments[].rules` (not just `segments[].id`) — verify by calling the endpoint and inspecting payload
- [ ] **WS tenant isolation:** BFF/backend WS broadcast filters by `tenant_id` before sending invalidation — verify by toggling a flag for Tenant A while Tenant B SDK is connected and confirming Tenant B does NOT receive the invalidation message
- [ ] **MUI route registration race:** Browser refresh on `/flags`, `/tenants`, `/users` routes (now living in remotes) does NOT redirect to `/unauthorized` — verify with Playwright navigation test against hard URL

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Pinia loaded twice in MF (wrong shared config) | MEDIUM | Add `singleton: true` + `requiredVersion` to all shared configs; rebuild all packages; verify with network tab. No data loss, but requires full rebuild. |
| Products migration collapsed into one revision loses data | HIGH | Restore from pre-migration backup; re-run three-revision sequence with defensive backfill; re-test against production data snapshot. |
| WS token in query param already in production logs | HIGH | Rotate all Keycloak client secrets; issue new API keys; migrate to first-message auth in an SDK patch release; purge affected log files. |
| Thundering herd on eval-events causes MySQL connection exhaustion | MEDIUM | Immediately increase `pool_size` + `max_overflow` in `database.py`; deploy SDK patch with jitter; add rate limiting at BFF level for `POST /sdk/eval-events`. |
| `evaluate_flag` makes DB calls, breaks <1ms eval | MEDIUM | Refactor bootstrap payload to include full segment definitions; revert any `db` parameter additions to `evaluate_flag`; add integration test that asserts no DB calls in SDK eval path. |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Pinia singleton breaks in MF | Phase 1 — Shell + MUI scaffold | `vite build` for all packages; Chrome DevTools confirms single Pinia instance; Playwright test authenticates and navigates to a remote route |
| HMR breaks in MF dev mode | Phase 1 — Shell + MUI scaffold | Document dev workflow; CI build script uses `vite build`, not `vite dev` for remotes |
| MySQL 5.6 JSON-to-relational data loss | Phase for Products — migration | Three Alembic revisions; migration test against seeded DB with NULL/empty products rows |
| WS JWT auth loop on expiry | Phase for SDK WebSocket | WS integration test that runs >5 minutes; checks no reconnect storm after token TTL elapses |
| Telemetry thundering herd | Phase for SDK telemetry batching | Load test: 50 SDK clients started simultaneously; monitor DB pool metrics for 120s post-start |
| Dynamic segment N+1 in eval path | Phase for Dynamic Segments (before SDK bootstrap) | Unit test for `evaluate_flag` with a mocked segment that asserts zero DB calls; benchmark confirms <1ms |
| MUI route registration race | Phase 1 — Shell routing | Playwright test: hard refresh on each remote route URL; all must resolve without redirect to /unauthorized |

---

## Sources

- Codebase inspection: `backend/app/domains/feature_flags/{models,service,router}.py`, `portal/src/{main,stores/auth,stores/flags,router/index}.ts`, `bff/src/{index,middleware/auth}.ts`, `portal/vite.config.ts`, `pnpm-workspace.yaml`
- [Module Federation shared singleton config — module-federation.io](https://module-federation.io/configure/shared)
- [originjs/vite-plugin-federation GitHub — shared module issues](https://github.com/originjs/vite-plugin-federation/issues/650)
- [Module Federation singleton version postfix bug — module-federation/core#4078](https://github.com/module-federation/core/issues/4078)
- [WebSocket reconnection and thundering herd — websocket.org/guides/reconnection](https://websocket.org/guides/reconnection/)
- [FastAPI WebSocket auth — why Depends() is not enough](https://dev.to/hamurda/how-i-solved-websocket-authentication-in-fastapi-and-why-depends-wasnt-enough-1b68)
- [websockets 16.0 authentication docs — token passing strategies](https://websockets.readthedocs.io/en/stable/topics/authentication.html)
- [Zero-downtime migrations with Alembic and SQLAlchemy — that.guru](https://that.guru/blog/zero-downtime-upgrades-with-alembic-and-sqlalchemy/)
- [Thundering herd jitter — exponential backoff patterns](https://medium.com/@avnein4988/mitigating-the-thundering-herd-problem-exponential-backoff-with-jitter-b507cdf90d62)
- [Feature flag anti-patterns from outages — shahbhat.medium.com](https://shahbhat.medium.com/feature-flag-anti-paterns-learnings-from-outages-e1b805f23725)
- [MySQL zero-downtime shadow table strategy — coffeebytes.dev](https://coffeebytes.dev/en/databases/zero-downtime-migrations-shadow-table-strategy-explained/)
- [LaunchDarkly flag evaluation rules — SDK evaluation order](https://launchdarkly.com/docs/sdk/concepts/flag-evaluation-rules)

---
*Pitfalls research for: BackOffice MVP2 — Module Federation migration, Feature Flag SDK, Dynamic Segments, Products relational migration*
*Researched: 2026-06-07*
