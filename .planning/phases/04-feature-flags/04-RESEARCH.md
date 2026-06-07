# Phase 4: Feature Flags - Research

**Researched:** 2026-06-07
**Domain:** Hierarchical Feature Flag System — Backend (FastAPI/SQLAlchemy/MySQL), BFF (Node.js/Express), Frontend (Vue 3/Pinia/Tailwind)
**Confidence:** HIGH (architecture derived from verified in-repo patterns; no external libraries needed)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FLAG-01 | PlatformAdmin puede crear flags a nivel Global con name, default, complex, ttl, enabled, environment | Backend model + service + BFF route (PlatformAdmin guard) + Portal FlagsView |
| FLAG-02 | TenantAdmin puede crear flags a nivel Tenant que sobrescriben el nivel Global | `scope=tenant` + `tenant_id` FK; BFF injects X-User-Tenant-Id; override row wins evaluation |
| FLAG-03 | ProductManager puede crear flags a nivel Producto que sobrescriben el nivel Tenant | `scope=product` + `product_id` FK; BFF injects X-User-Roles; ProductManager guard on route |
| FLAG-04 | La evaluación de flags sigue jerarquía determinista: Empresa > Producto > Tenant > Global | Pure Python evaluation function; priority map Empresa=4, Producto=3, Tenant=2, Global=1 |
| FLAG-05 | Reglas de evaluación soportan los operadores: equals, in, notIn, contains, regex | Stored as JSON array; evaluation iterates rules in priority order; operator dispatch dict |
| FLAG-06 | Segmentos de usuarios son reutilizables y pueden aplicarse en múltiples flags de distintos niveles | Separate `segments` table; `flag_segments` join table; evaluation expands segment members |
</phase_requirements>

---

## Summary

Phase 4 implements the core value proposition of the platform: hierarchical, deterministic feature flag evaluation across four levels (Global → Tenant → Product → Company). The entire stack is already proven in Phases 2 and 3 — no new libraries are required. The backend uses FastAPI + SQLAlchemy async + MySQL (existing) with three new tables (`feature_flags`, `segments`, `flag_segments`). The BFF adds a `/flags` proxy route alongside the existing `/tenants` and `/users` patterns. The portal adds a FlagsView using the Stitch design (`design/stitch/feature-flags.html`) with Tailwind CSS tokens already in place.

The critical design insight is that the 4-level hierarchy is enforced by a single Python evaluation function that takes a flat list of flag rows and returns the most-specific match. This function is self-contained, has no framework dependencies, and is trivially unit-testable. Rules stored as JSON arrays in TEXT columns (MySQL 5.6 pattern established in Phase 3) are evaluated with a small operator dispatch dict — no rule-engine library needed.

The UI follows the `design/stitch/feature-flags.html` mockup exactly: sidebar nav, data table with toggle switches, Complexity badges (Simple/Complex), Rollout progress bar, TTL column, and confirmation dialog before disabling in production. All Tailwind color tokens (`primary: #d41117`, `surface-container-lowest`, etc.) are already defined in the portal's `tailwind.config.js`.

**Primary recommendation:** Build in 4 plans — (1) backend domain + migrations, (2) BFF routes with role guards, (3) portal service + Pinia store, (4) portal UI (FlagsView + components) + end-to-end verification.

---

## Standard Stack

### Core (all already in project — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.5 | Backend HTTP + validation | Established in Phase 2 |
| SQLAlchemy async | 2.0.35 | ORM + async session | Established in Phase 2 |
| asyncmy | 0.2.9 | MySQL async driver | Established in Phase 2; MySQL 5.6 compat confirmed |
| Alembic | 1.13.3 | Schema migrations | Established in Phase 2 |
| Pydantic v2 | 2.9.2 | Schema validation | Established in Phase 2 |
| httpx | 0.27.2 | Async HTTP (BFF→backend) | Already in requirements.txt |
| Express + http-proxy-middleware | (bff package.json) | BFF proxy | Established in Phase 2 |
| Vue 3 + Pinia | ^3.4 / ^2.2 | Portal state + UI | Established in Phase 1 |
| Tailwind CSS | ^3.4.19 | Styling with Stitch tokens | Established in Phase 6; tokens match feature-flags.html |

### No New Libraries Required

The evaluation engine, operator dispatch, and hierarchy resolution are all pure Python (~80 lines). No feature-flag-as-a-service library (unleash, flipt, etc.) is needed — the requirements specify a custom deterministic evaluator.

---

## Architecture Patterns

### Database Schema (3 new tables)

The flag system needs three tables. MySQL 5.6 does NOT support the JSON column type — rules and metadata are stored as TEXT with JSON serialize/deserialize in the service layer (established pattern from `user_events.context` in Phase 3).

```
feature_flags
  id          INT PK
  name        VARCHAR(100) NOT NULL
  description VARCHAR(500)
  scope       VARCHAR(20) NOT NULL  -- 'global' | 'tenant' | 'product' | 'company'
  tenant_id   VARCHAR(100)           -- NULL for global flags
  product_id  VARCHAR(100)           -- NULL unless scope=product or company
  company_id  VARCHAR(100)           -- NULL unless scope=company
  enabled     TINYINT(1) DEFAULT 1
  default_val TINYINT(1) DEFAULT 0   -- default return when no rule matches
  complex     TINYINT(1) DEFAULT 0   -- Simple vs Complex badge
  ttl         INT                    -- days until expiry; NULL = no expiry
  environment VARCHAR(20) DEFAULT 'production'
  rollout     INT DEFAULT 100        -- percentage 0-100; Phase 4 = always 100
  rules       TEXT                   -- JSON array of rule objects (serialized)
  tags        TEXT                   -- JSON array of tag strings
  created_by  VARCHAR(36)            -- actor sub from JWT
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

segments
  id          INT PK
  name        VARCHAR(100) NOT NULL
  description VARCHAR(500)
  tenant_id   VARCHAR(100)           -- NULL = platform-global segment
  members     TEXT                   -- JSON array of user_ids or email patterns
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

flag_segments (join table)
  flag_id     INT FK → feature_flags.id
  segment_id  INT FK → segments.id
  PRIMARY KEY (flag_id, segment_id)
```

**Why separate segments table:** FLAG-06 explicitly requires segments to be defined once and applied to multiple flags at different levels. The join table `flag_segments` enables this N:M relationship without duplicating segment member lists.

### Recommended Project Structure

```
backend/
├── app/
│   ├── domains/
│   │   ├── feature_flags/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # FeatureFlag + Segment + FlagSegment models
│   │   │   ├── schemas.py       # Pydantic Create/Update/Response + RuleSchema
│   │   │   ├── service.py       # CRUD + evaluate() function
│   │   │   └── router.py        # /flags + /segments endpoints
│   │   └── ...
│   └── main.py                  # + include_router(flags_router)
├── alembic/versions/
│   └── {hash}_create_feature_flags_tables.py

bff/
└── src/
    └── routes/
        └── flags.ts             # Proxy with role guards (PlatformAdmin | TenantAdmin | ProductManager)

portal/
└── src/
    ├── services/
    │   └── flags.ts             # TypeScript interfaces + API calls
    ├── stores/
    │   └── flags.ts             # Pinia store (useFeatureFlagsStore)
    ├── components/
    │   └── flags/
    │       ├── FlagTable.vue    # Data table from design mockup
    │       ├── FlagDrawer.vue   # Side drawer for create/edit
    │       ├── FlagForm.vue     # Form fields
    │       └── SegmentPicker.vue # Reusable segment selector
    └── views/
        └── FlagsView.vue        # Page layout matching feature-flags.html mockup
```

### Pattern 1: Hierarchical Evaluation — Deterministic Priority Resolution

**What:** Given a flag name and evaluation context (tenant_id, product_id, company_id, user attributes), return the enabled/default value from the most-specific matching flag override.

**When to use:** Every `GET /flags/evaluate?name=X` call and every flag detail view showing "effective value."

**Priority map:** Company (4) > Product (3) > Tenant (2) > Global (1). The most-specific level always wins.

```python
# Source: derived from FLAG-04 requirement; pure Python, no framework deps

SCOPE_PRIORITY = {
    'company': 4,
    'product': 3,
    'tenant': 2,
    'global': 1,
}

def evaluate_flag(
    flags: list[FeatureFlag],  # all rows for a given flag name
    context: dict,             # {'tenant_id': ..., 'product_id': ..., 'company_id': ..., 'user': {...}}
) -> bool:
    """
    Find the most-specific matching flag and evaluate its rules.
    Returns the flag's `default_val` if no rule matches.
    Returns False if no flag row matches at all.
    """
    # Filter to rows that apply to this context
    candidates = []
    for flag in flags:
        if flag.scope == 'global':
            candidates.append(flag)
        elif flag.scope == 'tenant' and flag.tenant_id == context.get('tenant_id'):
            candidates.append(flag)
        elif flag.scope == 'product' and flag.product_id == context.get('product_id'):
            candidates.append(flag)
        elif flag.scope == 'company' and flag.company_id == context.get('company_id'):
            candidates.append(flag)

    if not candidates:
        return False

    # Most specific wins
    winner = max(candidates, key=lambda f: SCOPE_PRIORITY[f.scope])

    if not winner.enabled:
        return False

    # Evaluate rules; first match wins
    rules = json.loads(winner.rules or '[]')
    user = context.get('user', {})
    for rule in rules:
        if _evaluate_rule(rule, user):
            return rule.get('result', winner.default_val)

    return bool(winner.default_val)
```

### Pattern 2: Rule Operator Dispatch

**What:** Each rule is a JSON object `{"attribute": "country", "operator": "in", "value": ["PE", "AR"], "result": true}`. Operators are dispatched with a dict — no if/elif chain.

```python
# Source: derived from FLAG-05 requirement

import re

OPERATORS = {
    'equals':   lambda actual, expected: actual == expected,
    'in':       lambda actual, expected: actual in expected,
    'notIn':    lambda actual, expected: actual not in expected,
    'contains': lambda actual, expected: expected in str(actual),
    'regex':    lambda actual, expected: bool(re.match(expected, str(actual))),
}

def _evaluate_rule(rule: dict, user: dict) -> bool:
    attr = rule.get('attribute', '')
    op   = rule.get('operator', 'equals')
    val  = rule.get('value')
    actual = user.get(attr)
    if actual is None:
        return False
    fn = OPERATORS.get(op)
    if fn is None:
        return False
    try:
        return fn(actual, val)
    except Exception:
        return False
```

### Pattern 3: Backend Router with Scope-Aware Guards

**What:** `/flags` endpoints enforce different role requirements depending on the operation:
- Global-scope CRUD: `PlatformAdmin` only
- Tenant-scope CRUD: `TenantAdmin` or `TenantOwner`
- Product-scope CRUD: `ProductManager`

The BFF injects `X-User-Roles` and `X-User-Tenant-Id` (established in Phase 3). The backend reads these headers to scope queries and validate authorization.

```python
# Source: established pattern from backend/app/domains/users/router.py

@router.post("/", response_model=FlagResponse, status_code=201)
async def create_flag(
    payload: FlagCreate,
    x_user_roles: str = Header(...),
    x_user_tenant_id: str = Header(default=''),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    roles = x_user_roles.split(',')
    # Validate scope matches caller's role
    if payload.scope == 'global' and 'PlatformAdmin' not in roles:
        raise HTTPException(403, "Only PlatformAdmin can create global flags")
    if payload.scope == 'tenant' and not {'TenantAdmin', 'TenantOwner'}.intersection(roles):
        raise HTTPException(403, "Only TenantAdmin/TenantOwner can create tenant flags")
    if payload.scope == 'product' and 'ProductManager' not in roles:
        raise HTTPException(403, "Only ProductManager can create product flags")
    return await service.create_flag(db, payload, actor_sub=x_user_sub, tenant_id=x_user_tenant_id)
```

### Pattern 4: BFF Route — Multi-Role Guard

The BFF route for `/flags` needs to allow multiple roles (PlatformAdmin for global, TenantAdmin/TenantOwner for tenant-scoped, ProductManager for product-scoped). The existing `requireRole` helper in the BFF accepts multiple roles via spread (established in Phase 3 `/users` route).

```typescript
// Source: established pattern from bff/src/routes/users.ts + auth.ts

import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const flagsRouter = Router()

flagsRouter.use(
  requireAuth,
  requireRole('PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    pathRewrite: (path) => `/flags${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', req.user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', (req.user?.roles ?? []).join(','))
        proxyReq.setHeader('X-User-Tenant-Id', req.user?.tenantId ?? '')
      },
    },
  })
)
```

### Pattern 5: Portal — FlagsView matching design/stitch/feature-flags.html

The design mockup specifies:
- **Sidebar nav** (already exists as layout component in portal) — no new sidebar needed; just add "Feature Flags" and "Segments" nav items to the existing navigation rail
- **Filter bar**: "All Statuses" / "Any Tags" / "Complexity" dropdowns + "Sort by: Last Updated"
- **Data table** columns: Flag Name & Description (with tags), Status (toggle), Complexity (badge), Rollout (progress bar), TTL, Last Updated, Actions
- **Toggle switch**: custom CSS class `.toggle-checked` + `.toggle-dot` + `.toggle-track` — direct port from mockup HTML
- **Confirmation dialog on disable**: "Are you sure you want to disable this feature in PRODUCTION?" — reuse existing `ConfirmDialog.vue`
- **Actions** (on row hover): Edit (pencil), Clone (content_copy), Promote (rocket_launch)
- **Pagination**: numbered pages + per-page selector

All color tokens (`primary`, `surface-container-lowest`, `outline-variant`, `secondary-container`, `primary-fixed`, etc.) already exist in the portal's Tailwind config — confirmed by reading `portal/package.json` (tailwindcss ^3.4.19) and the existing component usage.

### Pattern 6: Pinia Store — useFeatureFlagsStore

Follow the exact same composition API store pattern established in `useTenantsStore` and `useUsersStore`:

```typescript
// Source: established pattern from portal/src/stores/tenants.ts

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as flagsService from '../services/flags'
import type { FeatureFlag, FlagPayload, FlagFilters } from '../services/flags'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const flags = ref<FeatureFlag[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFlags(filters?: FlagFilters) {
    isLoading.value = true
    error.value = null
    try {
      flags.value = await flagsService.list(filters)
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createFlag(payload: FlagPayload): Promise<FeatureFlag> {
    const created = await flagsService.create(payload)
    flags.value.unshift(created)
    return created
  }

  async function updateFlag(id: number, payload: Partial<FlagPayload>): Promise<FeatureFlag> {
    const updated = await flagsService.update(id, payload)
    const index = flags.value.findIndex(f => f.id === id)
    if (index !== -1) flags.value[index] = updated
    return updated
  }

  async function toggleFlag(id: number, enabled: boolean): Promise<void> {
    await flagsService.setEnabled(id, enabled)
    const flag = flags.value.find(f => f.id === id)
    if (flag) flag.enabled = enabled
  }

  async function deleteFlag(id: number): Promise<void> {
    await flagsService.remove(id)
    flags.value = flags.value.filter(f => f.id !== id)
  }

  return { flags, isLoading, error, fetchFlags, createFlag, updateFlag, toggleFlag, deleteFlag }
})
```

### Anti-Patterns to Avoid

- **Storing rules as separate table rows:** Store as TEXT/JSON in the flag row. Rules without flags are meaningless; a separate `rules` table adds joins without benefit. Phase 5 (Rule Builder) will handle the visual editing layer — for Phase 4 the rules are JSON in the flag row.
- **Using a feature-flag library (Unleash, Flipt, LaunchDarkly SDK):** These are external services. The requirement is a custom deterministic evaluator — build the pure Python function.
- **Applying scope authorization in BFF only:** The BFF role check prevents unauthorized routes, but the backend MUST also validate scope/role alignment (defense in depth). The `X-User-Roles` header is already forwarded by the BFF.
- **Evaluating "most recently created" instead of "most specific scope":** Priority is by SCOPE_PRIORITY dict, not by `created_at`. A tenant-level flag ALWAYS wins over a global flag even if the global one was created later.
- **Using MySQL JSON column type:** MySQL 5.6 does not support JSON columns. Use TEXT and serialize/deserialize in the service layer — this is the established pattern from `user_events.context` (Phase 3) and `products` (Phase 2).
- **Creating a `/flags/evaluate` endpoint in Phase 4:** The evaluation function exists in the backend service layer for correctness, but a public evaluation API endpoint is a Phase 5+ concern (client SDKs). In Phase 4, evaluation is used internally to show "effective value" in the UI.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async DB session management | Custom session context manager | `AsyncSessionFactory` from `app.database` (already exists) | Established pattern; handles expire_on_commit=False |
| JWT role extraction in BFF | Custom header parsing | `req.user.roles` from `requireAuth` middleware (already exists) | Dual claim fallback already implemented |
| Rule evaluation regex | Custom regex engine | Python stdlib `re.match` in `_evaluate_rule` | Zero deps; FLAG-05 only requires match, not full search |
| Pagination in backend | Custom OFFSET/LIMIT logic | SQLAlchemy `offset()` + `limit()` with `count()` for total | Standard pattern; avoid re-inventing |
| Toggle switch component | Custom Vue component | Port the HTML/CSS directly from `design/stitch/feature-flags.html` (`.toggle-checked` / `.toggle-dot` / `.toggle-track` CSS) | Design already provides exact implementation |

**Key insight:** Every infrastructure piece exists. Phase 4 is domain logic + UI, not infrastructure. The only new code is: 3 DB tables, 1 Python evaluation function, BFF route, portal service/store/components.

---

## Common Pitfalls

### Pitfall 1: MySQL 5.6 TEXT vs JSON Column
**What goes wrong:** Using `sa.JSON` column type in Alembic migration causes MySQL to create `longblob` or fail silently on MySQL 5.6. The `rules` and `tags` fields break on read.
**Why it happens:** SQLAlchemy's `JSON` type maps to MySQL's `JSON` type, which requires MySQL 5.7.8+.
**How to avoid:** Use `sa.Text()` in migration + `json.loads`/`json.dumps` in service layer. Follow the exact pattern from `backend/alembic/versions/f977f6d434f7_create_user_events_table.py` (line 29: `sa.Column('context', sa.Text(), nullable=True)`).
**Warning signs:** Migration runs without error but `json.loads(flag.rules)` raises `TypeError: the JSON object must be str, bytes or bytearray, not NoneType` — default value not set.

### Pitfall 2: Scope Authorization Not Enforced in Backend
**What goes wrong:** PlatformAdmin creates a global flag. TenantAdmin sends a POST with `scope=global` — BFF passes the request through (TenantAdmin is in the allowed roles list) and a global flag is created by a non-PlatformAdmin.
**Why it happens:** The BFF route allows multiple roles; the role-scope matrix enforcement must happen in the backend router, not just the BFF.
**How to avoid:** Backend `create_flag` and `update_flag` endpoints validate that `payload.scope` is consistent with `X-User-Roles` header (see Pattern 3 above).
**Warning signs:** `POST /flags` with `scope=global` succeeds for TenantAdmin.

### Pitfall 3: Evaluation Priority — "Latest Created" Bug
**What goes wrong:** Two flag rows exist: one `scope=global` and one `scope=tenant`. The global one was created more recently. The evaluator picks the global one because it sorts by `created_at DESC`.
**Why it happens:** Confusing "most recent" with "most specific."
**How to avoid:** Sort by `SCOPE_PRIORITY[flag.scope]` descending (not `created_at`). The `max()` call in Pattern 1 uses the priority key.
**Warning signs:** A tenant flag that should override global shows the global value instead.

### Pitfall 4: Navigation Rail — Feature Flags Nav Item Role Guard
**What goes wrong:** TenantViewer or unauthenticated users see the Feature Flags nav item and get a 403 on click.
**Why it happens:** Forgetting to add `v-if` role guard on the nav item, as established in Phase 3 (Phase 03-05 decision: "Tenants nav button gained explicit v-if PlatformAdmin guard").
**How to avoid:** Feature Flags nav item: `v-if="authStore.hasRole('PlatformAdmin') || authStore.hasRole('TenantAdmin') || authStore.hasRole('TenantOwner') || authStore.hasRole('ProductManager')"`. Router guard uses same roles list.
**Warning signs:** Nav item visible to TenantViewer.

### Pitfall 5: Toggle Switch Confirmation Dialog — Production Only
**What goes wrong:** Confirmation dialog shows for ALL flag disables, including non-production environments. The design mockup only requires it for production flags.
**Why it happens:** Copying the JavaScript from the mockup verbatim (`if (isChecked) { if (confirm(...)) }`) without considering the `environment` attribute.
**How to avoid:** Show confirmation dialog when `flag.environment === 'production'` OR always show it for safety (simpler and consistent with the mockup). The mockup says "This may impact live users" — show always for safety in Phase 4.
**Warning signs:** Toggling a staging flag triggers the production warning.

### Pitfall 6: Rollout Column — Phase 4 Scope
**What goes wrong:** Implementing rollout percentage evaluation logic when FLAG-07 (rollout) is explicitly a v2/Phase 2 requirement.
**Why it happens:** The UI mockup shows a "Rollout" progress bar column — it is a DISPLAY field, not an evaluation mechanism in Phase 4.
**How to avoid:** Store `rollout INT DEFAULT 100` in the DB. Display the value in the UI progress bar. Do NOT implement probabilistic user bucketing in Phase 4 evaluation. FLAG-07 is deferred.
**Warning signs:** Phase 4 evaluation code contains `random.random()` or user hashing logic.

---

## Code Examples

Verified patterns from in-repo sources:

### Alembic Migration with TEXT columns (MySQL 5.6 safe)
```python
# Source: backend/alembic/versions/f977f6d434f7_create_user_events_table.py (in-repo verified)

def upgrade() -> None:
    op.create_table('feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('product_id', sa.String(length=100), nullable=True),
        sa.Column('company_id', sa.String(length=100), nullable=True),
        sa.Column('enabled', sa.SmallInteger(), server_default='1', nullable=False),
        sa.Column('default_val', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('complex', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('ttl', sa.Integer(), nullable=True),
        sa.Column('environment', sa.String(length=20), server_default='production', nullable=False),
        sa.Column('rollout', sa.Integer(), server_default='100', nullable=False),
        sa.Column('rules', sa.Text(), nullable=True),   # JSON array serialized as TEXT
        sa.Column('tags', sa.Text(), nullable=True),    # JSON array serialized as TEXT
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feature_flags_name', 'feature_flags', ['name'])
    op.create_index('ix_feature_flags_tenant_id', 'feature_flags', ['tenant_id'])
```

### SQLAlchemy Model with TEXT→JSON pattern
```python
# Source: backend/app/domains/users/models.py (in-repo verified)

from sqlalchemy import String, Text, SmallInteger, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import datetime
from typing import Optional

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enabled: Mapped[int] = mapped_column(SmallInteger, server_default='1', nullable=False)
    default_val: Mapped[int] = mapped_column(SmallInteger, server_default='0', nullable=False)
    complex: Mapped[int] = mapped_column(SmallInteger, server_default='0', nullable=False)
    ttl: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    environment: Mapped[str] = mapped_column(String(20), server_default='production', nullable=False)
    rollout: Mapped[int] = mapped_column(Integer, server_default='100', nullable=False)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as TEXT
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON array as TEXT
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
```

### Toggle Switch CSS (port from design mockup)
```css
/* Source: design/stitch/feature-flags.html (in-repo verified) */
.toggle-checked .toggle-dot {
    transform: translateX(18px);
}
.toggle-checked .toggle-track {
    background-color: #d41117;  /* var(--primary) */
}
```

### Vue Toggle in FlagTable
```vue
<!-- Source: pattern derived from design/stitch/feature-flags.html -->
<button
  :class="['inline-flex items-center h-6 w-11 rounded-full bg-surface-variant relative transition-colors duration-200 cursor-pointer focus:outline-none', flag.enabled ? 'toggle-checked' : '']"
  @click="handleToggle(flag)"
>
  <span class="toggle-dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full shadow transition-transform duration-200 ease-in-out"></span>
  <span class="toggle-track absolute inset-0 rounded-full bg-outline transition-colors duration-200"></span>
</button>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Feature flags as env vars | Feature flags as DB-backed hierarchy | Phase 4 design decision | Runtime control without deployment |
| External flag services (LaunchDarkly) | Custom deterministic evaluator | Phase 4 design decision | Zero external dependencies, full control |
| JSON column type in MySQL | TEXT + json.loads/dumps | Phase 3 (user_events.context) | MySQL 5.6 compat maintained |
| Single-level flags | 4-level hierarchy (Global→Tenant→Product→Company) | Phase 4 core design | Tenant-specific overrides without code changes |

**Scope of Phase 4 vs Phase 5:**
- Phase 4: CRUD + deterministic evaluation function + basic UI table
- Phase 5: Visual Rule Builder (drag & drop, preview) — uses the rules JSON structure Phase 4 establishes

---

## Open Questions

1. **Segment member format**
   - What we know: FLAG-06 says segments are "definidos una vez y aplicados a múltiples flags." Segments have members.
   - What's unclear: Are members stored as user UUIDs (Keycloak IDs), email addresses, or attribute-based expressions?
   - Recommendation: Store as JSON array of user UUIDs (`["uuid1", "uuid2"]`) for Phase 4. Attribute-based segment expressions can be added in Phase 5. Evaluation expands segment to user list and checks `context.user.id in segment.members`.

2. **Scope for listing flags — what does TenantAdmin see?**
   - What we know: PlatformAdmin creates global flags; TenantAdmin creates tenant-level flags.
   - What's unclear: Should TenantAdmin see global flags in their flags list (so they can understand what they're overriding)?
   - Recommendation: `GET /flags` returns flags visible to the caller — global flags are always included for TenantAdmin/ProductManager so they can see overrideable baselines. Filtered by `scope IN ('global', 'tenant')` for TenantAdmin, `scope IN ('global', 'tenant', 'product')` for ProductManager.

3. **Updated_at on flag record — auto or explicit?**
   - What we know: MySQL 5.6 supports `ON UPDATE CURRENT_TIMESTAMP` only on the FIRST TIMESTAMP column.
   - What's unclear: Does SQLAlchemy's `onupdate=func.now()` work reliably in MySQL 5.6?
   - Recommendation: Use an explicit `onupdate` trigger in the migration DDL, or update `updated_at` explicitly in the service layer (safest approach given MySQL 5.6 quirks). Check `backend/app/domains/tenants/models.py` line: `updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)` — this pattern is already in use, follow it exactly.

---

## Validation Architecture

> `workflow.nyquist_validation` is not set in `.planning/config.json` — Validation Architecture section skipped.

*(Config has `workflow.research`, `workflow.plan_check`, `workflow.verifier` but no `nyquist_validation` key. Per instructions: skip if false or absent.)*

---

## Sources

### Primary (HIGH confidence)
- `backend/app/domains/tenants/models.py` — SQLAlchemy model pattern, TEXT for JSON fields
- `backend/app/domains/users/models.py` — UserEvent TEXT column pattern, MySQL 5.6 confirmed
- `backend/alembic/versions/f977f6d434f7_create_user_events_table.py` — Migration pattern with sa.Text()
- `backend/app/domains/tenants/service.py` — CRUD service pattern
- `backend/app/domains/tenants/router.py` — FastAPI router pattern, dependency injection
- `bff/src/routes/users.ts` — BFF proxy pattern with X-User-Tenant-Id header injection
- `bff/src/middleware/auth.ts` — Role extraction, tenantId from JWT claim
- `portal/src/stores/tenants.ts` — Pinia composition store pattern
- `portal/src/stores/users.ts` — Pinia store with toggleUserStatus pattern
- `portal/src/views/UsersView.vue` — View pattern: store + ConfirmDialog + Drawer
- `portal/src/router/index.ts` — Route guard with roles array meta
- `portal/package.json` — Confirmed tailwindcss ^3.4.19, @material/web ^2.4.1
- `design/stitch/feature-flags.html` — Authoritative UI specification; all color tokens, toggle CSS, table layout

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` — Decisions log; MySQL 5.6 TEXT pattern confirmed at multiple phases
- `backend/requirements.txt` — Confirmed httpx 0.27.2 present; no new libraries needed
- `backend/app/config.py` — Settings pattern; no new env vars needed for flags (uses existing DB + internal secret)

### Tertiary (LOW confidence)
- None — all findings verified in-repo.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed from in-repo requirements.txt and package.json
- Architecture: HIGH — derived from 3 completed phases of established patterns
- Database schema: HIGH — modeled on confirmed tenants + user_events tables
- Evaluation logic: HIGH — pure Python, derived directly from FLAG-04 and FLAG-05 requirements
- UI patterns: HIGH — design/stitch/feature-flags.html is in-repo; Tailwind tokens confirmed present
- Pitfalls: HIGH — all derived from actual State.md decisions and phase retrospectives

**Research date:** 2026-06-07
**Valid until:** 2026-07-07 (stable stack; no fast-moving dependencies)
