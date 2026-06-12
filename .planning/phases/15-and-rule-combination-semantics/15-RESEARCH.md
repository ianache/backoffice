# Phase 15: AND Rule Combination Semantics + Flags Page Filters - Research

**Researched:** 2026-06-12
**Domain:** Feature-flag rule evaluation engine (Python backend + sdk-python + sdk-js + Vue composable) and Vue filter UI (mui-feature-flags)
**Confidence:** HIGH

## Summary

This phase has two independent halves that can be planned/executed as separate plan groups.

**Half 1 — AND combination semantics** is a core-logic change to the rule-evaluation loop that is byte-identical across 4 files: `backend/app/domains/feature_flags/service.py` (`evaluate_flag`/`_evaluate_rule`), `sdk/sdk-js/src/evaluator.ts` (`evaluateFlag`/`evaluateRule`), `sdk/sdk-python/src/backoffice_sdk/evaluator.py` (`evaluate_flag`/`evaluate_rule`), and `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` (`useRuleSimulator`). All four currently implement **first-match-wins**: iterate rules in order, on the first rule whose conditions match, return `bool(rule.result ?? default_val)` and stop. The phase goal requires the loop to become **AND across all rules** — true only if every rule matches, false otherwise — but this directly conflicts with the existing per-rule `result: true/false` field, which lets different rules independently target different (true OR false) outcomes. This is the central design question and is NOT resolved by the codebase as it stands; the planner/CONTEXT discussion must pick one of the documented options below before tasks can be written.

**Half 2 — `/flags` page filters** is comparatively low-risk and has an existing scaffold: `FlagsView.vue` already has a disabled, non-functional filter bar (`<select disabled>` for Status / Tags / Complexity / Environment) and `FlagFilters` interface in `services/flags.ts` already has `{scope?, q?}`. The backend `GET /flags/` already supports `scope` and `q` query params (`list_flags(db, scope_filter, tenant_id, q)`). Status, Tags, Complexity, Environment, and scope-target (Products/Tenants/Global) filters can ALL be implemented client-side (filter the already-fetched `flagsStore.flags` array in a computed property) since the full flag list (with `tags`, `complex`, `environment`, `enabled`, `scope`, `tenant_id`/`product_id`/`company_id`, `rules`) is already returned by `FlagResponse`. No backend changes are strictly required for Half 2, though a `tags`/`environment`/`complex` server-side query param could be added for parity with the existing `scope`/`q` pattern if the team prefers server-side filtering for large datasets (out of scope risk for this phase size — recommend client-side).

**Primary recommendation:** Treat Half 1 as the phase's hard problem requiring a CONTEXT.md decision on the AND-vs-per-rule-result conflict (see Open Questions); treat Half 2 as a mechanical UI task that wires up the existing disabled filter bar to computed client-side filters plus a derived "Complexity" value and a new scope-target filter, with FlagTable optionally gaining a Scope/Target column.

## Standard Stack

### Core
| Library/File | Role | Why it matters |
|---|---|---|
| `backend/app/domains/feature_flags/service.py` | Canonical `OPERATORS` dict + `_evaluate_rule` + `evaluate_flag` | Source of truth; sdk-js/sdk-python/useRuleSimulator are documented ports that must stay byte-identical in operator semantics |
| `sdk/sdk-js/src/evaluator.ts` | `OPERATORS` + `evaluateRule` + `evaluateFlag` (DB-free, bootstrap-cache) | Used by `sdk/sdk-js/src/client.ts::evaluate()` — changing the loop here changes SDK consumer behavior directly |
| `sdk/sdk-python/src/backoffice_sdk/evaluator.py` | `OPERATORS` + `evaluate_rule` + `evaluate_flag` (DB-free) | Mirrors sdk-js exactly; same loop structure |
| `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` | `OPERATORS` + `evaluateRule` + `useRuleSimulator` (Vue reactive) | Drives the Live Simulator's "Matched Rule" / Passing/Failing badge in `RuleSimulator.vue` |
| `backend/app/domains/sdk/service.py::resolve_segment_members` | rule_based segment condition evaluation | **Separate** `any()`-based OR loop over `conditions` — NOT the same code path as `evaluate_flag`'s rules loop; needs an explicit phase-scope decision (see Open Questions #2) |

### Supporting (Half 2 — Filters)
| File | Role |
|---|---|
| `microuis/mui-feature-flags/src/views/FlagsView.vue` | Has the existing disabled filter-bar scaffold (lines 105-119) — 4 `<select disabled>` elements already labeled "All Statuses / Any Tags / Complexity / Environment" |
| `microuis/mui-feature-flags/src/stores/flags.ts` | `useFeatureFlagsStore` — `flags` ref + `fetchFlags(filters?: FlagFilters)` |
| `microuis/mui-feature-flags/src/services/flags.ts` | `FlagFilters { scope?: string; q?: string }`, `FeatureFlag` interface (has `enabled`, `tags`, `complex`, `environment`, `scope`, `tenant_id`, `product_id`, `company_id`, `rules`) |
| `backend/app/domains/feature_flags/router.py::list_flags` (`GET /flags/`) | Already accepts `scope`, `q` query params; `scope_filter`/`tenant_id` permission logic in `_get_scope_filter` |
| `microuis/mui-tenants/src/views/ProductsView.vue` | Existing page-layout pattern (header + StitchButton + table+sidebar grid) — does NOT actually have a working filter bar (PROD-03 filter exists in `ProductTable`/store per REQUIREMENTS but file not inspected in depth this session — check `ProductTable.vue`/`stores/products.ts` if planner wants the exact pattern) |
| `microuis/mui-feature-flags/src/components/flags/FlagTable.vue` | Current columns: Flag Name & Description (incl. tags chips), Status (toggle), Complexity badge (already derived from `flag.complex`), Rollout, TTL, Last Updated, Actions. **No scope/target column exists today** |

### Alternatives Considered
| Instead of | Could use | Tradeoff |
|---|---|---|
| Client-side filtering (computed over `flagsStore.flags`) | Server-side query params (`tags`, `environment`, `complex`, `target`) added to `GET /flags/` | Server-side scales better for very large flag lists, but adds backend work (router params + service.py query building) for a dataset that is currently small (dev/dogfooding scale). Client-side is faster to implement, matches existing `disabled` scaffold intent, and the full `FlagResponse` already contains every field needed |
| New flag-level "combination mode" column/field | In-memory AND loop with no schema change | Adding a `rule_combination_mode` enum column would require an Alembic migration (3-step pattern per project convention) and FlagCreate/FlagUpdate/FlagResponse schema changes — likely overkill for "AND only, OR deferred" scope. Recommend pure logic change in the evaluator loop UNLESS the per-rule-`result` conflict (Open Question #1) forces a schema field |

**Installation:** No new packages — this is a pure logic/UI change within existing files.

## Architecture Patterns

### Pattern 1: 4-way Evaluator Parity (established in Phase 11/14)
**What:** Every change to flag-evaluation semantics must land in 4 files with byte-identical (or near-identical, language-idiomatic) logic:
1. `backend/app/domains/feature_flags/service.py`
2. `sdk/sdk-js/src/evaluator.ts`
3. `sdk/sdk-python/src/backoffice_sdk/evaluator.py`
4. `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts`

**When to use:** Any change to `_evaluate_rule`/`evaluate_rule`/`evaluateRule` (operator semantics) or `evaluate_flag`/`evaluateFlag` (rule-combination / matching loop).

**Example (current first-match-wins, to be changed):**
```python
# Source: backend/app/domains/feature_flags/service.py lines 85-91
rules_raw = winner.rules
rules = json.loads(rules_raw) if isinstance(rules_raw, str) and rules_raw else (rules_raw if isinstance(rules_raw, list) else [])
user = context.get('user', {})
for rule in rules:
    if _evaluate_rule(rule, user):
        return bool(rule.get('result', winner.default_val))
# falls through to segment check, then default_val
```
```typescript
// Source: sdk/sdk-js/src/evaluator.ts lines 70-72
for (const rule of entry.rules) {
  if (evaluateRule(rule, user)) return Boolean(rule.result ?? entry.default_val)
}
```
```typescript
// Source: microuis/mui-feature-flags/src/composables/useRuleSimulator.ts lines 83-91
for (let i = 0; i < ruleList.length; i++) {
  if (evaluateRule(ruleList[i], user)) {
    matchedIndex.value  = i
    matchedResult.value = ruleList[i].result
    return
  }
}
```

### Pattern 2: TDD per-task commits (established Phase 11-14)
Every evaluator-touching plan in Phase 14 used RED (failing test) → GREEN (implementation) → atomic commit per task. The phase 15 plans should follow the same pattern: write the new AND-semantics test cases first in each of the 4 test suites, confirm RED, then implement.

### Pattern 3: Client-side computed filters (no precedent found yet in this codebase, but standard Vue/Pinia idiom)
**What:** A `computed()` in `FlagsView.vue` (or a new small composable `useFlagFilters.ts`) that takes `flagsStore.flags` plus reactive filter refs (status, tags, complexity, environment, scopeTarget) and returns the filtered array, passed to `<FlagTable :flags="filteredFlags" .../>`.
**When to use:** Filter dimensions are all present in the already-fetched `FeatureFlag[]` array; no new network round-trip needed.

**Derivation logic needed:**
- **Status filter:** `flag.enabled` (boolean) → "Enabled"/"Disabled" — direct field, no derivation.
- **Tags filter:** `flag.tags: string[]` — multi-select; flag matches if it has ANY selected tag (consistent with PROD-03 "filtro por label tags" pattern referenced in REQUIREMENTS, though the actual products filter UI implementation wasn't inspected this session).
- **Complexity filter:** `flag.complex: boolean` is already a stored field (used today for the "Complex"/"Simple" badge in FlagTable, lines 117-133) — NOT something that needs deriving from rule count. **However**, the phase description says "Complexity is not a stored attribute — propose derivation." This is a discrepancy: `complex` IS stored (`FlagCreate.complex: bool = False`, `FlagResponse.complex: bool`). Two readings are possible:
  (a) Filter simply uses the existing `flag.complex` boolean (Simple/Complex) — trivial, matches the badge already shown.
  (b) The phase wants a NEW derived complexity tier (e.g., "Simple" = 0 rules, "Has Rules" = 1+ rules no segments, "Has Segments" = any linked segments) independent of the `complex` flag, which would require either fetching `flag_segments` per flag (extra N+1 calls) or a `segment_count`-style field added to `FlagResponse` (mirroring `SegmentResponse.flag_count`).
  **Recommendation:** Use existing `flag.complex` boolean for the Complexity filter (reading (a)) — zero backend changes, consistent with the visible badge. Flag reading (b) as a stretch/Open Question for CONTEXT.md if the user wants rule/segment-count-based tiers.
- **Environment filter:** `flag.environment: string` ('production'|'staging'|'development') — direct field.
- **Scope/Target filter (Products/Tenants/Global):** `flag.scope` ('global'|'tenant'|'product'|'company') combined with `tenant_id`/`product_id`/`company_id`. The phase description names only **"Products, Tenants, or Global"** as the 3 target buckets — `company` scope is NOT mentioned as a filter bucket (possible oversight given Phase 14 added `company` scope+Companies domain). Planner should decide: (i) 3-bucket filter exactly as worded (Products/Tenants/Global, with `company`-scoped flags falling into... an "Other"/uncategorized bucket or being included under one of the three?), or (ii) 4-bucket filter (Products/Tenants/Companies/Global) for full scope coverage. **Flagged as Open Question #4.**

### Anti-Patterns to Avoid
- **Don't add a 5th evaluator** — `resolve_segment_members`'s `any()` loop over `conditions` for `rule_based` segments is a 5th evaluation site that currently has OR semantics for segment membership. Phase 15's stated scope is "flag/segment with multiple rules evaluates true only when ALL individual rules match" — this literally includes segments. Decide explicitly whether `resolve_segment_members` (backend) and the sdk-js/sdk-python `seg.conditions.some(...)`/`any(...)` segment-membership checks are in-scope. See Open Question #2.
- **Don't silently change default behavior for existing flags without a flag-level opt-in** if the AND change is a breaking behavioral change for flags that rely on first-match-wins fallback chains (e.g., "if country=PE return true, else if plan=enterprise return true, else default false" — an OR-like pattern built from multiple `result:true` rules). See Open Question #1.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Comma-separated list parsing for rule values | New parser | Reuse `parseAnyOfInput`/`commitAnyOf` pattern from `RuleCard.vue` (Phase 14) if any new list-valued UI is needed | Already battle-tested with the "Pitfall 3" trailing-comma fix |
| Filter dropdown UI chrome | New custom dropdown component | Native `<select>` (already styled via `.filter-select` class in `FlagsView.vue` <style scoped>) for single-select (Status, Complexity, Environment, Scope-target); for Tags (multi-select), consider reusing `ChipTagInput.vue` in "filter mode" or a simple multi-checkbox dropdown — no existing multi-select component was found in `mui-feature-flags`, so this may need light new UI, but keep it minimal |
| Operator/lambda definitions | New per-operator logic | None needed — Half 1 does not touch `OPERATORS`/`_evaluate_rule`/`evaluateRule` (per-rule operator evaluation is unchanged); only the **loop that combines multiple rules' results** changes |

**Key insight:** Half 1 is a ~10-20 line change per evaluator (the combination loop), but the design decision behind those 10-20 lines is the crux of the phase — get the CONTEXT.md decision right before writing any code.

## Common Pitfalls

### Pitfall 1: AND-vs-`result` field semantic collision
**What goes wrong:** Today, `rules: [{attribute, operator, value, result: true|false}, ...]` lets each rule independently declare its outcome. A naive "AND of all rules, return true only if all match" loses the `result` field's meaning entirely — what does "AND, but rule 2 says result=false" mean for the overall flag value?
**Why it happens:** The `result` field was designed for first-match-wins (each rule is an independent if/elif branch with its own return value), which is fundamentally incompatible with "evaluate true only if ALL rules match" (a single boolean AND across conditions).
**How to avoid:** This MUST be resolved in CONTEXT.md before planning. See Open Question #1 for the documented options (with their pros/cons) the planner/user should choose from.
**Warning signs:** If a plan says "change the for-loop to use `all()`/`every()` and still read `rule.result`" without addressing what happens when rules have mixed `result` values, the design is incomplete.

### Pitfall 2: Segment `rule_based` conditions use a different (OR) loop
**What goes wrong:** `backend/app/domains/sdk/service.py::resolve_segment_members` (lines 108-112) does `if any(_evaluate_rule(c, user) for c in conditions): segment_members[...].append(user_id)` — this is OR-across-conditions for segment membership, a 5th site beyond the "4 evaluators" named in the phase description. The sdk-js/sdk-python/backend `evaluate_flag`/`evaluateFlag` functions ALSO have a `rule_based` segment check: `seg.conditions.some((c) => evaluateRule(c, user))` (sdk-js) / `any(evaluate_rule(c, user) for c in seg.get('conditions', []))` (sdk-python) / inline in backend `evaluate_flag` (not shown directly but documented as "any-match semantics" in evaluator.ts docstring).
**Why it happens:** Segments were built (Phase 8) before AND semantics was considered; "any condition matches → user is in segment" was a reasonable OR-membership model.
**How to avoid:** Explicitly scope: does "multi-rule evaluation combines with AND" apply ONLY to `flag.rules` (the FlagForm Rule Builder), or ALSO to `segment.conditions` (rule_based segments)? The phase title says "AND Rule Combination Semantics" generically. Recommend: keep segment `conditions` OR-based (any-match) for this phase — segments model "is user in this group" (OR of conditions = union of group-membership criteria), which is a different semantic than flag rules (AND of conditions = all criteria for an outcome). Document this exclusion explicitly in the plan/CONTEXT to avoid scope creep into 5 files instead of 4. **Flagged as Open Question #2.**

### Pitfall 3: useRuleSimulator's "Matched Rule" / single-index UI no longer fits AND semantics
**What goes wrong:** `RuleSimulator.vue`'s "Matched Rule" panel (lines 66-95) shows `matchedIndex`/`matchedRule`/`matchedResult` — a SINGLE rule's index and result. If AND semantics means "the overall flag result is true only if ALL rules' conditions evaluate true," there is no longer a single "matched rule" — there's a set of per-rule pass/fail results plus one overall result.
**Why it happens:** The current UI/composable was built for first-match-wins (exactly one rule "wins").
**How to avoid:** `useRuleSimulator` (or a new composable) needs to expose: (a) per-rule boolean results (which rules passed/failed their conditions), and (b) one overall flag result (AND of all per-rule conditions, or per the chosen Open-Question-#1 design). `RuleSimulator.vue`'s "Matched Rule" panel and "Passing/Failing" badge need a redesign — likely showing a list of rule rows each with a pass/fail icon, plus a single overall Passing/Failing badge at the top (the badge already exists at lines 11-27 and can be repurposed for the overall AND result).
**Warning signs:** A plan that keeps `matchedIndex`/`matchedRule` as singular without adding a per-rule results array will produce a UI that can't express "3 of 4 rules passed, overall = false."

### Pitfall 4: Backward compatibility for existing flags (dogfooding `bo.feature.*`)
**What goes wrong:** Flags created under v1.1 (Phase 12 dogfooding: `bo.feature`, `bo.feature.create`, `bo.feature.update`) and any other dev-DB flags have `rules` arrays written under first-match-wins assumptions. If those flags have 0 or 1 rules, AND-vs-first-match is behaviorally IDENTICAL (AND of a single condition = that condition; AND of zero conditions = vacuously true, which must map to the same `default_val` fallback as "no rules"). If any flag has 2+ rules with different `result` values (e.g., rule1: role=Admin→true, rule2: role=Viewer→false, intended as an if/elif chain), AND semantics would break it.
**Why it happens:** No migration/audit of existing `rules` JSON was done as part of this research (read-only constraint; DB not queried). Phase 12/13/14 docs do not document any flag with 2+ rules.
**How to avoid:** Recommend the plan include a verification/audit step: query `feature_flags.rules` in the dev DB (or via `GET /flags/`) for any flag where `json.loads(rules)` has `len(rules) > 1`, and manually review whether AND semantics changes its evaluated result for realistic contexts. Given the evidence (no documented multi-rule flags in phases 12-14), risk appears LOW but should be confirmed, not assumed.
**Warning signs:** If `bo.feature.create`/`bo.feature.update` (which gate UI elements based on user roles per Phase 12 CONTEXT "Real user context (sub, roles) — Enables per-role flag rules") have rules like `[{attribute:'roles', operator:'anyOf', value:['PlatformAdmin'], result:true}]` (single rule) — AND-safe. If they have 2 rules with different roles AND different `result` (e.g., "Admin→true" + "Viewer→false" as an if/elif), AND would break them (both would need to match simultaneously, which is impossible for a single `roles` attribute equality unless using `anyOf`/`in` against a combined set).

## Code Examples

### Current first-match-wins loop (backend) — what changes
```python
# Source: backend/app/domains/feature_flags/service.py lines 85-102
# Evaluate rules — first matching rule wins
rules_raw = winner.rules
rules = json.loads(rules_raw) if isinstance(rules_raw, str) and rules_raw else (rules_raw if isinstance(rules_raw, list) else [])
user = context.get('user', {})
for rule in rules:
    if _evaluate_rule(rule, user):
        return bool(rule.get('result', winner.default_val))

# If no inline rule matched, check segment membership.
segment_members = context.get('segment_members', {})
user_id = user.get('id') or user.get('sub')
if user_id and winner.id in segment_members:
    if user_id in segment_members[winner.id]:
        return True

return bool(winner.default_val)
```

### Illustrative AND-semantics rewrite (Option B from Open Question #1 — flag-level result ignores per-rule `result`)
```python
# ILLUSTRATIVE ONLY — exact design pending CONTEXT.md decision
rules = ...  # same parsing as above
user = context.get('user', {})
if rules:
    if all(_evaluate_rule(rule, user) for rule in rules):
        return True  # ALL rules matched -> flag is "on" for this user
    # fall through to segment check, then default_val (rules did not all match)
else:
    pass  # no rules -> go straight to segment check / default_val

# segment check unchanged...
return bool(winner.default_val)
```

### Illustrative per-rule simulator output shape (for RuleSimulator.vue redesign)
```typescript
// ILLUSTRATIVE — useRuleSimulator new return shape candidate
interface RuleEvalResult {
  index: number
  passed: boolean       // did this rule's condition match the context?
}
// returned alongside existing contextError:
{
  ruleResults: Ref<RuleEvalResult[]>,  // one entry per rule, in order
  overallResult: Ref<boolean | null>,  // AND of all ruleResults[].passed (or per Option chosen)
  contextError: Ref<string | null>,
}
```

## State of the Art

| Old Approach | Current/Proposed Approach | When Changed | Impact |
|---|---|---|---|
| First-match-wins with per-rule `result: true\|false` | AND-of-all-rules (exact return-value semantics TBD per Open Question #1) | Phase 15 (this phase) | Breaking change to multi-rule flag evaluation across backend, sdk-js, sdk-python, useRuleSimulator; UI (RuleSimulator "Matched Rule" panel) needs redesign |
| `/flags` page filter bar: 4 disabled `<select>` placeholders | Functional client-side filters (Status/Tags/Complexity/Environment) + new scope-target filter | Phase 15 (this phase) | Additive, non-breaking; existing `FlagFilters{scope,q}` + `GET /flags/?scope=...&q=...` already supported server-side if server-side filtering is later desired |

**Deprecated/outdated:** None — this is the first phase to revisit the rule-combination loop since it was introduced in Phase 4/5 (v1.0).

## Open Questions

1. **How should AND-of-all-rules interact with the per-rule `result: true/false` field?**
   - What we know: Today, `result` lets each rule independently specify the flag's outcome if THAT rule matches (if/elif chain). AND semantics requires ALL rules' conditions to be true simultaneously for "the flag is on."
   - What's unclear: What does the overall evaluated boolean become, and does `result` still have meaning per-rule?
   - Candidate options (documented for CONTEXT.md discussion, none implemented):
     - **Option A — Keep `result`, AND only gates whether ANY rule's `result` can fire:** All rules must match their conditions; if so, evaluate is `bool(rules[-1].result)` or `bool(rules[0].result)` or require all `result` values to agree (error/fallback if they disagree). Awkward — `result` becomes redundant/contradictory when rules disagree.
     - **Option B — Drop per-rule `result` from the evaluation outcome; AND-of-conditions directly produces `true`/`false` (true = all match → flag ON, else → default_val/segments):** Simplest mental model ("flag is on for users matching ALL these conditions"). Requires either ignoring the `result` field at evaluation time (UI could still show it but it's inert) or removing it from `RuleSchema` (breaking schema change — Alembic not needed since `rules` is JSON-text, but `RuleSchema.result: bool` is currently required/non-optional in `schemas.py` and `RuleSchema` types in sdk-js/sdk-python/useRuleSimulator).
     - **Option C — Add a flag-level `rule_combination_mode` field (e.g., `'first_match'` legacy vs `'and'` new), defaulting existing flags to `'first_match'`:** Zero behavioral change for existing flags (addresses Pitfall 4 directly), new flags can opt into `'and'`. Requires schema/migration work (new column on `feature_flags`, `FlagCreate`/`FlagUpdate`/`FlagResponse` schema changes, bootstrap entry field, all 4 evaluators branch on the mode). Larger scope but safest for backward compatibility and matches the phase's explicit "OR and rule groups deferred" framing (suggests the door should stay open for more modes later).
   - Recommendation: Given the phase explicitly defers OR/rule-groups to "a future release," Option C (flag-level mode field, default = legacy first-match, AND = new explicit opt-in) is the lowest-risk path and is consistent with the project's migration-safety conventions (3-step Alembic, additive columns per Phase 13's `test_context` precedent — a single additive nullable column, no 3-step needed since it's a new column not a data restructure). However, Option B (always-AND, drop `result` from evaluation) is simpler if the team is OK with a one-time behavioral change and confirms (per Pitfall 4) that no existing flags have 2+ rules with conflicting `result` values. **This must be resolved via `/gsd:discuss-phase` (CONTEXT.md) before `/gsd:plan-phase` proceeds** — the requirements IDs (AND-01, AND-02, etc.) and task breakdown depend entirely on which option is chosen.

2. **Does "AND rule combination" apply to `rule_based` segment `conditions`, or only to `flag.rules`?**
   - What we know: `backend/app/domains/sdk/service.py::resolve_segment_members` and the `evaluateFlag`/`evaluate_flag` segment-check blocks in sdk-js/sdk-python use `any()`/`.some()` (OR) over `seg.conditions` for segment membership.
   - What's unclear: The phase description says "a flag/segment with multiple rules evaluates true only when ALL individual rules match" — explicitly naming "segment." But changing segment `conditions` from OR to AND changes segment-membership semantics (Phase 8 SEG-02 conditions are "same JSON format as feature flag rules, same evaluation engine").
   - Recommendation: Treat `flag.rules` (AND, per Option from Q1) and `segment.conditions` (keep OR/any-match for membership) as separate, OR explicitly extend AND to segments too if CONTEXT.md confirms. If extended, `resolve_segment_members` (backend) AND the 3 `evaluateFlag`/`evaluate_flag` segment blocks (sdk-js/sdk-python/backend `evaluate_flag` itself doesn't have an inline segment-conditions-AND check today — only `resolve_segment_members` does, called separately to build `segment_members`) all need updating — a 5th-6th file beyond the "4 evaluators."

3. **Complexity filter: use existing `flag.complex` boolean, or derive a new tiered value (rule count / segment count)?**
   - What we know: `flag.complex: boolean` already exists and drives the "Complex"/"Simple" badge in `FlagTable.vue`. The phase description explicitly says "Complexity is not a stored attribute — propose derivation," which contradicts the existing stored field.
   - What's unclear: Whether the phase author was unaware `complex` is already stored, or wants a NEW derived metric (e.g., 0 rules = Simple, 1+ rules = Has Rules, has linked segments = Complex/Advanced) distinct from the manually-set `complex` toggle.
   - Recommendation: Default to using the existing `flag.complex` boolean for the filter (zero new code, consistent with the visible badge). If the user wants rule/segment-count-based tiers, that requires either fetching segment counts per flag (N+1) or adding a computed field to `FlagResponse` (e.g., `has_rules: bool` derived from `len(rules) > 0`, trivial to add in the `parse_text_fields` validator without a migration since `rules` is already loaded).

4. **Scope-target filter: 3 buckets (Products/Tenants/Global per phase wording) or 4 (include Companies, added in Phase 14)?**
   - What we know: `FeatureFlag.scope` is one of `'global'|'tenant'|'product'|'company'` (4 values, Phase 14 added `company`). The phase description for Phase 15 says filter "by scope target — Products, Tenants, or Global" (3 buckets, omitting Companies).
   - What's unclear: Whether `company`-scoped flags should be hidden/excluded from this filter dimension, lumped into one of the 3 named buckets, or the filter should actually have 4 options (Products/Tenants/Companies/Global) and the phase wording is just slightly stale relative to Phase 14's additions.
   - Recommendation: Implement 4 buckets (Products/Tenants/Companies/Global) for full coverage — trivial extra `<option>` and `case` branch, avoids silently hiding company-scoped flags from the filter UI. Flag this as a confirm-with-user item if `/gsd:discuss-phase` is run.

5. **Should `/flags` filters be persisted in the URL query string (shareable/bookmarkable) or purely client-side reactive state (lost on navigation)?**
   - What we know: No existing precedent for URL-synced filters was found in `mui-feature-flags` or `mui-tenants` during this research pass (not exhaustively searched).
   - What's unclear: Whether Vue Router query-param sync is expected.
   - Recommendation: Out of scope unless CONTEXT.md requests it — start with local reactive `ref`s in `FlagsView.vue`; URL sync can be a follow-up.

## Sources

### Primary (HIGH confidence — direct source code reads, this session)
- `backend/app/domains/feature_flags/service.py` — OPERATORS, `_evaluate_rule`, `evaluate_flag` (current first-match-wins, lines 23-102)
- `backend/app/domains/feature_flags/schemas.py` — `RuleSchema`, `FlagCreate`, `FlagUpdate`, `FlagResponse` (lines 1-155)
- `backend/app/domains/feature_flags/router.py` — `GET /flags/` query params (`scope`, `q`), `_get_scope_filter`, `_validate_update_target` (lines 1-130)
- `backend/app/domains/sdk/service.py` — `bootstrap_flags`, `resolve_segment_members` (segment OR-membership, lines 40-114)
- `backend/tests/test_feature_flags_eval.py` — `test_rule_match_returns_rule_result`, `test_no_rule_match_returns_default_val`, `test_all_eight_operators_have_true_case` (lines 100-238) — confirms current first-match semantics
- `sdk/sdk-js/src/evaluator.ts` — `OPERATORS`, `evaluateRule`, `evaluateFlag` (full file, 82 lines)
- `sdk/sdk-python/src/backoffice_sdk/evaluator.py` — `OPERATORS`, `evaluate_rule`, `evaluate_flag` (full file, 85 lines)
- `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` — `OPERATORS`, `evaluateRule`, `useRuleSimulator` first-match loop (full file, 97 lines)
- `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` — Matched Rule panel, Passing/Failing badge (full file, 184 lines)
- `microuis/mui-feature-flags/src/components/flags/RuleCard.vue` — per-rule `result` toggle UI, anyOf comma-input pattern (full file, 228 lines)
- `microuis/mui-feature-flags/src/views/FlagsView.vue` — existing disabled filter-bar scaffold (lines 105-119), page layout
- `microuis/mui-feature-flags/src/stores/flags.ts`, `microuis/mui-feature-flags/src/services/flags.ts` — `FlagFilters`, `FeatureFlag` interfaces, `fetchFlags`
- `microuis/mui-feature-flags/src/components/flags/FlagTable.vue` — current columns, Complexity badge using `flag.complex`
- `.planning/phases/14-flag-scope-targeting-list-valued-rules/14-02-SUMMARY.md`, `14-03-SUMMARY.md`, `14-04-SUMMARY.md`, `deferred-items.md` — Phase 14 anyOf/scope-target/list-value context, 4-evaluator-parity pattern, requirement-ID registration gaps (LST-01/LST-02/TGT-02/TGT-03/CMP-01 not in REQUIREMENTS.md — same gap likely applies to Phase 15's AND-01/AND-02/FLT-* IDs)
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` — phase history, decisions, requirement traceability

### Secondary (MEDIUM confidence)
- None — all findings this session were direct source-code/doc reads (no WebSearch/Context7 needed; this is a closed-stack internal-logic phase).

### Tertiary (LOW confidence)
- Assessment that "no existing flags have 2+ rules with conflicting `result` values" (Pitfall 4) — based on absence of documentation in Phase 12/13/14 docs, NOT a direct DB query (read-only research constraint). Recommend the planner add a verification task to query the dev DB.

## Metadata

**Confidence breakdown:**
- Standard stack / current code paths: HIGH — all 4 evaluator files and supporting schemas/router/store/UI files read directly this session
- Architecture patterns (4-way parity, TDD commits): HIGH — directly evidenced by Phase 14 summaries (anyOf operator landed identically in all 4 files with TDD RED/GREEN commits)
- AND-semantics design resolution (Open Question #1): LOW/UNRESOLVED by design — this is the phase's core open decision, intentionally left for CONTEXT.md/user discussion, not a research gap
- Filter implementation approach: HIGH — existing scaffold + `FlagResponse` fields directly confirm client-side feasibility
- Backward-compat risk for existing flags (Pitfall 4): LOW confidence — no DB access this session, recommend verification task

**Research date:** 2026-06-12
**Valid until:** No external dependency drift expected (internal logic only) — valid until phase 15 plans are written; re-check only if Phase 14's working-tree uncommitted changes (router.py, ws_router.py, sdk.ts, client.ts, useBoFlags.ts, main.ts) are committed/merged before planning, as they could shift line numbers/context slightly (content itself appeared unrelated to evaluator logic).
