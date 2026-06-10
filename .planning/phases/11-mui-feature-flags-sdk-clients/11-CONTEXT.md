# Phase 11: mui-feature-flags + SDK Clients - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Feature flags, rule builder, live simulator and segments are extracted into a new `mui-feature-flags` micro-UI federated remote (following the Phase 10 mui-tenants/mui-security pattern). Segments UI adds rule-based editing (reusing `RuleCard.vue`) and visual orphan/reference-count indicators. The JS/TS and Python SDK client packages (`sdk/sdk-js`, `sdk/sdk-python`) are created with local evaluation, WebSocket sync, and telemetry batching, per ROADMAP success criteria for Phase 11.

</domain>

<decisions>
## Implementation Decisions

### Segments — Orphan Detection & Reference Counts
- "Used in: X Flags" column in the segments table, matching `design/stitch/segments-management.html` row layout (flag icon + count) — backend already returns this via `SegmentResponse.flag_count` (`GET /flags/segments/`), no backend changes needed
- A "Orphan Segments" bento summary card (matching the Stitch design) shows the count of segments with `flag_count === 0` and a "Review segments" link
- Orphan rows (flag_count === 0) also get an inline visual highlight (e.g. amber "0 Flags" badge) in the table itself
- Clicking "Review segments" applies a client-side filter to the existing SegmentTable to show only orphans (no separate view/route)
- Keep the Stitch design's Type filter (All Types / Manual / Rule-based) on the segments table — useful since rule-based segments are new in v1.1

### Live Simulator
- Restore as an inline panel within the rule builder view (v1.0 pattern) — reuse `RuleSimulator.vue` + `useRuleSimulator.ts` directly, evaluates against the rules currently being edited
- Keep the v1.0 local TypeScript port of the evaluation engine for the simulator (instant feedback on unsaved rules) — do NOT switch to a live `POST /api/v1/sdk/evaluate` call for this purpose
- Keep the JSON context textarea input UX as-is from v1.0 — no saved-context presets

### SDK Scope & Packaging
- New top-level `sdk/` directory: `sdk/sdk-js` and `sdk/sdk-python`
- `sdk/sdk-js` is added to `pnpm-workspace.yaml` as `@backoffice/sdk-js`, following the existing `@backoffice/*` naming convention used by portal/bff/microuis
- `sdk/sdk-python` gets its own `pyproject.toml` (not part of the pnpm workspace)
- Sequencing within this phase: mui-feature-flags + segments orphan UI extraction FIRST (lower risk, follows proven Phase 10 pattern), then SDK-JS, then SDK-Python
- Functional-only for this phase — meet ROADMAP success criteria (`initialize()`, local eval <1ms, WS reconnect with backoff+jitter, telemetry batching) with unit tests. README/versioning/publish-readiness (npm/PyPI) deferred to a later milestone
- Telemetry (`POST /api/v1/sdk/eval-events`) sends a minimal payload per evaluation: `flag_key`, `result`, `timestamp`, anonymous `user_id` — do NOT send full evaluation context (PII risk), matching the Phase 8 `eval_events` schema

### Rule Builder Migration & Operators
- Restyle the rule builder to match `design/stitch/design-builder-feature-flags-rules.html`'s two-column layout: rule editor canvas (left) + inline Rule Simulator (right) — do not just restore v1.0's layout unchanged
- `RuleCard.vue` gets a `mode: 'flag' | 'segment'` prop: in `'segment'` mode the output-value/variant field is hidden (segment rules are boolean match/no-match conditions, not value-returning) — this is the single shared component for both flag rules and rule-based segment conditions (per ROADMAP)
- **NEW**: Add `greaterThan` and `lessThan` numeric comparison operators to the shared evaluation engine, alongside the existing `equals`, `in`, `notIn`, `contains`, `regex`. Motivated by the Stitch segments design's "Power Users (LTV > $500)" example. This touches the evaluation engine in THREE places: `backend/app/domains/feature_flags` (Python evaluator), `sdk/sdk-js` (TS local evaluator), and `sdk/sdk-python` (Python local evaluator) — must stay consistent across all three, plus the rule builder's TS-ported simulator evaluator

### Claude's Discretion
- Exact pnpm preview port assignment for mui-feature-flags (mui-security=5174, mui-tenants=5176 already taken — pick next available, e.g. 5178, and set consistently in vite.config.ts + package.json preview script + portal `.env.example`)
- Internal plan/wave breakdown given "Plans: TBD" — likely needs multiple plans/waves given the size (MUI extraction, segments orphan UI, rule builder restyle, SDK-JS, SDK-Python)
- Exact bento card / badge styling details (colors, spacing) within Stitch token system
- Whether `greaterThan`/`lessThan` need dedicated value-type validation (numeric vs string) in the rule builder UI

</decisions>

<specifics>
## Specific Ideas

- Stitch `segments-management.html`: "Used in: X Flags" column with flag icon, "Orphan Segments" bento card with warning icon + count + "Review segments →" link, Type filter dropdown (All Types / Manual / Rule-based)
- Stitch `design-builder-feature-flags-rules.html`: two-column layout — "Rule Blocks Canvas" (left) + "Rule Simulator" panel (right), rule chips with drag connectors
- Stitch segments example "Power Users (LTV > $500)" as the rule-based segment use case driving the new numeric operators

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets (restorable from git commit `917a4de`, deleted from `portal/` in commit `3e9f83a`)
- `portal/src/views/FlagsView.vue`, `RuleBuilderView.vue`, `SegmentsView.vue`
- `portal/src/components/flags/{ChipTagInput,FlagDrawer,FlagForm,FlagTable,RuleCard,RuleSimulator,SegmentForm,SegmentPicker,SegmentTable}.vue`
- `portal/src/composables/useRuleSimulator.ts` (TS port of the Python evaluation engine — will need extension for `greaterThan`/`lessThan`)
- `portal/src/stores/flags.ts`, `portal/src/services/flags.ts`
- Design refs: `design/stitch/feature-flags.html`, `design/stitch/design-builder-feature-flags-rules.html`, `design/stitch/segments-management.html`

### Established Patterns (from Phase 10 — mui-tenants/mui-security)
- Each MUI is a Vite Module Federation remote exposing `./routes`, registered in `portal/src/router/index.ts` REMOTE_MANIFEST and `portal/.env.example`
- Shared singletons consumed via `shell/*` imports (e.g. `shell/api`, `shell/toastStore`, `shell/StitchButton`) — Vue/Pinia/Router/Axios are federation singletons, never re-instantiated
- Each MUI has its own Pinia store + axios service file calling `shell/api`
- Each MUI has its own `tailwind.config.js` mapping to CSS vars in `portal/src/assets/theme.css` (Tailwind is not federated)
- Preview ports allocated per MUI in both `vite.config.ts` and `package.json` preview script (mui-security=5174, mui-tenants=5176)

### Integration Points
- `backend/app/domains/feature_flags` — flags + segments domain complete (Phase 4, 8); `list_segments()` already returns `(Segment, flag_count)` tuples, router already unpacks into `SegmentResponse.flag_count`
- `backend/app/domains/sdk` — SDK backend complete (Phase 8): bootstrap, evaluate, eval-events, WebSocket
- `bff/src/routes/flags.ts` and `bff/src/routes/sdk.ts` already exist and are registered in `bff/src/index.ts` (sdk.ts has `ws: true` proxy from Phase 10-05)
- `pnpm-workspace.yaml` needs `sdk/*` (or `sdk/sdk-js` explicitly) added for the new `@backoffice/sdk-js` package
- New evaluation operators (`greaterThan`/`lessThan`) need to land in: `backend/app/domains/feature_flags` evaluator, `portal`'s ported TS evaluator (now moving to `mui-feature-flags`), `sdk/sdk-js` local evaluator, `sdk/sdk-python` local evaluator

</code_context>

<deferred>
## Deferred Ideas

- SDK publish-readiness (README usage docs, semver, npm/PyPI publish config) — deferred to a later milestone (v1.2+)
- Saved/named JSON context presets for the Live Simulator — not requested for this phase

</deferred>

---

*Phase: 11-mui-feature-flags-sdk-clients*
*Context gathered: 2026-06-09*
