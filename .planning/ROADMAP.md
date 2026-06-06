# Roadmap: BackOffice Multi-Tenant Platform

## Overview

La plataforma se construye de afuera hacia adentro — primero la puerta de entrada (autenticación), luego el contenedor (tenants), luego los habitantes (usuarios), luego el núcleo de valor del producto (feature flags con evaluación jerárquica), y finalmente la interfaz visual que hace todo eso operable (rule builder). Cada fase entrega una capacidad completa y verificable antes de que empiece la siguiente.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Auth** - Autenticación funciona; PlatformAdmin puede entrar al sistema con roles propagados
- [ ] **Phase 2: Tenant Management** - PlatformAdmin puede crear, configurar y gestionar el ciclo de vida completo de tenants
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
**Plans**: TBD

### Phase 2: Tenant Management
**Goal**: PlatformAdmin puede gestionar el ciclo de vida completo de tenants — crear, configurar, filtrar, suspender y asociar productos
**Depends on**: Phase 1
**Requirements**: TNNT-01, TNNT-02, TNNT-03, TNNT-04, TNNT-05, TNNT-06
**Success Criteria** (what must be TRUE):
  1. PlatformAdmin puede crear un tenant con todos sus atributos (name, country, default_language, default_currency, default_units, status)
  2. PlatformAdmin puede editar cualquier atributo de un tenant existente y los cambios persisten
  3. PlatformAdmin puede suspender un tenant (bloqueando acceso) y eliminarlo definitivamente
  4. PlatformAdmin puede configurar logo, colores, tipografía y dominio del whitelabel del tenant
  5. PlatformAdmin puede buscar y filtrar la lista de tenants por estado, país y atributos clave
**Plans**: TBD

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
| 1. Foundation & Auth | 0/TBD | Not started | - |
| 2. Tenant Management | 0/TBD | Not started | - |
| 3. User Management | 0/TBD | Not started | - |
| 4. Feature Flags | 0/TBD | Not started | - |
| 5. Rule Builder | 0/TBD | Not started | - |
