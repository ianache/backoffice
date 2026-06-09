---
phase: 10-mui-tenants-security
plan: "05"
subsystem: bff
tags: [bff, proxy, products, websocket, sdk]
dependency_graph:
  requires: []
  provides:
    - BFF /products proxy route (GET/POST/PATCH forwarded to backend /api/v1/products/*)
    - BFF /sdk WebSocket proxy (ws: true, /sdk/ws/flags/:tenant_id -> backend /ws/flags/:tenant_id)
  affects:
    - TenantForm.vue (Plan 10-06 can now fetch live product catalog via /products)
    - SDK JS client (can now connect WebSocket through BFF instead of directly to backend)
tech_stack:
  added: []
  patterns:
    - http-proxy-middleware createProxyMiddleware with ws: true for WebSocket upgrade
    - pathRewrite function distinguishing WS paths from HTTP paths
key_files:
  created:
    - bff/src/routes/products.ts
  modified:
    - bff/src/index.ts
    - bff/src/routes/sdk.ts
decisions:
  - "products route uses requireAuth only (no role restriction at BFF level) — backend enforces PlatformAdmin for CRUD and TenantOwner|PlatformAdmin for subscription operations via X-User-Roles header"
  - "sdk pathRewrite checks path.startsWith('/ws/') to route WS and HTTP separately — WS paths pass through unchanged, HTTP paths get /api/v1/sdk prefix"
metrics:
  duration_seconds: 70
  completed_date: "2026-06-09T17:43:10Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
---

# Phase 10 Plan 05: BFF Products Route and SDK WebSocket Proxy Summary

**One-liner:** BFF /products proxy route created with auth header forwarding plus sdk.ts upgraded with ws:true for WebSocket tunneling to backend /ws/flags/:tenant_id.

## What Was Built

**Task 1 — BFF products proxy route (f36c146)**

Created `bff/src/routes/products.ts` following the same proxy pattern as `tenants.ts`. The route:
- Guards with `requireAuth` (Keycloak JWT validation)
- Rewrites paths from `/products/*` to `/api/v1/products/*` on the backend
- Forwards `X-Internal-Secret`, `X-User-Sub`, and `X-User-Roles` headers so the backend can apply role-specific access control (PlatformAdmin for catalog CRUD, TenantOwner|PlatformAdmin for subscription operations)

**Task 2 — Register productsRouter and enable WebSocket proxy (dfd259d)**

- `bff/src/index.ts`: imported `productsRouter` and registered it at `/products` after the `/sdk` mount
- `bff/src/routes/sdk.ts`: removed the Phase 8 deferral comment, added `ws: true` to `createProxyMiddleware`, and replaced the static `pathRewrite` string with a function that detects WebSocket paths (`/ws/...`) and passes them through unchanged while still prepending `/api/v1/sdk` for HTTP paths

## Decisions Made

1. **products route — requireAuth only, no role guard at BFF layer:** The backend's product endpoints have split role requirements (PlatformAdmin for catalog CRUD, TenantOwner OR PlatformAdmin for subscriptions). Enforcing at BFF would require duplicating the routing logic. The backend already receives `X-User-Roles` and enforces access per endpoint — consistent with the `flags` route pattern.

2. **sdk pathRewrite as function:** A string-based pathRewrite cannot conditionally handle both WebSocket and HTTP paths. A function checking `path.startsWith('/ws/')` cleanly separates the two cases without needing separate routes.

## Deviations from Plan

None — plan executed exactly as written. TypeScript check (`npx tsc --noEmit`) passed with no errors.

## Self-Check

- `bff/src/routes/products.ts` — FOUND
- `bff/src/index.ts` contains `productsRouter` — FOUND (line 9: import, line 46: app.use)
- `bff/src/routes/sdk.ts` contains `ws: true` — FOUND (line 14)
- Commits f36c146 and dfd259d — verified in git log

## Self-Check: PASSED
