# Phase 14: Flag Scope Targeting + List-Valued Rules — Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Dos capacidades sobre feature flags:

1. **Scope targeting**: al crear/editar un feature flag, cuando el `scope` seleccionado sea `product`, `tenant` o `company`, el formulario muestra un **combobox** para seleccionar la entidad específica a la que aplica el flag. La selección se **almacena en backend** (las columnas `tenant_id`/`product_id`/`company_id` ya existen). El **SDK** (bootstrap + evaluación local y remota) activa o desactiva el flag según el scope+target definidos. Incluye un **catálogo Companies con CRUD mínimo** (la entidad no existe hoy).

2. **List-valued rule values**: nuevo operador **`anyOf`** en el Rule Builder — el `value` de la Rule se escribe como lista separada por coma (ej. `PlatformAdmin, TenantOwner`) y hace match si **cualquiera** de los valores aplica contra la propiedad del contexto (lista o escalar). Paridad en los 4 evaluadores: backend OPERATORS, sdk-js, sdk-python, useRuleSimulator.ts.

</domain>

<decisions>
## Implementation Decisions

### Catálogo Companies (nueva entidad)
- **Nuevo catálogo Companies con CRUD mínimo** — no texto libre ni derivación de tenants.
- Modelo: **id slug** (alfanumérico definido por usuario, es lo que se guarda en `flags.company_id`) + **name** + **status** (active/inactive) + **tenant_id** — mismo patrón que Products (Fase 7).
- **Una company pertenece a un tenant**: TenantAdmin/TenantOwner ven y administran solo las companies de su tenant; PlatformAdmin ve todas.
- Permisos: **PlatformAdmin + TenantAdmin/TenantOwner** pueden administrar companies (con el aislamiento por tenant anterior).
- UI de administración: **en mui-tenants, ruta `/companies`** — replica el patrón Products (vista + tabla + drawer), nav en el Shell.

### Comboboxes de target en FlagForm
- Fuentes: **tenants y products desde los endpoints existentes** (`GET /tenants/`, `GET /products/` vía BFF) — mui-feature-flags crea sus propios services HTTP, sin compartir stores entre remotes. Companies desde el nuevo endpoint del catálogo.
- Etiquetas de opción: **nombre + id visible** (ej. "Acme Corp (acme)", "Tenant Alfa (#12)") — el id es lo que se persiste y compara el SDK.
- Products: **solo activos** (status=active), consistente con TenantForm de Fase 10. Companies: solo activas.
- **Target obligatorio** cuando el scope es product/tenant/company — el formulario valida y no permite guardar sin selección.
- **Al cambiar el scope se limpia el target anterior** — `product_id`/`tenant_id`/`company_id` mutuamente excluyentes en el payload (los otros dos viajan null).

### Enforcement en SDK y retrocompatibilidad
- **Doble capa**: `GET /sdk/bootstrap` filtra por target coincidente (tenant/product del cliente SDK) **y** los 4 evaluadores comparan también (en particular `company_id`, que es por-contexto/usuario, no por-cliente SDK — solo puede verificarse en evaluación).
- **Flags legacy** (scope no-global sin target): **comportamiento actual sin cambio** — no breaking change, no fail-closed; al editarlos en el form, se exigirá seleccionar target.

### Operador anyOf (match de listas)
- **Nuevo operador `anyOf`** — no se modifica la semántica de `in` ni `contains` existentes (cero regresión).
- Semántica: contexto **lista** → match si la intersección con el value no es vacía; contexto **escalar** → match si pertenece a la lista del value. Cubre ambos casos.
- Normalización: **trim de espacios** alrededor de cada valor al parsear; comparación **case-sensitive** (roles Keycloak son case-sensitive).
- Persistencia: el value se guarda como **array JSON real** (`["PlatformAdmin","TenantOwner"]`) — el UI parsea las comas al guardar; los evaluadores reciben lista tipada sin re-parsear.
- **Aditivo**: las reglas existentes con `in` quedan intactas; no hay migración de datos de reglas.
- Paridad obligatoria en 4 evaluadores: `backend/app/domains/feature_flags/service.py` (OPERATORS), `sdk/sdk-js/src/evaluator.ts`, `sdk/sdk-python` evaluator.py, `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts`.

### UX del value como lista
- Edición: **input de texto con comas** ("PlatformAdmin, TenantOwner") en el mismo input actual de RuleCard; se parsea a array al guardar. Sin chips de entrada.
- Visualización: en la regla guardada (RuleCard) y en "Matched Rule" del simulador, el array se muestra como **mini-chips de solo lectura** (un chip por valor).
- `anyOf` **siempre disponible** en el dropdown de operadores — sin detección de tipo del attribute.

### Claude's Discretion
- Nombre/copy exacto del operador en el dropdown (ej. "any of (comma-separated)").
- Diseño visual exacto de los mini-chips (puede inspirarse en ChipTagInput/chips existentes).
- Estructura exacta del router/service/schemas del catálogo Companies (seguir patrón Products).
- Migración Alembic para la tabla `companies` (head actual: `d002`; la nueva sería `d003`).
- Si el value con un solo elemento se guarda como array de 1 (recomendado: sí, shape uniforme).
- Manejo de errores y estados vacíos de los comboboxes (catálogo vacío → mensaje y link a /companies o /products).

</decisions>

<specifics>
## User specification (verbatim intent)

(2026-06-10, scope targeting): "cuando se seleccione en la creacion o edicion de un feature flag el scope de producto, un nuevo combobox se agrege para seleccionar el producto al que aplica el feature flag, y similar para el caso cuando el scope sea tenant o company se debe poder seleccionar el tenant o company segun el caso. La información debe quedar almacenada en backend. Se debe asegurar que el SDK incluya la activacion o no de la feature flag segun el scope definido."

(2026-06-11, list-valued rules): "cuando al editar las rules de un feature flag el contexto donde residen las propiedades no sea una propiedad simple (texto o numero) sino una lista, como por ejemplo, lista de roles, se pueda indicar en la Rule el value como una lista de valores (esto seria de gran utilidad si por ejemplo se selecciona como attribute de la Rule el campo 'roles' del context y se puede proporcionar en value separado por coma todos los roles a la que aplica el feature flag y evitar crear una regla por cada valor especifico de la lista)."

</specifics>

<code_context>
## Existing Code Insights (verificado en scouting 2026-06-11)

### Reusable Assets
- `backend/app/domains/feature_flags/models.py:14-17` — `scope` ya admite `global|tenant|product|company` y las columnas `tenant_id`, `product_id`, `company_id` (String(100) nullable) **ya existen**; no se necesita migración para el target de flags. Solo falta UI + enforcement consistente.
- `backend/app/domains/feature_flags/service.py:58-70` — `evaluate_flag()` ya prioriza company(4)>product(3)>tenant(2)>global(1) y compara `flag.company_id == context.get('company_id')` — base del enforcement en evaluación.
- `backend/app/domains/sdk/service.py` `bootstrap_flags()` — post-filtra por scope/tenant/product; extender para respetar target estricto (y decidir el paso de company al snapshot).
- Patrón Products (Fase 7): models/schemas/service/router + ProductTable/ProductDrawer/ProductsView en mui-tenants — molde directo para Companies.
- `microuis/mui-feature-flags/src/components/flags/FlagForm.vue:19-131` — select de scope existente; aquí se insertan los comboboxes condicionales.
- OPERATORS canónico en `service.py:23-27`: `in` = `actual in expected` (escalar∈lista), `contains` = substring — confirma que ninguno hace lista-vs-lista; `anyOf` es nuevo.
- `ChipTagInput.vue` (mui-feature-flags, Fase 11) — referencia visual para los mini-chips de solo lectura.
- Head Alembic actual: `d002` (test_context) → la tabla `companies` sería `d003`.

### Established Patterns
- Slug inmutable definido por usuario como PK (Product.id, VARCHAR 50) — replicar en Company.id.
- IntegrityError capturado en router (409), service puro — patrón Fase 7 para el CRUD Companies.
- BFF proxy por dominio (`bff/src/routes/products.ts` con pathRewrite `/products${path}`) — nuevo route análogo para `/companies`.
- Paridad de operadores entre 4 evaluadores ya ejercitada en Fase 11 (greaterThan/lessThan) — mismo checklist para `anyOf`.

### Integration Points
- `FlagForm.vue` + `FlagDrawer.vue` — comboboxes condicionales por scope, validación target obligatorio, limpieza al cambiar scope.
- `backend/app/domains/feature_flags/schemas.py` — validación server-side: scope no-global requiere su id correspondiente (en create/update nuevos; legacy intocado).
- `bootstrap_flags()` + evaluadores sdk-js/sdk-python + `useRuleSimulator.ts` — enforcement doble capa y operador anyOf.
- Shell `MainLayout.vue` + `mui-tenants/src/routes.ts` — nav y ruta `/companies`.

</code_context>

<deferred>
## Deferred Ideas

- Companies con campos extendidos (description, labels) y paridad completa con Products — si el CRUD mínimo queda corto.
- Migración/deprecación del operador `in` hacia `anyOf` — decidido aditivo en esta fase; unificación queda para futuro.

</deferred>

---

*Phase: 14-flag-scope-targeting-list-valued-rules*
*Context gathered: 2026-06-11*
