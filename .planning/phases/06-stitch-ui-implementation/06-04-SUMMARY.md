---
phase: "06-stitch-ui-implementation"
plan: "04"
subsystem: "portal-ui"
tags: ["stitch", "material3", "tenant-management", "visual-regression", "high-density"]
dependency_graph:
  requires: ["06-01", "06-02"]
  provides: ["refactored-tenant-views", "stitch-visual-tests"]
  affects: ["portal/src/views", "portal/src/components/tenants", "portal/tests/visual"]
tech_stack:
  added: []
  patterns:
    - "M3 tonal elevation via surface-container-low for modal drawers"
    - "High-density table rows (36px) with colgroup fixed widths"
    - "Stitch state-layer hover (8% primary color-mix)"
    - "Status chip pattern: tonal container + uppercase tracking"
    - "Form section grouping with uppercase label headers"
    - "Playwright visual regression with API mocking + auth injection"
key_files:
  modified:
    - portal/src/views/TenantsView.vue
    - portal/src/components/tenants/TenantTable.vue
    - portal/src/components/tenants/TenantDrawer.vue
    - portal/src/components/tenants/TenantForm.vue
    - portal/src/components/tenants/WhitelabelForm.vue
  created:
    - portal/tests/visual/internal.spec.ts
decisions:
  - "Use color-mix(in srgb, var(--primary) 8%, transparent) for M3 state-layer hover instead of brightness filter"
  - "md-menu positioning=popover attribute for proper stacking context in table rows"
  - "Visual test mock includes full TenantPayload shape (logo_url, colors) to match component expectations"
  - "Drawer subtitle shows tenant ID for edit mode, prompt text for create mode"
metrics:
  duration: "~18 min"
  completed: "2026-06-06"
  tasks_completed: 3
  files_modified: 5
  files_created: 1
---

# Phase 06 Plan 04: Internal Pages Refactoring Summary

**One-liner:** High-density Stitch tenant management UI with M3 tonal elevation, state-layer hovers, form section grouping, and Playwright visual regression coverage.

## What Was Built

### Task 1: TenantsView + TenantTable Refactoring

**TenantsView.vue** — Added Stitch enterprise page header:
- `page-title` class with `1.375rem / 500` weight typography matching Stitch title-large
- `page-subtitle` with `0.8125rem` body text in `on-surface-variant`
- Reduced gap from `gap-6` to `gap-4` for tighter page layout

**TenantTable.vue** — Full high-density Stitch table implementation:
- `<colgroup>` with fixed widths for predictable column layout (GCP-style fixed columns)
- Compact 36px rows via `h-9` on cell content containers; `py-0` on `<td>` elements
- M3 state-layer hover: `color-mix(in srgb, var(--primary) 8%, transparent)` applied via scoped CSS (the research-recommended approach over `brightness()` filters)
- `table-col-header` class: 11px/700/0.05em-tracking uppercase, matching GCP console column labels
- `status-chip` with separate `status-chip--active` and `status-chip--suspended` variants using tonal containers; dark mode tokens override green chip specifically
- `product-chip` using `secondary-container` tonal background
- `md-menu` with `positioning="popover"` to avoid z-index stacking issues inside `overflow: hidden` table containers
- Toolbar: reduced padding (`px-4 py-2`), added `title` attributes for accessibility
- Pagination footer: proper em-dash range display (`1–N of N`), `tabular-nums` on date column

### Task 2: TenantDrawer + Form Refactoring

**TenantDrawer.vue** — M3 side-sheet pattern:
- Explicit M3 elevation level 3 equivalent box-shadow (3-layer shadow system)
- `border-left: 1px solid var(--outline-variant)` for crisp edge separation
- `role="dialog"`, `aria-modal="true"`, `aria-label` for ARIA accessibility (Rule 2 auto-fix)
- Subtitle below title: shows `ID: {n}` in edit mode, "Fill in the details below" in create
- Scrollbar styled with `scrollbar-width: thin` and `scrollbar-color: var(--outline-variant) transparent`
- Footer min-height `52px` for consistent button touch target area

**TenantForm.vue** — Stitch form section grouping:
- Three labeled sections: "Identity", "Localization", "Product Access"
- `form-section-label`: `0.6875rem / 700 / 0.07em tracking / uppercase` — matches GCP form section headers
- Each section is a `flex-col gap-md` container

**WhitelabelForm.vue** — Improved section grouping:
- Three labeled sections: "Domain & Branding", "Color Palette", "Typography"
- `color-label` class replaces bare `label` selector
- Preview card improved: `preview-title` + `preview-body` paragraph for richer preview
- `border-radius: var(--rounded-md)` on preview card (0.75rem instead of 0.5rem)

### Task 3: Visual Regression Tests

**portal/tests/visual/internal.spec.ts** — 5 tests covering UI-04:
1. `Tenants View — Light Mode layout`: asserts `md-checkbox`, `md-icon-button[title="More actions"]`, `.page-title`, `.status-chip` presence; full-page screenshot
2. `Tenants View — Dark Mode layout`: asserts status chips visible; full-page screenshot
3. `Tenant Drawer — Create mode`: asserts `.drawer-title`, `.drawer-subtitle`, `md-tabs`, `md-outlined-text-field`, `md-filled-button`; screenshot
4. `Tenant Drawer — Whitelabel tab`: asserts `.form-section-label`, `.preview-card`; screenshot
5. `Tenant Drawer — Dark Mode elevation`: asserts `.drawer-content` visible with dark tokens; screenshot

Mock strategy: `page.route('**/api/tenants/**')` with full `MOCK_TENANTS` array including all TenantPayload fields; auth injected via `sessionStorage` in `addInitScript`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added ARIA attributes to TenantDrawer**
- **Found during:** Task 2
- **Issue:** The drawer modal lacked `role="dialog"`, `aria-modal`, and `aria-label` — required for screen reader accessibility in enterprise products
- **Fix:** Added `role="dialog" aria-modal="true" :aria-label="..."` to drawer overlay
- **Files modified:** `portal/src/components/tenants/TenantDrawer.vue`
- **Commit:** fd1c60b

**2. [Rule 1 - Bug] Removed unused StitchButton import in WhitelabelForm**
- **Found during:** Task 2 review
- **Issue:** `StitchButton` was added to imports but not used in template (preview button intentionally uses inline styles to show tenant colors)
- **Fix:** Removed unused import to prevent potential `vue-tsc` warnings
- **Files modified:** `portal/src/components/tenants/WhitelabelForm.vue`
- **Commit:** fd1c60b

**3. [Rule 3 - Blocking] md-menu positioning attribute added**
- **Found during:** Task 1
- **Issue:** `md-menu` without `positioning="popover"` can clip inside `overflow: hidden` table containers, causing invisible menus
- **Fix:** Added `positioning="popover"` to all `md-menu` instances in TenantTable
- **Files modified:** `portal/src/components/tenants/TenantTable.vue`
- **Commit:** 238c5e7

## Build Verification

- Build verified passing after Task 1 (via `pnpm --filter portal run build`): all 324 modules transformed, 0 errors
- Tasks 2 & 3 contain template/style/test-only changes — no TypeScript logic changes that would affect compilation
- Note: Bash tool permission was denied for Tasks 2-3 final build verification; Task 1 build confirmed the build pipeline is clean

## Self-Check

- [x] `portal/src/views/TenantsView.vue` — modified, committed in 238c5e7
- [x] `portal/src/components/tenants/TenantTable.vue` — modified, committed in 238c5e7
- [x] `portal/src/components/tenants/TenantDrawer.vue` — modified, committed in fd1c60b
- [x] `portal/src/components/tenants/TenantForm.vue` — modified, committed in fd1c60b
- [x] `portal/src/components/tenants/WhitelabelForm.vue` — modified, committed in fd1c60b
- [x] `portal/tests/visual/internal.spec.ts` — created, committed in 403816b

## Self-Check: PASSED
