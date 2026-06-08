---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-06-07T18:30:00.000Z"
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 29
  completed_plans: 18
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-06)

**Core value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.
**Current focus:** Phase 5 — Rule Builder

## Current Position

Phase: 05-rule-builder — IN PROGRESS
Plan: 01 COMPLETE — vuedraggable@next installed; useRuleSimulator composable and ChipTagInput component built (Wave 1 foundations)
Status: Phase 5 plan 01/03 done — Wave 1 leaf-level pieces complete, Wave 2 (RuleCard + RuleBuilderView) ready to start
Last activity: 2026-06-07 — 05-01 foundations built: evaluation composable + chip-tag input

Progress: [████████░░] 62% (of phase 05, plan 1/3 done) | [█████████████████░░░] ~62% (of total roadmap)

## Performance Metrics

**Velocity:**
- Total plans completed: 9
- Average duration: ~12 min (including human checkpoint time)
- Total execution time: ~2.2 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-and-auth | 4 | ~50 min | ~12.5 min |
| 02-tenant-management | 4 | ~55 min | ~13.7 min |
| 02.1-ui-system | 1 | ~10 min | ~10.0 min |

**Recent Trend:**
- Last 5 plans: ~30 min (E2E), 10m (02-01), 10m (02-02), 15m (02-03), 20m (02-04)
- Trend: stable

*Updated after each plan completion*
| Phase 02-tenant-management P01 | 10m | 2 tasks | 13 files |
| Phase 02-tenant-management P02 | 10m | 3 tasks | 5 files |
| Phase 02-tenant-management P03 | 15m | 2 tasks | 4 files |
| Phase 02-tenant-management P04 | 20m | 3 tasks | 10 files |
| Phase 06-stitch-ui-implementation P03 | 20m | 2 tasks | 4 files |
| Phase 06-stitch-ui-implementation P04 | 18m | 3 tasks | 6 files |
| Phase 03-user-management P03 | 2m | 2 tasks | 2 files |
| Phase 03-user-management P01 | 20m | 2 tasks | 12 files |
| Phase 03-user-management P04 | 5m | 2 tasks | 7 files |
| Phase 03-user-management P05 | 10m | 2 tasks (1 auto + 1 human-verify) | 2 files |
| Phase 03-user-management P06 | 20m | 3 tasks (2 auto + 1 human-verify) | 3 files |
| Phase 04-feature-flags P01 | 5m | 2 tasks (TDD) | 9 files |
| Phase 04-feature-flags P02 | 1m | 1 task (TDD) | 1 file |
| Phase 04-feature-flags P03 | 5m | 2 tasks (1 impl + 1 smoke) | 2 files |
| Phase 04-feature-flags P04 | 6 | 2 tasks | 2 files |
| Phase 04-feature-flags P05 | 15m | 3 tasks | 7 files |
| Phase 04-feature-flags P06 | 4 | 2 tasks | 3 files |
| Phase 04-feature-flags P07 | ~30m | 2 tasks (1 auto + 1 human-verify) | 7 files |
| Phase 05-rule-builder P01 | 8m | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Stack cerrado: Vue 3 + Pinia / Node.js BFF / Python Backend / PostgreSQL / Keycloak
- Multi-tenant lógico (no físico) — decisión de arquitectura
- Feature flags son el core value; sin evaluación determinista el sistema no diferencia
- pnpm workspaces monorepo (bff, portal, microuis/*) with single root install [01-01]
- Keycloak realm roles (not client roles) for all app roles — realm_access.roles simpler in BFF JWT [01-01]
- lightweightAccessTokenEnabled=false on both clients to preserve JWT role claims [01-01]
- esbuild + vue-demi build scripts approved in pnpm-workspace.yaml (pnpm 11.x security policy) [01-01]
- [Phase 01-02]: JWKS singleton (createRemoteJWKSet) prevents per-request key fetching — caches and handles Keycloak key rotation
- [Phase 01-02]: APP_ROLES allowlist in auth middleware strips Keycloak internals (offline_access, uma_authorization) before propagating roles to frontend
- [Phase 01-02]: clockTolerance: 10s in jwtVerify to handle BFF/Keycloak clock skew
- [Phase 01-04]: Remote QA Keycloak (oauth2.qa.comsatel.com.pe, realm Apps) used instead of local Docker — eliminates Docker Desktop dependency
- [Phase 01-04]: checkLoginIframe: false required for cross-origin Keycloak (CSP frame-ancestors block)
- [Phase 01-04]: backoffice-portal (public PKCE) + backoffice-bff (confidential) clients provisioned in Apps realm
- [Phase 01-04]: Test user bo.admin / Backoffice1! with PlatformAdmin role — E2E verified
- [Phase 02-tenant-management]: Use asyncmy as the MySQL driver for SQLAlchemy async compatibility
- [Phase 02-tenant-management]: Set expire_on_commit=False in AsyncSessionFactory to prevent DetachedInstanceError
- [Phase 02-tenant-management]: Use http-proxy-middleware for BFF-to-Backend communication with header injection (X-Internal-Secret, X-User-Sub, X-User-Roles)
- [Phase 02-tenant-management]: Implement Tenants UI with side drawer pattern, tabs (General/Whitelabel), and color pickers.
- [Phase 06-stitch-ui-implementation]: Custom Vue login form uses Keycloak ROPC grant instead of redirect-based login — enables portal-native Stitch UX
- [Phase 06-stitch-ui-implementation]: Visual regression baselines captured for light, dark, and error states with maxDiffPixelRatio 0.1 tolerance
- [Phase 06-04]: Use color-mix(in srgb, var(--primary) 8%, transparent) for M3 state-layer hover — correct Stitch pattern (not brightness filter)
- [Phase 06-04]: md-menu requires positioning="popover" inside overflow:hidden table containers to avoid invisible menus
- [Phase 03-02]: req.user in auth.ts has no tenantId/attributes — X-User-Tenant-Id will be empty until Keycloak protocol mapper for tenant_id attribute is added
- [Phase 03-02]: Native fetch (Node 18+) used in keycloak-admin.ts — no additional HTTP library dependency needed
- [Phase 03-03]: UserPayload.productRoles uses Record<string, string> for multi-product role assignment
- [Phase 03-03]: setEnabled uses separate /enable and /disable endpoints (not a PATCH with body)
- [Phase 03-03]: activeCount/pendingCount exposed as plain functions (not computed refs) for simplicity
- [Phase 03-01]: MySQL 5.6 has no JSON column type — user_events.context stored as TEXT with JSON serialize/deserialize in service layer
- [Phase 03-01]: Keycloak role assignment requires GET /roles/{name} first for UUID — cannot assign by name only (returns 400)
- [Phase 03-01]: Tenant scoping enforced at service layer via actor_tenant_id parameter, never trusting request body for listing
- [Phase 03-04]: Router /users roles include PlatformAdmin + TenantAdmin + TenantOwner — permissive for Phase 3, can be narrowed later
- [Phase 03-04]: UserDrawer uses custom CSS tab bar (not md-tabs) — allows disabled Activity tab when user=null without MDWC disabled attribute inconsistencies
- [Phase 03-04]: UserActivityTab calls usersService.listEvents() directly on mount, not through store (per-user transient data pattern)
- [Phase 03-05]: Router /users roles narrowed to TenantAdmin + TenantOwner only — PlatformAdmin removed (was permissive in 03-04)
- [Phase 03-05]: Tenants nav button gained explicit v-if PlatformAdmin guard — TenantAdmins no longer see Tenants nav item
- [Phase 03-user-management]: Dual JWT claim name fallback (tenant_id / tenantId) in requireAuth covers both Keycloak mapper emission styles [03-06]
- [Phase 03-user-management]: Keycloak protocol mapper configured on usuario scope (covers both portal+bff clients) — tenant_id flows in JWT, cross-tenant isolation E2E verified [03-06]
- [Phase 04-01]: evaluate_flag() uses SCOPE_PRIORITY dict + max() for deterministic priority — company(4)>product(3)>tenant(2)>global(1), not recency-based
- [Phase 04-01]: _evaluate_rule() uses OPERATORS dispatch dict (not if/elif chain) — returns False on unknown operator or missing user attribute, never raises
- [Phase 04-01]: rules, tags, members stored as TEXT (JSON arrays) in feature_flags/segments tables — MySQL 5.6 safe, json.dumps/loads in service layer
- [Phase 04-01]: FlagResponse.model_validator(mode='before') handles both dict input and ORM objects for TEXT deserialization
- [Phase 04-02]: Tests import evaluate_flag/_evaluate_rule at module level — collection errors surface immediately (not as test failures)
- [Phase 04-02]: make_flag() uses SimpleNamespace per plan spec — minimal flag objects, no DB overhead for pure evaluation tests
- [Phase 04-02]: test_scope_priority_not_recency proves SCOPE_PRIORITY dict used (not list-order) — global first in list still loses to tenant
- [Phase 04-03]: flagsRouter uses all 4 roles (PlatformAdmin | TenantAdmin | TenantOwner | ProductManager) — feature flags are cross-role, unlike /tenants (PlatformAdmin only)
- [Phase 04-03]: /flags injects X-User-Tenant-Id (like /users, unlike /tenants) — backend evaluate_flag() uses tenant context for scoped evaluation
- [Phase 04-03]: express.json() deliberately excluded on /flags mount — proxy streams raw body, established pattern from /tenants and /users
- [Phase 04-feature-flags]: [Phase 04-05]: FlagsView filter bar is visual-only in Phase 4 — filter logic deferred to Phase 5 to keep scope focused
- [Phase 04-feature-flags]: [Phase 04-05]: FlagTable emits disable(flag)/enable(flag) separately — parent FlagsView decides confirm dialog vs direct toggleFlag call
- [Phase 04-feature-flags]: segment_members keyed by flag_id dict for O(1) lookup in evaluate_flag(); any-match semantics; user_id dual key fallback (id/sub) [04-06]
- [Phase 04-feature-flags]: FlagDrawer takes ownership of save flow (store calls + segment linking) — emits @saved(flag); FlagsView shows toast only [04-07]
- [Phase 04-feature-flags]: Capture-before-await pattern: snapshot reactive refs to local const before first async call to prevent reactivity teardown mid-handler [04-07]
- [Phase 04-feature-flags]: Diff-based segment sync (toAdd/toRemove) in FlagDrawer — correct general pattern for many-to-many UI associations; segment removal from flags implemented in Phase 4 (not deferred) [04-07]
- [Phase 04-feature-flags]: PlatformAdmin/ProductManager bypass tenant_id filter in list_flags — global roles see all flags across tenants [04-07]
- [Phase 05-01]: useRuleSimulator uses watchEffect (not watch+deep) — auto-tracks rules and contextJson refs without explicit dep list
- [Phase 05-01]: OPERATORS in/notIn use Array.isArray guard — matches Python isinstance(expected, list) semantics
- [Phase 05-01]: regex operator wraps new RegExp() in try/catch returning false — safe against malformed patterns

### Pending Todos

- [Phase 3 complete] User Management (USER-01 through USER-06) — DONE
- Plan Phase 4: Feature Flags (next phase)
- Verify BFF port 3000 is free before starting (Dashboard Studio may occupy it)
- [ui-brand] Apply Google Stitch System Design [DONE]
- [ui-brand] Implement Light and Dark Mode Toggle [DONE]

### Blockers/Concerns

- None — Phase 2 complete.

## Session Continuity

Last session: 2026-06-07
Stopped at: Completed 05-01-PLAN.md — Wave 1 foundations (useRuleSimulator + ChipTagInput) complete; ready for 05-02 (RuleCard)
Resume file: None
