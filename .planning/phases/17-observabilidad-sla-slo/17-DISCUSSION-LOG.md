# Phase 17: Observabilidad SLA SLO - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 17-observabilidad-sla-slo
**Areas discussed:** Dashboard scope/placement, Metrics endpoint scope, SLO status thresholds, Components monitored, Access roles, Dashboard content

---

## Dashboard scope & placement

REQUIREMENTS.md lists "mui-observability (SLA/SLO Dashboard)" as Out of Scope, deferred to v1.2. ROADMAP.md Phase 17 (added 2026-06-12) explicitly requires a frontend dashboard now — a direct conflict needing resolution.

| Option | Description | Selected |
|--------|-------------|----------|
| New mui-observability MUI | Follow mui-labeling precedent (Phase 20-07): new federated remote, port 5180, registered in Shell REMOTE_MANIFEST | ✓ |
| Embed in mui-tenants | Add "Observability" view inside existing mui-tenants remote alongside Audit Log | |
| Backend-only this phase | Build table/checker/endpoints now, defer ALL frontend to Phase 18/19, honoring REQUIREMENTS.md's original deferral | |

**User's choice:** New mui-observability MUI
**Notes:** ROADMAP Phase 17 (more recent than REQUIREMENTS.md's Out-of-Scope note) is treated as superseding — dashboard ships this phase.

---

## Metrics endpoint scope (GET /bff/observability/metrics)

Per-tenant SDK evaluation telemetry (SDK_EVAL_EVENTS_AGGREGATED) doesn't exist until Phase 18 — what can this endpoint return in Phase 17?

| Option | Description | Selected |
|--------|-------------|----------|
| Platform-wide health aggregates only | Aggregates service_health_samples (uptime%, latency p95/p99, error rate per component) over 24h/7d/30d; tenant_id accepted but not meaningfully filtered, documented as known limitation | ✓ |
| Defer this endpoint to Phase 18 | Phase 17 implements only GET /bff/health/services; /metrics ships in Phase 18 with real telemetry data | |

**User's choice:** Platform-wide health aggregates only
**Notes:** tenant_id query param remains in the ICD signature for forward-compatibility but has no effect yet.

---

## SLO status thresholds (UP/DEGRADED/DOWN)

| Option | Description | Selected |
|--------|-------------|----------|
| Simple latency thresholds per service | Hardcoded threshold (e.g. >100ms = DEGRADED per PROJECT.md's "health checks < 100ms" constraint), connection failure = DOWN | ✓ |
| You decide (Claude picks sensible defaults) | Claude proposes per-service thresholds during planning based on PROJECT.md constraints | |

**User's choice:** Simple latency thresholds per service

Follow-up — exact threshold value:

| Option | Description | Selected |
|--------|-------------|----------|
| 100ms flat for all 5 services | Matches PROJECT.md's existing "health checks < 100ms" constraint; single constant | ✓ |
| Per-service thresholds | e.g. MySQL/Keycloak get 200ms (external deps), FastAPI/BFF/WS Gateway use 100ms | |

**User's choice:** 100ms flat for all 5 services
**Notes:** Per-service thresholds noted as a deferred refinement (Phase 19 alert config).

---

## Components monitored

PRD §4.1 names 5 components: FastAPI Core, BFF, MySQL (DB), Keycloak, WebSocket Gateway.

| Option | Description | Selected |
|--------|-------------|----------|
| All 5 as specified | FastAPI (self-check), BFF, MySQL (SELECT 1), Keycloak (token-endpoint ping), WebSocket Gateway (active connection count from ConnectionManager) | ✓ |
| Drop WebSocket Gateway for now | Focus on the 4 'hard' infra dependencies; move WS connection-count to Phase 19 | |

**User's choice:** All 5 as specified
**Notes:** PRD ERD says "PostgreSQL" generically for the DB component — actual stack is MySQL (PROJECT.md constraint), CONTEXT.md documents this discrepancy.

---

## Access roles for mui-observability

| Option | Description | Selected |
|--------|-------------|----------|
| PlatformAdmin only | Matches PRD §3 literally; service_health_samples has no tenant_id so nothing tenant-specific exists yet | |
| PlatformAdmin + TenantOwner/TenantAdmin (read-only) | More permissive than PRD §3 strictly requires; builds toward Phase 19's tenant-local alert config | ✓ |

**User's choice:** PlatformAdmin + TenantOwner/TenantAdmin (read-only)

---

## Dashboard content

Per PRD: "current status, trends, and SLO breach indicators" — no existing mockup to anchor on.

| Option | Description | Selected |
|--------|-------------|----------|
| Status cards (5 services) | UP/DEGRADED/DOWN badge + current latency per component, from GET /bff/health/services | ✓ |
| Latency trend chart | Line/sparkline chart of latency over 24h/7d/30d per service, from GET /bff/observability/metrics | ✓ |
| Uptime % summary | % of samples in UP status over selected range, per service — addresses the "SLA" framing | ✓ |

**User's choice:** All three (multiSelect) — Status cards + Latency trend chart + Uptime % summary
**Notes:** No charting library exists anywhere in the monorepo (verified via package.json grep) — researcher should propose a lightweight option.

---

## Claude's Discretion

- Health Checker Engine polling architecture (no existing background-task pattern in `backend/app/main.py`)
- How the backend health-checks the BFF without circularity
- Charting library choice for the latency trend chart
- Retention/pruning policy for `service_health_samples`

## Deferred Ideas

- Per-service configurable thresholds (vs. flat 100ms) — revisit in Phase 19 (Alert Manager)
- `service_health_samples` retention/pruning job — revisit alongside Phase 18's eval-events pruning
