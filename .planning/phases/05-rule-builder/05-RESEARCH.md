# Phase 5: Rule Builder - Research

**Researched:** 2026-06-07
**Domain:** Vue 3 drag-and-drop UI, TypeScript evaluation engine port, visual rule builder
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Placement:** Full dedicated page at `/flags/:id/rules` (separate route, NOT inside FlagDrawer)
- **Card layout:** Logic block cards following `design/stitch/design-builder-feature-flags-rules.html` exactly
  - Card structure: `border-l-4 border-l-primary-container`, title header + delete button, attribute/operator/value/result fields inline
  - Attribute field: free-text input
  - Operator field: `<select>` with 5 operators: `equals`, `in`, `notIn`, `contains`, `regex`
  - Value field: chip-tags input for `in`/`notIn`; plain text for `equals`, `contains`, `regex`
  - Result field: boolean toggle (true/false)
- **AND connector:** Decorative only — vertical line + centered "AND" pill badge between cards; first-match-wins semantics preserved
- **Drag & drop library:** `vuedraggable@next` (vuedraggable@4.1.0, SortableJS wrapper) — install as new portal dependency
- **Drag handle:** Explicit `drag_indicator` icon on left edge, visible on hover; only handle triggers drag
- **Reorder is local-only:** No auto-save on drop; user must click "Save Changes"
- **Simulator:** Frontend-only TypeScript port of `_evaluate_rule()` + `evaluate_flag()` logic
- **Simulator input:** JSON textarea (`{"country": "PE", "plan": "pro"}`)
- **Simulator output:** Pass/fail result + matched rule name/index highlighted
- **Simulator timing:** Live/real-time — re-evaluates on every rule or context change (no Run button)
- **Layout:** 12-column grid — left 8 cols = rule editor canvas, right 4 cols = simulator sidebar
- **Environment tabs:** Production / Staging / Development — decorative only (rules shared across envs)
- **Rollout slider:** Included — maps to `FeatureFlag.rollout` (Integer 0–100)
- **Save:** PATCH `rules` + `rollout` via `useFeatureFlagsStore.updateFlag()`; Cancel navigates back to FlagsView

### Claude's Discretion

- Exact chip tag input component implementation
- Loading/saving state indicators
- Error handling for invalid JSON in simulator context
- Transition animations (card reorder, hover effects)

### Deferred Ideas (OUT OF SCOPE)

- Per-environment rule sets (different rules for prod vs staging) — backend schema change, separate phase
- Full evaluation trace (show each rule pass/fail in order) — post-Phase 5
- Rule templates/presets — separate phase
- Change History panel — audit log wiring belongs in a separate phase
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RULE-01 | User can create and edit evaluation rules visually without writing code | RuleBuilderView + RuleCard component with form fields; vuedraggable@next provides drag container; PATCH API already exists |
| RULE-02 | User can reorder rules with priority via drag & drop | vuedraggable@next v4.1.0 with `handle=".drag-handle"` prop; `v-model` binding syncs local rules array; save on explicit "Save Changes" |
| RULE-03 | User can preview the evaluation result of a rule before activating it | TypeScript port of `_evaluate_rule()` + first-match loop; `watchEffect` triggers re-evaluation on rules/context change; matched rule index highlighted |
</phase_requirements>

---

## Summary

Phase 5 is a pure frontend phase — no backend changes required. The PATCH endpoint and `updateFlag()` store action are already in place. The work is entirely new Vue components: `RuleBuilderView.vue` (the full-page route), `RuleCard.vue` (individual logic block), `ChipTagInput.vue` (for `in`/`notIn` operators), and a `useRuleSimulator` composable (TypeScript evaluation engine port). A new router entry at `/flags/:id/rules` must be added.

The hardest technical problem is the chip-tag input: it must distinguish between `in`/`notIn` operators (array values) and scalar operators (string value), and switch rendering modes dynamically as the operator changes. The second hardest is the simulator: it must parse the user's context JSON, handle parse errors gracefully, and re-evaluate in real-time without debounce lag (evaluation is synchronous and cheap).

The design reference (`design-builder-feature-flags-rules.html`) is the exact target. Key deviations from the raw design: (1) the project uses CSS variables from `theme.css` (not Tailwind inline colors), (2) the "AND" connector is truly decorative (no logic coupling), (3) the "Change History" and "Flag Health" sidebar sections are deferred — the right 4-col sidebar contains ONLY the Live Simulator panel.

**Primary recommendation:** Build in four waves — (1) route + shell layout, (2) RuleCard with all operators, (3) drag-and-drop + reorder, (4) simulator sidebar. Each wave is independently verifiable.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `vuedraggable@next` | 4.1.0 | Drag-and-drop sortable list wrapping SortableJS | User-locked decision; Vue 3 native; SortableJS 1.14.0 included |
| `vue-router` | 4.4.x (already installed) | New `/flags/:id/rules` route | Already in project |
| `pinia` | 2.2.x (already installed) | `useFeatureFlagsStore.updateFlag()` for save | Already in project |
| TypeScript | 5.5.x (already installed) | Simulator typed evaluation engine | Already in project |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Material Symbols | (CDN, already used) | `drag_indicator`, `delete`, `add_circle`, `play_circle` icons | Icon rendering in cards and simulator |
| Tailwind CSS | 3.4.x (already installed) | Utility classes for layout | Grid columns, spacing, color utilities |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `vuedraggable@next` | `@vueuse/gesture`, `dnd-kit`, native HTML5 drag | User locked `vuedraggable@next` — not negotiable |
| Custom chip input | `vue3-tags-input` npm package | Claude's discretion; hand-rolling is ~30 lines and avoids a dependency for simple behavior |

**Installation:**
```bash
cd portal && pnpm add vuedraggable@next
```

---

## Architecture Patterns

### Recommended Project Structure

```
portal/src/
├── views/
│   └── RuleBuilderView.vue          # Full-page route component (/flags/:id/rules)
├── components/flags/
│   ├── RuleCard.vue                 # Individual logic block card
│   ├── ChipTagInput.vue             # Chip input for in/notIn values
│   └── RuleSimulator.vue            # Right-sidebar simulator panel
└── composables/
    └── useRuleSimulator.ts          # TypeScript evaluation engine + reactive state
```

### Router Registration Pattern

**What:** Add named route `rule-builder` to `portal/src/router/index.ts`
**When to use:** Required for navigation from FlagDrawer and for direct URL access

```typescript
// portal/src/router/index.ts — add inside routes array
{
  path: '/flags/:id/rules',
  name: 'rule-builder',
  component: () => import('../views/RuleBuilderView.vue'),
  meta: {
    requiresAuth: true,
    roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'],
    layout: 'main',
    title: 'Rule Builder'
  },
}
```

### FlagDrawer Navigation Pattern

**What:** Add "Edit Rules" button to FlagDrawer that pushes to `/flags/:id/rules`
**When to use:** Only shown when editing an existing flag (not on create)

```typescript
// Inside FlagDrawer.vue — add import
import { useRouter } from 'vue-router'
const router = useRouter()

function openRuleBuilder() {
  if (props.flag?.id) {
    router.push({ name: 'rule-builder', params: { id: props.flag.id } })
    emit('close')
  }
}
```

FlagForm.vue: Remove the JSON textarea rules field (lines 222–233), replace with read-only summary text: "Rules are managed in the Rule Builder."

### RuleBuilderView Composition Pattern

**What:** `RuleBuilderView.vue` loads the flag by ID from route params, owns local mutable `rules` and `rollout` refs, saves via store
**When to use:** Full-page view — single source of truth for dirty state

```typescript
// RuleBuilderView.vue <script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFeatureFlagsStore } from '../stores/flags'
import type { RuleSchema } from '../services/flags'

const route = useRoute()
const router = useRouter()
const store = useFeatureFlagsStore()

const flagId = computed(() => Number(route.params.id))
const flag = computed(() => store.flags.find(f => f.id === flagId.value) ?? null)

// Local mutable copies — not saved until "Save Changes"
const localRules = ref<RuleSchema[]>([])
const localRollout = ref(0)
const isSaving = ref(false)

onMounted(async () => {
  if (store.flags.length === 0) await store.fetchFlags()
  if (flag.value) {
    localRules.value = structuredClone(flag.value.rules)
    localRollout.value = flag.value.rollout
  }
})

async function saveChanges() {
  isSaving.value = true
  try {
    await store.updateFlag(flagId.value, {
      rules: localRules.value,
      rollout: localRollout.value,
      complex: localRules.value.length > 0,  // auto-set complex=true when rules exist
    })
    router.push({ name: 'flags' })
  } finally {
    isSaving.value = false
  }
}
```

**Key insight:** `structuredClone()` (available in modern browsers / Node 17+) deep-copies the rules array so edits don't mutate the store directly before save.

### vuedraggable@next Usage Pattern

**What:** Wrap `localRules` array in `<draggable>` with explicit handle
**When to use:** RULE-02 — reordering via drag & drop

```vue
<!-- Source: https://github.com/SortableJS/vue.draggable.next README -->
<draggable
  v-model="localRules"
  item-key="attribute"
  handle=".drag-handle"
  animation="200"
  ghost-class="rule-card--ghost"
  @end="onDragEnd"
>
  <template #item="{ element, index }">
    <div class="relative group">
      <RuleCard
        :rule="element"
        :index="index"
        @update="updateRule(index, $event)"
        @delete="deleteRule(index)"
      />
    </div>
  </template>
</draggable>
```

**Critical:** `item-key` must be a unique key. Since rules don't have IDs, use index or a generated UUID assigned when creating a rule.

**Alternative item-key using generated ID:**
```typescript
interface RuleLocal extends RuleSchema {
  _id: string  // UUID assigned on creation, not sent to backend
}

function addRule(): void {
  localRules.value.push({
    _id: crypto.randomUUID(),
    attribute: '',
    operator: 'equals',
    value: '',
    result: true,
  })
}
```

Strip `_id` before saving: `localRules.value.map(({ _id, ...r }) => r)`

### RuleCard Component Pattern

**What:** Emits `update` and `delete` events; parent holds array; card is stateless except for operator-dependent value rendering
**When to use:** Stateless child for array of rules is the Vue standard pattern

```vue
<!-- RuleCard.vue -->
<script setup lang="ts">
import type { RuleSchema } from '../../services/flags'

const props = defineProps<{
  rule: RuleSchema & { _id: string }
  index: number
}>()

const emit = defineEmits<{
  update: [rule: RuleSchema & { _id: string }]
  delete: []
}>()

const OPERATORS = ['equals', 'in', 'notIn', 'contains', 'regex'] as const
const isArrayOperator = (op: string) => op === 'in' || op === 'notIn'

function onOperatorChange(newOp: string) {
  // When switching to array operator, convert value to array if not already
  // When switching away, join array to string
  let newValue = props.rule.value
  if (isArrayOperator(newOp) && !Array.isArray(newValue)) {
    newValue = newValue ? [String(newValue)] : []
  } else if (!isArrayOperator(newOp) && Array.isArray(newValue)) {
    newValue = newValue.join(', ')
  }
  emit('update', { ...props.rule, operator: newOp, value: newValue })
}
</script>
```

### TypeScript Evaluation Engine (Simulator)

**What:** Direct port of `service.py:_evaluate_rule()` + first-match loop into TypeScript
**When to use:** `useRuleSimulator` composable, triggered by `watchEffect`

```typescript
// composables/useRuleSimulator.ts
// Source: backend/app/domains/feature_flags/service.py

import { ref, watchEffect } from 'vue'
import type { RuleSchema } from '../services/flags'

type Operator = 'equals' | 'in' | 'notIn' | 'contains' | 'regex'

const OPERATORS: Record<Operator, (actual: unknown, expected: unknown) => boolean> = {
  equals:   (a, e) => a === e,
  in:       (a, e) => Array.isArray(e) ? e.includes(a) : false,
  notIn:    (a, e) => Array.isArray(e) ? !e.includes(a) : true,
  contains: (a, e) => String(a).includes(String(e)),
  regex:    (a, e) => { try { return new RegExp(String(e)).test(String(a)) } catch { return false } },
}

function evaluateRule(rule: RuleSchema, user: Record<string, unknown>): boolean {
  const actual = user[rule.attribute]
  if (actual === undefined || actual === null) return false
  const fn = OPERATORS[rule.operator as Operator]
  if (!fn) return false
  try { return fn(actual, rule.value) } catch { return false }
}

export function useRuleSimulator(
  rules: Readonly<Ref<RuleSchema[]>>,
  contextJson: Ref<string>
) {
  const matchedIndex = ref<number | null>(null)
  const matchedResult = ref<boolean | null>(null)
  const contextError = ref<string | null>(null)

  watchEffect(() => {
    contextError.value = null
    matchedIndex.value = null
    matchedResult.value = null

    let user: Record<string, unknown>
    try {
      user = JSON.parse(contextJson.value)
    } catch {
      contextError.value = 'Invalid JSON'
      return
    }

    for (let i = 0; i < rules.value.length; i++) {
      if (evaluateRule(rules.value[i], user)) {
        matchedIndex.value = i
        matchedResult.value = rules.value[i].result
        return
      }
    }
    // No rule matched — result is null (no match)
  })

  return { matchedIndex, matchedResult, contextError }
}
```

### AND Connector Pattern

**What:** Decorative vertical connector between cards; always present between adjacent cards
**When to use:** Rendered in the `#item` slot wrapper, before each card except the first

```vue
<!-- In RuleBuilderView.vue, inside draggable #item slot -->
<template #item="{ element, index }">
  <!-- AND connector: shown between rules, not before first -->
  <div v-if="index > 0" class="flex justify-center relative -my-2 z-20 pointer-events-none">
    <div class="w-px h-8 bg-outline-variant"></div>
    <div class="absolute top-1/2 -translate-y-1/2 bg-surface-container-lowest px-3 py-0.5 rounded-full border border-outline-variant text-xs font-bold text-primary select-none">
      AND
    </div>
  </div>
  <RuleCard :rule="element" :index="index" @update="..." @delete="..." />
</template>
```

### Chip Tag Input Pattern (Claude's Discretion)

**What:** Simple chip-tag input for `in`/`notIn` value arrays — type value + Enter to add, click X to remove
**When to use:** Only rendered when `rule.operator === 'in' || 'notIn'`

```vue
<!-- ChipTagInput.vue -->
<script setup lang="ts">
const props = defineProps<{ modelValue: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [v: string[]] }>()
const inputText = ref('')

function addChip() {
  const val = inputText.value.trim()
  if (val && !props.modelValue.includes(val)) {
    emit('update:modelValue', [...props.modelValue, val])
  }
  inputText.value = ''
}

function removeChip(index: number) {
  emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
}
</script>

<template>
  <div class="chip-input">
    <div class="chip-list">
      <span v-for="(chip, i) in modelValue" :key="i" class="chip">
        {{ chip }}
        <button type="button" @click="removeChip(i)" class="chip-remove">
          <span class="material-symbols-outlined text-[12px]">close</span>
        </button>
      </span>
      <input
        v-model="inputText"
        type="text"
        placeholder="Type + Enter"
        @keydown.enter.prevent="addChip"
        @keydown.comma.prevent="addChip"
        class="chip-input-field"
      />
    </div>
  </div>
</template>
```

**Styling:** Use `bg-primary-fixed text-on-primary-fixed` chip colors matching design reference.

### Anti-Patterns to Avoid

- **Mutating store directly:** Never `store.flags[i].rules.push(...)`. Always edit the local `localRules` ref and save explicitly.
- **Using `index` as `item-key` in vuedraggable:** Index-as-key breaks VNode reconciliation during drag. Use `_id` (UUID) or `element.attribute + element.operator` composite.
- **Two-way binding on RuleCard fields:** Card emitting `@input` that directly mutates `localRules[index]` via v-model can cause reactive loops. Use `emit('update', {...spread})` and let parent replace the element: `localRules.value[index] = newRule`.
- **Watching complex JSON in simulator with deep watch:** Use `watchEffect` (which tracks accessed refs automatically) not `watch(..., { deep: true })` to avoid unnecessary re-evaluations.
- **Forgetting to strip `_id` before PATCH:** The backend RuleSchema does not have an `_id` field — sending it will be ignored by Pydantic's `exclude_unset` but is cleaner to strip explicitly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag-and-drop sortable list | Custom mousedown/mousemove handlers | `vuedraggable@next` | Touch support, auto-scroll, ghost preview, keyboard accessibility, cross-browser edge cases |
| Evaluation engine | Re-implement from scratch | Direct TypeScript port of `service.py:_evaluate_rule()` + loop | Already battle-tested; any deviation breaks simulator accuracy |
| Deep clone of rules array | `JSON.parse(JSON.stringify(...))` | `structuredClone()` | Built-in, handles all primitives; JSON round-trip can corrupt regex strings |
| UUID generation for item-key | Custom random string | `crypto.randomUUID()` | Built-in browser API, no dependency |

**Key insight:** The evaluation logic already exists in Python — port it literally, line by line. Any "improvement" risks divergence from backend behavior.

---

## Common Pitfalls

### Pitfall 1: vuedraggable item-key collision
**What goes wrong:** Using `item-key="attribute"` when two rules have the same attribute (e.g., two `country` rules). Vue reuses VNodes incorrectly, causing UI glitches.
**Why it happens:** `item-key` must be globally unique within the list.
**How to avoid:** Assign a `_id: crypto.randomUUID()` to each rule on creation, use `item-key="_id"`.
**Warning signs:** Input values visually "jump" to wrong cards after drag.

### Pitfall 2: Operator change does not reset value type
**What goes wrong:** User selects `in` operator; value is stored as array `["PE","US"]`. User switches to `equals` — value is now an array sent to PATCH, causing backend rule mismatch.
**Why it happens:** Value field changes type with operator but old value persists.
**How to avoid:** `onOperatorChange()` in RuleCard must coerce value: array→string join when switching away from `in`/`notIn`; string→array wrap when switching to `in`/`notIn`.
**Warning signs:** Simulator gives wrong results; backend evaluation wrong.

### Pitfall 3: vuedraggable loses reactivity if list is replaced (not mutated)
**What goes wrong:** Parent replaces `localRules.value = newArray` during drag — SortableJS loses sync with DOM.
**Why it happens:** SortableJS manages DOM order internally; replacing the ref breaks its internal state.
**How to avoid:** Only mutate rule content via `localRules.value[index] = updated` or use `splice()`. Full replacement is safe only on initial load (not during active drag).
**Warning signs:** After drag + edit, saved order doesn't match UI order.

### Pitfall 4: RuleBuilderView loads without flag data
**What goes wrong:** User navigates directly to `/flags/42/rules` — `store.flags` is empty.
**Why it happens:** FlagsView populates the store; if bypassed the rule builder has no flag to edit.
**How to avoid:** `onMounted` must call `store.fetchFlags()` if `store.flags.length === 0` before reading the flag. Handle flag-not-found case (404/redirect).
**Warning signs:** `flag.value` is `null` — blank page with no error.

### Pitfall 5: Simulator JSON parse error swallows all results
**What goes wrong:** User types partial JSON `{"country":` — simulator shows nothing.
**Why it happens:** `JSON.parse` throws, watchEffect returns early, matched state stays null.
**How to avoid:** Set `contextError.value = 'Invalid JSON'` and show a styled error message in the simulator panel. Do not clear previous result — show stale result with an error badge.
**Warning signs:** Simulator goes blank while user is typing.

### Pitfall 6: `border-l-primary-container` Tailwind class mismatch
**What goes wrong:** Design uses `border-l-primary-container` but the project's Tailwind config uses CSS variables (`--primary-container`) not hardcoded color values.
**Why it happens:** The design HTML uses a custom Tailwind palette with direct hex values; the project uses CSS variables.
**How to avoid:** Use inline style `style="border-left-color: var(--primary-container)"` on the card's left border, or verify the Tailwind config extends with the CSS variable mapping. The existing Tailwind config (`portal/tailwind.config.js`) must be checked to confirm `primary-container` is registered.
**Warning signs:** Left border on cards renders with wrong color or defaults to `currentColor`.

---

## Code Examples

Verified patterns from official sources and project codebase:

### vuedraggable@next Full Component Usage
```vue
<!-- Source: https://github.com/SortableJS/vue.draggable.next README -->
<template>
  <draggable
    v-model="localRules"
    item-key="_id"
    handle=".drag-handle"
    :animation="200"
    ghost-class="rule-ghost"
  >
    <template #item="{ element, index }">
      <!-- AND connector between cards -->
      <div v-if="index > 0" class="and-connector">
        <div class="connector-line"></div>
        <span class="and-badge">AND</span>
      </div>
      <RuleCard
        :rule="element"
        :index="index"
        @update="(r) => localRules[index] = r"
        @delete="localRules.splice(index, 1)"
      />
    </template>
  </draggable>
</template>
```

### TypeScript Operator Port (from service.py)
```typescript
// Source: backend/app/domains/feature_flags/service.py — direct port
// OPERATORS dict lines 21-28 → TypeScript Record
const OPERATORS = {
  equals:   (a: unknown, e: unknown) => a === e,
  in:       (a: unknown, e: unknown) => Array.isArray(e) && e.includes(a),
  notIn:    (a: unknown, e: unknown) => Array.isArray(e) && !e.includes(a),
  contains: (a: unknown, e: unknown) => String(a).includes(String(e)),
  regex:    (a: unknown, e: unknown) => { try { return new RegExp(String(e)).test(String(a)) } catch { return false } },
} as const
```

### updateFlag Store Call (Save pattern)
```typescript
// Source: portal/src/stores/flags.ts — existing updateFlag action
await store.updateFlag(flagId.value, {
  rules: localRules.value.map(({ _id, ...r }) => r),  // strip _id
  rollout: localRollout.value,
  complex: localRules.value.length > 0,
})
```

### Canvas Background (dotted grid from design reference)
```css
/* Source: design/stitch/design-builder-feature-flags-rules.html line 313 */
.rule-canvas {
  background-image: radial-gradient(var(--primary) 0.5px, transparent 0.5px);
  background-size: 20px 20px;
  opacity-modifier: 0.03; /* apply via wrapper with opacity-[0.03] */
}
```
Use a `<div class="absolute inset-0 pointer-events-none opacity-[0.03]" style="background-image: radial-gradient(var(--primary) 0.5px, transparent 0.5px); background-size: 20px 20px;">` inside the canvas.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `vuedraggable` v2 (Vue 2) | `vuedraggable@next` v4.x (Vue 3) | 2021 | Composition API, `v-model`, slot-based API |
| `JSON.parse(JSON.stringify())` clone | `structuredClone()` | Node 17 / Chrome 98 (2022) | Native, handles all primitives correctly |
| `@change` event with `added`/`removed`/`moved` | `v-model` direct binding | vuedraggable 4.x | v-model is simpler; @change still available if needed |

**Deprecated/outdated:**
- vuedraggable v2 `element` prop: replaced by `tag` prop in v4
- `list` prop: works but `v-model` (modelValue) is preferred in Vue 3
- `draggable` default wrapper `div`: use `tag` prop or `:component-data` for custom tags

---

## Integration Checklist

The following existing files need modification (not new files):

| File | Change |
|------|--------|
| `portal/src/router/index.ts` | Add `/flags/:id/rules` route named `rule-builder` |
| `portal/src/components/flags/FlagDrawer.vue` | Add "Edit Rules" button → `router.push({ name: 'rule-builder', params: { id: flag.id } })` |
| `portal/src/components/flags/FlagForm.vue` | Replace JSON textarea (lines 222–233) with read-only label; remove `rulesRaw` ref and its validation |

New files to create:

| File | Purpose |
|------|---------|
| `portal/src/views/RuleBuilderView.vue` | Full-page view, owns localRules + localRollout, grid layout |
| `portal/src/components/flags/RuleCard.vue` | Logic block card, emits update/delete |
| `portal/src/components/flags/ChipTagInput.vue` | Chip-tags for in/notIn values |
| `portal/src/components/flags/RuleSimulator.vue` | Right-sidebar simulator panel |
| `portal/src/composables/useRuleSimulator.ts` | Reactive evaluation engine composable |

---

## Open Questions

1. **Tailwind `border-l-primary-container` availability**
   - What we know: Project uses CSS variables in `theme.css`; Tailwind config at `portal/tailwind.config.js` extends colors
   - What's unclear: Whether `primary-container` is registered as a Tailwind color class or only as a CSS variable
   - Recommendation: Check `portal/tailwind.config.js` during Wave 1; if not registered, use `style="border-left-color: var(--primary-container)"` inline

2. **Flag loading in RuleBuilderView when navigating directly (not from FlagsView)**
   - What we know: `store.flags` is populated by FlagsView's `onMounted`; direct navigation bypasses this
   - What's unclear: Whether to add a `getFlag(id)` service call or always `fetchFlags()`
   - Recommendation: `fetchFlags()` if empty is sufficient; flags list is small and the store pattern is already established

3. **rollout field in FlagForm vs RuleBuilderView**
   - What we know: FlagForm currently shows no rollout slider; rollout is stored on the flag
   - What's unclear: Should FlagForm keep rollout field or defer entirely to RuleBuilderView?
   - Recommendation: FlagForm keeps rollout as it currently exists (it's not shown per the existing code — check if it was ever added); RuleBuilderView adds the rollout slider per design reference

---

## Sources

### Primary (HIGH confidence)
- `backend/app/domains/feature_flags/service.py` — exact evaluation engine to port (lines 15–49)
- `portal/src/services/flags.ts` — RuleSchema interface, `update()` PATCH function
- `portal/src/stores/flags.ts` — `updateFlag()` action signature
- `portal/src/router/index.ts` — existing route pattern to follow
- `design/stitch/design-builder-feature-flags-rules.html` — exact visual target
- npm info `vuedraggable@next` — confirmed version 4.1.0, peerDep vue ^3.0.1, dep sortablejs 1.14.0

### Secondary (MEDIUM confidence)
- [github.com/SortableJS/vue.draggable.next](https://github.com/SortableJS/vue.draggable.next) — README: `handle` prop, `item-key`, `v-model`, `@change` event, `#item` slot (verified via WebFetch)
- [vuedraggable docs](https://sortablejs.github.io/vue.draggable.next/) — official site (content minimal but confirms API surface)

### Tertiary (LOW confidence)
- None — all critical claims verified via official sources or project codebase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed via npm registry and project package.json
- Architecture: HIGH — based on existing project patterns (FlagDrawer, SegmentPicker, router.ts) and verified vuedraggable API
- Evaluation engine port: HIGH — source Python is in codebase, port is literal translation
- Pitfalls: MEDIUM — item-key and operator-coercion pitfalls confirmed via vuedraggable docs; others from first-principles reasoning

**Research date:** 2026-06-07
**Valid until:** 2026-07-07 (vuedraggable is stable; Vue 3 API won't change)
