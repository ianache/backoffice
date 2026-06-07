# Requirements: BackOffice Multi-Tenant Platform

**Defined:** 2026-06-06
**Core Value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.

## v1 Requirements

Requirements para la Fase 1 (Tenants + Usuarios + Feature Flags). Cada uno mapea a una fase del roadmap.

### Tenant Management

- [x] **TNNT-01**: PlatformAdmin puede crear un tenant con name, country, default_language, default_currency, default_units y status
- [x] **TNNT-02**: PlatformAdmin puede editar los datos de un tenant existente
- [x] **TNNT-03**: PlatformAdmin puede suspender y eliminar tenants
- [x] **TNNT-04**: PlatformAdmin puede configurar el whitelabel básico del tenant (logo, colores, tipografía, dominio)
- [x] **TNNT-05**: PlatformAdmin puede asociar y deshabilitar productos en un tenant
- [x] **TNNT-06**: PlatformAdmin puede buscar y filtrar la lista de tenants por estado, país y atributos clave

### UI System & Brand Alignment

- [x] **UI-01**: La interfaz del portal sigue el System Design de Google Stitch
- [x] **UI-02**: El sistema soporta modos Light y Dark con un toggle persistente en la barra de navegación
- [x] **UI-03**: La página de login sigue el diseño de Google Stitch (https://stitch.withgoogle.com/projects/5651761190718398526?node-id=501bb1c4dfdb456d9cd2672135daee2d)
- [ ] **UI-04**: Todas las páginas internas (excepto login) siguen el diseño de 'Tenant Management' de Google Stitch (https://stitch.withgoogle.com/projects/5651761190718398526?node-id=acc51e9c26554064a2e0a45864688b85)


### User Management

- [ ] **USER-01**: TenantAdmin puede crear usuarios dentro de su tenant con email y nombre
- [ ] **USER-02**: TenantAdmin puede asignar roles por tenant (TenantOwner, TenantAdmin, TenantViewer) y por producto (ProductManager, ProductDeveloper, ProductQA)
- [ ] **USER-03**: TenantAdmin puede editar datos de usuarios existentes
- [ ] **USER-04**: TenantAdmin puede activar y desactivar usuarios del tenant
- [ ] **USER-05**: TenantAdmin puede resetear los dispositivos MFA de un usuario
- [ ] **USER-06**: Toda acción sobre usuarios genera entrada en audit log con actor, acción, timestamp y contexto

### Authentication

- [x] **AUTH-01**: Usuario puede autenticarse con email/password via Keycloak como IdP
- [x] **AUTH-02**: Sesión persiste con tokens JWT emitidos por Keycloak
- [x] **AUTH-03**: Roles del usuario se propagan desde Keycloak al BFF y respetados en el frontend

### Feature Flags

- [ ] **FLAG-01**: PlatformAdmin puede crear flags a nivel Global con name, default, complex, ttl, enabled, environment
- [ ] **FLAG-02**: TenantAdmin puede crear flags a nivel Tenant que sobrescriben el nivel Global
- [ ] **FLAG-03**: ProductManager puede crear flags a nivel Producto que sobrescriben el nivel Tenant
- [ ] **FLAG-04**: La evaluación de flags sigue jerarquía determinista: Empresa > Producto > Tenant > Global
- [ ] **FLAG-05**: Reglas de evaluación soportan los operadores: equals, in, notIn, contains, regex
- [ ] **FLAG-06**: Segmentos de usuarios son reutilizables y pueden aplicarse en múltiples flags de distintos niveles

### Rule Builder

- [ ] **RULE-01**: Usuario puede crear y editar reglas visualmente sin escribir código
- [ ] **RULE-02**: Usuario puede reordenar reglas con prioridad via drag & drop
- [ ] **RULE-03**: Usuario puede previsualizar el resultado de evaluación de una regla antes de activarla

## v2 Requirements

Diferidos a fases futuras. Reconocidos pero no en el roadmap actual.

### MFA Avanzado (Fase 2)

- **MFA-01**: MFA obligatorio para roles críticos (PlatformAdmin, TenantOwner, TenantAdmin)
- **MFA-02**: Usuario puede registrar dispositivo TOTP como segundo factor
- **MFA-03**: Usuario puede registrar clave WebAuthn/FIDO2 como segundo factor
- **MFA-04**: OTP via email/SMS como fallback de MFA
- **MFA-05**: Autenticación adaptativa basada en riesgo (IP, geolocalización, comportamiento)

### Feature Flags Avanzados (Fase 2)

- **FLAG-07**: Rollout porcentual — activación gradual de flag para porcentaje configurable de usuarios

### Client Management (Fase 2)

- **CLNT-01**: TenantAdmin puede crear clientes tipo Persona con datos básicos, idioma y país
- **CLNT-02**: TenantAdmin puede crear clientes tipo Empresa con whitelabel propio
- **CLNT-03**: CompanyAdmin puede gestionar usuarios internos de su empresa
- **CLNT-04**: Whitelabel de empresa hereda y sobrescribe whitelabel del tenant (segundo nivel)

### Localización Avanzada (Fase 2)

- **LOCL-01**: Localización configurable por Plataforma, Tenant, Empresa y Usuario
- **LOCL-02**: Resolución de localización: Empresa > Tenant > Plataforma > Usuario
- **LOCL-03**: Labels y mensajes personalizados por nivel

## Out of Scope

Exclusiones explícitas para prevenir scope creep.

| Feature | Reason |
|---------|--------|
| Observabilidad / SLA / SLO / Alertas | Phase 3 — requiere sistema maduro en producción |
| MFA biométrico | Phase 4 — alta complejidad, dependencia de hardware |
| Experimentos A/B | Phase 4 — funcionalidad diferenciadora, no core |
| Integraciones externas | Phase 4 — scope separado |
| Mobile app | Web-first strategy, móvil posterior |
| Real-time notifications | No bloqueante para Fase 1 |

## Traceability

Cual fase cubre cuáles requerimientos. Actualizado durante creación del roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| TNNT-01 | Phase 2 | Complete |
| TNNT-02 | Phase 2 | Complete |
| TNNT-03 | Phase 2 | Complete |
| TNNT-04 | Phase 2 | Complete |
| TNNT-05 | Phase 2 | Complete |
| TNNT-06 | Phase 2 | Complete |
| USER-01 | Phase 3 | Pending |
| USER-02 | Phase 3 | Pending |
| USER-03 | Phase 3 | Pending |
| USER-04 | Phase 3 | Pending |
| USER-05 | Phase 3 | Pending |
| USER-06 | Phase 3 | Pending |
| FLAG-01 | Phase 4 | Pending |
| FLAG-02 | Phase 4 | Pending |
| FLAG-03 | Phase 4 | Pending |
| FLAG-04 | Phase 4 | Pending |
| FLAG-05 | Phase 4 | Pending |
| FLAG-06 | Phase 4 | Pending |
| RULE-01 | Phase 5 | Pending |
| RULE-02 | Phase 5 | Pending |
| RULE-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-06*
*Last updated: 2026-06-06 after roadmap creation*
