---
phase: 08-advanced-segments-sdk-backend
plan: "03"
subsystem: backend/sdk
tags: [sdk, feature-flags, websocket, authentication, telemetry]
dependency_graph:
  requires:
    - 08-01 (EvalEvent model in feature_flags/models.py, Segment type+conditions columns)
  provides:
    - GET /api/v1/sdk/bootstrap endpoint
    - POST /api/v1/sdk/evaluate endpoint
    - POST /api/v1/sdk/eval-events endpoint
    - ConnectionManager class (ready for Plan 04 WebSocket mount)
    - verify_sdk_secret FastAPI dependency
  affects:
    - backend/app/config.py (sdk_secret_key added)
    - backend/app/database.py (pool_size=10, max_overflow=20)
    - backend/app/dependencies.py (verify_sdk_secret added)
tech_stack:
  added: []
  patterns:
    - hmac.compare_digest for timing-safe SDK Bearer token auth
    - SQLAlchemy insert().values([...]) for bulk eval-events (single SQL statement)
    - in-process defaultdict(set) ConnectionManager keyed by tenant_id
key_files:
  created:
    - backend/app/ws/__init__.py
    - backend/app/ws/connection_manager.py
    - backend/app/domains/sdk/__init__.py
    - backend/app/domains/sdk/models.py
    - backend/app/domains/sdk/schemas.py
    - backend/app/domains/sdk/service.py
    - backend/app/domains/sdk/router.py
  modified:
    - backend/app/config.py
    - backend/app/database.py
    - backend/app/dependencies.py
decisions:
  - sdk_secret_key default is "dev-sdk-secret-change-in-prod" — override via SDK_SECRET_KEY env var in prod
  - pool_size=10 max_overflow=20 per STATE.md research decision for concurrent SDK instances
  - eval-events uses single INSERT statement to avoid N+1 DB writes
  - resolve_segment_members keys by flag_id (int) to match evaluate_flag() context['segment_members'] format
  - bulk_insert_events skips events missing any of flag_key/user_id/result/evaluated_at and returns skipped count
  - tenant_id hardcoded to 'unknown' in eval-events Phase 8 (per-tenant keys deferred to Phase 11)
metrics:
  duration: "~3 min"
  completed_date: "2026-06-09"
  tasks_completed: 2
  files_created: 7
  files_modified: 3
---

# Phase 08 Plan 03: SDK HTTP Backend Summary

**One-liner:** SDK Bearer-auth HTTP endpoints (bootstrap/evaluate/eval-events) with ConnectionManager class, backed by hmac timing-safe auth and single-statement bulk INSERT telemetry.

## What Was Built

Three SDK HTTP endpoints under `/api/v1/sdk` prefix, all protected by a shared Bearer secret key checked via `hmac.compare_digest`. The bootstrap endpoint assembles a per-tenant flag snapshot pre-serialized with inlined segment rules so the SDK client can evaluate flags locally without further DB calls. The evaluate endpoint resolves rule_based segment membership before calling the existing `evaluate_flag()` function. The eval-events endpoint accepts batches and uses a single `insert().values([...])` SQL statement to avoid N+1 DB writes.

Supporting infrastructure: `sdk_secret_key` setting in config, `pool_size=10 max_overflow=20` on the SQLAlchemy engine, `verify_sdk_secret` FastAPI dependency, and the `ConnectionManager` class (in-process, `defaultdict(set)` keyed by `tenant_id`) ready for Plan 04 to mount the WebSocket endpoint.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | SDK infrastructure — config, database pool, auth dependency, ConnectionManager | 602613a | config.py, database.py, dependencies.py, ws/connection_manager.py |
| 2 | SDK domain — schemas, service functions, HTTP router | 0bef55d | sdk/schemas.py, sdk/service.py, sdk/router.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] EvalEvent ORM model already present (Plan 01 already executed)**
- **Found during:** Task 2 investigation
- **Issue:** The plan context said EvalEvent would be in feature_flags/models.py "added by Plan 01" — verified that Plan 01 had indeed been executed and the model was already present (Segment type+conditions columns also already added)
- **Fix:** No fix needed — proceeded with sdk/service.py importing EvalEvent directly
- **Files modified:** None
- **Commit:** N/A (no deviation fix commit needed)

None — plan executed exactly as written. All files created per specification.

## Success Criteria Check

- [x] settings.sdk_secret_key = "dev-sdk-secret-change-in-prod" (default)
- [x] database.py engine has pool_size=10, max_overflow=20
- [x] verify_sdk_secret in dependencies.py uses hmac.compare_digest
- [x] ConnectionManager.broadcast() deregisters dead connections silently
- [x] SDK router has 3 routes under /api/v1/sdk prefix
- [x] bootstrap_flags() post-filters by product_id and environment
- [x] bulk_insert_events() uses insert().values([...]) — single SQL statement
- [x] resolve_segment_members() keys result by flag_id (int), not segment_id
