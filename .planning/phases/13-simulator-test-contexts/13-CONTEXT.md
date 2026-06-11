# Phase 13: Simulator Test Contexts — Context

**Gathered:** 2026-06-11
**Status:** Spec captured at phase creation (no discuss session yet)

<domain>
## Phase Boundary

Mejoras al "Live Simulator" del editor de reglas (Rule Builder):

1. **Test Context persistente**: el JSON de "Test Context" editado por el usuario se puede **guardar en base de datos asociado al flag/regla**, convirtiéndose en un ejemplo de prueba reutilizable para futuros ajustes de esa regla. Al reabrir el Rule Builder, el contexto guardado se recupera automáticamente.

2. **Toggle "contexto real del usuario logeado"**: un toggle en el simulador reemplaza el ejemplo por los **valores reales de las propiedades del usuario logeado** (sub/email, roles, tenant_id, etc.), para validar que las reglas funcionan con el caso real, no solo con ejemplos sintéticos.

</domain>

<specifics>
## User specification (verbatim intent, 2026-06-11)

"en el 'Live Simulator' el ejemplo del 'Test Context' al editarlo se pueda guardar en base de datos para esa regla (se convierte en un ejemplo de prueba para ajustes que sobre la regla se requiera realizar) y se añada un Toggle que permita visualizar para el usuario logeado los valores específicos reales de las propiedades del usuario que se usaría como un 'Test Context' (a fin de validar que las reglas funcionan no solo con un ejemplo sino con el caso real del usuario logeado)"

</specifics>

<code_context>
## Existing Code Insights (verified at phase creation)

### Reusable Assets
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` — el Live Simulator actual (Test Context editable como JSON en textarea, badge PASSING/FAILING, Matched Rule). Usado en `RuleBuilderView.vue` (columna derecha).
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` — evaluador TS local (paridad con backend OPERATORS).
- `portal/src/stores/auth.ts` — fuente de los datos reales del usuario logeado (user.email/sub, roles); `VITE_BO_TENANT_ID` aporta tenant_id (patrón de Fase 12 en `portal/src/main.ts:30`).
- Patrón de migración Alembic: head actual `d001` (add_tenant_owner); la nueva columna/tabla sería `d002`.

### Established Patterns
- Los flags viven en `feature_flags` (MySQL); `rules` y `tags` son columnas TEXT con JSON serializado — un `test_context` TEXT JSON nullable seguiría el mismo patrón.
- Guardado del Rule Builder: `PATCH /flags/{id}` vía BFF proxy con payload parcial (rules, rollout, complex) — el test_context puede viajar en el mismo PATCH.
- El Shell expone composables a remotes vía Module Federation (`shell/useBoFlags` en Fase 12) — mismo mecanismo para exponer un `shell/useUserContext` si se necesita pasar las propiedades reales del usuario al remote.

### Integration Points
- `RuleBuilderView.vue` — carga/guardado del flag; pasaría test_context guardado al RuleSimulator y lo incluiría en el PATCH.
- `backend/app/domains/feature_flags/` — modelo, schema (FlagUpdate/FlagResponse) y service para el nuevo campo.
- `SegmentForm.vue` reutiliza `RuleCard` (mode=segment) pero hoy NO monta RuleSimulator — decidir en planning si el alcance cubre también segmentos (el goal del roadmap lo sugiere si es barato).

</code_context>

<decisions>
## Open questions for planning

1. **Dónde persiste**: ¿columna `test_context` TEXT en `feature_flags` (un contexto por flag, simple) o tabla `flag_test_contexts` (múltiples ejemplos nombrados por flag)? La spec habla de "el ejemplo" en singular — columna única parece suficiente para esta fase.
2. **Toggle de contexto real**: al activarlo, ¿el Test Context textarea se vuelve solo-lectura mostrando los valores reales, o se copian al editor como punto de partida editable? La spec dice "visualizar… los valores específicos reales" → solo-lectura con opción de volver al ejemplo guardado parece lo fiel.
3. **Qué propiedades reales del usuario**: sub/email, roles, tenant_id están disponibles hoy. ¿Incluir claims adicionales del token Keycloak (name, preferred_username)? Decidir set exacto en planning.
4. **Alcance segmentos**: ¿montar RuleSimulator también en SegmentForm con persistencia análoga (columna en `segments`), o flags-only en esta fase?

</decisions>

<deferred>
## Deferred Ideas

- Múltiples test contexts nombrados por flag (librería de casos de prueba) — si se elige columna única, esto queda para una fase futura.

</deferred>

---

*Phase: 13-simulator-test-contexts*
*Context gathered: 2026-06-11*
