# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-06)

**Core value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.
**Current focus:** Phase 1 — Foundation & Auth

## Current Position

Phase: 1 of 5 (Foundation & Auth)
Plan: 1 of 4 in current phase
Status: Executing
Last activity: 2026-06-06 — Plan 01-01 completed (monorepo bootstrap + Keycloak dev env)

Progress: [█░░░░░░░░░] 5%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 7 min
- Total execution time: 0.12 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-and-auth | 1 | 7 min | 7 min |

**Recent Trend:**
- Last 5 plans: 7 min
- Trend: -

*Updated after each plan completion*

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

### Pending Todos

- Start Docker Desktop and run `docker compose up -d` to complete Keycloak runtime verification

### Blockers/Concerns

- Docker Desktop not in PATH during plan execution — Keycloak runtime verification deferred to user

## Session Continuity

Last session: 2026-06-06
Stopped at: Completed 01-01-PLAN.md (monorepo bootstrap + Keycloak dev env)
Resume file: None
