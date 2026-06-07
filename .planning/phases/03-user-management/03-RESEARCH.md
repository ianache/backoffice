# Phase 3: User Management - Research

**Researched:** 2026-06-07
**Domain:** Keycloak Admin REST API + FastAPI + Vue 3 user management
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**User Storage**
- Users are created and managed via Keycloak Admin REST API — Keycloak is the source of truth for identity
- No local `users` table; auth is not duplicated in PostgreSQL
- Tenant membership tracked via a Keycloak user attribute (`tenant_id`) set at creation time
- A local `user_events` table (PostgreSQL) stores the audit log only — not user identity data
- Deactivating a user sets `enabled: false` in Keycloak, which immediately blocks login and token refresh

**Keycloak Admin Auth**
- BFF authenticates with Keycloak Admin API using a dedicated service account client with `manage-users` realm role via `client_credentials` grant
- Separate from the user-facing backoffice Keycloak client

**Role Assignment Model**
- Tenant role: one per user, mutually exclusive (TenantOwner / TenantAdmin / TenantViewer) — assigned as Keycloak realm roles
- Product roles: one per product, per user (ProductManager / ProductDeveloper / ProductQA) — modeled as Keycloak realm roles with naming convention `product:{product_id}:{RoleName}`
- Role assignment presented in a single form with two sections: tenant role dropdown at top, then a per-product role dropdown list

**User Table**
- Columns: Name, Email, Tenant Role, Status, Created At, Actions
- Status chip reuses the existing active/suspended pattern from TenantTable
- Actions: edit (opens drawer), activate/deactivate toggle, reset MFA
- Toolbar and filter chips mirror the TenantTable pattern (all / active / inactive filters)
- Density toggle (compact/normal) same as TenantTable

**Navigation & Scoping**
- New nav rail item: People icon + "Users" label at `/users` route
- Role-guarded: visible only to TenantAdmin, TenantOwner
- Tenant context is implicit — TenantAdmin's JWT `tenant_id` attribute determines which users are fetched; no tenant picker shown

**Audit Log**
- Placement: tab inside UserDrawer (third tab: "Activity"), showing chronological event list for that specific user
- Triggered for all user management actions: `user.created`, `user.updated`, `user.enabled`, `user.disabled`, `user.roles_changed`, `user.mfa_reset`
- Each event stores: actor (TenantAdmin's Keycloak `sub`), action, timestamp, context (changed fields or role details)
- Stored in local `user_events` PostgreSQL table

**MFA Reset**
- Calls Keycloak Admin API to remove all OTP/WebAuthn credentials for the user
- User is forced to re-enroll on next login
- Triggers `user.mfa_reset` audit entry
- Does not automatically revoke active sessions

### Claude's Discretion
- Exact Keycloak Admin API client setup details (client name, service account config)
- Backend module structure (mirrors `domains/tenants/` pattern)
- BFF route guard details for TenantAdmin role enforcement
- UserDrawer form field design and validation
- Audit tab visual layout (timeline vs table)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| USER-01 | TenantAdmin puede crear usuarios dentro de su tenant con email y nombre | Keycloak POST /users with `attributes.tenant_id`, `email`, `firstName`, `lastName` |
| USER-02 | TenantAdmin puede asignar roles por tenant y por producto | Keycloak GET /roles/{name} + POST /users/{id}/role-mappings/realm; product role naming `product:{product_id}:{RoleName}` |
| USER-03 | TenantAdmin puede editar datos de usuarios existentes | Keycloak PUT /users/{id} to update email/name/attributes; role delta via DELETE + POST role-mappings |
| USER-04 | TenantAdmin puede activar y desactivar usuarios del tenant | Keycloak PUT /users/{id} with `{ "enabled": false/true }` |
| USER-05 | TenantAdmin puede resetear los dispositivos MFA de un usuario | Keycloak GET /users/{id}/credentials → filter type "otp"/"webauthn-two-factor" → DELETE each |
| USER-06 | Toda acción sobre usuarios genera entrada en audit log | PostgreSQL `user_events` table; backend service writes entry on every mutation |
</phase_requirements>

---

## Summary

Phase 3 adds user management capabilities for the TenantAdmin role. Users live entirely in Keycloak — no PostgreSQL user table. The BFF calls the Keycloak Admin REST API using a service account (client_credentials grant), which requires a dedicated confidential client with `manage-users` and `view-users` client roles assigned from the `realm-management` client. The backend (FastAPI) acts as an orchestration layer: it receives BFF calls, calls Keycloak Admin API, and writes audit entries to the local `user_events` PostgreSQL table.

Filtering users by `tenant_id` uses Keycloak's `q` parameter in the format `q=tenant_id:{value}`. Realm roles follow two patterns: simple tenant roles (TenantOwner, TenantAdmin, TenantViewer) already configured in the realm, and product roles that must be pre-created with the naming convention `product:{product_id}:{RoleName}` (e.g., `product:analytics:ProductManager`). Assigning roles requires knowing the role's UUID (`id`) and `name`, retrieved via GET `/roles/{role-name}` first.

The portal layer closely mirrors the established TenantTable/TenantDrawer/TenantsView pattern. The UserDrawer has three tabs: General (profile), Roles (single form with tenant role dropdown + per-product dropdowns), and Activity (audit log timeline). The Pinia store (`useUsersStore`) follows the same `isLoading/error/async CRUD` pattern as `useTenantsStore`.

**Primary recommendation:** Build the backend `domains/users/` service as the Keycloak Admin API orchestrator, use a singleton token cache in the BFF Keycloak service, and mirror TenantTable/TenantDrawer exactly for the UI layer.

---

## Standard Stack

### Core (no new packages needed for most layers)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Keycloak Admin REST API | Realm-specific | User identity CRUD, role management | Source of truth per architectural decision |
| FastAPI | existing | Backend orchestrator for Keycloak calls + audit log | Already in stack |
| SQLAlchemy async | existing | Audit log persistence | Already in stack |
| Alembic | existing | `user_events` table migration | Already in stack |
| axios (BFF→Backend) | existing | BFF proxies to backend via http-proxy-middleware | Already in stack |
| Pinia | existing | `useUsersStore` state | Already in stack |

### New BFF Dependency (optional but recommended)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| node-fetch / native fetch | Node 18+ built-in | BFF calls Keycloak Admin API directly (no npm package needed) | Service account token acquisition |

**Note:** Do NOT use `@keycloak/keycloak-admin-client` npm package. It adds a heavy dependency and wraps the same REST calls. The existing codebase uses native `fetch`/`axios` directly — stay consistent.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw fetch for Keycloak Admin calls | `@keycloak/keycloak-admin-client` | Library adds 200+ KB, same API calls, inconsistent with existing pattern |
| Backend orchestrating Keycloak | BFF calling Keycloak directly | Backend already handles DB; keeping Keycloak calls in backend avoids dual-layer token management |

**Installation:** No new packages required. All dependencies already present.

---

## Architecture Patterns

### Recommended Project Structure

```
backend/app/domains/users/
├── __init__.py
├── models.py          # UserEvent SQLAlchemy model (audit log only)
├── schemas.py         # Pydantic: UserCreate, UserUpdate, UserResponse, UserEventResponse
├── service.py         # Keycloak Admin calls + audit log writes
└── router.py          # FastAPI routes, registered in main.py

backend/app/services/
└── keycloak_admin.py  # Singleton: token cache + raw HTTP helpers

bff/src/routes/
└── users.ts           # requireAuth + requireRole('TenantAdmin','TenantOwner') + proxy

portal/src/
├── services/users.ts      # axios calls to BFF /users
├── stores/users.ts        # useUsersStore (isLoading, error, CRUD)
├── components/users/
│   ├── UserTable.vue      # mirror of TenantTable.vue
│   ├── UserDrawer.vue     # 3 tabs: General / Roles / Activity
│   ├── UserForm.vue       # email, firstName, lastName fields
│   ├── UserRolesForm.vue  # tenant role dropdown + product role dropdowns
│   └── UserActivityTab.vue # audit log timeline
└── views/UsersView.vue    # page: stats + table + drawer
```

### Pattern 1: BFF Service Account Token Cache

The BFF needs to call the Keycloak Admin API on behalf of operations triggered by user actions. Never fetch a new token per request — cache it and refresh before expiry.

```typescript
// bff/src/services/keycloak-admin.ts
// Source: Keycloak official docs + cbioportal Keycloak API guide

let _adminToken: string | null = null
let _tokenExpiry: number = 0

async function getAdminToken(): Promise<string> {
  const now = Date.now() / 1000
  // Refresh if expires within 30s
  if (_adminToken && _tokenExpiry - now > 30) return _adminToken

  const params = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: config.keycloakAdmin.clientId,
    client_secret: config.keycloakAdmin.clientSecret,
  })
  const res = await fetch(
    `${config.keycloak.url}/realms/${config.keycloak.realm}/protocol/openid-connect/token`,
    { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: params }
  )
  if (!res.ok) throw new Error(`Keycloak admin token failed: ${res.status}`)
  const data = await res.json()
  _adminToken = data.access_token
  _tokenExpiry = now + data.expires_in
  return _adminToken!
}

export async function kcAdminFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = await getAdminToken()
  const base = `${config.keycloak.url}/admin/realms/${config.keycloak.realm}`
  return fetch(`${base}${path}`, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  })
}
```

### Pattern 2: Keycloak Admin API — User Operations

```typescript
// Source: Keycloak Admin REST API official docs https://www.keycloak.org/docs-api/latest/rest-api/

// List users by tenant_id attribute
// q parameter format: "attribute_name:value"
GET /admin/realms/{realm}/users?q=tenant_id:{tenantId}&max=100

// Create user with tenant_id attribute
POST /admin/realms/{realm}/users
Body: {
  "username": "user@email.com",
  "email": "user@email.com",
  "firstName": "First",
  "lastName": "Last",
  "enabled": true,
  "attributes": { "tenant_id": ["{tenantId}"] }
}
// Returns 201 with Location header containing new user ID
// Returns 409 if email/username already exists

// Enable / disable user
PUT /admin/realms/{realm}/users/{userId}
Body: { "enabled": false }

// Get realm roles currently assigned to user
GET /admin/realms/{realm}/users/{userId}/role-mappings/realm

// Assign realm roles (must know role id + name)
POST /admin/realms/{realm}/users/{userId}/role-mappings/realm
Body: [{ "id": "role-uuid", "name": "TenantAdmin" }]

// Remove realm roles
DELETE /admin/realms/{realm}/users/{userId}/role-mappings/realm
Body: [{ "id": "role-uuid", "name": "TenantAdmin" }]

// Get role by name (to retrieve its UUID for assignment)
GET /admin/realms/{realm}/roles/{role-name}

// Get user credentials (OTP, WebAuthn)
GET /admin/realms/{realm}/users/{userId}/credentials
// Returns: [{ "id": "cred-uuid", "type": "otp" | "webauthn-two-factor", ... }]

// Delete a specific credential (MFA reset)
DELETE /admin/realms/{realm}/users/{userId}/credentials/{credentialId}
```

### Pattern 3: Backend `user_events` Audit Model

```python
# backend/app/domains/users/models.py
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import JSON
from app.database import Base
from datetime import datetime

class UserEvent(Base):
    __tablename__ = "user_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    keycloak_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_sub: Mapped[str] = mapped_column(String(36), nullable=False)  # TenantAdmin's Keycloak sub
    action: Mapped[str] = mapped_column(String(50), nullable=False)     # user.created, user.disabled, etc.
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # changed fields, role details
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
```

### Pattern 4: BFF Route (mirrors tenants.ts exactly)

```typescript
// bff/src/routes/users.ts
import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const usersRouter = Router()

usersRouter.use(
  requireAuth,
  requireRole('TenantAdmin', 'TenantOwner'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    pathRewrite: (path) => `/users${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
        // Pass tenant_id from JWT for backend scoping
        const userAttrs = (req as any).user?.attributes ?? {}
        proxyReq.setHeader('X-User-Tenant-Id', userAttrs.tenant_id ?? '')
      },
    },
  })
)
```

**Important:** The auth middleware already extracts `realm_access.roles` but NOT user attributes like `tenant_id`. The `tenant_id` comes from the Keycloak access token claim, not the user object in `req.user`. The backend must either: (a) receive `tenant_id` forwarded by the BFF, or (b) look it up via the Keycloak Admin API using the actor's `sub`. Option (a) is simpler — BFF reads `tenant_id` from the decoded JWT claims.

### Pattern 5: Frontend Service + Store (mirrors tenants.ts / tenants store)

```typescript
// portal/src/services/users.ts
import api from './api'

export interface KcUser {
  id: string            // Keycloak UUID
  username: string
  email: string
  firstName: string
  lastName: string
  enabled: boolean
  attributes: { tenant_id?: string[] }
  createdTimestamp: number
  tenantRole?: string   // derived from realm role mappings
}

export interface UserPayload {
  email: string
  firstName: string
  lastName: string
  tenantRole: string
  productRoles: Record<string, string>  // { productId: roleName | '' }
}

// portal/src/stores/users.ts — same isLoading/error/CRUD pattern as useTenantsStore
```

### Anti-Patterns to Avoid

- **Fetching a new admin token per Keycloak Admin API call:** Token acquisition costs 100-200ms. Cache the token and reuse until 30s before expiry.
- **Passing raw `manage-users` token through the BFF to the frontend:** The service account token is a privileged credential. It must never leave the BFF/backend layer.
- **Storing user identity in PostgreSQL alongside Keycloak:** Keycloak is the source of truth. Only the audit log lives in Postgres.
- **Assigning roles by name only:** Keycloak role assignment requires the role's UUID (`id`) not just the name. Always GET the role first to retrieve its `id`.
- **Using `max=100` without awareness of pagination:** For tenants with many users, the default `max=100` may miss users. Use `first` + `max` pagination or set `max=500` (Keycloak upper limit varies by version).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Admin token acquisition | Custom OAuth2 client_credentials flow | Thin fetch wrapper with module-level cache (see Pattern 1) | Already sufficient; library adds unnecessary weight |
| Keycloak user attribute search | Custom filter in application | `?q=tenant_id:{value}` query parameter | Built into Keycloak Admin API |
| Role UUID lookup | Hardcode role UUIDs | `GET /roles/{role-name}` at runtime | UUIDs differ per Keycloak installation |
| Audit log | Keycloak built-in audit events | Local `user_events` table | Keycloak events have limited retention; local gives full control |
| MFA credential type detection | Guess credential types | `GET /users/{id}/credentials` → filter by `type` | Keycloak returns type with each credential object |

**Key insight:** The Keycloak Admin REST API handles all the complex identity logic. The backend service is primarily an orchestrator + audit logger, not a custom identity store.

---

## Common Pitfalls

### Pitfall 1: tenant_id Scoping Not Enforced on Backend
**What goes wrong:** Backend receives a request from TenantAdmin and queries Keycloak for users without filtering by `tenant_id`, exposing users from other tenants.
**Why it happens:** Forgetting that the BFF's `requireRole` only checks role, not tenant context.
**How to avoid:** Backend MUST always filter Keycloak user queries with `q=tenant_id:{tenant_id}` where `tenant_id` comes from `X-User-Tenant-Id` header (set by BFF from JWT claims). Never trust a `tenant_id` from the request body for listing — use the actor's own tenant.
**Warning signs:** Returning users without an active `tenant_id` filter in the Keycloak query.

### Pitfall 2: Role Assignment Requires Role UUID, Not Just Name
**What goes wrong:** POST to `/role-mappings/realm` with only `{ "name": "TenantAdmin" }` returns 400 Bad Request.
**Why it happens:** Keycloak's role assignment endpoint requires the role representation to include `id` (UUID).
**How to avoid:** Always call `GET /roles/{role-name}` to retrieve the full `RoleRepresentation` (including `id`) before assigning or removing.
**Warning signs:** 400 responses on role-mapping POST with only `name` in body.

### Pitfall 3: Admin Token Not Cached — One Token Per Request
**What goes wrong:** BFF makes a token acquisition call to Keycloak for every user management operation, adding 100-300ms latency.
**Why it happens:** Token acquisition code placed inside request handlers rather than a shared singleton.
**How to avoid:** Use module-level singleton with expiry check (Pattern 1 above).
**Warning signs:** Keycloak token endpoint logs showing tokens acquired with every API request.

### Pitfall 4: `tenant_id` Attribute Stored as Array in Keycloak
**What goes wrong:** Comparing `attributes.tenant_id === "some-id"` fails because Keycloak stores custom attributes as string arrays.
**Why it happens:** Keycloak's UserRepresentation stores `attributes` as `Record<string, string[]>`.
**How to avoid:** Always read as `attributes.tenant_id?.[0]`, write as `{ "tenant_id": ["value"] }`.
**Warning signs:** Attribute comparison returning false even when values match visually.

### Pitfall 5: User Creation Returns 201 with No Body — Extract ID from Location Header
**What goes wrong:** Trying to read the new user's `id` from the response body of `POST /users` fails because the body is empty.
**Why it happens:** Keycloak returns 201 with a `Location` header like `.../users/{userId}`, no body.
**How to avoid:** Parse the `Location` header to extract the new user UUID: `const userId = res.headers.get('location')?.split('/').pop()`.
**Warning signs:** Null/undefined user ID after user creation despite 201 response.

### Pitfall 6: Deactivating a User Does Not Revoke Active Sessions
**What goes wrong:** Setting `enabled: false` on a Keycloak user prevents new logins and token refreshes but does NOT immediately kill active sessions (existing access tokens remain valid until they expire, typically 5 minutes).
**Why it happens:** Keycloak `enabled: false` blocks authentication, not active token validation.
**How to avoid:** This is accepted behavior per CONTEXT.md decision. Document it clearly in the UI (e.g., "User will be unable to log in. Active sessions expire within 5 minutes.").
**Warning signs:** Users reporting they can still access the system immediately after deactivation.

### Pitfall 7: MFA Reset — Only Removes Credentials, Not Required Actions
**What goes wrong:** Deleting OTP credentials doesn't force re-enrollment because the "Configure OTP" required action isn't re-added.
**Why it happens:** Credential deletion and required actions are separate Keycloak concepts.
**How to avoid:** After deleting OTP credentials, optionally call `PUT /users/{id}` with `requiredActions: ["CONFIGURE_TOTP"]` to force re-enrollment on next login. This is a recommended enhancement, not strictly required by the spec.
**Warning signs:** Users not prompted to re-enroll MFA after admin reset.

### Pitfall 8: `q` Parameter Attribute Search Is Case-Sensitive and Partial-Match
**What goes wrong:** `q=tenant_id:Tenant1` doesn't match a user with `tenant_id=tenant1`.
**Why it happens:** Keycloak attribute search is case-sensitive by default.
**How to avoid:** Normalize `tenant_id` values to consistent casing (lowercase UUID or consistent string) at creation time. Store IDs, not display names.
**Warning signs:** Users missing from results despite having the correct tenant_id value.

---

## Code Examples

### Creating a User in Keycloak (Backend Service)
```python
# backend/app/domains/users/service.py
# Source: Keycloak Admin REST API docs https://www.keycloak.org/docs-api/latest/rest-api/

async def create_user_in_keycloak(
    payload: UserCreate,
    tenant_id: str,
    admin_token: str,
    kc_base: str,
    realm: str,
) -> str:
    """Returns new Keycloak user UUID."""
    body = {
        "username": payload.email,
        "email": payload.email,
        "firstName": payload.first_name,
        "lastName": payload.last_name,
        "enabled": True,
        "attributes": {"tenant_id": [tenant_id]},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{kc_base}/admin/realms/{realm}/users",
            json=body,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    if resp.status_code == 409:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    resp.raise_for_status()
    # Extract UUID from Location header
    location = resp.headers.get("location", "")
    user_id = location.rstrip("/").split("/")[-1]
    return user_id
```

### Assigning a Realm Role (Backend Service)
```python
# Source: Keycloak Admin REST API docs

async def assign_realm_role(user_id: str, role_name: str, admin_token: str, kc_base: str, realm: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        # Step 1: Get role representation (need UUID)
        role_resp = await client.get(
            f"{kc_base}/admin/realms/{realm}/roles/{role_name}",
            headers=headers,
        )
        role_resp.raise_for_status()
        role = role_resp.json()  # { "id": "uuid", "name": "TenantAdmin", ... }

        # Step 2: Assign role to user
        assign_resp = await client.post(
            f"{kc_base}/admin/realms/{realm}/users/{user_id}/role-mappings/realm",
            json=[{"id": role["id"], "name": role["name"]}],
            headers={**headers, "Content-Type": "application/json"},
        )
        assign_resp.raise_for_status()
```

### MFA Reset (Backend Service)
```python
# Source: Keycloak Admin REST API docs

async def reset_mfa(user_id: str, admin_token: str, kc_base: str, realm: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with httpx.AsyncClient() as client:
        # Get all credentials
        creds_resp = await client.get(
            f"{kc_base}/admin/realms/{realm}/users/{user_id}/credentials",
            headers=headers,
        )
        creds_resp.raise_for_status()
        credentials = creds_resp.json()  # [{"id": "...", "type": "otp"|"webauthn-two-factor", ...}]

        # Delete all MFA credentials (otp and webauthn)
        mfa_types = {"otp", "webauthn-two-factor"}
        for cred in credentials:
            if cred.get("type") in mfa_types:
                del_resp = await client.delete(
                    f"{kc_base}/admin/realms/{realm}/users/{user_id}/credentials/{cred['id']}",
                    headers=headers,
                )
                del_resp.raise_for_status()
```

### List Users Filtered by Tenant (Backend Service)
```python
# Source: Keycloak Admin REST API docs

async def list_users_by_tenant(tenant_id: str, admin_token: str, kc_base: str, realm: str) -> list:
    headers = {"Authorization": f"Bearer {admin_token}"}
    params = {"q": f"tenant_id:{tenant_id}", "max": 500}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{kc_base}/admin/realms/{realm}/users",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()
```

### Vue Store (mirrors useTenantsStore)
```typescript
// portal/src/stores/users.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as usersService from '../services/users'
import type { KcUser, UserPayload } from '../services/users'

export const useUsersStore = defineStore('users', () => {
  const users = ref<KcUser[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers() {
    isLoading.value = true
    error.value = null
    try {
      users.value = await usersService.list()
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createUser(payload: UserPayload) {
    const created = await usersService.create(payload)
    users.value.unshift(created)
    return created
  }

  async function updateUser(id: string, payload: Partial<UserPayload>) {
    const updated = await usersService.update(id, payload)
    const index = users.value.findIndex(u => u.id === id)
    if (index !== -1) users.value[index] = updated
    return updated
  }

  async function toggleUserStatus(id: string, enabled: boolean) {
    await usersService.setEnabled(id, enabled)
    const user = users.value.find(u => u.id === id)
    if (user) user.enabled = enabled
  }

  async function resetMfa(id: string) {
    await usersService.resetMfa(id)
  }

  return { users, isLoading, error, fetchUsers, createUser, updateUser, toggleUserStatus, resetMfa }
})
```

### Alembic Migration for user_events
```python
# backend/alembic/versions/{hash}_create_user_events_table.py
def upgrade() -> None:
    op.create_table(
        "user_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("keycloak_user_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("actor_sub", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_user_events_keycloak_user_id", "keycloak_user_id"),
        sa.Index("ix_user_events_tenant_id", "tenant_id"),
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Keycloak `/auth/admin/realms/...` URL prefix | `/admin/realms/...` (no `/auth/`) | Keycloak 17+ | URL in BFF/backend must use `/admin/realms/`, not `/auth/admin/realms/` |
| Separate Keycloak Admin username/password | Service account client_credentials | Current best practice | No admin password in env vars; service account has least-privilege roles |
| `@keycloak/keycloak-admin-client` for Node.js | Native fetch + thin wrapper | N/A | Library adds weight; raw fetch is sufficient |

**Deprecated/outdated:**
- `/auth/admin/realms/...` URL pattern: If the Keycloak instance is using the newer URL scheme (Keycloak 17+), the `/auth` prefix was removed. The QA Keycloak at `oauth2.qa.comsatel.com.pe` must be verified — check if it uses `/admin/realms/` or `/auth/admin/realms/` by testing the token endpoint URL pattern. The `.env` currently uses `https://oauth2.qa.comsatel.com.pe` with no `/auth` prefix, suggesting the modern scheme.

---

## Open Questions

1. **What is the exact URL base for Keycloak Admin API on the QA instance?**
   - What we know: BFF `.env` has `KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe` (no `/auth` suffix, suggesting Keycloak 17+)
   - What's unclear: Whether the Admin API is at `https://oauth2.qa.comsatel.com.pe/admin/realms/Apps/...` (Keycloak 17+ standard) or a custom path
   - Recommendation: Verify on first BFF run — a 404 on `/admin/realms/` means try `/auth/admin/realms/`

2. **Does the service account client already exist in the QA Keycloak, or does it need to be created?**
   - What we know: `backoffice-bff` client exists (used for JWT auth). A separate service account client is needed.
   - What's unclear: Whether manual Keycloak setup is needed before BFF code runs
   - Recommendation: Wave 0 task should include "Provision `backoffice-admin-svc` client in QA Keycloak with `manage-users` + `view-users` roles from `realm-management`"

3. **Does the `q=tenant_id:value` filter do exact match or prefix match?**
   - What we know: Format is `q=attribute:value`; multiple verified sources confirm this syntax
   - What's unclear: Whether it's exact match (desired) or prefix match (risky if tenant IDs share prefixes)
   - Recommendation: Use UUIDs or clearly distinct tenant identifiers to avoid prefix collision risk. Test on QA instance first.

4. **Are the realm roles TenantOwner/TenantAdmin/TenantViewer already provisioned in the QA Keycloak realm?**
   - What we know: AUTH-01/02/03 are complete, and the BFF already validates these role names in `APP_ROLES` allowlist
   - What's unclear: Whether roles exist as realm roles in Keycloak (they may only exist as an allowlist concept in the BFF)
   - Recommendation: Wave 0 task should verify roles exist in Keycloak Admin Console; create any missing ones

5. **Does `X-User-Tenant-Id` need to come from a JWT attribute claim or from a separate lookup?**
   - What we know: BFF `auth.ts` extracts `realm_access.roles` but not custom user attributes from the JWT
   - What's unclear: Whether `tenant_id` is included as a claim in the Keycloak access token for `TenantAdmin` users
   - Recommendation: Configure Keycloak to include `tenant_id` attribute as a token claim via a protocol mapper. Alternatively, the backend can look up the actor's tenant_id using the `sub` via Keycloak Admin API, but this adds a round-trip.

---

## Keycloak Admin Client Setup (Claude's Discretion)

Based on research, the recommended setup for the service account client:

**Client settings:**
- Client ID: `backoffice-admin-svc` (separate from `backoffice-bff`)
- Client authentication: ON (confidential)
- Standard flow: OFF
- Direct access grants: OFF
- Service accounts enabled: ON

**Service account roles to assign** (from `realm-management` client):
- `manage-users` — create, update, delete users
- `view-users` — list and read user details
- `view-realm` — needed to query realm roles

**New env vars to add to `bff/.env`:**
```
KEYCLOAK_ADMIN_CLIENT_ID=backoffice-admin-svc
KEYCLOAK_ADMIN_CLIENT_SECRET=<generated-secret>
```

**New config entry in `bff/src/config/index.ts`:**
```typescript
keycloakAdmin: {
  clientId: requireEnv('KEYCLOAK_ADMIN_CLIENT_ID'),
  clientSecret: requireEnv('KEYCLOAK_ADMIN_CLIENT_SECRET'),
}
```

---

## Sources

### Primary (HIGH confidence)
- Keycloak Admin REST API official docs https://www.keycloak.org/docs-api/latest/rest-api/ — user endpoints, role-mappings, credentials, q parameter
- cBioPortal Keycloak API Access guide https://docs.cbioportal.org/deployment/authorization-and-authentication/keycloak-api-access-and-user-creation/ — service account setup, token endpoint, minimum roles
- Existing codebase (direct file reads) — BFF auth/roles middleware, tenants domain pattern, Vue store/service pattern, config structure

### Secondary (MEDIUM confidence)
- https://blog.boottechsolutions.com/2025/04/14/manage-keycloak-using-admin-rest-api/ — client_credentials flow details, create user with attributes body format
- https://howtodoinjava.com/devops/search-keycloak-users/ — `q` parameter `attribute:value` format confirmation
- https://gist.github.com/thomasdarimont/c4e739c5a319cf78a4cff3b87173a84b — RoleRepresentation structure for role assignment

### Tertiary (LOW confidence)
- WebSearch result re: `q` parameter exact vs. prefix match behavior — not officially documented; needs QA instance validation
- MFA credential type names `"otp"` and `"webauthn-two-factor"` — confirmed from multiple sources but should be verified against the QA Keycloak version

---

## Metadata

**Confidence breakdown:**
- Keycloak Admin API endpoints: HIGH — verified against official docs
- Service account setup: HIGH — verified with official docs + cBioPortal guide
- `q` parameter behavior: MEDIUM — syntax confirmed, exact-vs-prefix match behavior needs validation
- Codebase patterns to mirror: HIGH — direct code inspection
- Credential type names for MFA: MEDIUM — multiple sources agree but QA version should be verified

**Research date:** 2026-06-07
**Valid until:** 2026-07-07 (Keycloak API is stable; patterns unlikely to change)
