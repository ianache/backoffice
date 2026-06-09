---
phase: 08-advanced-segments-sdk-backend
plan: "04"
subsystem: api
tags: [websocket, fastapi, sdk, realtime, bff, proxy, feature-flags]

# Dependency graph
requires:
  - phase: 08-advanced-segments-sdk-backend
    plan: "03"
    provides: ConnectionManager class and SDK HTTP service layer (bootstrap/evaluate/eval-events)
  - phase: 08-advanced-segments-sdk-backend
    plan: "02"
    provides: segments router and service

provides:
  - WebSocket endpoint /ws/flags/{tenant_id} with first-message auth (code 4001 on failure)
  - Broadcast hooks on flag update/enable/disable handlers in flags router
  - ConnectionManager initialized in app.state before router registration
  - SDK router registered in main.py (/api/v1/sdk/*)
  - BFF proxy route /sdk/* -> backend /api/v1/sdk/*

affects:
  - phase-09-microfrontend-shell
  - phase-10-sdk-js-client
  - phase-11-per-tenant-sdk-keys

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "First-message WebSocket auth: accept() first, then receive first text frame as token, close with 4001 on failure"
    - "app.state.ws_manager: ConnectionManager initialized before include_router() calls in main.py"
    - "request.app.state.ws_manager: broadcast accessed via Request at handler call time (not import time)"
    - "BFF SDK proxy: no Keycloak middleware, SDK key auth delegated entirely to backend"

key-files:
  created:
    - backend/app/domains/sdk/ws_router.py
    - bff/src/routes/sdk.ts
  modified:
    - backend/app/main.py
    - backend/app/domains/feature_flags/router.py
    - bff/src/index.ts

key-decisions:
  - "First-message auth (not Depends/header) because browser WebSocket API cannot send custom Authorization headers"
  - "app.state.ws_manager initialized BEFORE all include_router() calls to ensure handlers can access it at startup"
  - "BFF SDK route has no requireAuth/requireRole middleware — SDK key auth validated by backend, not Keycloak"
  - "Global flags (tenant_id=None) are not broadcast — SDK clients subscribe per tenant_id"
  - "WebSocket BFF proxy (ws: true) deferred to Phase 10 — SDK clients connect directly to backend in Phase 8"

patterns-established:
  - "WebSocket heartbeat: 30s receive timeout triggers ping frame; connection dropped on send failure"
  - "Dead connection cleanup: broadcast() collects failed sends, deregisters after iteration completes"

requirements-completed:
  - SDK-04

# Metrics
duration: 8min
completed: 2026-06-08
---

# Phase 8 Plan 04: WebSocket + BFF Wiring Summary

**WebSocket /ws/flags/{tenant_id} with first-message auth, broadcast hooks on all flag mutation endpoints, and BFF proxy for SDK HTTP routes — completing Phase 8 SDK backend**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-08T03:16:34Z
- **Completed:** 2026-06-08T03:24:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint:human-verify — approved)
- **Files modified:** 5

## Accomplishments
- WebSocket endpoint with 10s auth timeout and constant-time compare (hmac.compare_digest)
- Heartbeat loop (30s ping) keeps connections alive; dead connections removed silently on next broadcast
- Broadcast called after update_flag, enable_flag, disable_flag — only for tenant-scoped flags (tenant_id is not None)
- ConnectionManager initialized in app.state before all router registrations in main.py
- BFF /sdk/* proxy routes to backend /api/v1/sdk/* with SDK key auth delegated to backend

## Task Commits

Each task was committed atomically:

1. **Task 1: WebSocket endpoint + main.py wiring + broadcast hooks in flags router** - `db55359` (feat)
2. **Task 2: BFF proxy route for SDK HTTP endpoints** - `2913b7b` (feat)

3. **Checkpoint: human-verify approved** — end-to-end WebSocket auth, SDK HTTP, and broadcast verified

**Plan metadata:** (final commit after checkpoint approval)

## Files Created/Modified
- `backend/app/domains/sdk/ws_router.py` - WebSocket endpoint with first-message auth, heartbeat loop, register/deregister lifecycle
- `backend/app/main.py` - Added ConnectionManager init, sdk_router, ws_flags_endpoint WebSocket route
- `backend/app/domains/feature_flags/router.py` - Added Request param + manager.broadcast() to update_flag, enable_flag, disable_flag
- `bff/src/routes/sdk.ts` - Express proxy router for /sdk/* -> /api/v1/sdk/*
- `bff/src/index.ts` - Registered sdkRouter at /sdk mount point

## Decisions Made
- First-message auth chosen over Depends() because browser WebSocket API cannot send custom Authorization headers
- Global flags (tenant_id=None) excluded from broadcast — SDK clients subscribe per tenant_id, no global fan-out needed
- BFF SDK proxy carries no Keycloak auth middleware — backend validates SDK key directly from Authorization header
- WebSocket BFF proxy deferred to Phase 10 (SDK JS client will connect directly to backend ws://localhost:8000 in Phase 8)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full Phase 8 SDK backend complete: segments domain, SDK HTTP endpoints, WebSocket real-time invalidation
- Phase 9 (Microfrontend Shell) can proceed independently
- Phase 10 (SDK JS client) will use /ws/flags/{tenant_id} WebSocket + /api/v1/sdk/bootstrap for local evaluation
- Phase 11: per-tenant SDK keys will replace shared sdk_secret_key; WS BFF proxy revisited then

---
*Phase: 08-advanced-segments-sdk-backend*
*Completed: 2026-06-08*
