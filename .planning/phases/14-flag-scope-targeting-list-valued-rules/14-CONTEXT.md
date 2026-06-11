# Phase 14: Flag Scope Targeting + List-Valued Rules — Context

**Gathered:** 2026-06-11
**Status:** Spec captured at phase creation (no discuss session yet)

<domain>
## Phase Boundary

Dos capacidades sobre feature flags:

1. **Scope targeting**: al crear/editar un feature flag, cuando el `scope` seleccionado sea `product`, `tenant` o `company`, el formulario muestra un **combobox** para seleccionar el producto/tenant/company específico al que aplica el flag. La selección se **almacena en backend**. El **SDK** (bootstrap + evaluación local y remota) activa o desactiva el flag según el scope+target definidos.

2. **List-valued rule values**: en el editor de Rules del Rule Builder, cuando el `attribute` del contexto referencia una propiedad que es una **lista** (ej. `roles`), el `value` de la Rule puede indicarse como **lista de valores separados por coma** (ej. `PlatformAdmin, TenantOwner`), haciendo match si **cualquiera** de los valores aplica — evita crear una regla por cada valor específico de la lista.

</domain>

<specifics>
## User specification (verbatim intent)

(2026-06-10, scope targeting): "cuando se seleccione en la creacion o edicion de un feature flag el scope de producto, un nuevo combobox se agrege para seleccionar el producto al que aplica el feature flag, y similar para el caso cuando el scope sea tenant o company se debe poder seleccionar el tenant o company segun el caso. La información debe quedar almacenada en backend. Se debe asegurar que el SDK incluya la activacion o no de la feature flag segun el scope definido."

(2026-06-11, list-valued rules): "cuando al editar las rules de un feature flag el contexto donde residen las propiedades no sea una propiedad simple (texto o numero) sino una lista, como por ejemplo, lista de roles, se pueda indicar en la Rule el value como una lista de valores (esto seria de gran utilidad si por ejemplo se selecciona como attribute de la Rule el campo 'roles' del context y se puede proporcionar en value separado por coma todos los roles a la que aplica el feature flag y evitar crear una regla por cada valor especifico de la lista)."

</specifics>

<code_context>
## Existing Code Insights (known at phase creation, verify at research time)

### Scope targeting
- `feature_flags` ya tiene columnas `scope`, `tenant_id`, `product_id` — el modelo soporta parcialmente targets; falta `company` y la UI de selección. Verificar en research qué existe para `company` (¿columna nueva?).
- Fuentes para los comboboxes: productos vía `GET /products/` (catálogo Fase 7, store en mui-tenants — mui-feature-flags necesitaría su propio service o uno compartido); tenants vía `GET /tenants/`; **company**: verificar si existe entidad/endpoint — puede requerir definición (¿claim del token? ¿catálogo nuevo?).
- Enforcement actual del SDK: `bootstrap_flags()` en `backend/app/domains/sdk/service.py` ya post-filtra por scope/tenant/product — extender para el target persistido y para `company`. `evaluate_flag()` backend + evaluadores sdk-js/sdk-python evalúan desde el snapshot.
- `FlagForm.vue` (mui-feature-flags) es donde se selecciona el scope hoy.

### List-valued rule values
- OPERATORS canónico en `backend/app/domains/feature_flags/service.py` (equals, notEquals, contains, in, greaterThan, lessThan, etc. — verificar set exacto y semántica actual de `in`/`contains` con listas en ambos lados).
- Paridad requerida en 4 evaluadores: backend OPERATORS, `sdk/sdk-js/src/evaluator.ts`, `sdk/sdk-python` evaluator.py, `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts`.
- UI: `RuleCard.vue` edita attribute/operator/value — el value como string separado por coma con parsing/chips es decisión de UX a discutir.
- Caso de uso concreto: attribute `roles` (lista en el contexto, ver `useUserContext` Fase 13) + value `PlatformAdmin, TenantOwner` → match si intersección no vacía (match-any).

</code_context>

<decisions>
## Open questions for discuss/planning

1. **Company**: ¿existe la entidad company hoy (BD/endpoint/claim)? Si no, ¿de dónde sale el catálogo del combobox y qué se persiste?
2. **Modelo de target**: ¿reutilizar `tenant_id`/`product_id` existentes + nueva columna `company_id`, o una columna genérica `scope_target`? ¿Migración d003?
3. **Semántica del match de listas**: ¿nuevo operador (ej. `intersects`/`anyOf`) o extender `in`/`contains` para lista-vs-lista? Impacta paridad en 4 evaluadores.
4. **UX del value como lista**: ¿input texto con comas tal cual, o chips (patrón ChipTagInput existente)? ¿Trim de espacios, case-sensitivity?
5. **Retrocompatibilidad**: flags existentes con scope no-global sin target — ¿qué hace el SDK (fail-open/closed)?

</decisions>

<deferred>
## Deferred Ideas

- Ninguna por ahora.

</deferred>

---

*Phase: 14-flag-scope-targeting-list-valued-rules*
*Context gathered: 2026-06-11*
