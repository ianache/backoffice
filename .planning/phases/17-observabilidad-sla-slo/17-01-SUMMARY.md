---
phase: 17-observabilidad-sla-slo
plan: "01"
subsystem: backend
tags: [fastapi, sqlalchemy, alembic, mysql, sqlite, health-check]

# Dependency graph
requires: []
provides:
  - service_health_samples database table and ORM model
  - Health Checker Engine background polling loop running every 15 seconds
  - Observability service layer containing status, pruning, and metrics aggregations (including hourly/daily history latency trends)
  - Unit tests verifying classification, persistence, resilience, pruning, and aggregation
affects: [17-02, 17-03, 17-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Python-side percentile calculation (p95/p99) to support MySQL 5.6
    - Dialect-aware date formatting (strftime for SQLite, date_format for MySQL) for time-series history
    - AsyncSessionFactory-based isolated sessions for background thread safety

key-files:
  created:
    - backend/app/domains/observability/__init__.py
    - backend/app/domains/observability/models.py
    - backend/app/domains/observability/schemas.py
    - backend/app/domains/observability/service.py
    - backend/app/domains/observability/health_checker.py
    - backend/alembic/versions/h001_create_service_health_samples_table.py
    - backend/tests/test_observability_domain.py
  modified:
    - backend/app/config.py
    - backend/app/main.py

key-decisions:
  - "Calculated percentiles (p95, p99) in Python to circumvent lack of window functions and PERCENTILE_CONT in MySQL 5.6"
  - "Used DB dialect switching (sqlite vs mysql) to generate time-bucketed groups for history trend plotting dynamically"
  - "Wrapped each health check ping in a separate try/except block to ensure a single downstream service failure doesn't abort the background task or affect other health status updates"

patterns-established:
  - "Background engine runs via a FastAPI lifespan startup hook"
  - "Database session lifecycle isolated per check using AsyncSessionFactory to prevent session sharing or cross-request pollution"

requirements-completed: [OBS-01, OBS-02, OBS-05, OBS-06, OBS-09]

# Metrics
duration: 10min
completed: 2026-06-14
---

# Phase 17 Plan 01: Backend Observability Domain Foundation Summary

**Uptime, status, and latency metric collector and aggregator for 5 core system components, fully integrated into FastAPI lifespan and verified with SQLite/MySQL compatible unit tests.**

## Accomplishments
- **ORM Model and Table:** Added `ServiceHealthSample` schema and migration (`h001`) with composite index `(service_name, checked_at)` to support fast range aggregations.
- **Service layer:** Implemented metrics logic calculating percentiles in Python for MySQL 5.6 compatibility, and time-bucketed hourly/daily trend buckets.
- **Polling Loop:** Implemented non-blocking checks for FastAPI (self-ping), MySQL (SELECT 1), BFF (internal HTTP URL), Keycloak (well-known endpoint), and WebSocket Gateway (connections count).
- **Wiring & Robustness:** Configured FastAPI lifespan hook to manage background thread task startup/cancellation, and isolated check executions so that a single failure doesn't crash the loop.
- **Verification:** Unit tests written and verified passing (5/5) covering classification thresholds, DB model persistence, background checker resilience, pruning, and metrics time-series history.
