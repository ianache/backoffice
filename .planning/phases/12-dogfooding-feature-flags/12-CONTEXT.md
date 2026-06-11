# Phase 12: Dogfooding Feature Flags — Context

## User specification (verbatim intent, 2026-06-11)

La plataforma BackOffice debe consumir sus propios feature flags para controlar su UI ("dogfooding"). El producto ya existe con id `backoffice`.

### Flags y comportamiento esperado

| Flag | Controla | Comportamiento |
|------|----------|----------------|
| `bo.feature` | Opción de menú "Feature Flags" en el Shell (`MainLayout.vue`) | ON → visible; OFF → oculta |
| `bo.feature.create` | Botón "Create Flag" en la página `/flags` (FlagsView) **y** botón de acción "Clone" en la tabla de flags (FlagTable) | ON → visibles; OFF → ocultos |
| `bo.feature.update` | Ícono lápiz "Edit" en la tabla de flags (FlagTable) | ON → visible; OFF → oculto |

## Technical context (verified against codebase at phase creation)

- Los flags se evalúan para el producto `backoffice`. Los flags ya existen en la plataforma (creados por el usuario vía UI).
- Evaluación disponible vía:
  - `@backoffice/sdk-js` (sdk/sdk-js, Fase 11): `initialize()` (bootstrap snapshot del BFF), `evaluate()` síncrono cache-only, WebSocket live-sync (`flag_updated` invalida cache), `TelemetryBatcher`.
  - BFF: `GET /api/v1/sdk/bootstrap` (proxy en `/sdk`), auth por `sdk_key` (header o query param).
- Consumidores afectados:
  - `portal/src/components/layout/MainLayout.vue` — menú "Feature Flags" (también "Segments" depende del mismo remote; el alcance pedido solo cubre el menú "Feature Flags").
  - `microuis/mui-feature-flags/src/views/FlagsView.vue` — botón "Create Flag".
  - `microuis/mui-feature-flags/src/components/flags/FlagTable.vue` — acciones "Clone" y "Edit" (lápiz).

## Resolved Decisions (2026-06-11)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Q1: SDK key provisioning | `VITE_BO_SDK_KEY` env var | Simple, consistent with SDK contract |
| Q2: Fail-safe default | Fail-open (`true`) | Admin UI must never be blocked by SDK failure |
| Q3: Evaluation context | Real user context (`sub`, `roles`) | Enables per-role flag rules |
| Q4: Reactivity model | Live WS (`flag_updated` → re-eval) | Demonstrates full SDK capability |
