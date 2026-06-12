---
phase: 14-flag-scope-targeting-list-valued-rules
verified: 2026-06-12T00:30:00Z
status: passed
score: 7/7 must-haves verified
---

# Phase 14: Flag Scope Targeting + List-Valued Rules Verification Report

**Phase Goal:** Combobox de producto/tenant/company según scope del flag (target persistido en backend, enforcement en SDK bootstrap/evaluación) + Rule values como lista separada por coma con match-any para atributos lista (ej. roles), con paridad de operador en backend/sdk-js/sdk-python/useRuleSimulator.

**Verified:** 2026-06-12T00:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A Companies catalog (CMP-01) exists with CRUD API, role/tenant isolation, and is reachable via BFF | ✓ VERIFIED | `backend/app/domains/companies/{models,schemas,service,router}.py` exist, registered in `main.py:7,22`; Alembic `d003` is head and revises `d002`; `bff/src/routes/companies.ts` proxies `/companies` with `X-User-Roles`/`X-User-Tenant-Id`/`X-Internal-Secret`, registered in `bff/src/index.ts:51`. 99 backend tests pass (`test_companies_router.py` 15/15). |
| 2 | Non-global flags require a target at create/update time (TGT-02), and scope changes enforce mutual exclusivity | ✓ VERIFIED | `FlagCreate.validate_scope_target` (schemas.py:30-39) raises on missing tenant/product/company id per scope. `router._validate_update_target` + `_TARGET_FIELD_BY_SCOPE` (router.py:61-101) validate merged PATCH state and null out non-matching target columns on scope change. `TestFlagCreateScopeTargetValidation`/`TestFlagUpdateScopeTargetFields`/`TestValidateUpdateTarget` pass. |
| 3 | SDK bootstrap enforces per-scope target dispatch, including the company-scope gap fix, and entries carry target fields | ✓ VERIFIED | `_flag_matches_target()` (sdk/service.py:8-31) dispatches per scope; company-scope flags with no tenant_id are included; bootstrap entries include `tenant_id`/`product_id`/`company_id` (sdk/service.py:77-80). `TestBootstrapTargetFiltering` passes. |
| 4 | /sdk/evaluate resolves product- and company-scoped flags (no longer starved by tenant-only pre-filter) | ✓ VERIFIED | `sdk/router.py:38` calls `list_flags(db)` unfiltered with explanatory comment; `evaluate_flag()` (untouched, service.py:58-75) does per-scope candidate matching including `company_id`. `TestSdkEvaluateScoping` passes. |
| 5 | `anyOf` operator (8th) has identical list-intersection/scalar-membership semantics across backend OPERATORS, sdk-js, sdk-python, and useRuleSimulator.ts, plus a company-scope guard in both SDK local evaluators | ✓ VERIFIED | `anyOf` lambda present and byte-identical in `backend/app/domains/feature_flags/service.py:31-34`, `sdk/sdk-python/.../evaluator.py:19-22`, `sdk/sdk-js/src/evaluator.ts:19-25`, `useRuleSimulator.ts:26-32`. Company guard present in sdk-js (`evaluator.ts:66-68`) and sdk-python (`evaluator.py:66-68`), `entry.company_id != null` / `is not None` skip logic for legacy entries. All 4 suites green (backend 148, sdk-js 74, sdk-python 70, mui-feature-flags 25). |
| 6 | Rule Builder UI (RuleCard.vue / RuleSimulator.vue) supports anyOf with comma-separated text input, parse-on-blur, and read-only mini-chips in both RuleCard and the Matched Rule panel | ✓ VERIFIED | `RuleCard.vue`: `OPERATORS` includes `'anyOf'` (line 137), `isAnyOfOperator`/`isArrayValueOperator` helpers, `anyOfRaw` ref + `commitAnyOf`/`parseAnyOfInput` on `@blur`/`@keydown.enter`, `.mini-chip` style. `RuleSimulator.vue`: `matchedRule` computed + conditional mini-chips for `operator === 'anyOf'` (lines 78-82, 180). `pnpm build` succeeds. |
| 7 | FlagForm.vue shows per-scope target comboboxes (TGT-01), validates required target, clears on scope switch, and persists exactly one target id with explicit nulls; Companies admin UI (CMP-01) exists at /companies with Shell nav | ✓ VERIFIED | `FlagForm.vue` imports `listProductsLookup/listCompaniesLookup/listTenantsLookup` + `validateFlagTarget/buildTargetFields`; conditional `<select>` blocks for product/tenant/company with "Name (id)"/"Name (#id)" labels and empty-state hints; `watch(scope, ...)` clears all three target refs on scope change. `microuis/mui-tenants/src/{services,stores}/companies.ts`, `views/CompaniesView.vue`, `components/companies/{CompanyTable,CompanyDrawer}.vue` exist; `/companies` route registered with roles `[PlatformAdmin, TenantAdmin, TenantOwner]`; Shell `MainLayout.vue` Companies nav button gated to the 3 roles. `pnpm build` green for mui-feature-flags, mui-tenants, and portal. |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/domains/companies/router.py` | POST/GET/PATCH /companies with role + tenant isolation | ✓ VERIFIED | `_require_companies_role`, `_tenant_filter_for`, `_check_create_tenant` all present and used; 409 on duplicate slug. |
| `backend/alembic/versions/d003_create_companies_table.py` | companies table migration, revision d003 revises d002 | ✓ VERIFIED | `revision='d003'`, `down_revision='d002'`; `alembic heads` → `d003 (head)`. |
| `bff/src/routes/companies.ts` | BFF proxy route, requireAuth-only, forwards identity headers | ✓ VERIFIED | `requireAuth` + proxy forwarding `X-Internal-Secret`, `X-User-Sub`, `X-User-Roles`, `X-User-Tenant-Id`. |
| `backend/tests/test_companies_router.py` | DB-free schema/role/tenant tests | ✓ VERIFIED | 15 tests, all pass. |
| `backend/app/domains/feature_flags/schemas.py` | FlagCreate scope-target validator; FlagUpdate target fields | ✓ VERIFIED | `validate_scope_target` model_validator; FlagUpdate has scope/tenant_id/product_id/company_id, no validator (per design). |
| `backend/app/domains/sdk/service.py` | `_flag_matches_target` + target fields in bootstrap entries | ✓ VERIFIED | Function present (lines 8-31); entries include `tenant_id`/`product_id`/`company_id` (lines 78-80). |
| `backend/app/domains/sdk/router.py` | /sdk/evaluate unfiltered fetch | ✓ VERIFIED | `list_flags(db)` unfiltered with explanatory comment (line 38). |
| `sdk/sdk-js/src/evaluator.ts` | anyOf + company-scope guard | ✓ VERIFIED | `anyOf` in OPERATORS (lines 19-25); guard at lines 66-68. |
| `sdk/sdk-js/src/types.ts` | FlagEntry optional tenant_id/product_id/company_id | ✓ VERIFIED | Optional fields present (lines 29-31). |
| `sdk/sdk-python/src/backoffice_sdk/evaluator.py` | anyOf + company-scope guard | ✓ VERIFIED | `anyOf` (lines 19-22); guard at lines 66-68. |
| `microuis/mui-feature-flags/src/composables/useRuleSimulator.ts` | anyOf in OPERATORS (4th evaluator parity) | ✓ VERIFIED | `anyOf` arrow fn present (lines 26-32), byte-identical to sdk-js. |
| `microuis/mui-feature-flags/src/components/flags/RuleCard.vue` | anyOf dropdown, comma text input, mini-chips | ✓ VERIFIED | All present and wired. |
| `microuis/mui-feature-flags/src/components/flags/RuleSimulator.vue` | Matched Rule mini-chips for anyOf | ✓ VERIFIED | `matchedRule` computed + conditional chips. |
| `microuis/mui-feature-flags/src/services/lookups.ts` | listTenants/Products/CompaniesLookup via shell/api | ✓ VERIFIED | All three exports present, `{items}`-wrapper tolerant. |
| `microuis/mui-feature-flags/src/components/flags/flagFormModel.ts` | validateFlagTarget + buildTargetFields | ✓ VERIFIED | Both pure functions present, 9 unit tests pass. |
| `microuis/mui-feature-flags/src/components/flags/FlagForm.vue` | conditional target comboboxes wired to lookups + validation | ✓ VERIFIED | Imports lookups + flagFormModel + useUserContext; scope watcher, validate(), handleSave() wired. |
| `microuis/mui-tenants/src/views/CompaniesView.vue` | Companies management view | ✓ VERIFIED | Exists, ProductsView pattern. |
| `microuis/mui-tenants/src/components/companies/CompanyDrawer.vue` | Create/Edit drawer with tenant select + 403 fallback | ✓ VERIFIED | Tenant select via `listTenants()`, catch → `useUserContext()` fallback; slug/tenant immutable on edit. |
| `microuis/mui-tenants/src/stores/companies.ts` | Pinia store mirroring stores/products.ts | ✓ VERIFIED | fetch/create/update actions, surfaces 409 detail. |
| `microuis/mui-tenants/src/routes.ts` | /companies route with roles PlatformAdmin/TenantAdmin/TenantOwner | ✓ VERIFIED | Route registered with correct roles meta. |
| `portal/src/components/layout/MainLayout.vue` | Companies nav button (apartment icon) gated by role | ✓ VERIFIED | Nav button present, gated `hasRole('PlatformAdmin') || ... TenantAdmin || ... TenantOwner`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `backend/app/main.py` | `app.domains.companies.router` | `app.include_router(companies_router)` | ✓ WIRED | main.py:7,22 |
| `bff/src/index.ts` | `bff/src/routes/companies.ts` | `app.use('/companies', companiesRouter)` | ✓ WIRED | index.ts:10,51 |
| `backend/alembic/env.py` | `app.domains.companies.models` | model import for metadata registration | ✓ WIRED | env.py:15 |
| `backend/app/domains/feature_flags/router.py` | merged flag+payload state | `_validate_update_target` on PATCH | ✓ WIRED | router.py:61-101, 164-166 |
| `backend/app/domains/sdk/service.py` | bootstrap response entries | `tenant_id`/`product_id`/`company_id` keys | ✓ WIRED | service.py:77-81 |
| `sdk/sdk-js/src/evaluator.ts evaluateFlag` | `FlagEntry.company_id` | scope==='company' guard before rule loop | ✓ WIRED | evaluator.ts:66-68 |
| `backend/tests/test_feature_flags_eval.py` | OPERATORS keys assertion | 8-operator set including anyOf | ✓ WIRED | confirmed via passing test suite |
| `RuleCard.vue anyOf text input` | `rule.value as string[]` | `parseAnyOfInput` on `@blur`/`@change` | ✓ WIRED | RuleCard.vue:64-66, 179-187 |
| `RuleSimulator.vue Matched Rule panel` | `props.rules[matchedIndex].value` | conditional mini-chips when `operator === 'anyOf'` | ✓ WIRED | RuleSimulator.vue:78-82, 180 |
| `FlagForm.vue` | `services/lookups.ts` | fetch on scope selection | ✓ WIRED | FlagForm.vue:4, 104/112/120 |
| `FlagForm.vue handleSave payload` | backend FlagCreate/FlagUpdate target columns | `buildTargetFields` in payload | ✓ WIRED | FlagForm.vue:163-167 |
| `microuis/mui-tenants/src/services/companies.ts` | BFF /companies | `shell/api` axios singleton | ✓ WIRED | confirmed via successful `pnpm build` and service contract match |
| `portal/src/components/layout/MainLayout.vue` | /companies route | `router.push('/companies')` nav button | ✓ WIRED | MainLayout.vue:152 |
| `CompanyDrawer.vue` | `services/tenants.ts` list() + `shell/useUserContext` fallback | tenant select population | ✓ WIRED | CompanyDrawer.vue:4-5, 41-55 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CMP-01 | 14-01, 14-06 | Companies catalog with CRUD UI | ✓ SATISFIED | Backend domain + Alembic + BFF route (14-01); admin UI + nav (14-06) all verified present and wired. |
| TGT-01 | 14-05 | Combobox por scope | ✓ SATISFIED | FlagForm.vue conditional comboboxes per scope, "Name (id)" labels, active-only catalogs. |
| TGT-02 | 14-02, 14-05 | Persistencia del target | ✓ SATISFIED | Backend validators (create+update) + FlagForm `buildTargetFields` payload with explicit nulls. |
| TGT-03 | 14-02, 14-03 | Enforcement en SDK/bootstrap/evaluate | ✓ SATISFIED | `_flag_matches_target` (bootstrap), unfiltered `/sdk/evaluate` fetch, company-scope guard in both SDK local evaluators. |
| LST-01 | 14-04 | Value como lista separada por coma con match-any | ✓ SATISFIED | RuleCard.vue comma-text input, parse-on-blur, mini-chips. |
| LST-02 | 14-03, 14-04 | Paridad del operador en los 4 evaluadores | ✓ SATISFIED | `anyOf` present and tested in backend, sdk-js, sdk-python, useRuleSimulator.ts — all 4 evaluators. |

**Note on REQUIREMENTS.md gap:** None of CMP-01/TGT-01/TGT-02/TGT-03/LST-01/LST-02 are registered as entries in `.planning/REQUIREMENTS.md` (confirmed: grep for these IDs returns no matches). This is a pre-existing planning gap documented in `deferred-items.md` across Plans 14-01, 14-03, and 14-04. It does not block phase goal achievement — all six requirement IDs are fully satisfied in the codebase per the must_haves in the 6 PLAN.md files and the phase CONTEXT.md. Recommend registering these IDs in REQUIREMENTS.md as a follow-up housekeeping item (out of scope for this verification).

No orphaned requirements found beyond the six already covered by the 6 plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | No TODO/FIXME/placeholder/stub patterns found in phase-14 deliverable files. All endpoints return real query results; all UI components render real state (no `return null`/empty-handler stubs in the reviewed files). |

### Human Verification Required

None required for automated pass — all must-haves verified via code inspection, full test suites (backend 148, sdk-js 74, sdk-python 70, mui-feature-flags 25 — all green), and successful builds (mui-feature-flags, mui-tenants, portal, bff).

Optional manual UAT (not blocking, nice-to-have per plan verification sections):
1. **Live create/edit flag with each scope** — Login to mui-feature-flags, create a product-scoped flag without selecting a product → inline validation error appears; select a product → 201 saved with `product_id` set and `tenant_id`/`company_id` null. (14-05 Task 3 already verified this contract against the live backend during execution: 422 without target, 201 with.)
2. **Companies CRUD end-to-end with duplicate slug** — Login as PlatformAdmin/TenantAdmin, create company `acme`, attempt duplicate `acme` → 409 message surfaces in CompanyDrawer.
3. **anyOf rule live simulation** — Add a rule `roles anyOf "PlatformAdmin, TenantOwner"`, run Live Simulator with context `{"roles": ["TenantOwner"]}` → rule matches and Matched Rule panel shows mini-chips.

### Gaps Summary

No gaps found. All 7 observable truths verified, all 20 required artifacts exist/are substantive/are wired, all 13 key links wired, and all 6 requirement IDs (CMP-01, TGT-01, TGT-02, TGT-03, LST-01, LST-02) are satisfied in the codebase despite the pre-existing REQUIREMENTS.md registration gap (documented in deferred-items.md, non-blocking).

Uncommitted working-tree changes (portal/src/main.ts, portal/src/composables/useBoFlags.ts, sdk/sdk-js/src/client.ts + tests, backend/app/domains/feature_flags/router.py segment-removal endpoint, backend/app/domains/sdk/ws_router.py, bff/src/routes/sdk.ts, documentations/) were left untouched as instructed — they belong to a different (later/concurrent) workstream and are unrelated to phase 14's scope-targeting / list-valued-rules deliverables. Full backend suite (148 tests) passes with these changes present, confirming no regression from phase 14's perspective.

---

_Verified: 2026-06-12T00:30:00Z_
_Verifier: Claude (gsd-verifier)_
