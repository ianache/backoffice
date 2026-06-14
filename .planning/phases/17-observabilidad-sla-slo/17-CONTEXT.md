# Phase 17: Observabilidad SLA SLO - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Implements PRD_MVP3.md §4 (Módulo de Observabilidad, SLAs y SLOs):

1. **Backend** — A new `service_health_samples` table populated by a non-blocking Health Checker Engine that polls 5 internal components every 15s (FastAPI core, BFF, MySQL, Keycloak, WebSocket Gateway).
2. **Backend endpoints** — `GET /bff/health/services` (current status of all 5 components) and `GET /bff/observability/metrics` (historical aggregates: uptime %, latency p95/p99, error rate per service over 24h/7d/30d).
3. **Frontend** — A new federated micro-UI `mui-observability` showing current status cards, latency trend charts, and uptime % summaries (SLO breach indicators).

This phase resolves a scope ambiguity between REQUIREMENTS.md (which lists "mui-observability dashboard" as deferred to v1.2) and ROADMAP.md Phase 17 (added 2026-06-12, explicitly requires a frontend dashboard now). **Resolution: the ROADMAP Phase 17 entry supersedes the older REQUIREMENTS.md deferral** — the dashboard ships in this phase as a new MUI.

Out of scope for Phase 17 (explicitly deferred):
- Per-tenant SDK evaluation telemetry (`SDK_EVAL_EVENTS_AGGREGATED`, PRD §5) — Phase 18
- Redis Pub/Sub WS scaling, webhook alerts / Alert Manager (PRD §7, §8.1, §19) — Phase 19
- The broader "KPI cards" home dashboard (Active Tenants, Total Products) from PROJECT.md's Deferred section — different feature, not this phase

</domain>

<decisions>
## Implementation Decisions

### Frontend: New mui-observability micro-UI
- **D-01:** Build a new federated remote `mui-observability`, following the `mui-labeling` scaffold pattern from Phase 20-07 (package.json, vite.config.ts with shared Vue/Pinia/Router/Axios singletons, `./routes` export).
- **D-02:** Use port **5180** (next available after mui-labeling's 5179). Register `VITE_REMOTE_OBSERVABILITY` env var and add an entry to the Shell's `REMOTE_MANIFEST` (mirroring the mui-labeling registration).
- **D-03:** This resolves the REQUIREMENTS.md "mui-observability deferred to v1.2" note — ROADMAP Phase 17 (more recent) supersedes that deferral for this milestone.

### GET /bff/observability/metrics scope (Phase 17)
- **D-04:** Returns **platform-wide aggregates only**, computed from `service_health_samples` — uptime %, latency p95/p99, and error rate per service over the requested `range` (24h/7d/30d).
- **D-05:** The `tenant_id` query param from the PRD ICD is **accepted but not meaningfully filtered yet** (no tenant dimension exists in `service_health_samples`). Document this as a known Phase 17 limitation — true per-tenant metrics arrive in Phase 18 once `SDK_EVAL_EVENTS_AGGREGATED` exists.

### Health status determination (UP / DEGRADED / DOWN)
- **D-06:** **DEGRADED** = response latency > **100ms flat threshold**, applied uniformly to all 5 components. This matches PROJECT.md's existing constraint "health checks < 100ms" — no per-service threshold config in this phase.
- **D-07:** **DOWN** = connection failure / timeout, regardless of latency.
- **D-08:** **UP** = responds within 100ms.

### Components monitored (per PRD §4.1, all 5 confirmed)
- **D-09:** FastAPI Core (self-check), BFF, MySQL (the actual DB — PRD's ERD says "PostgreSQL" generically but the project stack is MySQL per PROJECT.md constraints), Keycloak (lightweight token-endpoint ping), WebSocket Gateway (active connection count from the existing `ConnectionManager`).

### Access roles for mui-observability
- **D-10:** **PlatformAdmin** — full access (per PRD §3: "Acceso completo al dashboard de salud global").
- **D-11:** **TenantOwner / TenantAdmin** — **read-only** access to the same platform health dashboard (more permissive than PRD §3 strictly states, chosen to build toward Phase 19's tenant-local alert config).

### Dashboard content (mui-observability)
- **D-12:** **Status cards** — one per monitored component (5 total), showing UP/DEGRADED/DOWN badge + current latency, sourced from `GET /bff/health/services`.
- **D-13:** **Latency trend chart** — line/sparkline chart per component over the selected range (24h/7d/30d), sourced from `GET /bff/observability/metrics`.
- **D-14:** **Uptime % summary** — % of samples in UP status per service over the selected range, directly addressing the "SLA" framing (PROJECT.md's 99.9% uptime target).

### Claude's Discretion
- Exact polling architecture (FastAPI lifespan background task vs. another mechanism) — no existing background-task pattern exists in `backend/app/main.py`; researcher/planner should propose one.
- How the backend health-checks "BFF" without circularity (e.g., backend pings BFF's `/health`, BFF separately reports backend status) — implementation detail for planner.
- Charting library choice for the latency trend chart — no chart library exists anywhere in the monorepo yet (verified via package.json grep). Researcher should propose a lightweight option.
- Retention/pruning policy for `service_health_samples` (15s interval × 5 services = significant row growth) — not specified by PRD for this table (unlike SDK eval events in §5.4); planner may propose a sensible default or defer.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 17 scope source
- `PRD_MVP3.md` §4 — Módulo de Observabilidad, SLAs y SLOs (components monitored, SLIs, Health Checker Engine description, Collector/Dashboard/AlertManager diagram)
- `PRD_MVP3.md` §8.1 — ICD: `GET /bff/health/services`, `GET /bff/observability/metrics` (query params: tenant_id, range)
- `PRD_MVP3.md` §9 — Data model: `SERVICE_HEALTH_SAMPLES` table (id, checked_at, service_name, status, latency_ms, details)
- `PRD_MVP3.md` §10.2 — Resilience requirement: observability collection failures must never block flag evaluation
- `.planning/ROADMAP.md` — Phase 17 entry (goal, requirements placeholder OBS-01..OBS-0x, dependency on Phase 16)
- `.planning/REQUIREMENTS.md` — Out of Scope table (superseded for mui-observability per D-03), OBS-01/OBS-02/OBS-03 under "v2 Requirements"

### Closest existing pattern (reuse)
- `backend/app/domains/audit/` (Phase 16) — ORM model → Alembic migration → service → router → BFF proxy → frontend view; closest analog for `service_health_samples` table + endpoints
- `mui-labeling/` (Phase 20-07, port 5179) — most recent new-MUI scaffold; mirror its vite.config.ts singleton sharing and Shell REMOTE_MANIFEST registration for `mui-observability`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/domains/audit/models.py`, `router.py`, `service.py`, `schemas.py` — structural template for the new health/observability domain (model, migration, service, router)
- `backend/app/ws/connection_manager.py` — existing WS connection registry; source for WebSocket Gateway "active connections" health signal
- `portal/vite.config.ts` — REMOTE_MANIFEST pattern for registering new remotes (`mui-labeling` entry at line ~28 is the most recent example to mirror for `mui-observability`)

### Established Patterns
- All MVP3-era tables use `Text` for JSON-like fields (MySQL 5.6 has no native JSON type) — apply same convention if `service_health_samples.details` needs structured data
- Audit domain (Phase 16) shows the BFF proxy pattern (`bff/src/routes/audit.ts`) — `bff/src/routes/observability.ts` would follow the same shape
- Existing `/health` endpoints: `backend/app/main.py:30-32` (`GET /health` → `{"status": "ok", "service": "backoffice-backend"}`) and `bff/src/index.ts:22` — these are simple liveness checks, distinct from the new SLI-tracking health checker

### Integration Points
- `backend/app/main.py` — register new domain router + initialize health-checker background task (after `ConnectionManager` init, per existing ordering constraint)
- `portal/vite.config.ts` + Shell `REMOTE_MANIFEST` — register `mui-observability` remote
- Shell `MainLayout` nav — add "Observability" nav item gated to PlatformAdmin/TenantOwner/TenantAdmin (per D-10/D-11)

</code_context>

<specifics>
## Specific Ideas

No additional UI mockup exists for the observability dashboard (unlike audit-log, feature-flags, etc. which have HTML prototypes in `design/stitch/`). The dashboard layout (status cards + trend chart + uptime summary, per D-12/D-13/D-14) is the user's stated content requirements — no visual reference to follow. Consider running `/gsd:ui-phase 17` for a design contract before/during planning since there's no existing mockup to anchor on.

</specifics>

<deferred>
## Deferred Ideas

- **Per-service configurable thresholds** (vs. the flat 100ms in D-06) — could be revisited in Phase 19 (Alert Manager / webhook config phase) where per-tenant alert thresholds become relevant.
- **`service_health_samples` retention/pruning job** — noted as Claude's discretion above; if deferred during planning, should be revisited alongside Phase 18's `SDK_EVAL_EVENTS_AGGREGATED` pruning (PRD §5.4 mentions pruning for that table explicitly).

### Reviewed Todos (not folded)
None — no pending todos matched Phase 17 (`todo_count: 0`).

</deferred>

---

*Phase: 17-observabilidad-sla-slo*
*Context gathered: 2026-06-13*
