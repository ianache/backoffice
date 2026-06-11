---
phase: 12-dogfooding-feature-flags
plan: 02
subsystem: portal-ui
tags: [vue, ui, gating]

requires: [12-01]
provides:
  - "Gating of Feature Flags and Segments nav items in MainLayout"
  - "Gating of Create Flag button in FlagsView"
  - "Gating of Edit and Clone action buttons in FlagTable"
affects: [12-03]

tech-stack:
  added: []
  patterns:
    - "Direct import of useBoFlags composable in Shell layout and Module Federation import 'shell/boFlags' in remote MUIs"
    - "Template-level v-if bindings on action buttons and menu items mapping to readonly refs"

key-files:
  created: []
  modified:
    - portal/src/components/layout/MainLayout.vue
    - microuis/mui-feature-flags/src/views/FlagsView.vue
    - microuis/mui-feature-flags/src/components/flags/FlagTable.vue

key-decisions:
  - "Hide both Feature Flags and Segments menu options under the single bo.feature flag as Segments belongs to the Feature Flags subdomain"
  - "Promote action in FlagTable remains ungated (always visible) per specification"

requirements-completed: [DOGF-01, DOGF-02, DOGF-03]

duration: 10min
completed: 2026-06-11
---

# Phase 12 Plan 02: UI Gating Summary

Wired the feature flags evaluate refs into the template of the Shell layout and the `mui-feature-flags` remote application views.

## Accomplishments
- Gated the "Feature Flags" and "Segments" buttons in `MainLayout.vue` sidebar menu using `v-if="boFeature"`.
- Gated the "Create Flag" `StitchButton` in `FlagsView.vue` using `v-if="boFeatureCreate"`.
- Gated the "Edit" (pencil) button in `FlagTable.vue` actions column using `v-if="boFeatureUpdate"`.
- Gated the "Clone" (copy) button in `FlagTable.vue` actions column using `v-if="boFeatureCreate"`.
- Removed duplicate declarations of `flagsStore` and `toast` in `FlagsView.vue` script block.
- Built both `@backoffice/portal` and `mui-feature-flags` workspaces to confirm zero compilation or TypeScript errors.
