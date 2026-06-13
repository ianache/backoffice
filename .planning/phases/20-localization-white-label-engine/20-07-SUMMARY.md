---
phase: 20-localization-white-label-engine
plan: 07
subsystem: ui
tags: [vue, vite, module-federation, tailwind, labeling, namespaces, i18n]

# Dependency graph
requires:
  - phase: 20-05
    provides: "BFF admin proxy bff/src/routes/labels.ts at /labels/* -> backend /api/v1/labels/*"
  - phase: 20-03
    provides: "backend labels_router with namespace/key CRUD + missing-reports diagnostics"
provides:
  - "New mui-labeling micro-UI (Module Federation, Vite, port 5179) mirroring mui-feature-flags structure"
  - "LabelingView.vue 12-column grid shell with header, global search, dark-mode toggle"
  - "WorkspaceContextSelector.vue (RF-01) tenant/company/product context selector"
  - "NamespaceSidebar.vue (RF-02) namespace list + create modal with unique-ID validation"
  - "KeysMatrix.vue (RF-03) key matrix grouped by label_key with search/filter tabs"
  - "useLabelingState.ts shared reactive state composable for cross-component coordination"
  - "services/labels.ts typed API client for /labels/* (namespaces, keys, restore, missing reports)"
  - "Portal WhiteLabels nav entry activated -> /labeling (mui-labeling remote)"
affects: [20-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "mui-labeling scaffolded as structural copy of mui-feature-flags (Module Federation, Vite, Tailwind, shared vue/pinia/vue-router/axios singletons)"
    - "useLabelingState.ts: singleton reactive object exported via a composable function, consumed directly by sibling components (no provide/inject keys needed in practice, but LABELING_STATE_KEY InjectionKey exported for 20-08's TranslationDrawer if it prefers provide/inject)"
    - "Key matrix groups raw per-locale LocalizedLabel rows into one row per label_key client-side (es_PE/en_US columns)"

key-files:
  created:
    - microuis/mui-labeling/package.json
    - microuis/mui-labeling/vite.config.ts
    - microuis/mui-labeling/index.html
    - microuis/mui-labeling/postcss.config.js
    - microuis/mui-labeling/tailwind.config.js
    - microuis/mui-labeling/tsconfig.json
    - microuis/mui-labeling/src/env.d.ts
    - microuis/mui-labeling/src/main.ts
    - microuis/mui-labeling/src/routes.ts
    - microuis/mui-labeling/src/assets/tailwind.css
    - microuis/mui-labeling/src/services/labels.ts
    - microuis/mui-labeling/src/services/lookups.ts
    - microuis/mui-labeling/src/views/LabelingView.vue
    - microuis/mui-labeling/src/components/labeling/WorkspaceContextSelector.vue
    - microuis/mui-labeling/src/components/labeling/NamespaceSidebar.vue
    - microuis/mui-labeling/src/components/labeling/KeysMatrix.vue
    - microuis/mui-labeling/src/composables/useLabelingState.ts
  modified:
    - portal/src/components/layout/MainLayout.vue
    - portal/src/router/index.ts
    - portal/vite.config.ts
    - portal/.env.example
    - pnpm-lock.yaml

key-decisions:
  - "mui-labeling package.json includes @backoffice/sdk-js as workspace:* dependency per plan spec, though not yet imported (reserved for 20-08's live-preview features)"
  - "WorkspaceContextSelector pre-selects the user's own tenant_id and locks the Tenant dropdown for non-PlatformAdmin roles; PlatformAdmin gets the full listTenantsLookup() list"
  - "Company/Product lookups left unfiltered by tenant (LookupOption has no tenant_id field) with a TODO comment for future client-side filtering"
  - "KeysMatrix groups per-locale LocalizedLabel rows into one row per label_key (es_PE/en_US side-by-side columns) to match the prototype's #keysTableBody layout, which the flat backend list response doesn't provide directly"
  - "'+ Agregar Clave' button is wired to a no-op with a console.warn('TODO: 20-08') marker per plan instructions — full Add Key modal deferred to 20-08"
  - "Portal registers mui-labeling remote on port 5179 via VITE_REMOTE_LABELING env var, following the exact REMOTE_MANIFEST/importRemote pattern used for mui-feature-flags"

patterns-established:
  - "New micro-UI scaffolding checklist: package.json (name/preview port/deps) -> vite.config.ts (federation name/port/remotes/exposes/shared) -> index.html/postcss/tailwind/tsconfig copied verbatim -> env.d.ts shell module declarations -> main.ts/routes.ts -> pnpm install at workspace root"

requirements-completed: [LBL-15]

# Metrics
duration: 14min
completed: 2026-06-13
---

# Phase 20 Plan 07: mui-labeling Scaffold + RF-01/02/03 Summary

**New `mui-labeling` Vue/Vite micro-UI on port 5179 (Module Federation) with a 12-column LabelingView grid hosting WorkspaceContextSelector (tenant/company/product context), NamespaceSidebar (namespace list + create modal), and KeysMatrix (searchable/filterable key table), wired to the BFF `/labels/*` API; portal's WhiteLabels nav entry is now active.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-06-13T20:25:35Z
- **Completed:** 2026-06-13T20:35:30Z
- **Tasks:** 3 completed
- **Files modified:** 21 (17 created, 4 modified in portal, plus pnpm-lock.yaml)

## Accomplishments
- Scaffolded `microuis/mui-labeling/` as a structural mirror of `mui-feature-flags`: Module Federation exposing `./routes`, port 5179, shared vue/pinia/vue-router/axios singletons, Tailwind design tokens copied from the shared config
- Added `@backoffice/sdk-js` workspace dependency and ran `pnpm install` at the monorepo root (resolved cleanly, `pnpm-lock.yaml` updated)
- Created `services/labels.ts` with full typed CRUD for namespaces, keys, value-only updates, restore-override, and missing-label reports matching the 20-01/20-02/20-03/20-05 backend contract
- Built `LabelingView.vue` 12-col grid shell with header (global search bound to shared state, dark-mode toggle persisted to `localStorage`), `WorkspaceContextSelector`, `NamespaceSidebar`, `KeysMatrix`, and a `TranslationDrawer` placeholder for 20-08
- `WorkspaceContextSelector.vue` (RF-01): tenant dropdown locked to the logged-in user's `tenant_id` for non-PlatformAdmin roles (via `useUserContext()`), full tenant list for PlatformAdmin via `listTenantsLookup()`; company/product dropdowns populated via lookups
- `NamespaceSidebar.vue` (RF-02): lists namespaces from `GET /labels/namespaces`, auto-selects `common` (or first) namespace on initial load, "+ Namespace" modal with id/strategy/description fields, regex-validated ID (`^[a-z0-9_]{1,100}$`), 409 duplicate-ID handled as inline field error
- `KeysMatrix.vue` (RF-03): groups per-locale `LocalizedLabel` rows into one row per `label_key` (es_PE/en_US columns), filter tabs (Todas/Sobrescritas/Falta traducción), client-side case-insensitive search across key + both locale values, row click sets `selectedKey` shared state
- Activated the portal's previously-disabled "WhiteLabels" nav entry -> `/labeling` route, gated by `PlatformAdmin|TenantAdmin|TenantOwner|ProductManager|UXWriter`, following the exact pattern used for "Feature Flags"
- `npx vue-tsc --noEmit` passes cleanly for both `mui-labeling` and `portal`
- `npm run build` succeeds (remoteEntry.js + routes chunk generated); `npm run preview` serves on port 5179 (verified `/` and `/assets/remoteEntry.js` both return HTTP 200)

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold mui-labeling package (Module Federation, Vite, Tailwind, port 5179)** - `fde65d3` (feat)
2. **Task 2: services/labels.ts + services/lookups.ts API clients** - `8716584` (feat)
3. **Task 3: LabelingView.vue grid shell + WorkspaceContextSelector (RF-01) + NamespaceSidebar (RF-02) + KeysMatrix (RF-03)** - `4f7c41b` (feat)

**Plan metadata:** (pending — final commit below)

## Files Created/Modified
- `microuis/mui-labeling/package.json` - New package manifest (`@backoffice/mui-labeling`, preview port 5179, `@backoffice/sdk-js` workspace dep)
- `microuis/mui-labeling/vite.config.ts` - Module Federation config: `name: 'mui-labeling'`, exposes `./routes`, shared vue/pinia/vue-router/axios
- `microuis/mui-labeling/index.html`, `postcss.config.js`, `tailwind.config.js`, `tsconfig.json`, `src/assets/tailwind.css`, `src/env.d.ts` - Copied/adapted from `mui-feature-flags`
- `microuis/mui-labeling/src/main.ts` - Mounts `LabelingView.vue`
- `microuis/mui-labeling/src/routes.ts` - Registers `/labeling` route, roles `[PlatformAdmin, TenantAdmin, TenantOwner, ProductManager, UXWriter]`
- `microuis/mui-labeling/src/services/labels.ts` - Typed CRUD: `listNamespaces`, `createNamespace`, `updateNamespace`, `deleteNamespace`, `listKeys`, `createKey`, `updateKey`, `updateKeyValue`, `deleteKey`, `restoreOverride`, `listMissingLabels`
- `microuis/mui-labeling/src/services/lookups.ts` - `listProductsLookup`/`listCompaniesLookup`/`listTenantsLookup`, copied from `mui-feature-flags`
- `microuis/mui-labeling/src/composables/useLabelingState.ts` - Shared reactive state singleton: `activeNamespace`, `workspaceContext`, `searchQuery`, `selectedKey`
- `microuis/mui-labeling/src/views/LabelingView.vue` - 12-col grid shell, header (search + dark mode), hosts the three main components
- `microuis/mui-labeling/src/components/labeling/WorkspaceContextSelector.vue` - RF-01 tenant/company/product selectors
- `microuis/mui-labeling/src/components/labeling/NamespaceSidebar.vue` - RF-02 namespace list + create modal
- `microuis/mui-labeling/src/components/labeling/KeysMatrix.vue` - RF-03 key matrix with search/filter
- `portal/src/components/layout/MainLayout.vue` - WhiteLabels nav entry activated, routes to `/labeling`, breadcrumb label added
- `portal/src/router/index.ts` - `mui-labeling` added to `REMOTE_MANIFEST` and `importRemote()` switch
- `portal/vite.config.ts` - `mui-labeling` remote registered (port 5179, `VITE_REMOTE_LABELING`)
- `portal/.env.example` - `VITE_REMOTE_LABELING=http://localhost:5179` documented
- `pnpm-lock.yaml` - Updated for new `@backoffice/mui-labeling` workspace package and `@backoffice/sdk-js` dependency link

## Decisions Made
- `@backoffice/sdk-js` added as a workspace dependency per plan spec but not yet used — reserved for 20-08
- Tenant dropdown is disabled (locked) for non-PlatformAdmin roles, pre-filled with the user's own `tenant_id`; PlatformAdmin sees the full tenant catalog
- Company/Product lookup options are not filtered by tenant client-side (no `tenant_id` on `LookupOption`) — documented as a TODO in `WorkspaceContextSelector.vue`
- KeysMatrix groups the flat per-locale `LocalizedLabel[]` response into per-`label_key` rows with `es_PE`/`en_US` columns — necessary because the backend returns one row per (locale, key) pair but the prototype UI shows one row per key
- "+ Agregar Clave" button is a stub (`console.warn('TODO: 20-08')`) per plan instructions, to be wired by 20-08's Add Key modal

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed invalid `:key` binding referencing non-existent `KeyRow.locale` property**
- **Found during:** Task 3 (`npx vue-tsc --noEmit` verification of KeysMatrix.vue)
- **Issue:** The `v-for` row key used `` `${row.label_key}-${row.locale}` ``, but the `KeyRow` interface (grouped by `label_key`, with separate `es_PE`/`en_US` fields) has no `locale` property — this was a leftover from an earlier per-locale-row mental model and would have caused a TypeScript error.
- **Fix:** Changed the `:key` binding to `row.label_key` (unique per grouped row).
- **Files modified:** `microuis/mui-labeling/src/components/labeling/KeysMatrix.vue`
- **Verification:** `npx vue-tsc --noEmit` passes with zero errors for `mui-labeling`.
- **Committed in:** `4f7c41b` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial type-error fix discovered during the plan's own verification step. No scope creep.

## Issues Encountered

None - `pnpm install` at the workspace root resolved the new `@backoffice/mui-labeling` package and its `@backoffice/sdk-js` workspace dependency without conflicts. Build and preview both succeeded on the first attempt after the type-error fix above.

## User Setup Required

None - no external service configuration required. `VITE_REMOTE_LABELING=http://localhost:5179` was added to both `portal/.env.example` (tracked) and `portal/.env` (local, gitignored) for local dev convenience.

## Next Phase Readiness
- `mui-labeling` builds, type-checks, and previews on port 5179; ready for 20-08 to add the TranslationDrawer (RF-04/05), Add Key/Import-Export/Diagnostics modals (RF-06/07), and finish RF-08 (dark mode is already scaffolded in LabelingView.vue)
- `useLabelingState.ts` exposes `activeNamespace`, `workspaceContext`, `searchQuery`, `selectedKey` for 20-08's TranslationDrawer to consume directly
- The "+ Agregar Clave" button in KeysMatrix.vue has a `console.warn('TODO: 20-08')` marker for 20-08 to locate and wire up
- No blockers identified

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

- FOUND: microuis/mui-labeling/package.json
- FOUND: microuis/mui-labeling/vite.config.ts
- FOUND: microuis/mui-labeling/src/main.ts
- FOUND: microuis/mui-labeling/src/routes.ts
- FOUND: microuis/mui-labeling/src/services/labels.ts
- FOUND: microuis/mui-labeling/src/services/lookups.ts
- FOUND: microuis/mui-labeling/src/views/LabelingView.vue
- FOUND: microuis/mui-labeling/src/components/labeling/WorkspaceContextSelector.vue
- FOUND: microuis/mui-labeling/src/components/labeling/NamespaceSidebar.vue
- FOUND: microuis/mui-labeling/src/components/labeling/KeysMatrix.vue
- FOUND: microuis/mui-labeling/src/composables/useLabelingState.ts
- FOUND: portal/src/components/layout/MainLayout.vue
- FOUND: fde65d3
- FOUND: 8716584
- FOUND: 4f7c41b
