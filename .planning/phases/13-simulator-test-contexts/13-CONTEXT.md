# Phase 13: Simulator Test Contexts — Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Mejoras al "Live Simulator" del editor de reglas (Rule Builder de feature flags y editor de segmentos rule-based):

1. **Test Context persistente**: el JSON de "Test Context" editado por el usuario se puede **guardar en base de datos asociado al flag/segmento**, convirtiéndose en un ejemplo de prueba reutilizable. Al reabrir el editor, el contexto guardado se recupera automáticamente.

2. **Toggle "contexto real del usuario logeado"**: un toggle en el simulador reemplaza el ejemplo por los **valores reales de las propiedades del usuario logeado** (sub/email, roles, tenant_id, product_id), para validar que las reglas funcionan con el caso real, no solo con ejemplos sintéticos.

Aplica tanto a `RuleBuilderView.vue` (flags) como a `SegmentForm.vue` (segmentos `type='rule_based'`) — `RuleSimulator.vue` es compartido entre ambos vía `mode='flag'|'segment'`.

</domain>

<decisions>
## Implementation Decisions

### Persistencia del Test Context
- Columna única `test_context` (TEXT, JSON, nullable) — un ejemplo por flag, no una tabla de múltiples ejemplos nombrados.
- Misma columna agregada a **ambas** tablas: `feature_flags` y `segments` (migración `d002`, mismo patrón 3-step si aplica por MySQL 5.6).
- Guardado mediante **botón explícito "Save Test Context"**, separado del guardado general del flag/segmento (no viaja automáticamente en el PATCH de rules/rollout).
- **Validación de JSON obligatoria**: si el contenido del textarea no es JSON válido, el botón "Save Test Context" se deshabilita / muestra error — nunca se persiste JSON inválido.
- Si el flag/segmento nunca tuvo un Test Context guardado, se muestra el **ejemplo genérico actual** (el placeholder/sintético que ya existe hoy en `RuleSimulator.vue`) como punto de partida.

### Toggle "usar mi contexto real"
- Al activarse, el textarea de Test Context pasa a **solo-lectura** y muestra los valores reales del usuario logeado (no es una copia editable).
- Al desactivarse, el textarea vuelve al **Test Context guardado** (o al ejemplo genérico si nunca se guardó nada) — preserva cualquier edición previa no guardada.
- Estado inicial: **apagado por defecto** cada vez que se abre el editor — no se persiste preferencia de toggle (ni localStorage ni BD).
- Mientras está activo, el badge PASSING/FAILING y "Matched Rule" se **recalculan en vivo** usando el motor existente (`useRuleSimulator.ts`/`evaluateRule()`), simplemente con el contexto real como input — sin lógica de evaluación nueva.

### Propiedades reales del usuario a mostrar
- Conjunto: **sub/email, roles, tenant_id, product_id**.
  - sub/email, roles, tenant_id: ya disponibles en `portal/src/stores/auth.ts` + `VITE_BO_TENANT_ID` (patrón Fase 12, `portal/src/main.ts:30`).
  - product_id: hardcodeado a `'backoffice'` (la app actual, dogfooding Fase 12) — permite validar reglas con `scope: 'product'`.
- Las claves del JSON de contexto real **coinciden con los nombres de atributo usados en las reglas** (mapeo, ej. `sub`→`id`/`email`, `roles`→`role`, `tenant_id`→`tenant_id`, `product_id`→`product_id`), no el shape crudo del JWT/authStore.
- Origen de los datos: **composable expuesto por el Shell vía Module Federation** (mismo mecanismo que `shell/useBoFlags` de la Fase 12) — ej. `shell/useUserContext` que retorna `{ sub, email, roles, tenant_id, product_id }`. `mui-feature-flags` lo consume sin duplicar lógica de auth.

### Alcance: segmentos rule-based
- `segments` recibe la misma columna `test_context` (mismo patrón de migración que `feature_flags`).
- `RuleSimulator.vue` con `mode='segment'` obtiene el **mismo toggle y comportamiento de contexto real**, sin código específico para segmentos (componente compartido).
- En `SegmentForm.vue`, el simulador (y por tanto el Test Context + toggle) se monta **solo cuando `type === 'rule_based'`** — segmentos `manual` no tienen condiciones que evaluar, igual que `RuleCard mode='segment'` ya hace hoy.

### Claude's Discretion
- Nombre exacto del composable expuesto por el Shell (`shell/useUserContext` o similar) y su registro en `vite.config.ts`/`env.d.ts`.
- Diseño visual exacto del toggle (posición, label, icono) dentro de `RuleSimulator.vue`.
- Endpoint/payload exacto del PATCH para `test_context` (puede ser el mismo `PATCH /flags/{id}` y `PATCH /segments/{id}` existentes, con `test_context` como campo opcional).
- Manejo de errores de red al guardar el Test Context (toast, inline error, etc.).

</decisions>

<specifics>
## User specification (verbatim intent, 2026-06-11)

"en el 'Live Simulator' el ejemplo del 'Test Context' al editarlo se pueda guardar en base de datos para esa regla (se convierte en un ejemplo de prueba para ajustes que sobre la regla se requiera realizar) y se añada un Toggle que permita visualizar para el usuario logeado los valores específicos reales de las propiedades del usuario que se usaría como un 'Test Context' (a fin de validar que las reglas funcionan no solo con un ejemplo sino con el caso real del usuario logeado)"

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` — el Live Simulator actual (Test Context editable como JSON en textarea, badge PASSING/FAILING, Matched Rule). Usado en `RuleBuilderView.vue` (columna derecha) y compartido vía `mode='flag'|'segment'`.
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` — evaluador TS local con `evaluateRule()` exportado (paridad con backend OPERATORS); reutilizable sin cambios para evaluar contra el contexto real.
- `portal/src/stores/auth.ts` — fuente de sub/email/roles del usuario logeado.
- `portal/src/main.ts:30` — patrón `VITE_BO_TENANT_ID` para tenant_id; `product_id='backoffice'` por dogfooding (Fase 12).
- `portal/src/composables/useBoFlags.ts` + exposición en `portal/vite.config.ts` (Fase 12) — patrón a replicar para exponer `shell/useUserContext`.
- Patrón de migración Alembic: head actual `d001` (add_tenant_owner); la nueva sería `d002`.

### Established Patterns
- `feature_flags.rules` y `.tags` son columnas TEXT con JSON serializado — `test_context` TEXT JSON nullable sigue el mismo patrón, en `feature_flags` y `segments`.
- Guardado del Rule Builder: `PATCH /flags/{id}` / `PATCH /segments/{id}` vía BFF proxy con payload parcial.
- El Shell expone composables a remotes vía Module Federation (`shell/useBoFlags`, Fase 12) — mismo mecanismo para `shell/useUserContext`.

### Integration Points
- `RuleBuilderView.vue` — carga/guardado del flag; pasa `test_context` guardado al `RuleSimulator` y lo persiste vía botón dedicado.
- `SegmentForm.vue` — monta `RuleSimulator mode='segment'` solo para `type='rule_based'`, con la misma persistencia/toggle.
- `backend/app/domains/feature_flags/` — modelo, schema (`FlagUpdate`/`FlagResponse`, `SegmentUpdate`/`SegmentResponse`) y service para el nuevo campo `test_context` en ambas entidades.
- `portal/vite.config.ts` / `env.d.ts` — nueva exposición federada `shell/useUserContext`.

</code_context>

<deferred>
## Deferred Ideas

- Múltiples test contexts nombrados por flag/segmento (librería de casos de prueba) — al elegir columna única, queda para una fase futura.
- **Nueva fase (Phase 14 candidata)**: al crear/editar un feature flag, si el `scope` es `product`, `tenant` o `company`, mostrar un combobox para seleccionar el producto/tenant/company específico al que aplica; almacenar esa selección en backend; el SDK debe activar/desactivar el flag según ese scope+selección al evaluar. Solicitado por el usuario durante esta sesión de discusión, pero es una capacidad distinta (targeting de scope) no relacionada con el Live Simulator — se propone como fase independiente posterior a la 13.

</deferred>

---

*Phase: 13-simulator-test-contexts*
*Context gathered: 2026-06-11*
