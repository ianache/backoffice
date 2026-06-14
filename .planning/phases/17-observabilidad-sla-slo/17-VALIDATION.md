---
phase: 17
slug: observabilidad-sla-slo
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-13
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest 8.3.3 + pytest-asyncio 0.24.0 |
| **Framework (frontend/microuis)** | vitest ^1.6.0 (mirrors mui-labeling/mui-feature-flags) |
| **Config file** | none — no `conftest.py` in `backend/tests/`; each test file is self-contained (per `test_audit_domain.py` precedent) |
| **Quick run command (backend)** | `cd backend && python -m pytest tests/test_observability_domain.py -x` |
| **Quick run command (frontend)** | `cd microuis/mui-observability && pnpm test` (vitest run) |
| **Full suite command (backend)** | `cd backend && python -m pytest` |
| **Full suite command (frontend)** | `pnpm -w test` (or per-workspace `pnpm --filter @backoffice/mui-observability test`) |
| **Estimated runtime** | ~30 seconds (backend), ~20 seconds (frontend) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_observability_*.py -x` (backend) and/or `pnpm --filter @backoffice/mui-observability test` (frontend), depending on which layer the task touches
- **After every plan wave:** Run `cd backend && python -m pytest` (full backend suite) + `pnpm -w test` (full frontend suite)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-T1 | 17-01 | 1 | OBS-01 | — | `service_health_samples` model/migration creates table with correct columns/indexes | unit (model import) | `pytest tests/test_observability_domain.py::test_service_health_sample_model -x` | ❌ W0 | ⬜ pending |
| 17-01-T2 | 17-01 | 1 | OBS-02 | — | `_classify()` returns UP/DEGRADED per 100ms threshold; each `_check_*` isolates exceptions | unit | `pytest tests/test_observability_domain.py::test_classify_thresholds -x` | ❌ W0 | ⬜ pending |
| 17-02-T1 | 17-02 | 2 | OBS-03 | V2/V4 | `GET /health/services` returns 5 services with status/latency, requires `X-Internal-Secret` | integration (httpx ASGI client) | `pytest tests/test_observability_router.py::test_health_services_endpoint -x` | ❌ W0 | ⬜ pending |
| 17-02-T1 | 17-02 | 2 | OBS-04 | V4/V5 | `GET /observability/metrics?range=24h` returns uptime_pct/p95/p99/error_rate per service, `tenant_id` accepted-not-filtered | integration | `pytest tests/test_observability_router.py::test_metrics_endpoint_ranges -x` | ❌ W0 | ⬜ pending |
| 17-01-T2 | 17-01 | 1 | OBS-05 | — | UP/DEGRADED/DOWN classification matches D-06/D-07/D-08 thresholds | unit | covered by OBS-02 test | ❌ W0 | ⬜ pending |
| 17-01-T2 | 17-01 | 1 | OBS-06 | — | Health checker loop survives per-check exceptions (DOWN classification on failure, loop continues) | unit (mock check raises, assert loop continues + writes DOWN sample) | `pytest tests/test_observability_domain.py::test_health_checker_resilience -x` | ❌ W0 | ⬜ pending |
| 17-04-T2 | 17-04 | 4 | OBS-07 | — | mui-observability remote builds and exposes `./routes`; Shell loads it via REMOTE_MANIFEST | smoke (vitest + manual federation build check) | `pnpm --filter @backoffice/mui-observability build` | ❌ W0 | ⬜ pending |
| 17-03-T2 | 17-03 | 3 | OBS-08 | V4 | StatusCard/LatencyTrendChart/UptimeSummary components render with mock data; role gating hides nav for unauthorized roles | unit (vitest component tests, mirrors mui-labeling conventions) | `pnpm --filter @backoffice/mui-observability test` | ❌ W0 | ⬜ pending |
| 17-01-T2 | 17-01 | 1 | OBS-09 | — | `prune_old_samples()` deletes rows older than 30 days, leaves recent rows intact | unit (async SQLite session, mirrors `test_labels_service.py`) | `pytest tests/test_observability_domain.py::test_prune_old_samples -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Task IDs are placeholders — planner fills in actual plan/task numbers when PLAN.md files are generated.*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_observability_domain.py` — stubs for OBS-01, OBS-02, OBS-05, OBS-06, OBS-09 (model, classification, health-checker resilience, pruning) — follow `test_labels_service.py`'s async SQLite AsyncSession + autouse fixture conventions for DB-touching tests, and `test_audit_domain.py`'s no-DB pure-function style for `_classify()`
- [ ] `backend/tests/test_observability_router.py` — stubs for OBS-03, OBS-04 (endpoint integration tests) — follow `test_labels_router.py`/`test_audit_domain.py` ASGI test client conventions
- [ ] `microuis/mui-observability/` — entire scaffold is new (package.json, vite.config.ts, vitest config) — follow `mui-labeling`'s exact file layout; vitest config inherited from root `vite.config.ts` `test:` block
- [ ] Framework install: none — pytest/pytest-asyncio/vitest already present at workspace root; only `chart.js`+`vue-chartjs` need installing in the new microui

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard visual layout (status cards + trend chart + uptime summary) renders correctly in browser | OBS-08 | Component tests verify render with mock data, but visual layout/charting fidelity needs manual confirmation | Start dev servers, log in as PlatformAdmin, navigate to Observability nav item, confirm 5 status cards, latency trend chart, and uptime % summary all display |
| Role gating hides/shows nav item correctly for PlatformAdmin vs TenantOwner/TenantAdmin vs other roles | OBS-08, D-10/D-11 | Requires logging in as different roles via Keycloak | Log in as each role per D-10/D-11, confirm nav visibility and read-only vs full access |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
