---
phase: 20-localization-white-label-engine
plan: 05
subsystem: api
tags: [express, http-proxy-middleware, bff, labels, keycloak, rbac]

# Dependency graph
requires:
  - phase: 20-03
    provides: "backend labels_router mounted at /api/v1/labels/* with namespace/key CRUD + missing-reports diagnostics"
provides:
  - "BFF admin proxy route bff/src/routes/labels.ts at /labels/* -> backend /api/v1/labels/*"
  - "UXWriter role added to BFF role-gating vocabulary (for labels value edits)"
affects: [20-07, 20-08]

# Tech tracking
tech-stack:
  added: []
  patterns: ["BFF admin proxy route mirroring flags.ts (requireAuth + requireRole + createProxyMiddleware + X-User-* header forwarding)"]

key-files:
  created: [bff/src/routes/labels.ts]
  modified: [bff/src/index.ts]

key-decisions:
  - "labels.ts pathRewrite is /api/v1/labels${path} (not /flags${path}-style /labels${path}) because the backend labels_router is mounted at /api/v1/labels/* (per 20-03 decision), whereas flags_router is mounted directly at /flags/* with no /api/v1 prefix — verified via live FastAPI route inspection"
  - "UXWriter added to requireRole(...) allow-list alongside PlatformAdmin/TenantAdmin/TenantOwner/ProductManager; backend enforces the finer-grained value-only restriction on PATCH /keys/{id}/value"

patterns-established:
  - "BFF admin proxy routes must verify their backend router's actual mount prefix via FastAPI route inspection rather than assuming flags.ts's pathRewrite convention applies uniformly"

requirements-completed: [LBL-10]

# Metrics
duration: 8min
completed: 2026-06-13
---

# Phase 20 Plan 05: BFF Labels Admin Proxy Summary

**New `bff/src/routes/labels.ts` proxies `/labels/*` to backend `/api/v1/labels/*` with Keycloak auth, 5-role gating (incl. UXWriter), and full X-User-* header forwarding, mounted in `bff/src/index.ts`.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-13T20:18:19Z (session start)
- **Completed:** 2026-06-13
- **Tasks:** 1 completed
- **Files modified:** 2

## Accomplishments
- Created `bff/src/routes/labels.ts` mirroring `flags.ts`'s auth/role/proxy structure, with `UXWriter` added to the role allow-list per PRD §4
- Verified backend route mount paths via live FastAPI introspection (`venv/Scripts/python.exe -c "from app.main import app; ..."`) before fixing the `pathRewrite` value — confirmed `flags_router` mounts at `/flags/*` directly while `labels_router` mounts at `/api/v1/labels/*`
- Mounted `labelsRouter` at `/labels` in `bff/src/index.ts`, immediately after the `/flags` mount
- Confirmed (by inspection, no code change) that `/sdk/labels/bootstrap`, `/sdk/labels/prefetch`, and `/sdk/labels/missing` are already covered by the existing `sdk.ts` proxy's `/sdk/... -> /api/v1/sdk/...` rewrite — backend exposes them at `/api/v1/sdk/labels/*`
- `npx tsc --noEmit` passes with no errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create bff/src/routes/labels.ts and mount it** - `ce92538` (feat)

**Plan metadata:** (pending — final commit below)

## Files Created/Modified
- `bff/src/routes/labels.ts` - New admin proxy router: requireAuth, requireRole(PlatformAdmin, TenantAdmin, TenantOwner, ProductManager, UXWriter), createProxyMiddleware to backend with pathRewrite `/api/v1/labels${path}`, X-Internal-Secret + X-User-Sub/Roles/Tenant-Id/Email header forwarding
- `bff/src/index.ts` - Added `labelsRouter` import and `app.use('/labels', labelsRouter)` mount, after the `/flags` mount block

## Decisions Made
- `pathRewrite` for labels.ts uses `/api/v1/labels${path}` (differs from flags.ts's `/flags${path}`) — confirmed by directly inspecting `app.routes` in the running FastAPI app rather than assuming a uniform convention. This matches the 20-03 decision that `labels_router` is registered via `app.include_router(labels_router, prefix="/api/v1")`.
- Added `UXWriter` to the role allow-list as specified by the plan; backend's `PATCH /api/v1/labels/keys/{label_id}/value` endpoint enforces the finer-grained "value-only" restriction for UXWriter (out of scope for this BFF-layer change).

## Deviations from Plan

None - plan executed exactly as written. The plan's primary code listing (pathRewrite `/api/v1/labels${path}`) was correct and was verified against the real backend route table as instructed by the plan's verification step.

## Issues Encountered

The plan's verification command (`cd backend && python -c "from app.main import app; ..."`) failed initially because `python` on PATH lacked `sqlalchemy` (no active venv). Resolved by invoking `backend/venv/Scripts/python.exe` directly (the project's actual venv directory is `venv`, not `.venv`). This is an environment-discovery note, not a code deviation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `/labels/*` admin API surface is now available to the BFF for the mui-labeling admin UI (Plans 20-07/20-08)
- SDK-facing `/sdk/labels/*` endpoints continue to work unchanged via the existing `sdk.ts` proxy
- No blockers identified

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

- FOUND: bff/src/routes/labels.ts
- FOUND: ce92538
