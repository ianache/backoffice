---
phase: 13-simulator-test-contexts
verified: 2026-06-11T14:05:00Z
status: passed
score: 5/5 must-haves verified
---

# Phase 13: Simulator Test Contexts Verification Report

**Phase Goal:** El "Test Context" del Live Simulator en el Rule Builder deja de ser efímero: (1) al editarlo se puede guardar en base de datos asociado al flag/regla como ejemplo de prueba persistente, recuperado automáticamente al reabrir el editor (sirve para futuros ajustes de la regla); (2) un Toggle "usar mi contexto real" reemplaza el ejemplo por los valores reales de las propiedades del usuario logeado (sub, roles, tenant_id, etc.) para validar la regla contra el caso real, no solo contra ejemplos sintéticos. Aplica tanto al Rule Builder de flags como a la edición de segmentos rule-based (RuleSimulator es compartido).

**Verified:** 2026-06-11T14:05:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A flag/segment can have a `test_context` (raw JSON string) persisted and retrieved via the API | VERIFIED | `backend/alembic/versions/d002_add_test_context.py` adds nullable `test_context TEXT` to `feature_flags` and `segments` (down_revision='d001'); `models.py` lines 26/42 add `test_context: Mapped[Optional[str]]`; `schemas.py` adds `test_context: Optional[str] = None` to `FlagUpdate`, `FlagResponse`, `SegmentCreate`, `SegmentResponse` (lines 42, 61, 96, 107), excluded from `parse_text_fields`/`parse_json_fields` loops (verified — only `rules`/`tags`/`members`/`conditions` touched); `service.py` line 267 `segment.test_context = payload.test_context`; `update_flag()` passes through generic setattr loop. 4 new domain tests pass (`test_flag_response_schema_includes_test_context`, `test_flag_response_test_context_defaults_to_none`, `test_segment_create_schema_accepts_test_context`, `test_update_segment_test_context_assignment_logic`). |
| 2 | Opening Rule Builder/segment editor recovers the saved `test_context`, falling back to synthetic placeholder when null | VERIFIED | `RuleSimulator.vue` line 119: `const contextJson = ref(props.testContext \|\| PLACEHOLDER_CONTEXT)`. `RuleBuilderView.vue` line 199 passes `:test-context="flag?.test_context"`. `SegmentForm.vue` line 235 passes `:test-context="props.segment?.test_context"`, mounted only inside `v-if="form.type === 'rule_based'"` (lines 201-238). |
| 3 | "Save Test Context" button persists current textarea JSON, gated on JSON validity, independent of main Save | VERIFIED | `RuleSimulator.vue` lines 56-63: button `:disabled="!!contextError"`, emits `save-test-context` with `contextJson`. `RuleBuilderView.vue` `handleSaveTestContext()` (lines 73-80) calls `store.updateFlag(flagId.value, { test_context: json })` with toast feedback — separate from `saveChanges()`. `SegmentForm.vue` `handleSaveTestContext()` (lines 122-126) builds full payload via `buildPayload()` + `test_context`, emits `save-test-context`. `SegmentsView.vue` `handleSaveTestContext()` (lines 82-92) calls `updateSegment()` (full-replacement PATCH), reassigns `editingSegment`, does not close form. |
| 4 | "Use my real context" toggle replaces context with real logged-in user attributes (sub, roles, tenant_id, etc.) and live re-evaluates PASSING/FAILING | VERIFIED | `portal/src/stores/auth.ts` line 8/52: `user.sub` populated from `keycloak.tokenParsed?.sub`. `portal/src/composables/useUserContext.ts` returns `{sub, email, roles, tenant_id, product_id}` from live Pinia store. Exposed via `portal/vite.config.ts` (`'./useUserContext'`) and declared in `microuis/mui-feature-flags/src/env.d.ts` (`declare module 'shell/useUserContext'`). `RuleSimulator.vue` lines 125-154: `toggleRealContext()` swaps `contextJson.value` to `JSON.stringify({sub,email,roles,tenant_id,product_id})`, sets `:readonly="useRealContext"`, restores `previousContextJson` on toggle-off. Re-evaluation happens automatically via existing `useRuleSimulator` watchEffect (no new evaluation logic — confirmed unchanged). 2 new regression tests in `useRuleSimulator.test.ts` confirm evaluator handles real-context shape. |
| 5 | RuleSimulator (and Save/Toggle) shared identically across flag Rule Builder and rule-based segment editor; manual segments show no simulator | VERIFIED | `RuleSimulator.vue` is a single shared component with `mode?: 'flag'\|'segment'` prop, used identically by both `RuleBuilderView.vue` (mode="flag") and `SegmentForm.vue` (mode="segment"). `SegmentForm.vue`'s `<RuleSimulator>` mount (line 232) sits inside `<template v-if="form.type === 'rule_based'">` (line 201) — manual-type segments never render it. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/alembic/versions/d002_add_test_context.py` | Adds nullable `test_context TEXT` to `feature_flags`/`segments`, down_revision='d001' | VERIFIED | File exists, parses, `down_revision: Union[str, None] = 'd001'`, upgrade/downgrade correct (segments dropped first on downgrade) |
| `backend/app/domains/feature_flags/models.py` | `test_context` column on `FeatureFlag`/`Segment` | VERIFIED | Lines 26, 42 — `Mapped[Optional[str]]`, `Text`, nullable |
| `backend/app/domains/feature_flags/schemas.py` | `test_context: Optional[str] = None` on 4 schemas | VERIFIED | Lines 42, 61, 96, 107; excluded from parse loops (verified) |
| `backend/app/domains/feature_flags/service.py` | `update_segment()` persists test_context | VERIFIED | Line 267: `segment.test_context = payload.test_context` |
| `portal/src/composables/useUserContext.ts` | `useUserContext()` returns `{sub, email, roles, tenant_id, product_id}` | VERIFIED | Exists, exports `useUserContext`, reads live `useAuthStore()` |
| `portal/src/stores/auth.ts` | `user.sub` populated from JWT | VERIFIED | Line 8 type, line 52 `sub: keycloak.tokenParsed?.sub ?? ''` |
| `portal/vite.config.ts` | exposes `./useUserContext` | VERIFIED | Line 47: `'./useUserContext': './src/composables/useUserContext.ts'` |
| `microuis/mui-feature-flags/src/env.d.ts` | declares `shell/useUserContext` | VERIFIED | `declare module 'shell/useUserContext'` with `UserContext` interface and `useUserContext(): UserContext` |
| `microuis/mui-feature-flags/src/services/flags.ts` | `test_context` on FeatureFlag/FlagPayload/Segment/SegmentPayload | VERIFIED | Lines 26, 47, 63, 76 |
| `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` | props rules/mode/testContext, emits save-test-context, real-context toggle | VERIFIED | Full file read; all elements present and functional |
| `microuis/mui-feature-flags/src/views/RuleBuilderView.vue` | passes test_context, handles save-test-context via updateFlag | VERIFIED | Lines 73-80, 196-201 |
| `microuis/mui-feature-flags/src/components/flags/SegmentForm.vue` | mounts RuleSimulator mode="segment" for rule_based, emits save-test-context with full payload | VERIFIED | Lines 91-126, 232-238 |
| `microuis/mui-feature-flags/src/views/SegmentsView.vue` | handles save-test-context via updateSegment | VERIFIED | Lines 82-92, 144-148 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `service.py update_flag()` | `FeatureFlag.test_context` | generic exclude_unset setattr loop | WIRED | No special-casing needed; `test_context` flows through `payload.model_dump(exclude_unset=True)` + `setattr` |
| `service.py update_segment()` | `Segment.test_context` | explicit field assignment | WIRED | `segment.test_context = payload.test_context` (line 267) |
| `useUserContext.ts` | `auth.ts useAuthStore()` | reads `authStore.user.sub/.email/.roles` | WIRED | Confirmed in composable body |
| `vite.config.ts` exposes | `useUserContext.ts` | federation exposes entry | WIRED | `'./useUserContext': './src/composables/useUserContext.ts'` |
| `RuleSimulator.vue` | `shell/useUserContext` | `import { useUserContext } from 'shell/useUserContext'` | WIRED | Line 93 |
| `RuleSimulator.vue` real-context toggle | `useRuleSimulator.ts` evaluateRule/watchEffect | swaps `contextJson.value` | WIRED | `toggleRealContext()` reassigns `contextJson.value`; passed unchanged to `useRuleSimulator` |
| `RuleSimulator.vue` Save button | parent (`RuleBuilderView`/`SegmentForm`) | `emit('save-test-context', json)` | WIRED | Line 59; both parents handle the emit |
| `RuleBuilderView.vue` | `useFeatureFlagsStore().updateFlag()` | `@save-test-context` handler | WIRED | `handleSaveTestContext()` calls `store.updateFlag(flagId.value, { test_context: json })` |
| `SegmentForm.vue` | `SegmentsView.vue handleSaveTestContext()` | `emit('save-test-context', payload)` | WIRED | Full `SegmentPayload` via `buildPayload()` + `test_context` |
| `SegmentsView.vue handleSaveTestContext()` | `updateSegment(id, payload)` | full-replacement PATCH | WIRED | Reassigns `editingSegment` to response |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SIM-01 | 13-01, 13-04 | Persist test_context to DB associated with flag/segment | SATISFIED | d002 migration + models/schemas/service + UI wiring (RuleBuilderView/SegmentForm save paths) |
| SIM-02 | 13-03, 13-04 | Recover saved test_context automatically on reopen | SATISFIED | `RuleSimulator.vue` initializes `contextJson` from `props.testContext`; both views pass saved value |
| SIM-03 | 13-02, 13-03 | "Use my real context" toggle with logged-in user's real attributes | SATISFIED | `useUserContext` composable + federation + toggle in `RuleSimulator.vue` |
| SIM-04 | 13-04 | Applies to both flag Rule Builder and rule-based segment editing (shared RuleSimulator) | SATISFIED | `SegmentForm.vue` mounts shared `RuleSimulator` mode="segment" inside rule_based-only block; manual segments excluded |

**Traceability gap note:** SIM-01 through SIM-04 do not appear in `.planning/REQUIREMENTS.md`'s traceability table — this is a known, pre-documented gap (`.planning/phases/13-simulator-test-contexts/deferred-items.md`), since Phase 13 was added after the v1.1 requirements list was finalized. The roadmap's Phase 13 "Requirements" line (SIM-01..SIM-04) is treated as the authoritative ID source per verification instructions. No orphaned requirements found beyond this documented gap — all 4 IDs are claimed across the 4 plans and all are satisfied by code.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/domains/feature_flags/service.py` | 210 | `TODO(08-02)` comment | None — pre-existing | Predates Phase 13 (commit `4a79d4f8`, Phase 08); not in scope of this phase's changes |

No blocker or warning anti-patterns found in Phase 13's modified files. `PLACEHOLDER_CONTEXT` in `RuleSimulator.vue` is the intentional, documented synthetic-example fallback (by design, per plan).

### Test Results

- `cd backend && python -m pytest tests/test_feature_flags_domain.py -k "test_context" -v` → 4/4 PASSED (the 4 new Phase 13 tests)
- The remaining 24 tests in `test_feature_flags_domain.py` fail with `ModuleNotFoundError: No module named 'sqlalchemy'` — confirmed **pre-existing environment issue** (global Python 3.14 lacks the project's venv dependencies), reproducible on a pre-existing test (`test_evaluate_rule_equals_match`) unrelated to Phase 13. Not a regression introduced by this phase.
- `cd portal && npx vitest run src/stores/auth.test.ts src/composables/useUserContext.test.ts` → 5/5 PASSED
- `cd microuis/mui-feature-flags && npx vitest run` → 8/8 PASSED (`useRuleSimulator.test.ts`, including 2 new real-context-shape tests)
- `cd microuis/mui-feature-flags && npx vue-tsc --noEmit -p tsconfig.json` → clean, no errors

### Human Verification Required

The following require manual end-to-end testing with a running dev stack (documented in 13-04-PLAN.md verification section, not yet executed):

#### 1. Persistence round-trip in Rule Builder

**Test:** Open Rule Builder for a flag, edit Test Context JSON, click "Save Test Context", reload the page.
**Expected:** Reopened Rule Builder shows the saved JSON (not the synthetic placeholder); a success toast appeared on save.
**Why human:** Requires running dev stack + browser interaction + page reload to confirm DB round-trip and UI recovery.

#### 2. Real-context toggle live re-evaluation

**Test:** In the Live Simulator, toggle "Use my real context" ON.
**Expected:** Textarea becomes read-only and shows `{sub, email, roles, tenant_id, product_id}` of the logged-in user; PASSING/FAILING badge and Matched Rule update live; toggling OFF restores the prior (possibly unsaved) textarea content.
**Why human:** Requires authenticated session with real Keycloak JWT claims and visual confirmation of read-only styling and live badge updates.

#### 3. Segment full-payload save (no field loss)

**Test:** Open a `rule_based` segment, edit Test Context, click "Save Test Context".
**Expected:** `name`/`description`/`conditions`/`members`/`type` are preserved (not wiped) by the full-replacement PATCH; toast confirms; form stays open.
**Why human:** Requires DB state inspection or UI re-check after PATCH to confirm no field-loss regression (Pitfall 1 from RESEARCH.md).

#### 4. Manual segment shows no simulator

**Test:** Open a `manual`-type segment's editor.
**Expected:** No Live Simulator panel is rendered.
**Why human:** Visual confirmation in browser; code structure confirms `v-if="form.type === 'rule_based'"` gating, but a runtime visual check closes the loop.

### Gaps Summary

No gaps found. All 5 derived observable truths are verified against the actual codebase at three levels (exists, substantive, wired). All artifacts from all 4 plans (13-01 through 13-04) exist, are substantive (no stubs/placeholders beyond the intentional synthetic-example constant), and are wired end-to-end: backend persistence (d002 migration, ORM, schemas, service) -> shared RuleSimulator UI (save button, real-context toggle) -> both consuming views (RuleBuilderView for flags, SegmentForm/SegmentsView for rule-based segments). Automated test suites (backend test_context tests, portal auth/useUserContext tests, mui-feature-flags useRuleSimulator tests) all pass; vue-tsc compiles cleanly. The only failing tests (24 in `test_feature_flags_domain.py`) are due to a pre-existing global-Python `sqlalchemy` import environment issue unrelated to and predating Phase 13.

The SIM-01..SIM-04 requirement IDs are absent from `.planning/REQUIREMENTS.md`'s traceability table, but this is a pre-documented, expected gap (Phase 13 was added after v1.1 requirements finalization) and does not block phase completion — the roadmap's own Requirements line is treated as authoritative and all 4 IDs are satisfied by code.

Four items are flagged for human verification — these are end-to-end UI/UX behaviors (persistence round-trip, live re-evaluation, segment field-preservation, manual-segment exclusion) that are structurally verified in code but benefit from a final manual smoke test with a running dev stack, as already documented in 13-04-PLAN.md.

---

*Verified: 2026-06-11T14:05:00Z*
*Verifier: Claude (gsd-verifier)*
