# Requirements: BackOffice Multi-Tenant Platform

**Defined:** 2026-06-06
**Core Value:** Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.

## v1 Requirements (Complete — v1.0)

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
- [x] **UI-03**: La página de login sigue el diseño de Google Stitch
- [x] **UI-04**: Todas las páginas internas siguen el diseño de 'Tenant Management' de Google Stitch

### User Management

- [x] **USER-01**: TenantAdmin puede crear usuarios dentro de su tenant con email y nombre
- [x] **USER-02**: TenantAdmin puede asignar roles por tenant (TenantOwner, TenantAdmin, TenantViewer) y por producto (ProductManager, ProductDeveloper, ProductQA)
- [x] **USER-03**: TenantAdmin puede editar datos de usuarios existentes
- [x] **USER-04**: TenantAdmin puede activar y desactivar usuarios del tenant
- [x] **USER-05**: TenantAdmin puede resetear los dispositivos MFA de un usuario
- [x] **USER-06**: Toda acción sobre usuarios genera entrada en audit log con actor, acción, timestamp y contexto

### Authentication

- [x] **AUTH-01**: Usuario puede autenticarse con email/password via Keycloak como IdP
- [x] **AUTH-02**: Sesión persiste con tokens JWT emitidos por Keycloak
- [x] **AUTH-03**: Roles del usuario se propagan desde Keycloak al BFF y respetados en el frontend

### Feature Flags

- [x] **FLAG-01**: PlatformAdmin puede crear flags a nivel Global con name, default, complex, ttl, enabled, environment
- [x] **FLAG-02**: TenantAdmin puede crear flags a nivel Tenant que sobrescriben el nivel Global
- [x] **FLAG-03**: ProductManager puede crear flags a nivel Producto que sobrescriben el nivel Tenant
- [x] **FLAG-04**: La evaluación de flags sigue jerarquía determinista: Empresa > Producto > Tenant > Global
- [x] **FLAG-05**: Reglas de evaluación soportan los operadores: equals, in, notIn, contains, regex
- [x] **FLAG-06**: Segmentos de usuarios son reutilizables y pueden aplicarse en múltiples flags de distintos niveles

### Rule Builder

- [x] **RULE-01**: Usuario puede crear y editar reglas visualmente sin escribir código
- [x] **RULE-02**: Usuario puede reordenar reglas con prioridad via drag & drop
- [x] **RULE-03**: Usuario puede previsualizar el resultado de evaluación de una regla antes de activarla

---

## v1.1 Requirements (MVP2)

### Micro-UI Architecture

- [ ] **MUI-01**: El portal se refactoriza en Shell ligero: maneja auth (Keycloak), layout, navegación y servicios transversales; no contiene lógica de dominio
- [ ] **MUI-02**: Vue, Pinia, Vue Router y Axios se exponen como singletons (`singleton: true`) desde el Shell; los remotos no instancian estas librerías
- [ ] **MUI-03**: El Shell registra rutas de los remotos de forma asíncrona y espera `loadMicroUIRoutes()` antes de `app.mount()` para evitar race condition en hard refresh
- [ ] **MUI-04**: `mui-security` extraído como MUI remota (Module Federation) que expone `./routes` con las vistas de gestión de usuarios
- [ ] **MUI-05**: `mui-tenants` creado como MUI remota que expone `./routes` con las vistas de gestión de tenants y productos
- [ ] **MUI-06**: `mui-feature-flags` extraído como MUI remota que expone `./routes` con las vistas de feature flags, rule builder, simulador y segmentos

### Products

- [ ] **PROD-01**: PlatformAdmin puede crear un producto con id alfanumérico, name, description, status y labels (tags)
- [ ] **PROD-02**: PlatformAdmin puede editar metadatos de un producto y activarlo/desactivarlo
- [ ] **PROD-03**: La lista de productos soporta filtro por status y por label tags
- [ ] **PROD-04**: TenantOwner puede suscribir y desuscribir productos para su tenant desde la UI de gestión de tenants
- [ ] **PROD-05**: Las feature flags pueden asociarse a uno o más productos (migración desde campo JSON en tenants a tabla relacional `flag_products`)
- [ ] **PROD-06**: La migración de productos usa tres revisiones Alembic separadas (expand: crear tablas → backfill: migrar datos → cleanup: eliminar campo JSON) para evitar pérdida de datos en MySQL 5.6

### Advanced Segments

- [ ] **SEG-01**: Los segmentos tienen campo `type`: `manual` (lista estática de UUIDs, comportamiento existente) o `rule_based` (condiciones dinámicas)
- [ ] **SEG-02**: Segmentos `rule_based` almacenan condiciones en formato JSON idéntico al de las reglas de feature flags (mismos operadores, mismo motor de evaluación)
- [ ] **SEG-03**: El editor de condiciones de segmentos `rule_based` reutiliza `RuleCard.vue` (no nuevo editor)
- [ ] **SEG-04**: La lista de segmentos muestra el conteo de feature flags que referencian activamente cada segmento
- [ ] **SEG-05**: Segmentos con cero referencias activas a feature flags se marcan visualmente como huérfanos en la UI

### Feature Flag SDK

- [ ] **SDK-01**: Backend expone `GET /api/v1/sdk/bootstrap` que retorna snapshot consolidado de flags para `tenant_id + product_id + environment` (composición de `list_flags()` existente, sin cambios al motor de evaluación)
- [ ] **SDK-02**: Backend expone `POST /api/v1/sdk/evaluate` para evaluación remota de una flag con contexto de usuario (delega a `evaluate_flag()` existente)
- [ ] **SDK-03**: Backend expone `POST /api/v1/sdk/eval-events` para ingesta de eventos de telemetría en batch
- [ ] **SDK-04**: Backend expone WebSocket endpoint que transmite `{type:"flag_updated", flag_key}` a clientes registrados para `tenant_id + product_id` cuando se guarda una flag; usa first-message auth (no `Depends()` en handshake)
- [ ] **SDK-05**: SDK cliente JS/TS (`sdk/sdk-js`) hace fetch del bootstrap al inicializar y almacena config de flags en caché en memoria
- [ ] **SDK-06**: SDK cliente JS/TS evalúa flags localmente desde caché con latencia <1ms, sin llamadas de red
- [ ] **SDK-07**: SDK cliente JS/TS tiene fallback a evaluación remota via `POST /api/v1/sdk/evaluate` cuando se requiere contexto confidencial
- [ ] **SDK-08**: SDK cliente JS/TS mantiene conexión WebSocket con reconexión exponential-backoff nativa (sin dependencias externas) e invalida caché al recibir `flag_updated`
- [ ] **SDK-09**: SDK cliente JS/TS envía telemetría en batch con doble trigger: cada 60s o al acumular 100 eventos, con jitter de inicio para evitar thundering herd post-deploy
- [ ] **SDK-10**: SDK cliente JS/TS usa `navigator.sendBeacon()` para flush de telemetría pendiente en evento `beforeunload`
- [ ] **SDK-11**: SDK servidor Python (`sdk/sdk-python`) hace fetch async del bootstrap, evalúa flags localmente y soporta evaluación remota async
- [ ] **SDK-12**: SDK servidor Python mantiene conexión WebSocket con reconexión exponential-backoff + jitter para sincronización de caché

---

## v2 Requirements (Deferred — v1.2+)

### MFA Avanzado

- **MFA-01**: MFA obligatorio para roles críticos (PlatformAdmin, TenantOwner, TenantAdmin)
- **MFA-02**: Usuario puede registrar dispositivo TOTP como segundo factor
- **MFA-03**: Usuario puede registrar clave WebAuthn/FIDO2 como segundo factor
- **MFA-04**: OTP via email/SMS como fallback de MFA
- **MFA-05**: Autenticación adaptativa basada en riesgo (IP, geolocalización, comportamiento)

### Feature Flags Avanzados

- **FLAG-07**: Rollout porcentual — activación gradual de flag para porcentaje configurable de usuarios

### Client Management

- **CLNT-01**: TenantAdmin puede crear clientes tipo Persona con datos básicos, idioma y país
- **CLNT-02**: TenantAdmin puede crear clientes tipo Empresa con whitelabel propio
- **CLNT-03**: CompanyAdmin puede gestionar usuarios internos de su empresa
- **CLNT-04**: Whitelabel de empresa hereda y sobrescribe whitelabel del tenant (segundo nivel)

### Localización Avanzada

- **LOCL-01**: Localización configurable por Plataforma, Tenant, Empresa y Usuario
- **LOCL-02**: Resolución de localización: Empresa > Tenant > Plataforma > Usuario
- **LOCL-03**: Labels y mensajes personalizados por nivel

### Observabilidad

- **OBS-01**: Dashboard con KPI cards (Active Tenants, Total Products, System Health)
- **OBS-02**: Sección de eventos, alertas y notificaciones en tiempo real
- **OBS-03**: SLA/SLO monitoring con health checks activos cada 15s

---

## Out of Scope

Exclusiones explícitas para prevenir scope creep.

| Feature | Reason |
|---------|--------|
| mui-clients (Company Management UI) | v1.2 — requiere client management backend primero |
| mui-observability (SLA/SLO Dashboard) | v1.2 — requiere datos de telemetría en producción primero |
| Experimentos A/B | v2.0 — funcionalidad diferenciadora, no core |
| Integraciones externas | v2.0 — scope separado |
| Mobile app | Web-first strategy, móvil posterior |
| Real-time notifications UI (push) | v1.2 — no bloqueante para v1.1 |
| Redis pub/sub para WS multi-worker | v1.2 upgrade path — in-memory registry suficiente para MVP2 |

---

## Traceability

Qué fases cubren qué requerimientos. Actualizado durante creación del roadmap.

### v1.0 (Complete)

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
| USER-01 | Phase 3 | Complete |
| USER-02 | Phase 3 | Complete |
| USER-03 | Phase 3 | Complete |
| USER-04 | Phase 3 | Complete |
| USER-05 | Phase 3 | Complete |
| USER-06 | Phase 3 | Complete |
| FLAG-01 | Phase 4 | Complete |
| FLAG-02 | Phase 4 | Complete |
| FLAG-03 | Phase 4 | Complete |
| FLAG-04 | Phase 4 | Complete |
| FLAG-05 | Phase 4 | Complete |
| FLAG-06 | Phase 4 | Complete |
| RULE-01 | Phase 5 | Complete |
| RULE-02 | Phase 5 | Complete |
| RULE-03 | Phase 5 | Complete |
| UI-01 | Phase 2.1 | Complete |
| UI-02 | Phase 2.1 | Complete |
| UI-03 | Phase 6 | Complete |
| UI-04 | Phase 6 | Complete |

### v1.1 (Pending — phases 7+)

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROD-01 | Phase 7 | Pending |
| PROD-02 | Phase 7 | Pending |
| PROD-03 | Phase 7 | Pending |
| PROD-04 | Phase 7 | Pending |
| PROD-05 | Phase 7 | Pending |
| PROD-06 | Phase 7 | Pending |
| SEG-01 | Phase 8 | Pending |
| SEG-02 | Phase 8 | Pending |
| SEG-03 | Phase 8 | Pending |
| SEG-04 | Phase 8 | Pending |
| SEG-05 | Phase 8 | Pending |
| SDK-01 | Phase 8 | Pending |
| SDK-02 | Phase 8 | Pending |
| SDK-03 | Phase 8 | Pending |
| SDK-04 | Phase 8 | Pending |
| MUI-01 | Phase 9 | Pending |
| MUI-02 | Phase 9 | Pending |
| MUI-03 | Phase 9 | Pending |
| MUI-04 | Phase 10 | Pending |
| MUI-05 | Phase 10 | Pending |
| MUI-06 | Phase 11 | Pending |
| SDK-05 | Phase 11 | Pending |
| SDK-06 | Phase 11 | Pending |
| SDK-07 | Phase 11 | Pending |
| SDK-08 | Phase 11 | Pending |
| SDK-09 | Phase 11 | Pending |
| SDK-10 | Phase 11 | Pending |
| SDK-11 | Phase 11 | Pending |
| SDK-12 | Phase 11 | Pending |

**Coverage v1.1:**
- v1.1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-06*
*Last updated: 2026-06-07 — v1.1 MVP2 requirements added (29 new: MUI-01..06, PROD-01..06, SEG-01..05, SDK-01..12)*
