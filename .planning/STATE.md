---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: MVP2
current_plan: 1
status: executing
stopped_at: Phase 21 UI-SPEC approved
last_updated: "2026-06-13T23:06:01.314Z"
last_activity: 2026-06-13
progress:
  total_phases: 15
  completed_phases: 11
  total_plans: 59
  completed_plans: 59
  percent: 73
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-07)

**Core value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.
**Current focus:** Phase 20 — localization-white-label-engine

## Current Position

Phase: 20 (localization-white-label-engine) — EXECUTING
Plan: 1 of 9
**Current Plan:** 1
**Total Plans in Phase:** 9
**Status:** Executing Phase 20
**Last Activity:** 2026-06-13
Last activity detail: 2026-06-13 — Completed 20-02-PLAN.md (labels service layer: backend/app/domains/labels/service.py implementing resolve_labels() 3-level inheritance resolver (tenant/company/product override-by-proximity) with an in-memory cache + invalidate_namespace_cache(), full Namespace/LocalizedLabel CRUD with optimistic-concurrency 409s on update_label/update_label_value (PI-02 message), and missing-label report dedup/hit-counting with auto-cleanup on create_label() (RF-06); 11 async unit tests across test_labels_resolve.py and test_labels_service.py). LBL-03/LBL-04/LBL-13 complete (pending REQUIREMENTS.md traceability entries — see deferred-items.md).

**Progress:** [██████████] 98%

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
| Phase 11-mui-feature-flags-sdk-clients P06 | 12min | 3 tasks | 13 files |
| Phase 11-mui-feature-flags-sdk-clients P07 | 12min | 2 tasks | 4 files |
| Phase 11-mui-feature-flags-sdk-clients P09 | 16min | 3 tasks | 7 files |
| Phase 11-mui-feature-flags-sdk-clients P10 | 8min | 2 tasks | 5 files |
| Phase 11-mui-feature-flags-sdk-clients P08 | 10min | 3 tasks | 8 files |
| Phase 13-simulator-test-contexts P02 | 12min | 3 tasks | 6 files |
| Phase 13-simulator-test-contexts P01 | 12min | 3 tasks | 5 files |
| Phase 13-simulator-test-contexts P03 | 8min | 3 tasks | 3 files |
| Phase 13-simulator-test-contexts P04 | 8min | 3 tasks | 3 files |
| Phase 14-flag-scope-targeting-list-valued-rules P01 | 12min | 3 tasks | 11 files |
| Phase 14-flag-scope-targeting-list-valued-rules P04 | 12min | 3 tasks | 4 files |
| Phase 14 P03 | 9min | 3 tasks | 7 files |
| Phase 14-flag-scope-targeting-list-valued-rules P02 | 18min | 3 tasks | 6 files |
| Phase 14-flag-scope-targeting-list-valued-rules P05 | 12min | 3 tasks | 5 files |
| Phase 15-and-rule-combination-semantics P02 | 12min | 2 tasks | 5 files |
| Phase 15 P01 | 10min | 3 tasks | 8 files |
| Phase 15-and-rule-combination-semantics P04 | 12min | 3 tasks | 3 files |
| Phase 15-and-rule-combination-semantics P03 | 9min | 3 tasks | 5 files |
| Phase 16-mvp2-auditoria P01 | 12min | 3 tasks | 10 files |
| Phase 16-mvp2-auditoria P02 | 8min | 2 tasks | 3 files |
| Phase 16 P03 | 8min | 2 tasks | 5 files |
| Phase 16-mvp2-auditoria P04 | 10min | 3 tasks | 6 files |
| Phase 16-mvp2-auditoria P05 | 8min | 2 tasks | 4 files |
| Phase 20-localization-white-label-engine P01 | 15min | 3 tasks | 7 files |
| Phase 20-localization-white-label-engine P02 | 20min | 2 tasks | 3 files |
| Phase 20-localization-white-label-engine P09 | 12min | 2 tasks | 3 files |
| Phase 20 P04 | 18min | 2 tasks | 3 files |
| Phase 20-localization-white-label-engine P03 | 25min | 2 tasks | 4 files |
| Phase 20-localization-white-label-engine P05 | 8min | 1 tasks | 2 files |
| Phase 20-localization-white-label-engine P06 | 12min | 2 tasks | 4 files |
| Phase 20 P07 | 14min | 3 tasks | 21 files |

## Accumulated Context

### Roadmap Evolution

- Phase 12 added (2026-06-11): Dogfooding Feature Flags — portal gated by its own flags (product `backoffice`): bo.feature (menu), bo.feature.create (Create Flag + Clone), bo.feature.update (Edit pencil)
- Phase 13 added (2026-06-11): Simulator Test Contexts — persistent per-flag test contexts in the Live Simulator + toggle to use the logged-in user's real property values as Test Context
- Phase 14 added (2026-06-11): Flag Scope Targeting + List-Valued Rules — combobox producto/tenant/company según scope del flag (target persistido en backend, enforcement en SDK bootstrap/evaluación) + Rule values como lista separada por coma con match-any para atributos lista (ej. roles), con paridad de operador en backend/sdk-js/sdk-python/useRuleSimulator
- Phase 15 added (2026-06-12): AND Rule Combination Semantics — multi-rule evaluation combina con AND (true solo si TODAS las reglas matchean, false en caso contrario) con paridad en los 4 evaluadores (backend, sdk-js, sdk-python, useRuleSimulator); OR y grupos de reglas diferidos a un release futuro
- Phase 15 expanded (2026-06-12): Flags Page Filters — filtros en `/flags` por Status, Tags, Complexity, Environment y target de scope (Products, Tenants o Global)
- Phase 16 added (2026-06-12): MVP2 Auditoria — scope set to PRD_MVP3.md §6 (Audit Log Timeline + Diff Viewer)
- Phases 17-19 added (2026-06-12): PRD_MVP3.md scope split across phases — 17=Observabilidad/SLA-SLO (§4), 18=Telemetry Ingestion SDK Eval Events (§5, §8.2), 19=Redis PubSub WS Scaling + Webhook Alerts (§7, §8.1)
- Phase 20 added (2026-06-12): Localization White Label Engine — scope set to docs/white_labeling_engine_design.md (localized_labels DAG inheritance, BFF resolver+Redis cache, namespace lazy-loading, two-phase hydration, Vue/Flutter SDKs, WS/SSE hot-reload)
- Phase 21 added (2026-06-13): Login Localization via Labeling SDK — apply LabelClient/$t to the portal login, including pre-auth context/locale resolution, eager hydration, missing-key reporting, safe fallback, and namespace hot reload

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
- [Phase 11-mui-feature-flags-sdk-clients]: [11-06]: verify_sdk_secret header takes precedence over sdk_key query param even if query param is invalid - preserves existing route behavior
- [Phase 11-mui-feature-flags-sdk-clients]: [11-06]: bootstrap_flags() adds members:[] to ALL segment types for schema consistency - rule_based segments get empty array
- [Phase 11-mui-feature-flags-sdk-clients]: [11-06]: sdk/sdk-js uses vitest@^2.1.0 (isolated devDependency) per plan spec, not workspace-standard ^1.6.0
- [Phase 11-mui-feature-flags-sdk-clients]: [11-07]: index.ts switched from export * (types/evaluator) to explicit named exports plus FeatureFlagClient/InitOptions/initialize() factory - OPERATORS no longer re-exported from package root, still importable from ./evaluator directly
- [Phase 11-mui-feature-flags-sdk-clients]: [11-09]: Created dedicated sdk/sdk-python/.venv (own pyproject.toml, outside pnpm workspace) to avoid downgrading global httpx/pytest/pytest-asyncio used by other tools
- [Phase 11-mui-feature-flags-sdk-clients]: [11-09]: sdk-python evaluate_flag(entry, user) operates on a single bootstrap FlagEntry dict (Plan 06/sdk-js shape), distinct from backend's evaluate_flag(flags_list, context) - both share identical OPERATORS/_evaluate_rule core
- [Phase 11-mui-feature-flags-sdk-clients]: [11-10]: ws_base_url derived via simple string replace (https->wss, http->ws) on api_base_url, overridable via constructor kwarg
- [Phase 11-mui-feature-flags-sdk-clients]: [11-10]: WS reconnect attempt counter resets to 0 immediately after ws.send(sdk_key) succeeds, matching sdk-js 'attempt resets on successful connect'
- [Phase 11-mui-feature-flags-sdk-clients]: [11-10]: test_client.py gained autouse fixture mocking ws_reconnect_loop to prevent dangling background WS-connect tasks after initialize() was extended
- [Phase 11-mui-feature-flags-sdk-clients]: [11-08]: ReconnectingSocket attempt counter resets to 0 on successful onopen - backoff restarts from 1s after a stable connection drops
- [Phase 11-mui-feature-flags-sdk-clients]: [11-08]: TelemetryBatcher.flush() swallows fetch errors - failed batches dropped rather than retried/requeued (acceptable telemetry tradeoff)
- [Phase 11-mui-feature-flags-sdk-clients]: [11-08]: client.test.ts/cache.test.ts now stub WebSocket/navigator/window globals since initialize() constructs ReconnectingSocket and TelemetryBatcher as side effects
- [Phase 13-02]: useUserContext exposes both real JWT sub and email as separate keys (not collapsing sub into email like existing main.ts useBoFlags init pattern)
- [Phase 13-02]: product_id hardcoded to 'backoffice' per CONTEXT.md dogfooding decision
- [Phase 13-02]: useUserContext reuses the existing shared pinia singleton - no new shared dependency entry needed in vite.config.ts
- [Phase 13-simulator-test-contexts]: [13-01]: test_context stored as sa.Text() (not sa.JSON()) - MySQL 5.6 has no native JSON type, matches rules/tags/conditions/members precedent
- [Phase 13-simulator-test-contexts]: [13-01]: Single additive migration (no 3-step expand/backfill/cleanup) - purely additive nullable column, no data backfill needed
- [Phase 13-simulator-test-contexts]: [13-01]: test_context excluded from parse_text_fields()/parse_json_fields() model_validators - JSON object string passed through verbatim, not a JSON array needing deserialization
- [Phase 13-simulator-test-contexts]: [13-03]: Real-context mapping uses useUserContext()'s exact key names (sub, email, roles, tenant_id, product_id) with no renaming - matches Phase 12 dogfooding rule attribute names
- [Phase 13-simulator-test-contexts]: [13-03]: contextJson initialization uses props.testContext || PLACEHOLDER_CONTEXT (truthy check) so empty-string saved contexts also fall back to placeholder
- [Phase 13-simulator-test-contexts]: [13-04]: RuleBuilderView omits isSavingTestContext loading flag - RuleSimulator has no loading-state prop, kept handler minimal
- [Phase 13-simulator-test-contexts]: [13-04]: SegmentsView.handleSaveTestContext reassigns editingSegment to updateSegment() response so SegmentForm reflects persisted test_context without remounting
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-01]: Companies domain mirrors products domain 1:1 (models/schemas/service/router) - Company.id is immutable slug, tenant_id has no FK, CompanyUpdate excludes id+tenant_id
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-01]: BFF /companies route uses requireAuth only - backend enforces role+tenant isolation via X-User-Roles/X-User-Tenant-Id headers, per resolved open question #3
- [Phase 14-04]: isArrayValueOperator (in/notIn/anyOf) replaces isArrayOperator for RuleCard operator-switch value coercion; ChipTagInput rendering stays gated on isArrayOperator (in/notIn only)
- [Phase 14-04]: anyOfRaw local ref synced via watch on [rule._id, rule.operator] with immediate:true (not on rule.value change) to avoid trailing-comma keystroke round-trip
- [Phase 14-04]: RuleSimulator.vue mini-chips use inline Tailwind utility classes instead of adding a new scoped style block
- [Phase 14]: [14-03]: anyOf operator lambda identical across backend/sdk-js/sdk-python - set intersection for list actual, membership for scalar actual, case-sensitive
- [Phase 14]: [14-03]: Company-scope target guard in SDK evaluators uses null-check (!= null / is not None) so missing/null company_id skips guard - preserves legacy cached payload behavior
- [Phase 14]: [14-03]: No tenant/product guards added to SDK local evaluators - bootstrap already filters by SDK client identity per CONTEXT.md
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-02]: FlagUpdate has NO model_validator - merged-state scope/target validation happens in router._validate_update_target() only when scope/tenant_id/product_id/company_id are present in the PATCH payload, preserving legacy partial-update behavior
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-02]: bootstrap_flags company-scope inclusion treats company_id as per-user-context (checked by evaluate_flag), not per-SDK-client - company-scoped flags are included in bootstrap unless flag.tenant_id also mismatches the requesting tenant
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-02]: /sdk/evaluate now calls list_flags(db) unfiltered - the previous tenant_id pre-filter starved product/company-scoped flags (tenant_id NULL) before evaluate_flag's existing per-scope candidate matching could resolve them
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-05]: validateFlagTarget/buildTargetFields kept dependency-free (no Vue) for direct vitest unit testing
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-05]: Tenant lookup wrapped in try/catch with useUserContext().tenant_id fallback ('My tenant') on 403 from PlatformAdmin-only /tenants
- [Phase 14-flag-scope-targeting-list-valued-rules]: [14-05]: Scope-switch watcher clears all three target refs unconditionally when oldScope !== newScope
- [Phase 15-and-rule-combination-semantics]: [15-02]: Both SDK evaluators branch on rule_combination_mode immediately after the company-scope guard and before the existing rules loop, mirroring backend Plan 15-01 placement exactly
- [Phase 15-and-rule-combination-semantics]: [15-02]: AND mode with non-empty rules is strict-false (any failure returns false immediately, no segment/default_val fallback); empty rules fall through unchanged to legacy path
- [Phase 15]: [15-01]: AND mode with non-empty rules is strict-false (no segment/default_val fallback) - locked CONTEXT.md Option C decision
- [Phase 15]: [15-01]: Empty rules + mode='and' falls through to exact legacy no-rules path - vacuous AND unchanged
- [Phase 15]: [15-01]: FlagUpdate keeps no model_validator (14-02 precedent) - rule_combination_mode validated via standalone field_validator
- [Phase 15-and-rule-combination-semantics]: [15-04]: Client-side computed filtering only for /flags (no URL sync, no backend params); FlagFilterState as single reactive ref with spread-reset clearFilters; Scope Target uses 4 buckets (Global/Tenants/Products/Companies)
- [Phase 15-and-rule-combination-semantics]: [15-03]: overallResult computed inside the existing watchEffect (AND: ruleResults.every(Boolean) when rules non-empty else null; first_match: mirrors matchedResult) - unifies badge logic across both modes
- [Phase 15-and-rule-combination-semantics]: [15-03]: RuleSimulator badge bound to overallResult in both modes (overallResult === matchedResult in first_match) - avoids duplicate badge branches
- [Phase 15-and-rule-combination-semantics]: [15-03]: AND/ELSE IF connector label dynamic on localMode - first_match chains no longer visually read as AND
- [Phase 16-mvp2-auditoria]: [16-01]: AuditLogResponse excludes payload_before/payload_after (list view stays light, <150ms target) - only the /diff endpoint deserializes payloads
- [Phase 16-mvp2-auditoria]: [16-01]: AuditLogCreate is internal-only (no HTTP exposure) - write_audit_log() is the single insertion point called from other domains' service/router layers in Plans 16-02/16-03
- [Phase 16-mvp2-auditoria]: [16-01]: e001 down_revision = 'd004' per plan; pre-existing multi-head condition in alembic/versions/ left untouched (out of scope)
- [Phase 16-mvp2-auditoria]: [16-01]: bff audit.ts forwards X-User-Email in addition to Sub/Roles/Tenant-Id for future write-path use (Plans 16-02/16-03)
- [Phase 16-mvp2-auditoria]: [16-02]: Flag audit writes use flag.tenant_id (own nullable field) not X-User-Tenant-Id header - matches audit_logs.tenant_id nullability for global-scope flags
- [Phase 16-mvp2-auditoria]: [16-02]: update_segment/delete_segment fetch existing segment via get_segment() before mutation to capture non-trivial payload_before diff
- [Phase 16-mvp2-auditoria]: [16-03]: users/service.py write_audit_log() calls use user_email=None for target user - Keycloak Admin API service layer has no FastAPI Request/Header context
- [Phase 16-mvp2-auditoria]: [16-03]: tenants router update_tenant/delete_tenant accept extra pre-fetch select(Tenant) for before-snapshot, no service signature refactor
- [Phase 16-mvp2-auditoria]: [16-03]: companies router gained x_user_sub/x_user_email Header(default='') params for audit actor attribution
- [Phase 16-mvp2-auditoria]: [16-04]: Environment badges colored via mockup convention - production=error-container, staging=tertiary-container, development=secondary-container
- [Phase 16-mvp2-auditoria]: [16-04]: Pagination reuses lastFilters ref (set only by Apply Filters) so page navigation doesn't reset filter form fields
- [Phase 16-mvp2-auditoria]: [16-04]: User filter is a plain text input bound to user_id (Keycloak sub) - no user-picker dropdown for MVP per CONTEXT.md
- [Phase 16-mvp2-auditoria]: [16-05]: AuditLogDiff interface flattened to {id, added, removed, modified} to match real backend AuditLogDiffResponse - no .diff nesting
- [Phase 16-mvp2-auditoria]: [16-05]: DiffModal derives Action/Target meta from a new entry: AuditLogEntry | null prop sourced from the timeline, not from the diff response
- [Phase 16-mvp2-auditoria]: [16-05]: bff tenants.ts proxyReq forwards X-User-Email (mirroring companies.ts/flags.ts) without X-User-Tenant-Id - tenants endpoints are PlatformAdmin-only
- [Phase 20-localization-white-label-engine]: [20-01]: Namespace.id is user-defined String(100) slug PK (mirrors Product.id), LocalizedLabel unique index covers tenant_id/company_id/product_id/namespace/locale/label_key, g002 seed targets real tenant id=5 with fallback, UXWriter realm role appended as last realm role entry
- [Phase ?]: [20-02]: service.py written as single file containing both Task 1 (resolver/cache) and Task 2 (CRUD/missing-report) logic per plan's full code listing; commits split by test file rather than physical file diff
- [Phase ?]: [20-02]: test_labels_service.py follows test_labels_resolve.py's async SQLite AsyncSession + autouse clear_cache() fixture conventions, not the no-DB MockFlag style used in test_feature_flags_domain.py
- [Phase ?]: [20-09]: export_namespace_csv() level column reflects the most-specific level contributing the es_PE value (documented via code comment)
- [Phase ?]: [20-09]: GET /labels/export inherits router-level verify_internal_secret dependency (X-Internal-Secret header), no new auth mechanism
- [Phase ?]: [20-09]: Actual mounted path is /labels/export (router prefix is /labels, not /api/v1/labels despite main.py comment)
- [Phase 20]: labels_report_missing returns 204 with no body (matches plan's status_code=204 spec); service.report_missing_label() return value discarded
- [Phase 20]: delete_namespace also broadcasts INVALIDATE_NAMESPACE (per plan prose: cascades label invalidation), gated on x_user_tenant_id being non-empty since namespace deletion has no per-row tenant_id to snapshot
- [Phase 20]: Test 6's PATCH path resolved dynamically via app.routes lookup by route name (update_key_value) to be resilient to the /labels vs /api/v1/labels prefix decision made in app/main.py by concurrent plan 20-03
- [Phase 20-03]: labels_router registered with app.include_router(labels_router, prefix="/api/v1") - router.py declares prefix="/labels", admin API mounts at /api/v1/labels/* to match test_labels_sdk_router.py (20-04) expectations
- [Phase 20-03]: RestoreOverridePayload(BaseModel) declared via standard top-level pydantic import, not walrus-operator hack
- [Phase ?]: [20-05]: labels.ts pathRewrite is /api/v1/labels (not /labels like flags.ts) - backend labels_router mounted at /api/v1/labels per 20-03, verified via live FastAPI route inspection
- [Phase ?]: [20-05]: UXWriter added to labels.ts requireRole allow-list alongside PlatformAdmin/TenantAdmin/TenantOwner/ProductManager - backend enforces value-only restriction on PATCH /keys/{id}/value
- [Phase ?]: [20-06]: Tests placed in sdk/sdk-js/tests/labels.test.ts (matching client.test.ts/websocket.test.ts location), not src/labels.test.ts as plan literally states
- [Phase ?]: [20-06]: vue added as optional peerDependency (^3.4.0) + devDependency (^3.4.29) to sdk-js; pnpm install --filter @backoffice/sdk-js linked vue@3.5.35 from workspace store
- [Phase ?]: [20-06]: LabelClient owns its own ReconnectingSocket to /sdk/ws/flags/{tenantId}, filtering INVALIDATE_NAMESPACE - fully decoupled from FeatureFlagClient, no shared WS state
- [Phase 20-07]: WorkspaceContextSelector tenant dropdown locked to user's own tenant_id for non-PlatformAdmin roles; PlatformAdmin gets full listTenantsLookup() list
- [Phase 20-07]: KeysMatrix groups flat per-locale LocalizedLabel[] response into per-label_key rows with es_PE/en_US columns - matches prototype one-row-per-key #keysTableBody layout
- [Phase 20-07]: mui-labeling registers as Module Federation remote on port 5179 via VITE_REMOTE_LABELING, following the exact REMOTE_MANIFEST/importRemote pattern as mui-feature-flags

### Pending Todos

- alembic.ini: EXISTS at backend/alembic.ini (confirmed during 07-01 execution)
- SDK telemetry data model: decide DB table vs log file before Phase 8 schema (affects eval-events endpoint design)
- WebSocket BFF proxy validation: spike task at start of Phase 11 for Keycloak token refresh in long-lived WS connection (ws: true proxy itself implemented in 10-05)

### Blockers/Concerns

- None — v1.0 complete, v1.1 roadmap defined, ready to plan Phase 7

## Session Continuity

**Last session:** 2026-06-13T23:06:01.287Z
**Stopped At:** Phase 21 UI-SPEC approved
**Resume File:** .planning/phases/21-aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini/21-UI-SPEC.md
