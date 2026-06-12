# Phase 15: AND Rule Combination Semantics + Flags Page Filters - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning
**Source:** User decisions via AskUserQuestion during /gsd:plan-phase 15 (research-driven questions)

<domain>
## Phase Boundary

Two deliverables:

1. **AND rule combination (opt-in mode):** A flag whose rules combine with AND evaluates true only when ALL individual rules match, false otherwise — implemented via a new flag-level `rule_combination_mode` field, with parity across the 4 evaluators (backend `feature_flags/service.py`, `sdk-js/src/evaluator.ts`, `sdk-python evaluator.py`, `useRuleSimulator.ts`).
2. **`/flags` page filters:** Status, Tags, Complexity, Environment, and scope target (Products / Tenants / Companies / Global), wiring up the existing disabled filter-bar scaffold in FlagsView.vue.

Out of scope: OR operator, rule groups / nested compositions (deferred to a future release). Segment condition semantics unchanged.

</domain>

<decisions>
## Implementation Decisions

### AND semantics design (LOCKED — Option C from 15-RESEARCH.md Open Question #1)
- Add a flag-level `rule_combination_mode` field: `'first_match'` (legacy, default) | `'and'` (new).
- Existing flags keep current first-match-wins behavior with per-rule `result` — zero behavioral change for legacy flags (including bo.feature.* dogfooding flags).
- In `'and'` mode: evaluation returns true only if ALL rules' conditions match; otherwise false (falls through per current non-match path semantics: segments check / default_val as the planner determines consistent with "other case the result is false").
- Per-rule `result` field is not consulted in `'and'` mode.
- Additive nullable column on `feature_flags` (NULL treated as `'first_match'`), following the Phase 13 `test_context` single-additive-migration precedent (MySQL 5.6 safe). Expose in FlagCreate/FlagUpdate/FlagResponse and in SDK bootstrap entries.
- All 4 evaluators branch on the mode with identical semantics + tests (TDD per established phase 11/14 pattern). Design keeps the door open for `'or'`/groups modes in a future release.

### Segment conditions (LOCKED — Open Question #2)
- AND applies ONLY to `flag.rules`. `rule_based` segment `conditions` keep OR/any-match membership semantics (`resolve_segment_members` and SDK segment blocks untouched).

### Complexity filter (LOCKED — Open Question #3)
- Filter uses the existing stored `flag.complex: boolean` (Simple/Complex), consistent with the FlagTable badge. No derived tiers, no backend changes.

### Scope-target filter (LOCKED — Open Question #4)
- 4 buckets: Products / Tenants / Companies / Global (includes the Phase 14 `company` scope).

### Filters implementation
- Client-side computed filtering over the already-fetched `flagsStore.flags` (all needed fields exist on FlagResponse). No backend query-param changes required.
- No URL query-string sync (Open Question #5) — local reactive state in FlagsView.vue is sufficient this phase.

### Claude's Discretion
- Filter bar UX details (multi-select vs single-select per dimension, clear-filters affordance), matching existing UI patterns.
- UI for choosing `rule_combination_mode` in FlagForm/RuleCard area (e.g., a small "Match: first rule / all rules (AND)" selector) and how RuleSimulator displays per-rule pass/fail + overall result in AND mode (research Pitfall 3).
- Whether `/flags` filter state lives in FlagsView or a small `useFlagFilters` composable.
- Requirement IDs: suggest AND-01/AND-02, FLT-01..FLT-0x; note REQUIREMENTS.md registration gap (same as phase 14) in deferred-items.

</decisions>

<specifics>
## Specific Ideas

- User's original phrasing: "for AND operators all individual rules must evaluate to true other case the result is false."
- Future release explicitly mentioned by user: OR operators and rule groups for building more complex rules — the mode-field design was chosen to keep this extension path open.
- Filters requested verbatim: "filters by Status, Tags, Complexity, Environment, by Products and Tenants or Global" on the `/flags` page.

</specifics>

<deferred>
## Deferred Ideas

- OR combination mode and rule groups/nesting (next release).
- Derived complexity tiers (rule-count/segment-count based) — only if requested later.
- URL query-param sync for `/flags` filters.

</deferred>

---

*Phase: 15-and-rule-combination-semantics*
*Context gathered: 2026-06-12 via in-workflow user decisions*
