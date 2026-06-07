# Roadmap: BackOffice Multi-Tenant Platform

## Overview

La plataforma se construye de afuera hacia adentro — primero la puerta de entrada (autenticación), luego el contenedor (tenants), luego los habitantes (usuarios), luego el núcleo de valor del producto (feature flags con evaluación jerárquica), y finalmente la interfaz visual que hace todo eso operable (rule builder). Cada fase entrega una capacidad completa y verificable antes de que empiece la siguiente.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Auth** - Autenticación funciona; PlatformAdmin puede entrar al sistema con roles propagados
- [x] **Phase 2: Tenant Management** - PlatformAdmin puede crear, configurar y gestionar el ciclo de vida completo de tenants
- [ ] **Phase 2.1: UI System & Brand Alignment** (INSERTED) - Alineación con Google Stitch y sistema de temas Light/Dark
- [ ] **Phase 3: User Management** - TenantAdmin puede gestionar usuarios dentro de su tenant con audit completo
- [ ] **Phase 4: Feature Flags** - Flags configurables en 4 niveles con evaluación jerárquica determinista
- [ ] **Phase 5: Rule Builder** - Usuarios pueden crear, ordenar y previsualizar reglas de evaluación visualmente

## Phase Details

### Phase 1: Foundation & Auth
**Goal**: Los usuarios autorizados pueden acceder al sistema con sus roles correctamente propagados desde Keycloak al frontend
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03
**Success Criteria** (what must be TRUE):
  1. Un usuario puede ingresar con email/password y Keycloak autentica la sesión
  2. La sesión persiste con JWT válido entre recargas de página y navegación interna
  3. Los roles del usuario (PlatformAdmin, TenantAdmin, etc.) son visibles y correctamente aplicados en el frontend
  4. Un usuario sin los permisos correctos no puede acceder a rutas protegidas
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Monorepo scaffold (pnpm workspaces) + Keycloak Docker Compose with pre-configured backoffice realm
- [x] 01-02-PLAN.md — BFF Node.js/Express: jose JWT validation middleware, /auth/me endpoint, role enforcement
- [x] 01-03-PLAN.md — Vue 3 portal shell: keycloak-js, Pinia auth store, Vue Router guards, login/dashboard views
- [x] 01-04-PLAN.md — End-to-end integration verification (automated smoke tests + human checkpoint)

**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md — Bootstrap FastAPI + MySQL + Alembic
- [x] 02-02-PLAN.md — FastAPI Tenants domain (Models, Schemas, Service, Router)
- [x] 02-03-PLAN.md — BFF Proxy to Backend
- [x] 02-04-PLAN.md — Portal UI (Tenants list, drawer, forms, store)

### Phase 2.1: UI System & Brand Alignment
**Goal**: El portal sigue los lineamientos de diseño de Google Stitch y soporta temas Light/Dark para mejorar la experiencia de usuario y coherencia visual
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. Los componentes visuales y espaciado siguen las especificaciones de Google Stitch
  2. El usuario puede alternar entre modo Light y Dark mediante un toggle en el menú principal
  3. La preferencia de tema persiste entre sesiones
**Plans**: 1 plan

Plans:
- [ ] 02.1-01-PLAN.md — Research & UI Planning (Stitch alignment + Theme System)

### Phase 3: User Management
**Goal**: TenantAdmin puede gestionar usuarios dentro de su tenant — crear, asignar roles, activar/desactivar y auditar todas las acciones
**Depends on**: Phase 2
**Requirements**: USER-01, USER-02, USER-03, USER-04, USER-05, USER-06
**Success Criteria** (what must be TRUE):
  1. TenantAdmin puede crear un usuario en su tenant con email, nombre y rol asignado
  2. TenantAdmin puede asignar y modificar roles de tenant (TenantOwner, TenantAdmin, TenantViewer) y de producto (ProductManager, ProductDeveloper, ProductQA)
  3. TenantAdmin puede activar y desactivar usuarios — los desactivados no pueden autenticarse
  4. TenantAdmin puede resetear los dispositivos MFA de un usuario
  5. Toda acción sobre usuarios aparece en el audit log con actor, acción, timestamp y contexto
**Plans**: TBD

### Phase 4: Feature Flags
**Goal**: Los feature flags funcionan con evaluación jerárquica determinista en 4 niveles, con soporte completo de operadores de reglas y segmentos reutilizables
**Depends on**: Phase 3
**Requirements**: FLAG-01, FLAG-02, FLAG-03, FLAG-04, FLAG-05, FLAG-06
**Success Criteria** (what must be TRUE):
  1. PlatformAdmin puede crear un flag a nivel Global con todos sus atributos (name, default, complex, ttl, enabled, environment)
  2. TenantAdmin puede crear un flag a nivel Tenant y ProductManager a nivel Producto; ambos sobrescriben el nivel superior según la jerarquía
  3. La evaluación de un flag sigue el orden determinista Empresa > Producto > Tenant > Global — el nivel más específico gana siempre
  4. Las reglas de evaluación funcionan con los operadores equals, in, notIn, contains y regex
  5. Un segmento de usuarios puede definirse una vez y aplicarse a múltiples flags en distintos niveles
**Plans**: TBD

### Phase 5: Rule Builder
**Goal**: Los usuarios pueden crear, ordenar y previsualizar reglas de evaluación visualmente sin escribir código
**Depends on**: Phase 4
**Requirements**: RULE-01, RULE-02, RULE-03
**Success Criteria** (what must be TRUE):
  1. Un usuario puede crear y editar reglas de evaluación usando una interfaz visual sin escribir código
  2. Un usuario puede reordenar reglas arrastrando y soltando (drag & drop) para cambiar su prioridad de evaluación
  3. Un usuario puede previsualizar el resultado de evaluación de una regla antes de activarla en producción
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Auth | 4/4 | Complete | 2026-06-07 |
| 2. Tenant Management | 4/4 | Complete | 2026-06-07 |
| 2.1. UI System & Brand Alignment | 0/1 | Not started | - |
| 3. User Management | 0/TBD | Not started | - |
| 4. Feature Flags | 0/TBD | Not started | - |
| 5. Rule Builder | 0/TBD | Not started | - |
