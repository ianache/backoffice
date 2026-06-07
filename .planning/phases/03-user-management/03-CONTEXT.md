# Phase 3: User Management - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning

<domain>
## Phase Boundary

TenantAdmin can manage users within their own tenant — create, assign roles, activate/deactivate, reset MFA devices, and audit all actions. PlatformAdmin is out of scope. Multi-tenant scoping is enforced by the TenantAdmin's auth context (their `tenant_id` Keycloak attribute), not a tenant picker UI. Client management and company-level users are future phases.

</domain>

<decisions>
## Implementation Decisions

### User Storage
- Users are created and managed via **Keycloak Admin REST API** — Keycloak is the source of truth for identity
- No local `users` table; auth is not duplicated in PostgreSQL
- Tenant membership tracked via a **Keycloak user attribute** (`tenant_id`) set at creation time
- A local **`user_events` table** (PostgreSQL) stores the audit log only — not user identity data
- Deactivating a user sets `enabled: false` in Keycloak, which immediately blocks login and token refresh

### Keycloak Admin Auth
- BFF authenticates with Keycloak Admin API using a **dedicated service account client** with `manage-users` realm role via `client_credentials` grant
- Separate from the user-facing backoffice Keycloak client

### Role Assignment Model
- **Tenant role:** one per user, mutually exclusive (TenantOwner / TenantAdmin / TenantViewer) — assigned as Keycloak realm roles
- **Product roles:** one per product, per user (ProductManager / ProductDeveloper / ProductQA) — modeled as Keycloak realm roles with naming convention `product:{product_id}:{RoleName}`
- Role assignment uses **radio cards** (bordered cards with radio input, not dropdowns) — one card per role with name + description, selected card highlighted with `border-primary bg-primary/5`
- The drawer panel is titled **"Manage Access"** (not "Edit User") following the Stitch design reference

### User Table
- Page title: **"Access Management"** with subtitle "Control user access and granular permissions across your tenant environment"
- Columns: User (avatar + name + email), Role (colored badge), Status (dot indicator), Actions (edit icon button)
- Avatar: initials circle (`w-10 h-10 rounded-full`) using first 2 letters of name when no photo
- Role badge: colored inline pill — primary tint for TenantAdmin, secondary tint for ProductManager, neutral for Viewer
- Status: colored dot + label (green=Active, amber=Pending, grey=Inactive)
- Header shows active/pending counts as badges: "12 Active", "2 Pending"
- Primary CTA: "Invite Member" button (`person_add` icon + primary)
- Tab navigation: **Members** | Roles | API Keys (implement Members tab only in Phase 3)
- Filter chips follow TenantTable pattern (all / active / inactive)

### Navigation & Scoping
- New nav rail item: **People icon + "Users" label** at `/users` route
- Role-guarded: visible only to TenantAdmin, TenantOwner (not PlatformAdmin, who manages tenants not users)
- Tenant context is **implicit** — TenantAdmin's JWT `tenant_id` attribute determines which users are fetched; no tenant picker shown

### Audit Log
- Placement: **tab inside UserDrawer** (third tab: "Activity"), showing chronological event list for that specific user
- Triggered for all user management actions: `user.created`, `user.updated`, `user.enabled`, `user.disabled`, `user.roles_changed`, `user.mfa_reset`
- Each event stores: actor (TenantAdmin's Keycloak `sub`), action, timestamp, context (changed fields or role details)
- Stored in local `user_events` PostgreSQL table

### MFA Reset
- Calls Keycloak Admin API to **remove all OTP/WebAuthn credentials** for the user
- User is forced to re-enroll on next login
- Triggers `user.mfa_reset` audit entry
- Does not automatically revoke active sessions (user finishes current session, re-enrolls on next login)

### Claude's Discretion
- Exact Keycloak Admin API client setup details (client name, service account config)
- Backend module structure (mirrors `domains/tenants/` pattern)
- BFF route guard details for TenantAdmin role enforcement
- UserDrawer form field design and validation
- Audit tab visual layout (timeline vs table)

</decisions>

<specifics>
## Specific Ideas

**Stitch design reference:** `design/stitch/permission-user-roles.html`

Key patterns to follow from the design:
- Page title "Access Management" + subtitle on the left, "Invite Member" primary button on the right
- Tab bar: Members | Roles | API Keys — Members tab active, others placeholder for future phases
- **12-column grid layout:** member table takes 8 cols, role insights sidebar takes 4 cols
- **Role sidebar panel:** "Role Insights" card shows role definitions, each as a hoverable card
- **Drawer "Manage Access":** 440px wide, contains "Assignment Scope" segmented toggle + radio cards for roles + "Summary of Permissions" preview section
- Radio card pattern for role selection: `border-2 border-primary bg-primary/5` for selected, `border border-outline-variant` for unselected — each card shows role name + description
- **"Summary of Permissions"** section in the drawer (below role cards): shows what the selected role can do with `check_circle` icons — static list per role
- Avatar: `w-10 h-10 rounded-full bg-secondary-container` with 2-letter initials when no photo
- The existing TenantTable component (toolbar + filter chips + density toggle + `md-menu` actions) remains the structural reference, but visuals adapt to the Stitch Roles & Permissions design

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TenantTable.vue` (portal/src/components/tenants/TenantTable.vue): Full data table with toolbar, filter chips, density toggle, status chip, `md-menu` actions — direct template for UserTable
- `TenantDrawer.vue` (portal/src/components/tenants/TenantDrawer.vue): Side-sheet drawer with `md-tabs`, scrollable body, footer actions — direct template for UserDrawer
- `ConfirmDialog.vue`: Reusable confirm modal for destructive actions (disable, delete)
- `StitchButton.vue`, `StitchTextField.vue`: Established UI components — use in UserForm
- `useTenantsStore` pattern (portal/src/stores/tenants.ts): Pinia store with `isLoading`, `error`, async CRUD — mirror for `useUsersStore`
- `status-chip` CSS classes (active/suspended, light/dark variants): Reuse for user active/inactive status

### Established Patterns
- BFF proxy: `requireAuth` + `requireRole(...)` middleware, then `createProxyMiddleware` to backend — new `/users` route follows this pattern, with `requireRole('TenantAdmin')` guard
- Backend domain module: `models.py` + `schemas.py` + `service.py` + `router.py` under `app/domains/` — create `app/domains/users/` following the same structure
- Auth store: `roles` array from `keycloak.realmAccess?.roles` — existing `hasRole()` function used for route guards
- Alembic migrations: existing versions in `backend/alembic/versions/` — add migration for `user_events` table

### Integration Points
- **Nav rail** (`portal/src/components/layout/MainLayout.vue`): Add Users nav item here, role-guarded
- **Vue Router** (`portal/src/router/`): Add `/users` route, guarded by TenantAdmin role
- **BFF** (`bff/src/routes/`): Add `users.ts` route, proxy to backend with `requireRole('TenantAdmin')`
- **Backend** (`backend/app/main.py`): Register new `users` router
- **Keycloak Admin**: BFF needs new env vars for service account credentials (`KEYCLOAK_ADMIN_CLIENT_ID`, `KEYCLOAK_ADMIN_CLIENT_SECRET`)

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-user-management*
*Context gathered: 2026-06-07*
