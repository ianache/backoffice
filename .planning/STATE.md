---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: MVP2
status: unknown
last_updated: "2026-06-09T04:22:29.619Z"
progress:
  total_phases: 9
  completed_phases: 9
  total_plans: 37
  completed_plans: 37
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-07)

**Core value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.
**Current focus:** Phase 8 — Advanced Segments + SDK Backend (plan 04 of 4 — awaiting checkpoint:human-verify)

## Current Position

Phase: 8 of 11 (Advanced Segments + SDK Backend)
Plan: 4 of 4 auto tasks complete (checkpoint:human-verify pending)
Status: In progress — awaiting human verification
Last activity: 2026-06-08 — 08-04 auto tasks complete (WS endpoint + broadcast hooks + BFF proxy)

Progress: [███░░] 15% (v1.1) | [████████████████████░░░░░] ~65% (overall)

## Performance Metrics

**Velocity (v1.0 baseline):**
- Total plans completed: 25
- Average duration: ~12 min (including human checkpoint time)
- Total execution time: ~5 hours

**By Phase (v1.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-and-auth | 4 | ~50 min | ~12.5 min |
| 02-tenant-management | 4 | ~55 min | ~13.7 min |
| 03-user-management | 6 | ~57 min | ~9.5 min |
| 04-feature-flags | 7 | ~61 min | ~8.7 min |
| 05-rule-builder | 3 | ~26 min | ~8.7 min |
| 06-stitch-ui | 4 | ~48 min | ~12.0 min |

**Recent Trend:**
- Last 5 plans (v1.0): 15m, 20m, 8m, 3m, 15m
- Trend: stable

*Updated after each plan completion*
| Phase 07-products-domain P04 | 6 | 2 tasks | 3 files |
| Phase 08-advanced-segments-sdk-backend P01 | 12 | 2 tasks | 6 files |
| Phase 08-advanced-segments-sdk-backend P03 | 3 | 2 tasks | 10 files |
| Phase 08-advanced-segments-sdk-backend P02 | 25 | 2 tasks | 7 files |
| Phase 08-advanced-segments-sdk-backend P04 | 8 | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting v1.1:

- [v1.1 research]: @originjs/vite-plugin-federation@1.4.1 — already scaffolded in mui-security, do not upgrade beyond Vite 5.x
- [v1.1 research]: Pinia singleton split is silent — identical `shared` block required in all 4 vite.config.ts files (Shell + 3 remotes); verified at Phase 9 boundary
- [v1.1 research]: 3-step Alembic migration mandatory for MySQL 5.6 (expand → backfill → cleanup); single revision risks irreversible data loss
- [v1.1 research]: SDK local evaluator must be DB-free — bootstrap pre-serializes full segment rules; no AsyncSession in evaluate_flag() path
- [v1.1 research]: WS JWT auth via first-message pattern (no Authorization header in browser WS); tokenProvider callback on every reconnect
- [v1.1 research]: Telemetry jitter: Math.random() * 30000 at SDK init to avoid thundering herd post-deploy; pool_size=10, max_overflow=20
- [v1.1 research]: reconnecting-websocket npm package is abandoned (2020) — use inline 30-line exponential-backoff class in sdk-js
- [07-01]: Product.id is a user-defined slug (VARCHAR 50), not auto-increment — enables stable cross-system references
- [07-01]: TenantSubscription.tenant_id has no FK constraint — consistent with feature_flags.tenant_id pattern (Keycloak-managed)
- [07-01]: labels stored as TEXT JSON array (MySQL 5.6 safe) — deserialized to List[str] in ProductResponse model_validator
- [07-02]: IntegrityError caught in router layer (not service) — service stays pure, router owns HTTP 409 semantics
- [07-02]: label filtering Python-side in list_products — json.loads membership check, no SQL LIKE or JSON_CONTAINS
- [07-03]: 3-step migration used (expand/backfill/cleanup) — prevents irreversible data loss on MySQL 5.6
- [07-03]: INSERT IGNORE in b002 ensures idempotency — safe to re-run if migration partially fails
- [07-03]: b003 downgrade re-adds column as nullable TEXT (not JSON) — MySQL 5.6 lacks native JSON type
- [Phase 07-04]: subscribe_product raises ValueError('inactive_product') — service stays pure, router owns HTTP 422 semantics
- [Phase 07-04]: Subscription and association endpoints are idempotent — re-subscribing returns 200, concurrent calls safe
- [Phase 07-04]: TenantOwner OR PlatformAdmin required for subscription operations (TenantAdmin alone insufficient)
- [Phase 08-01]: No server_default on segments.type — NULL treated as 'manual' at schema layer; avoids MySQL 5.6 table rewrite pitfall
- [Phase 08-01]: list_segments() returns (Segment, int) tuples — router update to unpack tuples deferred to Plan 02 with TODO comment
- [Phase 08-01]: EvalEvent ORM model added in Plan 01 for Plan 03 bulk-insert importability without mid-phase model changes
- [Phase 08-03]: sdk_secret_key default is dev-sdk-secret-change-in-prod — override via SDK_SECRET_KEY env var in prod
- [Phase 08-03]: bulk_insert_events uses single INSERT statement (insert().values) to avoid N+1 DB writes
- [Phase 08-03]: resolve_segment_members keys by flag_id (int) to match evaluate_flag context segment_members format
- [Phase 08-03]: tenant_id hardcoded to unknown in eval-events Phase 8 (per-tenant keys deferred to Phase 11)
- [Phase 08-02]: update_segment() uses SegmentCreate schema (full replacement) not partial — keeps service simple for Phase 8 scope
- [Phase 08-02]: Segments nav item uses same role check as Feature Flags (PlatformAdmin|TenantAdmin|TenantOwner|ProductManager)
- [Phase 08-04]: First-message WS auth (not Depends/header) — browser WebSocket API cannot send custom Authorization headers
- [Phase 08-04]: app.state.ws_manager initialized BEFORE all include_router() calls to ensure handlers can access it at startup
- [Phase 08-04]: BFF SDK route has no Keycloak middleware — SDK key auth delegated entirely to backend
- [Phase 08-04]: WS BFF proxy (ws: true) deferred to Phase 10 — SDK clients connect directly to backend in Phase 8

### Pending Todos

- alembic.ini: EXISTS at backend/alembic.ini (confirmed during 07-01 execution)
- SDK telemetry data model: decide DB table vs log file before Phase 8 schema (affects eval-events endpoint design)
- WebSocket BFF proxy validation: spike task at start of Phase 11 for http-proxy-middleware ws:true + Keycloak token refresh in long-lived WS connection

### Blockers/Concerns

- None — v1.0 complete, v1.1 roadmap defined, ready to plan Phase 7

## Session Continuity

Last session: 2026-06-08
Stopped at: 08-04 auto tasks complete (db55359, 2913b7b) — awaiting checkpoint:human-verify for WebSocket + SDK end-to-end verification
Resume file: None
