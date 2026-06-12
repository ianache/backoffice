---
phase: 14-flag-scope-targeting-list-valued-rules
plan: 06
subsystem: ui
tags: [vue, pinia, vite-federation, mui-tenants, companies, tenant-isolation]

# Dependency graph
requires:
  - phase: 14-flag-scope-targeting-list-valued-rules
    provides: "Companies backend (models/schemas/service/router) and BFF /companies route from Plan 14-01"
provides:
  - "Companies admin UI at /companies in mui-tenants (CompaniesView + CompanyTable + CompanyDrawer)"
  - "companies Pinia store + companies service mirroring the products pattern"
  - "Shell Companies nav button (apartment icon) gated to PlatformAdmin/TenantAdmin/TenantOwner"
affects: [14-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Companies CRUD UI mirrors Products pattern 1:1 (service/store/view/table/drawer) with tenant_id added and labels/description dropped"
    - "Tenant select with role-based fallback: PlatformAdmin gets full tenants.list(), TenantAdmin/TenantOwner catch 403 and fall back to useUserContext().tenant_id as a single locked option"

key-files:
  created:
    - microuis/mui-tenants/src/services/companies.ts
    - microuis/mui-tenants/src/stores/companies.ts
    - microuis/mui-tenants/src/views/CompaniesView.vue
    - microuis/mui-tenants/src/components/companies/CompanyTable.vue
    - microuis/mui-tenants/src/components/companies/CompanyDrawer.vue
  modified:
    - microuis/mui-tenants/src/routes.ts
    - microuis/mui-tenants/src/env.d.ts
    - portal/src/components/layout/MainLayout.vue

key-decisions:
  - "companies store create/update wrap service calls in try/catch and store err.response?.data?.detail (409 duplicate slug message) into error state, re-throwing so the view's toast also fires"
  - "CompanyDrawer accepts an optional error prop and renders it inline below the form (form-error style) in addition to the view's toast on catch"
  - "Tenant select pre-selects and locks to the fallback tenant_id in create mode when tenants.list() throws (403); in edit mode the select is always disabled showing the stored tenant_id"

patterns-established:
  - "shell/useUserContext declare-module block copied verbatim into mui-tenants/src/env.d.ts (previously only in mui-feature-flags) for cross-remote tenant fallback"

requirements-completed: [CMP-01]

# Metrics
duration: 13min
completed: 2026-06-12
---

# Phase 14 Plan 06: Companies Admin UI Summary

**Companies CRUD UI (list/create/edit, slug-immutable, tenant-scoped) at /companies in mui-tenants, mirroring the Products pattern with a role-aware tenant select and Shell nav entry**

## Performance

- **Duration:** 13 min
- **Started:** 2026-06-12T00:06:42Z
- **Completed:** 2026-06-12T00:19:47Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Companies service + Pinia store added to mui-tenants, mirroring services/stores/products.ts (Company has tenant_id instead of description/labels; id and tenant_id immutable on update)
- CompaniesView + CompanyTable + CompanyDrawer built against the Plan 14-01 backend: table shows Id/Name/Tenant/Status/Created/Updated with active/all/inactive filter; drawer supports create/edit with slug-immutable-on-edit and a tenant select that loads from tenants.ts (PlatformAdmin) or falls back to the user's own tenant (TenantAdmin/TenantOwner, 403 caught)
- /companies registered as a route in mui-tenants (roles PlatformAdmin/TenantAdmin/TenantOwner) and a Companies nav button (apartment icon) added to the Shell MainLayout right after Products, gated to the same three roles

## Task Commits

Each task was committed atomically:

1. **Task 1: companies service + Pinia store** - `0d70dbc` (feat)
2. **Task 2: CompaniesView + CompanyTable + CompanyDrawer (tenant select with 403 fallback)** - `2676077` (feat)
3. **Task 3: /companies route + Shell nav button** - `045c406` (feat)

**Plan metadata:** pending (this commit)

## Files Created/Modified
- `microuis/mui-tenants/src/services/companies.ts` - Company/CompanyPayload/CompanyUpdatePayload types + listCompanies/createCompany/updateCompany against BFF /companies/
- `microuis/mui-tenants/src/stores/companies.ts` - Pinia store (companies, isLoading, error) with fetch/create/update actions, surfaces 409 detail into error
- `microuis/mui-tenants/src/views/CompaniesView.vue` - Company Management header, table + drawer wiring, recent-changes sidebar (mirrors ProductsView)
- `microuis/mui-tenants/src/components/companies/CompanyTable.vue` - Id/Name/Tenant/Status/Created/Updated table with all/active/inactive filter and edit action
- `microuis/mui-tenants/src/components/companies/CompanyDrawer.vue` - Create/edit drawer: slug immutable on edit, tenant select (tenants.ts list or useUserContext fallback), client-side validation, inline 409 error display
- `microuis/mui-tenants/src/routes.ts` - /companies route registered (roles PlatformAdmin/TenantAdmin/TenantOwner)
- `microuis/mui-tenants/src/env.d.ts` - added shell/useUserContext declare-module block
- `portal/src/components/layout/MainLayout.vue` - Companies nav button (apartment icon) after Products, gated to PlatformAdmin/TenantAdmin/TenantOwner

## Decisions Made
- companies store's createCompany/updateCompany catch errors, set `error.value = err.response?.data?.detail || err.message` (capturing the backend's 409 duplicate-slug detail message), then re-throw so the existing toast-based error pattern in the view continues to work
- CompanyDrawer takes an `error` prop (bound to `companiesStore.error`) and renders it in a `.form-error` block below the form fields, in addition to the toast shown by CompaniesView's handleSave catch
- In create mode, when the tenant select falls back (403 from tenants.list()), the single fallback option (`My tenant (#<tenant_id>)`) is pre-selected and the select is disabled; in edit mode the select is always disabled showing the company's stored tenant_id

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- CMP-01 complete: Companies catalog is manageable end-to-end (create/edit, active/inactive, tenant isolation) and is now available as a source for the company-scoped flag-target combobox built in Plan 14-05 (parallel executor)
- `cd microuis/mui-tenants && pnpm build` and `cd portal && pnpm build` (with vue-tsc) both pass green
- Manual verification (login as PlatformAdmin, create/edit companies, duplicate-slug 409, tenant fallback for TenantAdmin/TenantOwner) deferred to integration testing with the dev stack running

---
*Phase: 14-flag-scope-targeting-list-valued-rules*
*Completed: 2026-06-12*
