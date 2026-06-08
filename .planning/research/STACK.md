# Stack Research — MVP2 Additions

**Domain:** Multi-Tenant BackOffice Platform (v1.1 new capabilities)
**Researched:** 2026-06-07
**Confidence:** MEDIUM-HIGH (Module Federation details HIGH via multiple sources; Python SDK packaging HIGH via official PyPI/Python docs; WebSocket approach HIGH via FastAPI official docs + websockets PyPI)

---

## Scope

This file covers ONLY net-new additions for v1.1. The existing stack (Vue 3 + Pinia, Vite 5, Node.js BFF, FastAPI + SQLAlchemy, Keycloak PKCE) is already validated and is not re-researched here.

---

## Recommended Stack — New Additions

### Module Federation (Shell + Micro-UIs)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `@originjs/vite-plugin-federation` | `^1.4.1` | Vite Module Federation plugin — host and remote config | Already used in `microuis/mui-security` scaffolding; well-understood config pattern for `shared: ['vue', 'pinia', 'vue-router', 'axios']`; simpler API than the @module-federation alternative for a 3-remote monorepo with no cross-org boundaries |
| `pnpm-workspace.yaml` | n/a (pnpm >=9 already required) | Declare all workspace packages (portal, microuis/*, bff, sdk-js) | Already using pnpm workspaces at root; adding `microuis/mui-tenants`, `microuis/mui-feature-flags` and `sdk/sdk-js` as new workspace members |

**Why NOT `@module-federation/vite`:** Version 1.15.5 is actively maintained and more production-capable for large multi-org systems, but it requires `@module-federation/runtime` as a peer and brings a heavier abstraction layer. For a closed monorepo with exactly 3 remotes and a single team, the additional complexity of runtime governance (circuit breakers, signed manifests, multi-tenant isolation) is unnecessary overhead. `@originjs/vite-plugin-federation@1.4.1` is sufficient and the proposal doc (`docs/micro_ui_proposal.md`) already targets its API. Switch to `@module-federation/vite` only if the remotes become independently deployed by separate teams.

### JS/TS SDK (`sdk/sdk-js` package)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `tsup` | `^8.x` | Bundle `sdk-js` to ESM + CJS + `.d.ts` | Zero-config, generates dual output + types; 6M weekly downloads, battle-tested; `tsdown` (successor) is at 500K downloads and still maturing — tsup remains path of least resistance for a single-entry SDK |
| Native `WebSocket` (browser) | n/a — no npm dep | WebSocket connection in browser SDK | All target browsers support native `WebSocket` (100% coverage as of 2026). No extra dependency needed for the invalidation channel. |
| `reconnecting-websocket` | AVOID — abandoned | Was a candidate for auto-reconnect | Original package v4.4.0, last published 6 years ago, no longer maintained. Use a small inline class (~30 lines) that wraps native `WebSocket` with exponential backoff and max-retries instead. Pattern is well-documented and keeps `sdk-js` dependency-free. |

**SDK JS/TS architecture pattern:**
```
sdk-js/
  src/
    index.ts          # public API: FeatureFlagClient
    bootstrap.ts      # GET /api/v1/sdk/bootstrap + in-memory cache
    evaluate.ts       # local eval (<1ms), remote fallback POST /api/v1/sdk/evaluate
    sync.ts           # WS wrapper with auto-reconnect, cache invalidation on message
    telemetry.ts      # batch queue, flush every 60s or 100 events
  package.json        # name: @backoffice/sdk-js, peerDeps: none
  tsup.config.ts
```

### Python SDK (`sdk/sdk-python` package)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `pyproject.toml` + `hatchling` | hatchling `>=1.27` | Package definition and build backend | Official Python Packaging Authority recommendation as of 2025; `pyproject.toml` replaces `setup.py`; `hatchling` is the default backend per PyPA guide and supports `pip install -e .` (PEP 660 editable installs) for local monorepo development |
| `websockets` | `>=14.0,<17` | Async WebSocket client for Python SDK sync channel | Latest stable is `16.0` (released Jan 2026); asyncio-native; the `websockets.asyncio` module was rewritten in v13+ with better connection lifecycle; `websockets.broadcast()` handles multi-client push; integrates cleanly with FastAPI/Uvicorn event loop |
| `httpx` (already in requirements.txt) | `^0.27.2` | HTTP calls for bootstrap and remote eval | Already present; no new dep needed |

**Python SDK `pyproject.toml` skeleton:**
```toml
[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[project]
name = "backoffice-sdk"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "websockets>=14.0,<17",
]

[tool.hatch.build.targets.wheel]
packages = ["src/backoffice_sdk"]
```

**Install during development:** `pip install -e sdk/sdk-python` from project root.

### Backend WebSocket endpoint (FastAPI)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI built-in WebSocket | already in FastAPI 0.115.5 | Server-side WS endpoint for SDK sync channel | FastAPI (via Starlette) has native `@app.websocket("/ws")` support — no new dependency. Uvicorn (already `uvicorn[standard]`) handles the async event loop. |
| In-process `ConnectionManager` class | n/a | Track active WS clients per tenant, broadcast flag-change events | Sufficient for single-worker development; documented upgrade path to Redis pub/sub for multi-worker production |

**Critical FastAPI WS pattern to follow:**
```python
# Cancel background tasks on disconnect to avoid resource leaks
@app.websocket("/api/v1/sdk/sync")
async def sdk_sync(websocket: WebSocket, tenant_id: str):
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping handler
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
```

**Authentication:** Browser `WebSocket` API does not support custom headers. Pass short-lived token as query param (`?token=xyz`, 60-second TTL). Validate in the endpoint before `accept()`.

---

## pnpm Workspace Changes

Add to `pnpm-workspace.yaml` (create if missing at project root):

```yaml
packages:
  - 'portal'
  - 'bff'
  - 'microuis/*'
  - 'sdk/sdk-js'
```

Each `microuis/mui-*` must add `@originjs/vite-plugin-federation` to its `devDependencies`. The portal shell gets it too and uses the `remotes` config.

---

## Installation Summary

```bash
# Each mui-* remote and portal shell
pnpm add -D @originjs/vite-plugin-federation

# sdk-js build tooling (inside sdk/sdk-js)
pnpm add -D tsup typescript

# Python SDK (inside sdk/sdk-python, or install editable from root)
pip install -e sdk/sdk-python

# Python SDK runtime dep (add to sdk-python pyproject.toml)
# websockets>=14.0,<17  — already handled by pyproject.toml
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Module Federation plugin | `@originjs/vite-plugin-federation@1.4.1` | `@module-federation/vite@1.15.5` | MF/vite is actively developed but heavier API surface; pnpm singleton resolution adds risk; overkill for 3-remote closed monorepo |
| WS auto-reconnect (JS SDK) | Inline ~30-line class | `reconnecting-websocket@4.4.0` | Abandoned since 2020; adds a dep for trivial logic |
| WS auto-reconnect (JS SDK) | Inline class | `@iam4x/reconnecting-websocket` | Small community fork; not worth the dependency |
| Python SDK build | `hatchling` + `pyproject.toml` | `setuptools` + `setup.py` | `setup.py` is legacy; setuptools still works but PyPA recommends pyproject.toml-first; hatchling is lighter |
| JS SDK bundler | `tsup@^8` | `tsdown` | tsdown is the long-term successor (Evan You backed) but at 500K weekly downloads vs tsup 6M; tsup is stable for now |
| JS SDK bundler | `tsup@^8` | `rollup` manually configured | More control but ~200 lines of config for what tsup does in 5 |
| WS server-side (Python) | `websockets@16` | `python-socketio` | Socket.IO overhead not needed; pure WS is simpler and sufficient for flag invalidation push |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `reconnecting-websocket` npm package | Abandoned 2020, no security updates | Native WebSocket + inline exponential-backoff class |
| `socket.io` / `socket.io-client` | 40KB+ bundle, server-side rooms abstraction overkill for a 1-event invalidation channel | Native WS (browser) + FastAPI `@app.websocket` |
| `@module-federation/vite` before stabilization | pnpm workspace singleton conflicts documented; `remoteHmr: true` only works for React, not Vue | `@originjs/vite-plugin-federation@1.4.1` which already works in `mui-security` scaffold |
| Sharing `@material/web` in Module Federation `shared` config | `@material/web` uses global custom element registry; registering twice causes `DOMException: CustomElement already defined` | Import `@material/web` in the Shell only; remotes use CSS custom properties inherited from Shell |
| Sharing `keycloak-js` in Module Federation `shared` config | `keycloak-js` is a singleton with internal state; version mismatch across remotes causes silent auth failures | Initialize Keycloak only in Shell; pass `useAuthStore()` from shared Pinia — remotes never import keycloak-js directly |
| `setup.py` for Python SDK | Legacy, not supported in newer pip workflows | `pyproject.toml` with hatchling |
| Multiple Pinia instances (one per MUI) | Breaks cross-remote state sharing; `useAuthStore()` in remote reads different instance | `pinia` in `shared` list with `singleton: true` — one Pinia instance, provided by Shell |

---

## Module Federation Shared Config Pattern

Every `vite.config.ts` in the monorepo (shell + all remotes) MUST use the same `shared` list with `singleton: true` for stateful libs:

```typescript
shared: {
  vue:            { singleton: true, requiredVersion: '^3.4' },
  'vue-router':   { singleton: true, requiredVersion: '^4.4' },
  pinia:          { singleton: true, requiredVersion: '^2.2' },
  axios:          { singleton: true, requiredVersion: '^1.7' },
  // DO NOT add @material/web, keycloak-js, or vuedraggable here
}
```

**Version mismatch rule:** If a remote declares a different semver range for a shared singleton, Module Federation loads a second copy silently. Because this monorepo uses a single `pnpm-workspace.yaml`, all packages resolve to the same hoisted version — no version mismatch risk. But if a MUI is ever extracted to a separate repo, this becomes a critical concern.

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `@originjs/vite-plugin-federation@1.4.1` | `vite@^5.x` | Known CORS issues in dev mode with `server.origin` set; workaround: do not set `server.origin` in dev; use absolute remote URLs only in prod config |
| `@originjs/vite-plugin-federation@1.4.1` | `@vitejs/plugin-vue@^5.0.5` | Both required; federation plugin wraps the vue plugin output |
| `@originjs/vite-plugin-federation@1.4.1` | `vite@6.x` | NOT verified; do not upgrade Vite past 5.x until federation plugin confirms v6 support |
| `websockets@16.0` | `Python 3.11+` | asyncio implementation in `websockets.asyncio` (introduced 13.0, stable 14+); do not use legacy `websockets.legacy` namespace |
| `websockets@16.0` | `FastAPI 0.115.5` + `uvicorn[standard]` | FastAPI uses Starlette's built-in WS implementation (not `websockets`); `websockets` is for the Python SDK *client*, not the server endpoint |
| `tsup@^8` | `typescript@^5.5` | Compatible; tsup uses esbuild under the hood, not tsc for transpilation; `vue-tsc` not needed for sdk-js |

---

## Sources

- [github.com/originjs/vite-plugin-federation](https://github.com/originjs/vite-plugin-federation) — version history, Vite 5 issues (#550, #613), maintenance status (last release Apr 2025) — HIGH confidence
- [npmjs.com/@module-federation/vite](https://www.npmjs.com/package/@module-federation/vite) — v1.15.5, last published June 2026, actively maintained — HIGH confidence
- [module-federation.io/guide/basic/vite](https://module-federation.io/guide/basic/vite) — official @module-federation/vite docs — HIGH confidence
- [pypi.org/project/websockets](https://pypi.org/project/websockets/) — v16.0 released Jan 2026, asyncio implementation changelog — HIGH confidence
- [fastapi.tiangolo.com/advanced/websockets](https://fastapi.tiangolo.com/advanced/websockets/) — FastAPI native WS, no extra dep required — HIGH confidence
- [packaging.python.org/en/latest/guides/writing-pyproject-toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — PyPA official recommendation for hatchling + pyproject.toml — HIGH confidence
- [tsup.egoist.dev](https://tsup.egoist.dev/) — tsup docs, dual ESM+CJS output — HIGH confidence
- [pkgpulse.com/guides/tsup-vs-tsdown...](https://www.pkgpulse.com/guides/tsup-vs-tsdown-vs-unbuild-typescript-library-bundling-2026) — tsup vs tsdown 2026 comparison — MEDIUM confidence (secondary source)
- `microuis/mui-security/package.json` + `docs/micro_ui_proposal.md` — existing project scaffolding confirms @originjs/vite-plugin-federation choice — HIGH confidence (first-party)

---
*Stack research for: BackOffice v1.1 MVP2 new capabilities*
*Researched: 2026-06-07*
