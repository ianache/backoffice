# Phase 2: Tenant Management - Research

**Researched:** 2026-06-06
**Domain:** FastAPI + async SQLAlchemy + MySQL 5.6 / Vue 3 admin CRUD UI / BFF proxy pattern
**Confidence:** HIGH (stack locked by CONTEXT.md, verified against official docs and current sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Database**
- MySQL 5.6 as the application database (separate from Keycloak's Postgres)
- Alembic for all schema migrations — no raw DDL outside of migration files
- SQLAlchemy models define the schema; Alembic autogenerates migration scripts

**Python Backend**
- Framework: FastAPI with async SQLAlchemy (AsyncSession + asyncmy driver for MySQL 5.6)
- Structure: router-per-domain — each domain (tenants, products) gets its own router module
- Lives at `backend/` at monorepo root, parallel to `bff/` and `portal/`
- First domain introduced in this phase: `tenants` router

**BFF Integration Pattern**
- Vue portal calls BFF only — BFF proxies all tenant requests to Python backend
- BFF uses `http-proxy-middleware` for proxying (minimal code, handles streaming)
- BFF authenticates with Python backend via `X-Internal-Secret` header (shared secret in env)
- BFF forwards `X-User-Sub` and `X-User-Roles` headers so Python backend knows the acting user
- Python backend does not validate Keycloak JWTs directly

**Tenant List UI**
- Data table with rows: one row per tenant
- Columns: Name, Status (color-coded badge), Country, Products (comma-separated or count), Created, Actions
- Actions column: Edit, Suspend/Unsuspend, Delete
- Search and filter in a horizontal top bar above the table: text search input + Status filter dropdown + Country filter dropdown
- Sorting on table columns

**Tenant Create/Edit UI**
- Side drawer (slide-over from right) — tenant list stays visible in background
- Drawer has 2 tabs:
  - **General**: name, country, default_language, default_currency, default_units, status
  - **Whitelabel**: logo URL, primary/secondary/accent colors, font family + weight, domain
- Same drawer used for both create and edit; tab selection persists within a session

**Whitelabel Configuration**
- Logo: external URL input only — no file upload in Phase 2
- Colors: free hex input with color picker for primary, secondary, and accent brand colors
- Typography: font family name text input + weight selection (regular, medium, bold)
- Domain: plain text input for custom domain string
- All whitelabel fields stored as columns/JSON in the tenants table

### Claude's Discretion
- Exact color picker component library choice for the whitelabel form
- Pagination vs infinite scroll for the tenant table (choose what fits the table component)
- Confirmation dialog design for suspend and delete actions
- Error state and empty state illustrations/copy
- Docker Compose additions for MySQL 5.6 service

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TNNT-01 | PlatformAdmin puede crear un tenant con name, country, default_language, default_currency, default_units y status | FastAPI POST /tenants endpoint; SQLAlchemy Tenant model; Vue drawer General tab |
| TNNT-02 | PlatformAdmin puede editar los datos de un tenant existente | FastAPI PATCH /tenants/{id} endpoint; same drawer reused in edit mode |
| TNNT-03 | PlatformAdmin puede suspender y eliminar tenants | FastAPI PATCH /tenants/{id} (status=suspended) + DELETE /tenants/{id}; confirmation dialog in Vue |
| TNNT-04 | PlatformAdmin puede configurar el whitelabel básico del tenant (logo, colores, tipografía, dominio) | WhitelabelConfig stored as JSON column or flat columns; drawer Whitelabel tab; color picker component |
| TNNT-05 | PlatformAdmin puede asociar y deshabilitar productos en un tenant | Products stored as enum list or junction table; minimal checklist UI in drawer |
| TNNT-06 | PlatformAdmin puede buscar y filtrar la lista de tenants por estado, país y atributos clave | FastAPI GET /tenants?status=&country=&q=; Vue table with filter bar |
</phase_requirements>

---

## Summary

Phase 2 introduces three new system layers simultaneously: the Python/FastAPI backend service with its own database, a BFF proxy layer connecting Express to FastAPI, and the first non-trivial admin UI page. The most important constraint is MySQL 5.6 compatibility — this version predates several MySQL 8 features and requires care with TIMESTAMP column DDL, the `asyncmy` driver, and Docker image selection.

The BFF proxy pattern using `http-proxy-middleware` v4 is straightforward: one `createProxyMiddleware` call per domain, with `on.proxyReq` used to inject the `X-Internal-Secret`, `X-User-Sub`, and `X-User-Roles` headers. The Python backend trusts these headers entirely — it does not validate Keycloak JWTs. This keeps the backend simple but means the BFF's `requireRole('PlatformAdmin')` guard is the sole authorization gate.

The Vue UI has two main components: a tenant list table (filterable, sortable, with inline actions) and a slide-over drawer for create/edit. The project already has established patterns for Pinia stores and Axios services — the tenant domain follows them exactly. For the color picker, `vue-color-input` is the recommended choice: zero dependencies, replaces `<input type="color">`, supports hex format natively, and is v-model compatible.

**Primary recommendation:** Bootstrap the `backend/` service first (FastAPI + DB model + Alembic), verify DB connectivity, then wire the BFF proxy, then build the Vue UI layer — each layer can be tested in isolation.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | ^0.115 | Python API framework | Official recommended async framework; native Pydantic v2 |
| uvicorn[standard] | ^0.30 | ASGI server | Official FastAPI server |
| sqlalchemy[asyncio] | ^2.0 | ORM + async engine | Mature, first-class async support since 2.0 |
| asyncmy | ^0.2.9 | Async MySQL driver | Only maintained async MySQL driver for SQLAlchemy 2.0 |
| alembic | ^1.13 | Schema migrations | Official SQLAlchemy migration tool; `-t async` template |
| pydantic | ^2.7 | Request/response validation | Ships with FastAPI; v2 is default since fastapi 0.100+ |
| python-dotenv | ^1.0 | Env var loading | Standard for .env in Python |
| http-proxy-middleware | ^4.1 | BFF → backend proxy | Zero-config Express proxy; current version 4.1.0 |
| vue-color-input | ^2.x | Hex color picker (Vue 3) | Zero deps, replaces `<input type="color">`, v-model ready |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mysql:5.6 (Docker) | 5.6 | MySQL 5.6 container | docker-compose app database service |
| pydantic-settings | ^2.3 | Settings management from env | Structured config object, replaces manual os.environ calls |
| httpx | ^0.27 | Async HTTP client (testing) | FastAPI TestClient uses it; also useful for integration tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| asyncmy | aiomysql | aiomysql is also maintained but asyncmy has slightly better MySQL 5.6 support; both work |
| vue-color-input | @cyhnkckali/vue3-color-picker | More UI options but heavier; vue-color-input is minimal and sufficient for hex |
| http-proxy-middleware | express-http-proxy | Both work; http-proxy-middleware is specified in CONTEXT.md (locked) |

**Installation (backend):**
```bash
# In backend/
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncmy alembic pydantic pydantic-settings python-dotenv
```

**Installation (BFF addition):**
```bash
pnpm --filter @backoffice/bff add http-proxy-middleware
```

**Installation (portal addition):**
```bash
pnpm --filter @backoffice/portal add vue-color-input
```

---

## Architecture Patterns

### Recommended Project Structure

```
backend/                          # New: Python FastAPI service
├── alembic/
│   ├── versions/                 # Migration scripts (autogenerated)
│   └── env.py                    # Async Alembic environment
├── alembic.ini                   # Alembic config (url set programmatically)
├── app/
│   ├── main.py                   # FastAPI app, router mounting
│   ├── config.py                 # pydantic-settings Settings class
│   ├── database.py               # async engine + AsyncSession factory
│   ├── dependencies.py           # get_db, verify_internal_secret
│   └── domains/
│       └── tenants/
│           ├── router.py         # APIRouter for /tenants
│           ├── models.py         # SQLAlchemy Tenant ORM model
│           ├── schemas.py        # Pydantic TenantCreate/Update/Response
│           └── service.py        # DB operations (create, list, update, delete)
├── requirements.txt
└── Dockerfile (optional, Phase 2 can run bare)

bff/src/
├── routes/
│   ├── auth.ts                   # Existing
│   └── tenants.ts                # New: proxy routes to backend
├── middleware/
│   ├── auth.ts                   # Existing
│   └── roles.ts                  # Existing
└── index.ts                      # Mount tenantsRouter

portal/src/
├── services/
│   ├── api.ts                    # Existing Axios instance
│   └── tenants.ts                # New: CRUD calls via api instance
├── stores/
│   ├── auth.ts                   # Existing
│   └── tenants.ts                # New: Pinia store for tenant state
├── views/
│   └── TenantsView.vue           # New: page with table + drawer
├── components/tenants/
│   ├── TenantTable.vue           # Table with filter bar
│   ├── TenantDrawer.vue          # Slide-over with tabs
│   ├── TenantForm.vue            # General tab form
│   ├── WhitelabelForm.vue        # Whitelabel tab form
│   └── ConfirmDialog.vue         # Reusable confirm for suspend/delete
└── router/index.ts               # Add /tenants route
```

### Pattern 1: FastAPI Async Session Dependency Injection

**What:** Every route handler receives an `AsyncSession` via `Depends(get_db)`. Session lifetime matches the request.
**When to use:** All database operations in FastAPI route handlers.

```python
# Source: https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)

# app/dependencies.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionFactory

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
```

### Pattern 2: FastAPI Internal Secret Dependency

**What:** Python backend verifies the `X-Internal-Secret` header on every request. Trusts `X-User-Sub` and `X-User-Roles` headers forwarded by BFF.
**When to use:** All backend routes — no Keycloak JWT validation in Python.

```python
# app/dependencies.py
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from .config import settings
import hmac

internal_secret_header = APIKeyHeader(name="X-Internal-Secret", auto_error=False)

async def verify_internal_secret(
    secret: str | None = Security(internal_secret_header),
) -> None:
    if not secret or not hmac.compare_digest(secret, settings.INTERNAL_SECRET):
        raise HTTPException(status_code=403, detail="Forbidden")

# In router: dependencies=[Depends(verify_internal_secret)]
```

### Pattern 3: BFF Proxy with Header Injection

**What:** BFF uses `createProxyMiddleware` to forward all `/tenants` traffic to the Python backend, injecting auth headers on every proxied request.
**When to use:** New domain routes in BFF.

```typescript
// Source: https://github.com/chimurai/http-proxy-middleware v4.1.0
// bff/src/routes/tenants.ts
import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const tenantsRouter = Router()

tenantsRouter.use(
  requireAuth,
  requireRole('PlatformAdmin'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', req.user!.sub)
        proxyReq.setHeader('X-User-Roles', req.user!.roles.join(','))
      },
    },
  })
)
```

### Pattern 4: Alembic Async env.py for MySQL

**What:** Alembic uses async engine to run migrations. This is required when the driver is async-only (asyncmy).
**When to use:** `alembic init -t async migrations` generates this template; customize for MySQL.

```python
# Source: Official Alembic async template + https://berkkaraal.com/blog/...
# alembic/env.py (key sections)
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from alembic import context
from app.config import settings
from app.domains.tenants.models import Base  # imports all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata

async def run_migrations_online() -> None:
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### Pattern 5: Pinia Tenant Store (composable setup style)

**What:** Tenant store follows the same composable setup pattern as the existing `auth` store.
**When to use:** All domain state in the portal.

```typescript
// portal/src/stores/tenants.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as tenantsService from '../services/tenants'
import type { Tenant, TenantCreatePayload, TenantFilters } from '../services/tenants'

export const useTenantsStore = defineStore('tenants', () => {
  const tenants = ref<Tenant[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTenants(filters?: TenantFilters) {
    isLoading.value = true
    try {
      tenants.value = await tenantsService.list(filters)
    } finally {
      isLoading.value = false
    }
  }

  async function createTenant(payload: TenantCreatePayload) {
    const created = await tenantsService.create(payload)
    tenants.value.push(created)
    return created
  }

  return { tenants, isLoading, error, fetchTenants, createTenant }
})
```

### Pattern 6: Vue Slide-Over Drawer

**What:** Side drawer uses Vue's built-in `<Transition>` for slide-in animation and a backdrop. No Headless UI dependency needed.
**When to use:** Create/edit patterns where the list should remain visible.

```vue
<!-- portal/src/components/tenants/TenantDrawer.vue -->
<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="modelValue" class="drawer-overlay">
        <div class="drawer-panel">
          <!-- tabs + form content -->
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-from, .drawer-leave-to { transform: translateX(100%); }
.drawer-enter-active, .drawer-leave-active { transition: transform 0.3s ease; }
</style>
```

### Anti-Patterns to Avoid

- **Raw DDL in Python files:** All schema changes must go through Alembic migration files. Never call `Base.metadata.create_all()` in production code.
- **Eager loading without async select:** Avoid accessing lazy-loaded relationships after `session.commit()` in async context — `expire_on_commit=False` mitigates this but explicit `selectinload()` is safer.
- **Portal calling backend directly:** All requests go Portal → BFF → Backend. Never add backend URL to portal env vars.
- **Storing Keycloak JWT in backend:** Python backend must not receive or parse Keycloak tokens — it trusts BFF-forwarded headers only.
- **Using MySQL 8-specific DDL in migrations:** MySQL 5.6 does not support `JSON_TABLE`, functional indexes, or `VISIBLE/INVISIBLE` columns. Keep migrations to column types available in 5.6.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DB session lifecycle | Custom context manager | `async_sessionmaker` + `Depends(get_db)` | FastAPI DI handles cleanup/rollback on exception |
| Schema migrations | Raw ALTER TABLE scripts | Alembic autogenerate | Tracks state, handles downgrades, avoids drift |
| BFF → backend proxy | Custom axios forwarder in BFF | `http-proxy-middleware` | Handles streaming, connection reuse, error mapping |
| Hex color picker | Custom `<input type="color">` wrapper | `vue-color-input` | Browser native picker has poor UX; vue-color-input is zero-dep |
| Secret comparison | `secret === process.env.SECRET` | `hmac.compare_digest` | Prevents timing attacks on string comparison |
| Confirmation dialogs | Inline confirm state in each component | Shared `ConfirmDialog.vue` | Reused for suspend + delete; prevents duplication |

**Key insight:** The BFF proxy pattern specifically avoids duplicating request parsing logic — `http-proxy-middleware` transparently forwards body, headers, and query strings, so the BFF routes stay under 20 lines each.

---

## Common Pitfalls

### Pitfall 1: MySQL 5.6 TIMESTAMP Column Default Behavior

**What goes wrong:** In MySQL 5.6, the first `TIMESTAMP NOT NULL` column in a table automatically gets `DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` even if you didn't specify it. This causes Alembic to detect spurious schema differences on subsequent autogenerate runs.
**Why it happens:** MySQL 5.6 defaults `explicit_defaults_for_timestamp=OFF`. MySQL 8 changed this to `ON`.
**How to avoid:** Add `server_default=func.now()` and `onupdate=func.now()` explicitly on all `created_at`/`updated_at` columns. Or set `explicit_defaults_for_timestamp=1` in the MySQL 5.6 Docker config.
**Warning signs:** `alembic revision --autogenerate` keeps generating empty or timestamp-only migration files.

### Pitfall 2: asyncmy + expire_on_commit

**What goes wrong:** After `session.commit()`, SQLAlchemy marks all loaded objects as expired. Accessing any attribute outside an active async context triggers a sync lazy-load attempt which fails with `MissingGreenlet` or `DetachedInstanceError`.
**Why it happens:** Async SQLAlchemy cannot transparently lazy-load outside async context.
**How to avoid:** Set `expire_on_commit=False` in `async_sessionmaker`. For relationships, use `selectinload()` or `joinedload()` in queries.
**Warning signs:** `DetachedInstanceError` or `greenlet_spawn` errors after returning from service functions.

### Pitfall 3: Alembic autogenerate not detecting models

**What goes wrong:** `alembic revision --autogenerate` creates a migration with no changes (empty `upgrade()`/`downgrade()`) even though models changed.
**Why it happens:** `target_metadata` in `env.py` points to a `Base.metadata` that has no models imported at migration time.
**How to avoid:** Import all model modules in `env.py` before `target_metadata = Base.metadata` is used. A wildcard import from a models package works: `from app.domains.tenants import models as _`.
**Warning signs:** Empty migration files generated despite model changes.

### Pitfall 4: http-proxy-middleware path stripping

**What goes wrong:** When mounting `tenantsRouter` at `/tenants` in Express and the proxy target is `http://backend:8000`, the `/tenants` prefix is forwarded to the backend, making routes `/tenants/` instead of `/`.
**Why it happens:** `http-proxy-middleware` v4 preserves the full path by default.
**How to avoid:** Either (a) mount the Python router with the same `/tenants` prefix so paths match, or (b) use `pathRewrite: { '^/tenants': '' }` in the proxy options. Option (a) is simpler.
**Warning signs:** Backend returns 404 on all proxied requests.

### Pitfall 5: MySQL 5.6 Docker on ARM Macs

**What goes wrong:** `mysql:5.6` official image does not have an ARM64 build. Docker on M1/M2/M3 Macs will run it via emulation, which is slow and sometimes unstable.
**Why it happens:** MySQL 5.6 predates ARM64 container builds.
**How to avoid:** Use `platform: linux/amd64` in the docker-compose service spec. This forces Rosetta emulation explicitly. Alternatively use `mysql:8.0` for local dev with MySQL 5.6-compatible SQL only.
**Warning signs:** Docker image pull hangs or produces architecture warnings on Apple Silicon.

### Pitfall 6: BFF config missing new env vars

**What goes wrong:** BFF starts but crashes at proxy time because `BACKEND_URL` or `INTERNAL_SECRET` is not in `requireEnv()`.
**Why it happens:** `bff/src/config/index.ts` uses `requireEnv()` which throws at startup if the variable is missing.
**How to avoid:** Add `BACKEND_URL` and `INTERNAL_SECRET` to both `bff/src/config/index.ts` and `.env.example` before writing any proxy code.
**Warning signs:** `Error: Missing required env var: BACKEND_URL` on BFF startup.

---

## Code Examples

Verified patterns from official sources:

### MySQL 5.6 Docker Compose Service

```yaml
# Source: https://hub.docker.com/_/mysql/ (official)
# docker-compose.yml addition
  mysql:
    image: mysql:5.6
    platform: linux/amd64   # Required for ARM Macs
    environment:
      MYSQL_DATABASE: backoffice
      MYSQL_USER: backoffice
      MYSQL_PASSWORD: backoffice
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-proot"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  mysql_data:
```

### FastAPI Tenant Model (SQLAlchemy)

```python
# Source: SQLAlchemy 2.0 docs https://docs.sqlalchemy.org/en/20/
# app/domains/tenants/models.py
from datetime import datetime
from sqlalchemy import String, Enum, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(10), nullable=False)
    default_language: Mapped[str] = mapped_column(String(10), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    default_units: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", name="tenant_status"),
        default="active",
        nullable=False,
    )
    # Whitelabel fields
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(7))   # #RRGGBB
    secondary_color: Mapped[str | None] = mapped_column(String(7))
    accent_color: Mapped[str | None] = mapped_column(String(7))
    font_family: Mapped[str | None] = mapped_column(String(100))
    font_weight: Mapped[str | None] = mapped_column(String(20))
    domain: Mapped[str | None] = mapped_column(String(255))
    # Products: stored as JSON list of product identifiers
    products: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # Timestamps — explicit to avoid MySQL 5.6 implicit TIMESTAMP behavior
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

### FastAPI Tenant Router

```python
# Source: https://fastapi.tiangolo.com/tutorial/bigger-applications/
# app/domains/tenants/router.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, verify_internal_secret
from .schemas import TenantCreate, TenantUpdate, TenantResponse
from . import service

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(verify_internal_secret)],
)

@router.get("/", response_model=list[TenantResponse])
async def list_tenants(
    status: str | None = Query(None),
    country: str | None = Query(None),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_tenants(db, status=status, country=country, q=q)

@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_tenant(db, payload)

@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: int, payload: TenantUpdate, db: AsyncSession = Depends(get_db)):
    tenant = await service.update_tenant(db, tenant_id, payload)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await service.delete_tenant(db, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")
```

### BFF Config Extension

```typescript
// bff/src/config/index.ts (additions)
export const config = {
  // ... existing fields ...
  backendUrl: requireEnv('BACKEND_URL'),
  internalSecret: requireEnv('INTERNAL_SECRET'),
}
```

### Portal Tenants Service

```typescript
// portal/src/services/tenants.ts
import api from './api'

export interface Tenant {
  id: number
  name: string
  country: string
  status: 'active' | 'suspended'
  default_language: string
  default_currency: string
  default_units: string
  logo_url?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  font_family?: string
  font_weight?: string
  domain?: string
  products: string[]
  created_at: string
}

export interface TenantFilters {
  status?: string
  country?: string
  q?: string
}

export type TenantCreatePayload = Omit<Tenant, 'id' | 'created_at'>

export async function list(filters?: TenantFilters): Promise<Tenant[]> {
  const { data } = await api.get('/tenants/', { params: filters })
  return data
}

export async function create(payload: TenantCreatePayload): Promise<Tenant> {
  const { data } = await api.post('/tenants/', payload)
  return data
}

export async function update(id: number, payload: Partial<TenantCreatePayload>): Promise<Tenant> {
  const { data } = await api.patch(`/tenants/${id}`, payload)
  return data
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/tenants/${id}`)
}
```

### vue-color-input Usage

```vue
<!-- Source: https://github.com/gVguy/vue-color-input -->
<script setup lang="ts">
import ColorInput from 'vue-color-input'
const primaryColor = ref('#3B82F6')
</script>

<template>
  <ColorInput v-model="primaryColor" format="hex" />
</template>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Alembic sync migrations | Alembic async template (`-t async`) | Alembic 1.10+ | Required when using async-only drivers like asyncmy |
| SQLAlchemy sessionmaker | `async_sessionmaker` with `expire_on_commit=False` | SQLAlchemy 2.0 | Prevents DetachedInstanceError in async context |
| http-proxy-middleware v2 | v4 (breaking: `on.proxyReq` instead of `onProxyReq`) | 2024 | Event API changed; v4 is current |
| Pydantic v1 models | Pydantic v2 (`model_config = ConfigDict(...)`) | FastAPI 0.100+ | v1 deprecated; v2 is default |
| `declare global { namespace Express }` | Already in `bff/src/middleware/auth.ts` | Phase 1 | No change needed; req.user typing works |

**Deprecated/outdated:**
- `create_engine()` with asyncmy: use `create_async_engine()` — sync engine does not work with asyncmy
- `onProxyReq` callback in http-proxy-middleware: replaced by `on: { proxyReq: ... }` in v3+
- `Base.metadata.create_all()` for schema setup: use Alembic exclusively per locked decision

---

## Open Questions

1. **TNNT-05: Products as enum vs products table**
   - What we know: CONTEXT.md leaves this to Claude's Discretion
   - What's unclear: Whether a static enum list is sufficient for Phase 2 or a `products` table should be created now for Phase 3/4 extensibility
   - Recommendation: Use a JSON column `products: List[str]` on the `tenants` table for Phase 2 (e.g., `["feature-flags", "reporting"]`). This avoids premature normalization while Phase 2 only needs associate/dissociate. Phase 4 can migrate to a proper products table with a migration.

2. **asyncmy + MySQL 5.6 on ARM64 dev machines**
   - What we know: `mysql:5.6` has no ARM64 image; requires `platform: linux/amd64`
   - What's unclear: Whether team members have ARM64 Macs (M-series)
   - Recommendation: Add `platform: linux/amd64` to the MySQL service in docker-compose.yml regardless — it's harmless on x86_64 and required on Apple Silicon.

3. **FastAPI backend port**
   - What we know: BFF runs on port 3000; Vite portal on 5173; Keycloak on 8080
   - What's unclear: Which port to assign Python backend
   - Recommendation: Use port 8000 (FastAPI/uvicorn default) — no conflict with existing services.

---

## Sources

### Primary (HIGH confidence)
- https://fastapi.tiangolo.com/tutorial/bigger-applications/ — FastAPI APIRouter multi-file structure
- https://docs.sqlalchemy.org/en/20/dialects/mysql.html — asyncmy dialect URL format, MySQL 5.6 TIMESTAMP notes
- https://github.com/chimurai/http-proxy-middleware — v4.1.0 release, `on.proxyReq` header injection API
- https://hub.docker.com/_/mysql/ — mysql:5.6 official image availability
- https://alembic.sqlalchemy.org/en/latest/ — async template (`-t async`), env.py structure

### Secondary (MEDIUM confidence)
- https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/ — Complete async SQLAlchemy + Alembic setup, 2024
- https://github.com/gVguy/vue-color-input — vue-color-input zero-dep hex picker for Vue 3
- https://github.com/long2ice/asyncmy — asyncmy driver README, connection string format

### Tertiary (LOW confidence)
- Multiple WebSearch results on FastAPI domain structure patterns — cross-verified with official FastAPI docs above

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified against current official sources
- Architecture: HIGH — follows established Phase 1 patterns + FastAPI official docs
- Pitfalls: MEDIUM — MySQL 5.6 TIMESTAMP behavior verified against SQLAlchemy docs; asyncmy expire_on_commit from official SQLAlchemy docs; http-proxy-middleware path behavior from GitHub issues

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (stable stack; asyncmy and http-proxy-middleware do version frequently)
