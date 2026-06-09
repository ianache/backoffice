---
phase: 10-mui-tenants-security
plan: "04"
subsystem: shell-router
tags: [module-federation, routing, port-config, gap-closure]
dependency_graph:
  requires: []
  provides: [shell-router-aware-of-mui-security, shell-router-aware-of-mui-tenants, correct-preview-ports]
  affects: [portal/src/router/index.ts, microuis/mui-security/package.json, microuis/mui-tenants/package.json]
tech_stack:
  added: []
  patterns: [REMOTE_MANIFEST-filter-pattern, loadMicroUIRoutes-activation]
key_files:
  created: []
  modified:
    - portal/src/router/index.ts
    - microuis/mui-security/package.json
    - microuis/mui-tenants/package.json
decisions:
  - "[10-04]: REMOTE_MANIFEST entries for mui-security and mui-tenants activated — loadMicroUIRoutes() now registers both remotes when env vars are set"
  - "[10-04]: Default redirect changed from /stub to /tenants — authenticated users land on primary domain"
  - "[10-04]: mui-security preview port fixed to 5174, mui-tenants to 5176 — aligns with vite.config.ts and Shell .env.example"
metrics:
  duration: 55s
  completed_date: "2026-06-09"
  tasks_completed: 2
  files_modified: 3
---

# Phase 10 Plan 04: Shell Router Activation and Port Fix Summary

Shell REMOTE_MANIFEST activated for mui-security (port 5174) and mui-tenants (port 5176) — loadMicroUIRoutes() now registers both remotes at runtime, with default redirect changed to /tenants and preview ports corrected to eliminate concurrent-run conflicts.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Activate REMOTE_MANIFEST entries and update default redirect | 1bfa61d | portal/src/router/index.ts |
| 2 | Fix preview port in mui-security and mui-tenants package.json | fb4f8d1 | microuis/mui-security/package.json, microuis/mui-tenants/package.json |

## What Was Built

**Task 1 — Shell router activation:**
- Removed `// Phase 10:` comment prefix from both REMOTE_MANIFEST entries
- `{ name: 'mui-security', envVar: 'VITE_REMOTE_SECURITY', displayName: 'Access Management', pathPrefix: 'users' }` is now active
- `{ name: 'mui-tenants', envVar: 'VITE_REMOTE_TENANTS', displayName: 'Tenant Management', pathPrefix: 'tenants' }` is now active
- `loadMicroUIRoutes()` will now register routes for both remotes when `VITE_REMOTE_SECURITY` and `VITE_REMOTE_TENANTS` env vars are set
- Default route redirect changed from `/stub` to `/tenants`

**Task 2 — Preview port correction:**
- mui-security: `vite preview --port 5175` → `vite preview --port 5174`
- mui-tenants: `vite preview --port 5175` → `vite preview --port 5176`
- Both ports now match their respective `vite.config.ts` `preview.port` values and Shell `.env.example` entries
- Eliminates port conflict when running all three MUIs simultaneously

## Verification Results

All checks passed:
- REMOTE_MANIFEST has 3 active entries (mui-stub, mui-security, mui-tenants) — none commented
- No `// Phase 10:` prefix remains in router/index.ts
- Default redirect points to `/tenants`
- mui-security package.json preview uses `--port 5174`
- mui-tenants package.json preview uses `--port 5176`

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
