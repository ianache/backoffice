---
phase: 03-user-management
plan: "01"
subsystem: api
tags: [fastapi, keycloak, sqlalchemy, alembic, mysql, httpx, pydantic]

# Dependency graph
requires:
  - phase: 02-tenant-management
    provides: backend SQLAlchemy/Alembic patterns, Base model, dependencies.py helpers
provides:
  - FastAPI /users endpoints (8 routes) backed by Keycloak Admin API
  - UserEvent SQLAlchemy model + user_events migration (audit log)
  - keycloak_admin.py singleton token cache with kcAdmin helpers
  - Full tenant-scoped CRUD: list, create, update, enable/disable, MFA reset
affects:
  - 03-02-bff-user-management
  - 03-03-portal-user-management

# Tech tracking
tech-stack:
  added: [httpx (already in requirements.txt)]
  patterns:
    - Keycloak Admin API via client_credentials grant + module-level token cache
    - context stored as TEXT (JSON string) due to MySQL 5.6 lack of JSON type
    - tenant_id stored as Keycloak attribute array — read via attributes.get("tenant_id", [""])[0]
    - Role assignment requires GET /roles/{name} for UUID before POST role-mappings

key-files:
  created:
    - backend/app/services/__init__.py
    - backend/app/services/keycloak_admin.py
    - backend/app/domains/users/__init__.py
    - backend/app/domains/users/models.py
    - backend/app/domains/users/schemas.py
    - backend/app/domains/users/service.py
    - backend/app/domains/users/router.py
    - backend/alembic/versions/f977f6d434f7_create_user_events_table.py
  modified:
    - backend/app/config.py
    - backend/app/main.py
    - backend/alembic/env.py

key-decisions:
  - "MySQL 5.6 does not support JSON column type — user_events.context stored as TEXT with JSON serialize/deserialize in service layer"
  - "Keycloak Admin API role assignment: always GET /roles/{name} first to obtain UUID before POSTing to role-mappings/realm"
  - "Tenant scoping enforced at service layer: service functions always use the actor_tenant_id parameter, never request body"
  - "User creation Location header extraction: location.rstrip('/').split('/')[-1] to get Keycloak UUID"

patterns-established:
  - "kcAdmin helpers pattern: module-level token cache (_admin_token, _token_expiry), 30s refresh buffer"
  - "Audit writes: every mutation calls _write_event() with UserEvent row before returning"
  - "Tenant ownership validation: fetch user from Keycloak, check attributes.tenant_id matches before mutation"

requirements-completed: [USER-01, USER-02, USER-03, USER-04, USER-05, USER-06]

# Metrics
duration: 20min
completed: 2026-06-07
---

# Phase 03 Plan 01: User Management Backend Summary

**FastAPI /users endpoints (8 routes) with Keycloak Admin API orchestration, tenant-scoped CRUD, and PostgreSQL audit log via UserEvent model**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-07T10:54:03Z
- **Completed:** 2026-06-07T11:14:00Z
- **Tasks:** 2
- **Files modified:** 12 (8 created, 4 modified)

## Accomplishments

- UserEvent SQLAlchemy model + Alembic migration applied to MySQL 5.6 DB (user_events table with indexes)
- Keycloak Admin API service (`keycloak_admin.py`) with singleton token cache (30s refresh buffer) and 5 helpers
- Full users domain: schemas, service (6 functions), router (8 endpoints), registered in main.py
- All mutations write UserEvent audit rows; tenant ownership validated before every write

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic migration + UserEvent model** - `b3e2802` (feat)
2. **Task 2: Keycloak Admin service + users domain** - `2d2b214` (feat)

**Plan metadata:** (pending — created after this summary)

## Files Created/Modified

- `backend/app/services/keycloak_admin.py` - Singleton admin token cache + kcAdminGet/Post/Put/Patch/Delete helpers
- `backend/app/domains/users/models.py` - UserEvent SQLAlchemy model (audit log, context as TEXT)
- `backend/app/domains/users/schemas.py` - UserCreate, UserUpdate, UserResponse, UserEventResponse
- `backend/app/domains/users/service.py` - All 6 user operations with audit writes and tenant scoping
- `backend/app/domains/users/router.py` - 8 endpoints at /users prefix
- `backend/alembic/versions/f977f6d434f7_create_user_events_table.py` - user_events migration
- `backend/app/config.py` - Added keycloak_url, keycloak_realm, keycloak_admin_client_id/secret fields
- `backend/app/main.py` - Registered users_router

## Decisions Made

- **MySQL 5.6 compatibility:** user_events.context stored as TEXT (not JSON) — MySQL 5.6 doesn't support the JSON column type (added in 5.7.8). Service layer serializes dict to JSON string on write and deserializes on read.
- **Keycloak role assignment pattern:** Must GET /roles/{name} first to obtain the role UUID before posting to role-mappings/realm. Keycloak returns 400 if you attempt to assign by name only.
- **Tenant scoping:** Service functions always receive tenant_id as a parameter from the router (sourced from X-User-Tenant-Id header), never from the request body — preventing tenant ID spoofing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MySQL 5.6 incompatible JSON column type**
- **Found during:** Task 1 (Alembic migration + UserEvent model)
- **Issue:** First migration run failed with MySQL syntax error: "near 'JSON'" — MySQL 5.6 does not support the JSON column type
- **Fix:** Changed `context` column type from `JSON` to `Text`. Service layer now JSON-serializes dict context to string on write and deserializes on read. Also removed the autogenerated `tenants.products TEXT→JSON` alter from the migration (same root cause, pre-existing column unaffected by this plan).
- **Files modified:** `backend/app/domains/users/models.py`, `backend/alembic/versions/f977f6d434f7_create_user_events_table.py`
- **Verification:** Migration applied successfully (`alembic current` shows f977f6d434f7 at head)
- **Committed in:** b3e2802 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Necessary compatibility fix. context is fully functional as TEXT with JSON serialization. No scope creep.

## Issues Encountered

- Alembic not in PATH (not installed system-wide) — used `./venv/Scripts/alembic` from the backend venv. All subsequent alembic commands use venv-relative path.

## User Setup Required

The following env vars need to be set in `backend/.env` before live Keycloak calls work:

```
KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
KEYCLOAK_REALM=Apps
KEYCLOAK_ADMIN_CLIENT_ID=<your-backend-client-id>
KEYCLOAK_ADMIN_CLIENT_SECRET=<your-backend-client-secret>
```

The `KEYCLOAK_URL` and `KEYCLOAK_REALM` values have been pre-populated in `.env` from the BFF config. `KEYCLOAK_ADMIN_CLIENT_SECRET` must be filled in once a confidential client with `manage-users` service account role is provisioned in Keycloak.

## Next Phase Readiness

- Backend /users endpoints are ready for the BFF proxy layer (Phase 03-02)
- Keycloak admin client provisioning required before live testing
- UserEvent audit table is in DB and ready to receive rows

---
*Phase: 03-user-management*
*Completed: 2026-06-07*
