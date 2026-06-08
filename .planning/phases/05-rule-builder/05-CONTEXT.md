# Phase 5: Rule Builder - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the raw JSON textarea in FlagForm with a full-page visual rule editor. Users can create logic-block rules, reorder them via drag & drop, and preview evaluation results — without writing JSON. The backend evaluation engine (`evaluate_flag()`) and its first-match-wins semantics are unchanged.

</domain>

<decisions>
## Implementation Decisions

### Rule card layout
- Each rule is a "logic block" card — follows design reference exactly (`design/stitch/design-builder-feature-flags-rules.html`)
- Card structure: left blue border accent (`border-l-4 border-l-primary-container`), title header + delete button, attribute/operator/value/result fields inline below
- Attribute field: free-text input (user types attribute name, e.g. `country`, `plan`)
- Operator field: `<select>` with the 5 backend operators: `equals`, `in`, `notIn`, `contains`, `regex`
- Value field: chip tags input for `in`/`notIn` operators (type + Enter to add chip); plain text input for `equals`, `contains`, `regex`
- Result field: boolean toggle — `true` (enabled) / `false` (disabled)
- "AND" connector between cards is decorative only — evaluation order matters (first-match wins), no logic change

### Drag & drop
- Library: `vuedraggable@next` (SortableJS wrapper) — install as new portal dependency
- Explicit drag handle: `drag_indicator` icon on the left edge of each card, visible on hover; only the handle triggers drag (prevents conflicts with card inputs)
- Reorder is local-only until user clicks "Save Changes" — no auto-save on drop

### Preview / simulation
- Frontend-only — re-implement the rule matching logic in TypeScript (attribute lookup, operator dispatch, first-match)
- Test context input: JSON textarea (`{"country": "PE", "plan": "pro"}`)
- Output: pass/fail result + name/index of the matched rule highlighted
- Live/real-time — simulator re-evaluates automatically as rules or context change (no Run button)

### Placement
- Full dedicated page at `/flags/:id/rules` — separate route
- FlagDrawer gets an "Edit Rules" button that navigates to this page; the JSON textarea is replaced by a read-only summary or removed
- Layout: 12-column grid — left 8 cols = rule editor canvas, right 4 cols = simulator sidebar
- Environment tabs (Production / Staging / Development) shown for context — decorative only, rules are shared across environments
- Rollout percentage slider included — maps to the existing `FeatureFlag.rollout` field (Integer 0–100)

### Save behavior
- "Save Changes" button in page header PATCHes `rules` and `rollout` fields on the flag
- "Cancel" navigates back to FlagsView without saving

### Claude's Discretion
- Exact chip tag input component implementation
- Loading/saving state indicators
- Error handling for invalid JSON in simulator context
- Transition animations (card reorder, hover effects)

</decisions>

<specifics>
## Specific Ideas

- Design reference: `design/stitch/design-builder-feature-flags-rules.html` — follow card style, AND connector, and Live Simulator layout exactly
- "AND" connector between rule cards: vertical line + centered pill badge with "AND" label (matches design)
- Dotted grid background on the canvas area (subtle radial-gradient dots, `opacity-[0.03]`)
- "Add New Logic Block" dashed-border button at the bottom of the canvas (matches design)
- Live Simulator right sidebar: shows test context JSON + expected outcome badge (green "Passing" / red "Failing")

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `portal/src/components/flags/FlagForm.vue:222-233` — JSON textarea with `rulesRaw` that says "Phase 5 will add a visual rule builder" — this is the integration point to replace
- `portal/src/components/flags/FlagDrawer.vue` — wraps FlagForm; needs an "Edit Rules" button added that routes to `/flags/:id/rules`
- `portal/src/services/flags.ts` — TypeScript interfaces for `FeatureFlag` and `FlagPayload`; `PATCH /flags/:id` already exists for saving
- `portal/src/stores/flags.ts` — `useFeatureFlagsStore` with `updateFlag()` action
- CSS variables from Material Design theme — `--primary`, `--outline-variant`, `--surface-container-lowest`, etc.

### Established Patterns
- Rule schema (backend): `{attribute: string, operator: "equals"|"in"|"notIn"|"contains"|"regex", value: any, result: boolean}`
- `FeatureFlag.rollout` — Integer 0–100, already in backend model and TypeScript interface
- `FeatureFlag.complex` — boolean toggle that enables multi-rule evaluation; rule builder should set this to `true` automatically when rules exist
- Evaluation engine: `service.py:_evaluate_rule()` + `evaluate_flag()` — exact TypeScript port for frontend simulator

### Integration Points
- New Vue Router route: `/flags/:id/rules` → `RuleBuilderView.vue`
- Navigation: `FlagDrawer.vue` "Edit Rules" button → `router.push({ name: 'rule-builder', params: { id: flag.id } })`
- Save: `useFeatureFlagsStore.updateFlag(id, { rules, rollout })` — existing action, no new API needed

</code_context>

<deferred>
## Deferred Ideas

- Per-environment rule sets (different rules for prod vs staging) — would require backend schema change, separate phase
- Full evaluation trace (show each rule pass/fail in order) — post-Phase 5 enhancement
- Rule templates/presets (common patterns like "equals country") — separate phase
- Change History panel (shown in design) — audit log exists but wiring it per-flag belongs in a separate phase

</deferred>

---

*Phase: 05-rule-builder*
*Context gathered: 2026-06-07*
