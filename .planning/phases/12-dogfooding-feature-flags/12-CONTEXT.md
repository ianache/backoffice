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

## Open questions for planning

1. ¿Cómo obtiene el portal su `sdk_key`? Hoy las SDK keys son per-tenant. ¿Key dedicada del tenant "plataforma" en env (`VITE_BO_SDK_KEY`), o evaluación vía BFF con la sesión del usuario (sin sdk_key)?
2. Fail-safe default: si el flag no existe / bootstrap falla → recomendado fail-open (mostrar UI) para no bloquear administración, pero decidir explícitamente.
3. ¿El gating es por tenant del usuario logueado o global de plataforma? (user context para evaluate(): sub/roles del usuario actual).
4. ¿Reactividad en vivo (WS flag_updated re-renderiza el menú) o snapshot por sesión?
