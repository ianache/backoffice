---
phase: 17-observabilidad-sla-slo
plan: "02"
subsystem: bff, backend
tags: [fastapi, express, proxy, roles, integration-tests]

# Dependency graph
requires: ["17-01"]
provides:
  - GET /observability/health/services backend route
  - GET /observability/metrics backend route
  - BFF proxy routing under /observability/* gated to PlatformAdmin/TenantOwner/TenantAdmin with headers forwarding
  - ASGI integration tests for both endpoints
affects: [17-03, 17-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Express proxy forwarding via http-proxy-middleware
    - Role-based route gating at BFF gateway
    - TestClient ASGI router testing under mocked database dependencies

key-files:
  created:
    - backend/app/domains/observability/router.py
    - backend/tests/test_observability_router.py
    - bff/src/routes/observability.ts
  modified:
    - backend/app/main.py
    - bff/src/index.ts

key-decisions:
  - "Enforced role gating on BFF layer (PlatformAdmin, TenantOwner, TenantAdmin) and used internal secret validation on FastAPI backend layer"
  - "Prevented the health check background task from starting during pytest runs to avoid blocking tests with connection/request timeouts"

patterns-established:
  - "Conditional lifespan tasks in FastAPI main.py based on pytest import detection"

requirements-completed: [OBS-03, OBS-04]

# Metrics
duration: 10min
completed: 2026-06-14
---

# Phase 17 Plan 02: Backend router & BFF proxy Summary

**Backend HTTP endpoints for health status and metrics trends, proxy-mapped through the BFF gateway with role gating and identity header forwarding.**

## Accomplishments
- **FastAPI Endpoints:** Created the `observability` router with `GET /health/services` and `GET /metrics`, restricted using the backend `verify_internal_secret` dependency.
- **FastAPI Integration:** Registered the router in `main.py` and updated the `lifespan` hook to conditionally disable the background loop when pytest is detected.
- **BFF Gateway Proxy:** Added the `observability` router in the BFF, configuring path rewrites and forwarding identity headers (Sub, Roles, Tenant-Id, Email) alongside the `X-Internal-Secret`.
- **Integration Tests:** Created a complete ASGI integration suite covering authentication checks, status mappings, history series shape validation, bad range query param rejection (422), and tenant ID transparency.
