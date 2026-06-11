# Phase 13: Simulator Test Contexts - Research

**Researched:** 2026-06-11
**Domain:** Full-stack feature (Alembic migration, FastAPI schema/service/router, Vue 3 composables, Module Federation)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Persistencia del Test Context
- Columna única `test_context` (TEXT, JSON, nullable) — un ejemplo por flag, no una tabla de múltiples ejemplos nombrados.
- Misma columna agregada a **ambas** tablas: `feature_flags` y `segments` (migración `d002`, mismo patrón 3-step si aplica por MySQL 5.6).
- Guardado mediante **botón explícito "Save Test Context"**, separado del guardado general del flag/segmento (no viaja automáticamente en el PATCH de rules/rollout).
- **Validación de JSON obligatoria**: si el contenido del textarea no es JSON válido, el botón "Save Test Context" se deshabilita / muestra error — nunca se persiste JSON inválido.
- Si el flag/segmento nunca tuvo un Test Context guardado, se muestra el **ejemplo genérico actual** (el placeholder/sintético que ya existe hoy en `RuleSimulator.vue`) como punto de partida.

#### Toggle "usar mi contexto real"
- Al activarse, el textarea de Test Context pasa a **solo-lectura** y muestra los valores reales del usuario logeado (no es una copia editable).
- Al desactivarse, el textarea vuelve al **Test Context guardado** (o al ejemplo genérico si nunca se guardó nada) — preserva cualquier edición previa no guardada.
- Estado inicial: **apagado por defecto** cada vez que se abre el editor — no se persiste preferencia de toggle (ni localStorage ni BD).
- Mientras está activo, el badge PASSING/FAILING y "Matched Rule" se **recalculan en vivo** usando el motor existente (`useRuleSimulator.ts`/`evaluateRule()`), simplemente con el contexto real como input — sin lógica de evaluación nueva.

#### Propiedades reales del usuario a mostrar
- Conjunto: **sub/email, roles, tenant_id, product_id**.
  - sub/email, roles, tenant_id: ya disponibles en `portal/src/stores/auth.ts` + `VITE_BO_TENANT_ID` (patrón Fase 12, `portal/src/main.ts:30`).
  - product_id: hardcodeado a `'backoffice'` (la app actual, dogfooding Fase 12) — permite validar reglas con `scope: 'product'`.
- Las claves del JSON de contexto real **coinciden con los nombres de atributo usados en las reglas** (mapeo, ej. `sub`→`id`/`email`, `roles`→`role`, `tenant_id`→`tenant_id`, `product_id`→`product_id`), no el shape crudo del JWT/authStore.
- Origen de los datos: **composable expuesto por el Shell vía Module Federation** (mismo mecanismo que `shell/useBoFlags` de la Fase 12) — ej. `shell/useUserContext` que retorna `{ sub, email, roles, tenant_id, product_id }`. `mui-feature-flags` lo consume sin duplicar lógica de auth.

#### Alcance: segmentos rule-based
- `segments` recibe la misma columna `test_context` (mismo patrón de migración que `feature_flags`).
- `RuleSimulator.vue` con `mode='segment'` obtiene el **mismo toggle y comportamiento de contexto real**, sin código específico para segmentos (componente compartido).
- En `SegmentForm.vue`, el simulador (y por tanto el Test Context + toggle) se monta **solo cuando `type === 'rule_based'`** — segmentos `manual` no tienen condiciones que evaluar, igual que `RuleCard mode='segment'` ya hace hoy.

### Claude's Discretion
- Nombre exacto del composable expuesto por el Shell (`shell/useUserContext` o similar) y su registro en `vite.config.ts`/`env.d.ts`.
- Diseño visual exacto del toggle (posición, label, icono) dentro de `RuleSimulator.vue`.
- Endpoint/payload exacto del PATCH para `test_context` (puede ser el mismo `PATCH /flags/{id}` y `PATCH /segments/{id}` existentes, con `test_context` como campo opcional).
- Manejo de errores de red al guardar el Test Context (toast, inline error, etc.).

### Deferred Ideas (OUT OF SCOPE)
- Múltiples test contexts nombrados por flag/segmento (librería de casos de prueba) — al elegir columna única, queda para una fase futura.
- **Nueva fase (Phase 14 candidata)**: combobox para seleccionar producto/tenant/company específico al crear/editar flags con scope `product`/`tenant`/`company` (targeting de scope) — fase independiente posterior a la 13, no relacionada con el Live Simulator.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-------------------|
| SIM-01 | Persistencia de test context por flag/segmento (columna `test_context` TEXT JSON nullable en `feature_flags` y `segments`, guardado vía botón explícito) | Migration pattern (d002), `FlagUpdate`/`SegmentCreate` schema changes, `update_flag`/`update_segment` service changes documented below |
| SIM-02 | Recuperación automática del test context guardado al reabrir el editor (fallback al ejemplo genérico si `null`) | `FlagResponse`/`SegmentResponse` field addition, `RuleSimulator.vue` prop wiring documented below |
| SIM-03 | Toggle "usar mi contexto real" — muestra valores reales del usuario logeado (sub/email, roles, tenant_id, product_id) en modo solo-lectura, re-evalúa en vivo | `shell/useUserContext` composable pattern (mirrors `shell/useBoFlags`), `useRuleSimulator.ts` reuse documented below |
</phase_requirements>

## Summary

This phase is a small, well-bounded full-stack addition that follows three already-established patterns in this codebase almost exactly: (1) the `d001` single-nullable-column Alembic migration pattern for adding `test_context TEXT` to both `feature_flags` and `segments`; (2) the existing TEXT-as-JSON serialization pattern used for `rules`/`tags`/`conditions`/`members`, applied identically to `test_context`; and (3) the Phase 12 `shell/boFlags` Module Federation composable pattern, replicated as `shell/useUserContext` to expose `{ sub, email, roles, tenant_id, product_id }` from the Shell's `auth` store to `mui-feature-flags`.

The trickiest non-obvious finding is that `PATCH /flags/segments/{id}` currently uses **`SegmentCreate`** (a full-replacement schema with required `name`), not a partial-update schema — unlike `FlagUpdate` which is already `Optional`-everything for flags. Adding `test_context` to segments therefore requires either (a) extending `SegmentCreate`/`SegmentResponse` and accepting that `update_segment()` continues to require all segment fields on every PATCH (current behavior, "Save Test Context" button would need to send the full segment payload plus `test_context`), or (b) introducing a true partial `SegmentUpdate` schema scoped to this phase. Given the CONTEXT.md's "Claude's Discretion" note that `test_context` can ride the *existing* PATCH endpoints, the simplest non-breaking approach documented below is to add `test_context: Optional[str] = None` to `SegmentCreate`/`SegmentResponse` and have `SegmentForm.vue`'s "Save Test Context" button call `updateSegment()` with the **current full form payload + test_context**, reusing `handleSubmit()`'s payload-building logic. This avoids a new schema while respecting the existing full-replacement contract.

A second key finding: `auth.ts`'s `user` ref currently exposes only `{ name, email }` — `sub` (the JWT `sub` claim) is available on `keycloak.tokenParsed?.sub` (standard `keycloak-js` `KeycloakTokenParsed` type) but is **not yet extracted**. The new `shell/useUserContext` composable (or an extension of `auth.ts`) must read `keycloak.tokenParsed?.sub` directly or add `sub` to the auth store's `_populate()`.

**Primary recommendation:** Follow the `d001` migration pattern (single `op.add_column`, nullable, no 3-step needed because this is a pure additive nullable column, not a data migration); extend `FlagUpdate`/`FlagResponse` and `SegmentCreate`/`SegmentResponse` with `test_context: Optional[str] = None` (raw JSON string, no `model_validator` parsing needed since the frontend already works with JSON strings in `RuleSimulator.vue`'s `contextJson` ref); add `shell/useUserContext` exposed via `portal/vite.config.ts` mirroring `./boFlags`; extend `RuleSimulator.vue` with `props: { testContext?: string | null, mode: 'flag'|'segment' }`, `emit('save-test-context', json)`, and an internal toggle that swaps `contextJson` for the real-user-context computed from `useUserContext()`.

## Standard Stack

### Core
| Component | Version/Pattern | Purpose | Why Standard |
|-----------|------------------|---------|---------------|
| Alembic migration `d002` | Single `op.add_column`, depends on `d001` | Add `test_context TEXT NULL` to `feature_flags` and `segments` | Matches `d001_add_tenant_owner.py` exactly — additive nullable column needs no 3-step expand/backfill/cleanup |
| Pydantic `Optional[str]` field | `test_context: Optional[str] = None` | Raw JSON-as-TEXT field, same as `rules`/`tags`/`conditions`/`members` | No `model_validator` needed — frontend already round-trips JSON as a string (`contextJson` ref in `RuleSimulator.vue`), unlike `rules`/`tags` which are parsed to typed lists |
| `@originjs/vite-plugin-federation` exposes entry | `'./useUserContext': './src/composables/useUserContext.ts'` | Shell-exposed composable for real user context | Mirrors `'./boFlags': './src/composables/useBoFlags.ts'` from Phase 12 exactly |
| `useRuleSimulator.ts` `evaluateRule()` | No changes | Live re-evaluation engine for both synthetic and real context | CONTEXT.md explicitly locks "sin lógica de evaluación nueva" |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `keycloak-js` `KeycloakTokenParsed.sub` | already installed | Source of `sub` claim (not currently surfaced by `auth.ts`) | Read directly via `keycloak.tokenParsed?.sub`, or add `sub` to `auth.ts`'s `_populate()` |
| `vitest` | `^1.6.0` (already in mui-feature-flags) | Unit tests for `useRuleSimulator.ts` real-context mapping and `RuleSimulator.vue` toggle behavior | Existing `useRuleSimulator.test.ts` is the pattern to extend |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `SegmentCreate` extension (full-replacement PATCH) | New `SegmentUpdate` partial schema + new partial `update_segment()` | Cleaner REST semantics but expands scope beyond CONTEXT.md's "use existing PATCH endpoints" discretion note; deferred unless planner decides the full-replacement payload is too fragile for a single-field save |
| Reading `keycloak.tokenParsed?.sub` directly in `useUserContext.ts` | Add `sub` to `auth.ts`'s `user` ref and `_populate()` | Either works; adding to `auth.ts` is more consistent with existing `roles`/`user.email` access pattern and testable via existing `auth.test.ts` mocks |

**Installation:** No new packages required — all building blocks (`@originjs/vite-plugin-federation`, `keycloak-js`, `vitest`, Alembic) are already present.

## Architecture Patterns

### Recommended Project Structure (new/changed files)
```
backend/
├── alembic/versions/d002_add_test_context.py   # NEW — single add_column x2
├── app/domains/feature_flags/
│   ├── models.py     # CHANGED — add test_context column to FeatureFlag and Segment
│   ├── schemas.py     # CHANGED — FlagUpdate/FlagResponse + SegmentCreate/SegmentResponse get test_context
│   └── service.py     # CHANGED — update_flag/update_segment pass through test_context (no JSON re-encode needed)

portal/
├── src/composables/useUserContext.ts   # NEW — mirrors useBoFlags.ts singleton pattern
├── src/stores/auth.ts                   # CHANGED (likely) — expose `sub` from tokenParsed
└── vite.config.ts                       # CHANGED — exposes './useUserContext'

microuis/mui-feature-flags/
├── src/env.d.ts                                  # CHANGED — declare module 'shell/useUserContext'
├── src/services/flags.ts                         # CHANGED — FeatureFlag/Segment/FlagPayload/SegmentPayload gain test_context
├── src/composables/useRuleSimulator.ts           # UNCHANGED (per CONTEXT.md — reused as-is)
├── src/composables/useRuleSimulator.test.ts      # CHANGED — add tests for real-context evaluation if logic added to RuleSimulator.vue
├── src/components/flags/RuleSimulator.vue        # CHANGED — props (testContext, mode), emits (save-test-context), toggle UI, real-context display
├── src/views/RuleBuilderView.vue                 # CHANGED — pass flag.test_context, handle @save-test-context -> PATCH /flags/{id}
├── src/components/flags/SegmentForm.vue          # CHANGED — mount RuleSimulator mode="segment" when type==='rule_based', handle @save-test-context
└── src/views/SegmentsView.vue                    # CHANGED (maybe) — wire updateSegment with test_context if SegmentForm doesn't call API directly
```

### Pattern 1: Additive Nullable Column Migration (d002)
**What:** Single Alembic revision adding `test_context TEXT NULL` to two tables.
**When to use:** Always for purely additive, nullable columns with no data backfill — the 3-step expand/backfill/cleanup pattern (used in `b001`-`b003`/PROD-06) is ONLY required when *migrating data* from one representation to another (e.g., JSON column → relational table) where an irreversible intermediate state could lose data on MySQL 5.6. A new nullable column with no existing data to migrate is safe in one step — `d001_add_tenant_owner.py` already established this precedent for the same scenario (added `tenants.owner` nullable in one revision, depends_on `c002`).
**Example:**
```python
# Source: backend/alembic/versions/d001_add_tenant_owner.py (existing pattern)
"""add_test_context

Revision ID: d002
Revises: d001
Create Date: 2026-06-11
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'd002'
down_revision: Union[str, None] = 'd001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('feature_flags', sa.Column('test_context', sa.Text(), nullable=True))
    op.add_column('segments', sa.Column('test_context', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('segments', 'test_context')
    op.drop_column('feature_flags', 'test_context')
```

### Pattern 2: TEXT-as-raw-JSON-string field (no list/dict parsing)
**What:** Unlike `rules`/`tags`/`conditions`/`members` (which are JSON arrays parsed into typed Python lists via `model_validator`), `test_context` should be stored and returned as a **raw JSON string** (or `None`), because the frontend already manipulates it as a string (`contextJson` ref bound directly to a `<textarea>` via `v-model`).
**When to use:** `FlagUpdate`/`FlagResponse`/`SegmentCreate`/`SegmentResponse` — add `test_context: Optional[str] = None` with NO custom validator. `update_flag()`/`update_segment()` pass it through unchanged (no `json.dumps`/`json.loads`).
**Validation responsibility:** CONTEXT.md locks JSON validation to the **client** ("el botón 'Save Test Context' se deshabilita / muestra error — nunca se persiste JSON inválido"). The backend can optionally double-validate with a Pydantic `field_validator` that does `json.loads(v)` and raises if invalid — recommended as defense-in-depth but not required by CONTEXT.md.
**Example:**
```python
# Source: backend/app/domains/feature_flags/schemas.py (pattern to extend)
class FlagUpdate(BaseModel):
    # ...existing fields...
    test_context: Optional[str] = None   # raw JSON string; null = no saved context

class FlagResponse(BaseModel):
    # ...existing fields...
    test_context: Optional[str] = None   # returned as-is, no parse_text_fields entry needed
```

### Pattern 3: Shell-exposed composable via Module Federation (shell/useUserContext)
**What:** A new singleton composable in `portal/src/composables/useUserContext.ts`, exposed in `portal/vite.config.ts` under `exposes` and declared in `microuis/mui-feature-flags/src/env.d.ts`.
**When to use:** Whenever a remote MUI needs read access to Shell-owned auth/session state without duplicating Keycloak logic — established by `shell/boFlags` in Phase 12.
**Example (vite.config.ts addition):**
```typescript
// Source: portal/vite.config.ts (existing exposes block, Phase 12 pattern)
exposes: {
  './StitchButton': './src/components/ui/StitchButton.vue',
  './StitchTextField': './src/components/ui/StitchTextField.vue',
  './toastStore': './src/stores/toast.ts',
  './api': './src/services/api.ts',
  './boFlags': './src/composables/useBoFlags.ts',
  './useUserContext': './src/composables/useUserContext.ts',   // NEW
},
```
**Example (env.d.ts addition in mui-feature-flags):**
```typescript
// Source: microuis/mui-feature-flags/src/env.d.ts (pattern from shell/boFlags declaration)
declare module 'shell/useUserContext' {
  export function useUserContext(): {
    sub: string
    email: string
    roles: string[]
    tenant_id: string
    product_id: string
  }
}
```
**Example (composable implementation, mapping JWT/auth-store fields to rule-attribute names per CONTEXT.md):**
```typescript
// Source: portal/src/composables/useUserContext.ts (NEW — mirrors useBoFlags.ts singleton style)
import { useAuthStore } from '../stores/auth'
import keycloak from '../plugins/keycloak'

export function useUserContext() {
  const authStore = useAuthStore()
  return {
    sub: keycloak.tokenParsed?.sub ?? '',          // OR authStore.user?.sub if added to auth store
    email: authStore.user?.email ?? '',
    roles: authStore.roles,
    tenant_id: import.meta.env.VITE_BO_TENANT_ID ?? '',
    product_id: 'backoffice',                       // hardcoded per CONTEXT.md (dogfooding Phase 12)
  }
}
```
**Note on key mapping:** CONTEXT.md specifies the JSON keys must match **rule attribute names**, not raw JWT/authStore shapes — e.g. "sub→id/email, roles→role, tenant_id→tenant_id, product_id→product_id". The exact attribute names used in existing rules should be confirmed by checking sample rules created in Phase 12 dogfooding (`bo.feature.create`'s tenant_id rule, referenced in CONTEXT.md). Recommend the planner inspect actual seeded rule `attribute` values (e.g. via `backend/seed_data.py` or DB) to get the precise key names — this is the one open question below.

### Pattern 4: RuleSimulator.vue prop/emit extension
**What:** Add `props.testContext: string | null` (saved value, fed by parent), `props.mode: 'flag' | 'segment'` (already implied by CONTEXT.md but not yet in code — currently `RuleSimulator.vue` has NO `mode` prop), `emit('save-test-context', json: string)`.
**When to use:** `RuleBuilderView.vue` passes `flag.test_context`; `SegmentForm.vue` passes `segment?.test_context` (only when `type === 'rule_based'`).
**Current state (IMPORTANT):** `RuleSimulator.vue` currently has **only one prop** (`rules`) and is mounted **only in `RuleBuilderView.vue`**. It is NOT currently mounted in `SegmentForm.vue` at all — CONTEXT.md's claim that "RuleCard mode='segment' already hides Result column today" is true for `RuleCard.vue` (which DOES have a `mode` prop), but `RuleSimulator.vue` has no `mode` prop yet and is not used by `SegmentForm.vue`. This phase must (a) add `mode` to `RuleSimulator.vue`, and (b) mount it for the first time inside `SegmentForm.vue`.
**Example skeleton:**
```typescript
// RuleSimulator.vue — extended props/emits
const props = defineProps<{
  rules: (RuleSchema & { _id: string })[]
  mode?: 'flag' | 'segment'        // default 'flag'
  testContext?: string | null      // saved value from backend, or null
}>()

const emit = defineEmits<{
  'save-test-context': [json: string]
}>()

// contextJson initializes from props.testContext if present, else existing placeholder
const contextJson = ref(props.testContext ?? '{\n  "country": "PE",\n  "plan": "pro"\n}')

const useRealContext = ref(false)   // off by default, never persisted

const realContextJson = computed(() => {
  const ctx = useUserContext()
  return JSON.stringify({ /* mapped attribute names */ }, null, 2)
})

// when useRealContext toggles on, contextJson display switches to realContextJson (readonly)
// when toggled off, restores previous edited/saved value
```

### Anti-Patterns to Avoid
- **Auto-saving `test_context` in the general flag/segment PATCH:** CONTEXT.md explicitly locks this to a separate "Save Test Context" button — do not bundle it into `saveChanges()` in `RuleBuilderView.vue` or `handleSubmit()` in `SegmentForm.vue`.
- **Persisting the toggle state:** "no se persiste preferencia de toggle (ni localStorage ni BD)" — keep `useRealContext` as a plain local `ref(false)`, reset on component mount.
- **New evaluation logic:** `useRuleSimulator.ts`'s `evaluateRule()`/`useRuleSimulator()` must be reused unchanged — the real-context toggle simply swaps the `contextJson` ref's source value, the existing `watchEffect` handles re-evaluation automatically.
- **Re-introducing JSON parsing for `test_context` on the backend** (treating it like `rules`/`tags` with `model_validator` array parsing) — it's a single JSON string/object, not an array; store/return as raw TEXT.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| Real-user-context evaluation | New evaluator branch in `useRuleSimulator.ts` | Existing `evaluateRule()` + swap `contextJson.value` | CONTEXT.md locks "sin lógica de evaluación nueva"; the existing `watchEffect` already reacts to any change in `contextJson` |
| Cross-MUI auth data access | Duplicate Keycloak/auth logic in `mui-feature-flags` | `shell/useUserContext` (Module Federation) | Established `shell/boFlags` precedent (Phase 12) — singleton in Shell, consumed by remote without re-instantiating Keycloak |
| JSON validation UI | Custom JSON schema validator library | `JSON.parse()` try/catch (same as `useRuleSimulator.ts`'s existing `contextError` handling) | Already proven pattern in `RuleSimulator.vue` — `contextError` ref + `try/catch` around `JSON.parse` |

**Key insight:** Every piece of infrastructure this phase needs (migration pattern, TEXT-as-JSON storage, Module Federation composable exposure, JSON validation, rule evaluation engine) already has a working precedent in this codebase from Phases 7, 11, and 12. The work is almost entirely "replicate pattern X for field/composable Y," not new architecture.

## Common Pitfalls

### Pitfall 1: Segment PATCH is full-replacement, not partial
**What goes wrong:** Calling `PATCH /flags/segments/{id}` with only `{ test_context: "..." }` would, under current `update_segment()` logic (`segment.name = payload.name`, etc., all unconditional assignments from `SegmentCreate`), **wipe out** `name`, `description`, `members`, `conditions`, etc. with their Pydantic defaults (`""`, `[]`) since `SegmentCreate.name` is required but other fields default to `[]`/`None`/`'manual'`.
**Why it happens:** `update_segment(db, segment_id, payload: SegmentCreate)` does direct field assignment (`segment.name = payload.name`, `segment.members = json.dumps(payload.members)...`, etc.) — there's no `exclude_unset` partial-update logic like `update_flag()` has.
**How to avoid:** "Save Test Context" in `SegmentForm.vue` must build and send the **full current segment payload** (same shape as `handleSubmit()`'s `payload` object) **plus** `test_context`, OR the planner introduces a small partial-update path. Given CONTEXT.md's discretion note allows reusing existing endpoints, the full-payload approach is simplest and avoids backend router/service changes beyond adding the `test_context` field to `SegmentCreate`/`SegmentResponse`.
**Warning signs:** After "Save Test Context" on a segment, `name`/`conditions`/`members` revert to empty/defaults — indicates the partial-payload bug.

### Pitfall 2: `auth.ts` doesn't expose `sub`
**What goes wrong:** `portal/src/stores/auth.ts`'s `user` ref is `{ name: string; email: string } | null` — no `sub` field. A naive `useUserContext()` reading `authStore.user?.sub` would always return `undefined`.
**Why it happens:** `_populate()` only extracts `preferred_username` and `email` from `keycloak.tokenParsed`.
**How to avoid:** Either (a) read `keycloak.tokenParsed?.sub` directly in `useUserContext.ts` (bypassing the store, since `keycloak-js`'s `KeycloakTokenParsed` interface includes `sub?: string` as a standard JWT claim — HIGH confidence, this is OIDC spec), or (b) add `sub: keycloak.tokenParsed?.sub ?? ''` to `auth.ts`'s `user` ref and update `auth.test.ts` mocks accordingly. Option (b) is more consistent with existing patterns and easier to unit-test via the existing `auth.test.ts` Keycloak mock (`tokenParsed: { preferred_username, email }` → add `sub`).
**Warning signs:** Real-context toggle shows `sub: ""` always.

### Pitfall 3: RuleSimulator.vue is not currently mounted in SegmentForm.vue at all
**What goes wrong:** Planner might assume "RuleSimulator already shared between flag/segment via mode prop" per CONTEXT.md's `code_context` section — but `mode` doesn't exist on `RuleSimulator.vue` today, and `SegmentForm.vue` has zero references to `RuleSimulator`. This is new mounting work, not a prop tweak.
**Why it happens:** CONTEXT.md's `code_context` describes the *target* shared state (post Phase 13), not the current state — `RuleCard.vue` has `mode`, `RuleSimulator.vue` does not.
**How to avoid:** Plan explicit tasks for (1) adding `mode` prop to `RuleSimulator.vue`, and (2) mounting `<RuleSimulator mode="segment" :rules="form.conditions" :test-context="segment?.test_context" @save-test-context="..." />` inside `SegmentForm.vue`'s `v-if="form.type === 'rule_based'"` block.
**Warning signs:** Segment editor shows no Live Simulator at all post-implementation.

### Pitfall 4: `updateSegment` not yet wired as a store action
**What goes wrong:** `useFeatureFlagsStore` (mui-feature-flags) has `updateFlag` but **no `updateSegment` action** — `SegmentsView.vue` calls `flagsService.updateSegment()` directly (per Grep results), bypassing the store. If `RuleBuilderView.vue`'s pattern (store-mediated PATCH) is copied verbatim for segments, it will fail because the store has no such method.
**How to avoid:** For segments, call `updateSegment()` from `services/flags.ts` directly (matching `SegmentsView.vue`'s existing pattern), not via the Pinia store — or add `updateSegment` to the store for consistency (optional, scope creep).

### Pitfall 5: MySQL 5.6 / `Optional[str] = None` JSON field — no native JSON type
**What goes wrong:** Using `sa.JSON()` column type would fail or behave unexpectedly on MySQL 5.6 (no native JSON type until 5.7.8).
**How to avoid:** Use `sa.Text()` for `test_context`, exactly as `rules`/`tags`/`conditions`/`members` already do — confirmed by `[07-03]` decision log entry: "downgrade re-adds column as nullable TEXT (not JSON) — MySQL 5.6 lacks native JSON type."

## Code Examples

### Backend: FlagUpdate/FlagResponse extension
```python
# Source: backend/app/domains/feature_flags/schemas.py (existing file, lines 31-84)
class FlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    default_val: Optional[bool] = None
    complex: Optional[bool] = None
    ttl: Optional[int] = None
    environment: Optional[str] = None
    rollout: Optional[int] = None
    rules: Optional[List[RuleSchema]] = None
    tags: Optional[List[str]] = None
    test_context: Optional[str] = None   # NEW — raw JSON string or None

class FlagResponse(BaseModel):
    # ...existing fields...
    test_context: Optional[str] = None   # NEW — no parsing in parse_text_fields needed
    model_config = ConfigDict(from_attributes=True)
    # parse_text_fields validator unchanged (only touches rules/tags)
```

### Backend: update_flag() — already handles arbitrary fields generically
```python
# Source: backend/app/domains/feature_flags/service.py (existing, lines 152-175)
# update_flag() uses payload.model_dump(exclude_unset=True) + setattr loop —
# test_context requires NO special-case code, it falls through the generic
# `for key, value in update_data.items(): setattr(flag, key, value)` path automatically.
```

### Backend: SegmentCreate/SegmentResponse + update_segment (full-replacement caveat)
```python
# Source: backend/app/domains/feature_flags/schemas.py (existing, lines 87-130)
class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    members: List[str] = []
    type: str = 'manual'
    conditions: List[RuleSchema] = []
    test_context: Optional[str] = None   # NEW

class SegmentResponse(BaseModel):
    # ...existing fields...
    test_context: Optional[str] = None   # NEW

# service.update_segment() — add one line:
# segment.test_context = payload.test_context
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-------------------|---------------|--------|
| Synthetic-only Test Context (hardcoded placeholder, ephemeral) | Persisted per-flag/segment + real-user-context toggle | Phase 13 | Test contexts survive editor close/reopen; real-case validation against logged-in user |
| `RuleSimulator.vue` mounted only in `RuleBuilderView.vue` | Shared via `mode='flag'\|'segment'`, also mounted in `SegmentForm.vue` | Phase 13 | First cross-reuse of the Live Simulator component |

**Deprecated/outdated:** None — this phase is purely additive.

## Open Questions

1. **Exact rule attribute names for the real-context key mapping**
   - What we know: CONTEXT.md specifies the mapping target shape `sub→id/email, roles→role, tenant_id→tenant_id, product_id→product_id` but uses "ej." (e.g.) — implying these are illustrative, not exhaustive/exact.
   - What's unclear: The precise attribute names used by actual seeded rules (e.g., `bo.feature.create`'s tenant_id-based rule from Phase 12) — is the attribute literally `tenant_id`, or `tenantId`, or something else? Is the user-id attribute `id`, `sub`, or `user_id`?
   - Recommendation: Planner should inspect `backend/seed_data.py` (new untracked file per git status) and/or query the DB for `bo.feature*` flag rules to confirm exact attribute strings before finalizing `useUserContext()`'s returned key names. If ambiguous, default to documenting both common aliases or making the mapping a small constant object easy to adjust.

2. **Where does "Save Test Context" button live in RuleBuilderView.vue's layout?**
   - What we know: CONTEXT.md defers visual design to Claude's discretion ("Diseño visual exacto del toggle... posición, label, icono").
   - What's unclear: Whether "Save Test Context" sits inside `RuleSimulator.vue` itself (self-contained, emits event to parent) or in `RuleBuilderView.vue`'s header area.
   - Recommendation: Place the button inside `RuleSimulator.vue` near the Test Context textarea (co-located with the field it saves), emitting `save-test-context` to the parent which performs the PATCH — keeps `RuleSimulator.vue` API-call-free and consistent with its current "dumb" presentational role.

3. **Does `SegmentForm.vue`'s "Save Test Context" need network-call wiring inside the form component, or does it bubble to `SegmentsView.vue`?**
   - What we know: `SegmentForm.vue` currently only `emit('save', payload)` on full submit; `SegmentsView.vue` owns `updateSegment()` calls.
   - What's unclear: Whether to add a new emit (`save-test-context`) from `SegmentForm.vue` → `SegmentsView.vue`, or have `SegmentForm.vue` call `updateSegment()` directly (breaking its current "dumb form" pattern).
   - Recommendation: Add `emit('save-test-context', payload)` from `SegmentForm.vue`, handled in `SegmentsView.vue` alongside its existing `updateSegment` call — keeps the dumb-form pattern intact, matches Pitfall 1's full-payload requirement naturally (SegmentsView already has `editingSegment` context).

## Sources

### Primary (HIGH confidence)
- `backend/app/domains/feature_flags/models.py` — current `FeatureFlag`/`Segment` table definitions
- `backend/app/domains/feature_flags/schemas.py` — current `FlagUpdate`/`FlagResponse`/`SegmentCreate`/`SegmentResponse`
- `backend/app/domains/feature_flags/service.py` — `update_flag()` (generic setattr loop) vs `update_segment()` (full-replacement assignments)
- `backend/app/domains/feature_flags/router.py` — `PATCH /flags/{id}` and `PATCH /flags/segments/{id}` signatures
- `backend/alembic/versions/d001_add_tenant_owner.py` — single nullable column migration precedent (head revision)
- `backend/alembic/versions/c001_expand_segments_type_conditions.py` — two-column nullable add precedent (no 3-step)
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` — current Test Context UI (no `mode` prop, single `rules` prop)
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` — `evaluateRule()`/`useRuleSimulator()` evaluation engine
- `microuis/mui-feature-flags/src/views/RuleBuilderView.vue` — current `RuleSimulator` mount + `saveChanges()` PATCH flow
- `microuis/mui-feature-flags/src/components/flags/SegmentForm.vue` — current segment form (no RuleSimulator mounted)
- `microuis/mui-feature-flags/src/views/SegmentsView.vue` — `updateSegment()` call site (not in store)
- `microuis/mui-feature-flags/src/services/flags.ts` — `FeatureFlag`/`Segment`/`FlagPayload`/`SegmentPayload` types, `update`/`updateSegment` functions
- `microuis/mui-feature-flags/src/stores/flags.ts` — Pinia store actions (`updateFlag` exists, `updateSegment` does not)
- `portal/src/composables/useBoFlags.ts` — Phase 12 singleton composable pattern to mirror
- `portal/src/stores/auth.ts` — `user: { name, email }`, `roles`, no `sub`
- `portal/src/main.ts` — `useBoFlags().init({ sub: authStore.user?.email, roles, tenant_id: VITE_BO_TENANT_ID })` pattern
- `portal/vite.config.ts` — `exposes` block (`./boFlags` etc.)
- `microuis/mui-feature-flags/src/env.d.ts` — `declare module 'shell/boFlags'` pattern
- `bff/src/routes/flags.ts` — generic proxy, no schema validation at BFF layer (passes `test_context` through transparently)
- `.planning/STATE.md` — decision log entries `[07-03]` (MySQL 5.6 TEXT not JSON), `[Phase 11]` (`evaluateRule()` exported for vitest)

### Secondary (MEDIUM confidence)
- `keycloak-js` `KeycloakTokenParsed.sub` — standard OIDC JWT claim, not directly verified in this codebase's installed type defs but is part of the stable `keycloak-js` public API and OIDC spec (training-data knowledge, low risk of being wrong since `sub` is a mandatory OIDC claim)

### Tertiary (LOW confidence)
- Exact attribute names for real-context key mapping (Open Question 1) — needs verification against `backend/seed_data.py` or live DB rules

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every piece (migration, schema field, Module Federation exposure) has a direct working precedent already in the codebase
- Architecture: HIGH — file-by-file changes mapped against actual current code
- Pitfalls: HIGH — Pitfalls 1, 3, 4 discovered by direct code inspection (not speculation); Pitfall 2 confirmed by reading `auth.ts` and `auth.test.ts`

**Research date:** 2026-06-11
**Valid until:** 30 days (stable internal codebase, no external dependency churn)
