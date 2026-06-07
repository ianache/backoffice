---
phase: 03-user-management
plan: "04"
subsystem: portal-ui
tags: [vue3, pinia, users, access-management, stitch-design, tailwind]
dependency_graph:
  requires:
    - 03-03-SUMMARY.md   # users store + service layer
  provides:
    - portal/src/components/users/UserTable.vue
    - portal/src/components/users/UserForm.vue
    - portal/src/components/users/UserRolesForm.vue
    - portal/src/components/users/UserActivityTab.vue
    - portal/src/components/users/UserDrawer.vue
    - portal/src/views/UsersView.vue
  affects:
    - portal/src/router/index.ts
tech_stack:
  added: []
  patterns:
    - TenantTable toolbar + filter chips + density toggle pattern replicated for users
    - TenantDrawer Teleport + slide-in animation replicated for UserDrawer
    - md-menu positioning="popover" inside overflow:hidden table (Phase 06-04 decision)
    - Radio card role selector with border-primary + bg-primary/5 for selected state
key_files:
  created:
    - portal/src/components/users/UserTable.vue
    - portal/src/components/users/UserForm.vue
    - portal/src/components/users/UserRolesForm.vue
    - portal/src/components/users/UserActivityTab.vue
    - portal/src/components/users/UserDrawer.vue
    - portal/src/views/UsersView.vue
  modified:
    - portal/src/router/index.ts
decisions:
  - Router roles for /users route include PlatformAdmin + TenantAdmin + TenantOwner (permissive for Phase 3; can be tightened later)
  - UserDrawer uses custom tab bar (not md-tabs) to match simpler 3-tab pattern and avoid md-tabs CSS complexity with disabled activity tab
  - UserActivityTab calls usersService.listEvents() directly on mount — not through store (per plan spec: events are per-user transient data)
metrics:
  duration: 5m
  completed_date: "2026-06-07"
  tasks_completed: 2
  files_created: 6
  files_modified: 1
---

# Phase 03 Plan 04: User Management Portal UI Summary

**One-liner:** Portal UI for user access management — UserTable with role badges/status dots, UserDrawer "Manage Access" with 3 tabs, radio-card role selector, activity timeline, and UsersView 12-col grid with Role Insights sidebar.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | UserTable + UserForm + UserRolesForm + UserActivityTab | 1b17d20 | 4 files created under portal/src/components/users/ |
| 2 | UserDrawer + UsersView page | 0002c52 | UserDrawer.vue, UsersView.vue, router/index.ts |

## What Was Built

### UserTable.vue
- Toolbar with "All Members" label and filter chips (all / active / inactive)
- Density toggle (compact / medium) matching TenantTable pattern
- Avatar: initials circle (`bg-secondary-container`) with 2 uppercase letters
- Role badge: colored pill — `bg-primary/10 text-primary` for Tenant Owner/Admin, `bg-secondary/10 text-secondary` for Product roles, neutral for Viewer/null
- Status indicator: colored dot (`bg-green-500` / `bg-neutral-400`) + text label
- Actions: edit icon button + context menu (`md-menu positioning="popover"`) for disable/enable/reset-mfa

### UserForm.vue
- Three StitchTextField fields: email (type="email"), firstName, lastName
- v-model pattern with computed setter emitting update:modelValue

### UserRolesForm.vue
- Section 1: radio cards for TenantOwner / TenantAdmin / TenantViewer with `border-2 border-primary bg-primary/5` on selected
- Section 2: product role dropdowns (analytics, platform as defaults) with options No role / ProductManager / ProductDeveloper / ProductQA

### UserActivityTab.vue
- Calls `usersService.listEvents(userId)` directly on mount (newest first)
- Vertical timeline with colored dot per action type (green/amber/red/blue)
- Action label mapping, formatted timestamps, context key-value pairs

### UserDrawer.vue
- 440px side-sheet titled "Manage Access"
- Custom tab bar: General / Roles / Activity (Activity disabled when creating new user)
- Activity tab only mounts UserActivityTab when `show && user && activeTab === 'activity'`
- Teleport + slide-in animation matching TenantDrawer pattern
- Footer: Cancel (text) + Save Changes / Invite Member (filled)

### UsersView.vue
- Page title: "Access Management" + subtitle
- Stats badges: N Active + N Pending in page header
- Tab bar: Members (active) | Roles (disabled) | API Keys (disabled)
- 12-column grid: UserTable (lg:col-span-8) + Role Insights sidebar (lg:col-span-4)
- Role Insights sidebar: static cards for TenantOwner / TenantAdmin / TenantViewer definitions
- Wired to useUsersStore(), UserDrawer, ConfirmDialog (reused from tenants)

### Router
- Added `/users` route: lazy import UsersView, requiresAuth, roles: [PlatformAdmin, TenantAdmin, TenantOwner]

## Deviations from Plan

### Auto-added: Router route
- **Found during:** Task 2 (plan did not explicitly list router update in files_modified)
- **Issue:** Without a router entry, /users page is unreachable
- **Fix:** Added /users route to portal/src/router/index.ts
- **Files modified:** portal/src/router/index.ts
- **Commit:** 0002c52

### Implementation choice: Custom tab bar vs md-tabs in UserDrawer
- **Decision:** Used custom CSS tab bar instead of md-tabs web component
- **Reason:** Activity tab needs disabled state when user=null; md-tabs disabled attribute not consistent across MDWC versions; custom bar matches the simpler pattern and avoids CSS var overrides
- **Impact:** Visually equivalent, slightly lighter markup

## Self-Check

- [x] portal/src/components/users/UserTable.vue — exists
- [x] portal/src/components/users/UserForm.vue — exists
- [x] portal/src/components/users/UserRolesForm.vue — exists
- [x] portal/src/components/users/UserActivityTab.vue — exists
- [x] portal/src/components/users/UserDrawer.vue — exists
- [x] portal/src/views/UsersView.vue — exists
- [x] Commit 1b17d20 — Task 1 (4 components)
- [x] Commit 0002c52 — Task 2 (drawer + view + router)
- [x] TypeScript: zero errors across all 6 new files (vue-tsc --noEmit clean)
