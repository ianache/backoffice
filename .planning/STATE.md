---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: MVP2
current_plan: 6
status: executing
stopped_at: Completed 11-05-PLAN.md
last_updated: "2026-06-10T12:09:29.995Z"
last_activity: 2026-06-10
progress:
  total_phases: 12
  completed_phases: 11
  total_plans: 57
  completed_plans: 52
  percent: 91
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-07)

**Core value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.
**Current focus:** Phase 9 — Shell Cutover (next phase, not yet started)

## Current Position

Phase: 11 of 11 (mui-feature-flags-sdk-clients)
**Current Plan:** 6
**Total Plans in Phase:** 10
**Status:** Ready to execute
**Last Activity:** 2026-06-10
Last activity detail: 2026-06-10 — 11-03 (flags core) and 11-04 (rule builder + simulator) complete; RuleCard/RuleSimulator/RuleBuilderView ported with 7-operator evaluator (greaterThan/lessThan), mode='flag'|'segment' prop, Stitch two-column layout

**Progress:** [█████████░] 91%

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
| Phase 10-mui-tenants-security P03 | 1 | 3 tasks | 14 files |
| Phase 10-mui-tenants-security P04 | 1 | 2 tasks | 3 files |
| Phase 10-mui-tenants-security P06 | 111 | 2 tasks | 2 files |
| Phase 11-mui-feature-flags-sdk-clients P01 | 3min | 1 tasks | 2 files |
| Phase 11-mui-feature-flags-sdk-clients P02 | 12min | 3 tasks | 14 files |
| Phase 11 P04 | 10min | 2 tasks | 7 files |
| Phase 11-mui-feature-flags-sdk-clients P03 | 18min | 3 tasks | 12 files |
| Phase 11-mui-feature-flags-sdk-clients P05 | 8min | 2 tasks | 4 files |

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
- [Phase 10-mui-tenants-security]: ConfirmDialog.vue stored as UTF-16 LE (auto-fixed to UTF-8) — Vite Vue parser requires UTF-8 encoded SFCs
- [Phase 10-mui-tenants-security]: All shell/* imports declared in env.d.ts using declare module pattern for TypeScript type safety across federation boundary
- [10-05]: products BFF route uses requireAuth only — backend enforces PlatformAdmin for CRUD and TenantOwner|PlatformAdmin for subscriptions via X-User-Roles header
- [10-05]: sdk pathRewrite is a function checking path.startsWith('/ws/') to route WS and HTTP paths separately without needing separate routes
- [10-04]: REMOTE_MANIFEST entries activated for mui-security and mui-tenants — loadMicroUIRoutes() now registers both remotes when env vars are set
- [10-04]: Default redirect changed from /stub to /tenants — authenticated users land on primary domain
- [10-04]: Preview ports corrected: mui-security=5174, mui-tenants=5176 — aligns with vite.config.ts and Shell .env.example
- [Phase 10-06]: availableProducts changed from const string[] to ref<Product[]> — reactive so template updates when fetch completes
- [Phase 10-06]: listProducts() passes status=active filter by default — only subscribable products rendered in form
- [Phase 10-06]: data.items ?? [] fallback in listProducts() — handles empty catalog or malformed response gracefully
- [Phase 11-01]: greaterThan/lessThan implemented as float() coercion comparisons relying on existing _evaluate_rule() try/except for fail-closed behavior on non-numeric input
- [Phase 11-mui-feature-flags-sdk-clients]: [11-02]: mui-tenants has single tsconfig.json (no app/node split) - mirrored exactly for mui-feature-flags
- [Phase 11-mui-feature-flags-sdk-clients]: [11-02]: vuedraggable@4.1.0 added to mui-feature-flags deps for future rule builder drag/drop; vue-color-input excluded
- [Phase 11]: [11-04]: evaluateRule() exported from useRuleSimulator.ts for direct vitest unit testing without Vue mounting
- [Phase 11]: [11-04]: RuleCard mode='flag'|'segment' prop (default flag) hides Result column in segment mode for Plan 05 reuse
- [Phase 11]: [11-04]: vitest@^1.6.0 added to mui-feature-flags matching portal's pinned version, zero extra config
- [Phase 11-mui-feature-flags-sdk-clients]: [11-03]: SegmentPicker.vue placeholder created (Plan 03 scope) - chip-toggle stub satisfies FlagForm.vue import; full port deferred to Plan 05
- [Phase 11-mui-feature-flags-sdk-clients]: [11-03]: Feature Flags/Segments nav buttons follow Tenants active-nav pattern without extra hasRole guard - role enforcement via routes.ts meta.roles
- [Phase 11-mui-feature-flags-sdk-clients]: [11-05]: SegmentForm.vue defaults conditions[].result=true on submit for rule_based segments - unused server-side by resolve_segment_members()
- [Phase 11-mui-feature-flags-sdk-clients]: [11-05]: SegmentPicker.vue ported as full checkbox-list from v1.0, replacing Plan 03's chip-toggle placeholder; FlagDrawer/FlagForm already wired, no drawer changes needed

### Pending Todos

- alembic.ini: EXISTS at backend/alembic.ini (confirmed during 07-01 execution)
- SDK telemetry data model: decide DB table vs log file before Phase 8 schema (affects eval-events endpoint design)
- WebSocket BFF proxy validation: spike task at start of Phase 11 for Keycloak token refresh in long-lived WS connection (ws: true proxy itself implemented in 10-05)

### Blockers/Concerns

- None — v1.0 complete, v1.1 roadmap defined, ready to plan Phase 7

## Session Continuity

**Last session:** 2026-06-10T12:09:29.985Z
**Stopped At:** Completed 11-05-PLAN.md
**Resume File:** None
