# Requirements: BackOffice Multi-Tenant Platform

**Defined:** 2026-06-06
**Core Value:** Los feature flags jerÃ¡rquicos con evaluaciÃ³n determinista deben funcionar â€” sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razÃ³n de existir.

## v1 Requirements (Complete â€” v1.0)

### Tenant Management

- [x] **TNNT-01**: PlatformAdmin puede crear un tenant con name, country, default_language, default_currency, default_units y status
- [x] **TNNT-02**: PlatformAdmin puede editar los datos de un tenant existente
- [x] **TNNT-03**: PlatformAdmin puede suspender y eliminar tenants
- [x] **TNNT-04**: PlatformAdmin puede configurar el whitelabel bÃ¡sico del tenant (logo, colores, tipografÃ­a, dominio)
- [x] **TNNT-05**: PlatformAdmin puede asociar y deshabilitar productos en un tenant
- [x] **TNNT-06**: PlatformAdmin puede buscar y filtrar la lista de tenants por estado, paÃ­s y atributos clave

### UI System & Brand Alignment

- [x] **UI-01**: La interfaz del portal sigue el System Design de Google Stitch
- [x] **UI-02**: El sistema soporta modos Light y Dark con un toggle persistente en la barra de navegaciÃ³n
- [x] **UI-03**: La pÃ¡gina de login sigue el diseÃ±o de Google Stitch
- [x] **UI-04**: Todas las pÃ¡ginas internas siguen el diseÃ±o de 'Tenant Management' de Google Stitch

### User Management

- [x] **USER-01**: TenantAdmin puede crear usuarios dentro de su tenant con email y nombre
- [x] **USER-02**: TenantAdmin puede asignar roles por tenant (TenantOwner, TenantAdmin, TenantViewer) y por producto (ProductManager, ProductDeveloper, ProductQA)
- [x] **USER-03**: TenantAdmin puede editar datos de usuarios existentes
- [x] **USER-04**: TenantAdmin puede activar y desactivar usuarios del tenant
- [x] **USER-05**: TenantAdmin puede resetear los dispositivos MFA de un usuario
- [x] **USER-06**: Toda acciÃ³n sobre usuarios genera entrada en audit log con actor, acciÃ³n, timestamp y contexto

### Authentication

- [x] **AUTH-01**: Usuario puede autenticarse con email/password via Keycloak como IdP
- [x] **AUTH-02**: SesiÃ³n persiste con tokens JWT emitidos por Keycloak
- [x] **AUTH-03**: Roles del usuario se propagan desde Keycloak al BFF y respetados en el frontend

### Feature Flags

- [x] **FLAG-01**: PlatformAdmin puede crear flags a nivel Global con name, default, complex, ttl, enabled, environment
- [x] **FLAG-02**: TenantAdmin puede crear flags a nivel Tenant que sobrescriben el nivel Global
- [x] **FLAG-03**: ProductManager puede crear flags a nivel Producto que sobrescriben el nivel Tenant
- [x] **FLAG-04**: La evaluaciÃ³n de flags sigue jerarquÃ­a determinista: Empresa > Producto > Tenant > Global
- [x] **FLAG-05**: Reglas de evaluaciÃ³n soportan los operadores: equals, in, notIn, contains, regex
- [x] **FLAG-06**: Segmentos de usuarios son reutilizables y pueden aplicarse en mÃºltiples flags de distintos niveles

### Rule Builder

- [x] **RULE-01**: Usuario puede crear y editar reglas visualmente sin escribir cÃ³digo
- [x] **RULE-02**: Usuario puede reordenar reglas con prioridad via drag & drop
- [x] **RULE-03**: Usuario puede previsualizar el resultado de evaluaciÃ³n de una regla antes de activarla

---

## v1.1 Requirements (MVP2)

### Micro-UI Architecture

- [ ] **MUI-01**: El portal se refactoriza en Shell ligero: maneja auth (Keycloak), layout, navegaciÃ³n y servicios transversales; no contiene lÃ³gica de dominio
- [ ] **MUI-02**: Vue, Pinia, Vue Router y Axios se exponen como singletons (`singleton: true`) desde el Shell; los remotos no instancian estas librerÃ­as
- [ ] **MUI-03**: El Shell registra rutas de los remotos de forma asÃ­ncrona y espera `loadMicroUIRoutes()` antes de `app.mount()` para evitar race condition en hard refresh
- [x] **MUI-04**: `mui-security` extraÃ­do como MUI remota (Module Federation) que expone `./routes` con las vistas de gestiÃ³n de usuarios
- [x] **MUI-05**: `mui-tenants` creado como MUI remota que expone `./routes` con las vistas de gestiÃ³n de tenants y productos
- [x] **MUI-06**: `mui-feature-flags` extraÃ­do como MUI remota que expone `./routes` con las vistas de feature flags, rule builder, simulador y segmentos

### Products

- [x] **PROD-01**: PlatformAdmin puede crear un producto con id alfanumÃ©rico, name, description, status y labels (tags)
- [x] **PROD-02**: PlatformAdmin puede editar metadatos de un producto y activarlo/desactivarlo
- [x] **PROD-03**: La lista de productos soporta filtro por status y por label tags
- [x] **PROD-04**: TenantOwner puede suscribir y desuscribir productos para su tenant desde la UI de gestiÃ³n de tenants
- [x] **PROD-05**: Las feature flags pueden asociarse a uno o mÃ¡s productos (migraciÃ³n desde campo JSON en tenants a tabla relacional `flag_products`)
- [x] **PROD-06**: La migraciÃ³n de productos usa tres revisiones Alembic separadas (expand: crear tablas â†’ backfill: migrar datos â†’ cleanup: eliminar campo JSON) para evitar pÃ©rdida de datos en MySQL 5.6

### Advanced Segments

- [x] **SEG-01**: Los segmentos tienen campo `type`: `manual` (lista estÃ¡tica de UUIDs, comportamiento existente) o `rule_based` (condiciones dinÃ¡micas)
- [x] **SEG-02**: Segmentos `rule_based` almacenan condiciones en formato JSON idÃ©ntico al de las reglas de feature flags (mismos operadores, mismo motor de evaluaciÃ³n)
- [x] **SEG-03**: El editor de condiciones de segmentos `rule_based` reutiliza `RuleCard.vue` (no nuevo editor)
- [x] **SEG-04**: La lista de segmentos muestra el conteo de feature flags que referencian activamente cada segmento
- [x] **SEG-05**: Segmentos con cero referencias activas a feature flags se marcan visualmente como huÃ©rfanos en la UI

### Feature Flag SDK

- [x] **SDK-01**: Backend expone `GET /api/v1/sdk/bootstrap` que retorna snapshot consolidado de flags para `tenant_id + product_id + environment` (composiciÃ³n de `list_flags()` existente, sin cambios al motor de evaluaciÃ³n)
- [x] **SDK-02**: Backend expone `POST /api/v1/sdk/evaluate` para evaluaciÃ³n remota de una flag con contexto de usuario (delega a `evaluate_flag()` existente)
- [x] **SDK-03**: Backend expone `POST /api/v1/sdk/eval-events` para ingesta de eventos de telemetrÃ­a en batch
- [x] **SDK-04**: Backend expone WebSocket endpoint que transmite `{type:"flag_updated", flag_key}` a clientes registrados para `tenant_id + product_id` cuando se guarda una flag; usa first-message auth (no `Depends()` en handshake)
- [x] **SDK-05**: SDK cliente JS/TS (`sdk/sdk-js`) hace fetch del bootstrap al inicializar y almacena config de flags en cachÃ© en memoria
- [x] **SDK-06**: SDK cliente JS/TS evalÃºa flags localmente desde cachÃ© con latencia <1ms, sin llamadas de red
- [ ] **SDK-07**: SDK cliente JS/TS tiene fallback a evaluaciÃ³n remota via `POST /api/v1/sdk/evaluate` cuando se requiere contexto confidencial
- [ ] **SDK-08**: SDK cliente JS/TS mantiene conexiÃ³n WebSocket con reconexiÃ³n exponential-backoff nativa (sin dependencias externas) e invalida cachÃ© al recibir `flag_updated`
- [ ] **SDK-09**: SDK cliente JS/TS envÃ­a telemetrÃ­a en batch con doble trigger: cada 60s o al acumular 100 eventos, con jitter de inicio para evitar thundering herd post-deploy
- [ ] **SDK-10**: SDK cliente JS/TS usa `navigator.sendBeacon()` para flush de telemetrÃ­a pendiente en evento `beforeunload`
- [ ] **SDK-11**: SDK servidor Python (`sdk/sdk-python`) hace fetch async del bootstrap, evalÃºa flags localmente y soporta evaluaciÃ³n remota async
- [ ] **SDK-12**: SDK servidor Python mantiene conexiÃ³n WebSocket con reconexiÃ³n exponential-backoff + jitter para sincronizaciÃ³n de cachÃ©

---

## v2 Requirements (Deferred â€” v1.2+)

### MFA Avanzado

- **MFA-01**: MFA obligatorio para roles crÃ­ticos (PlatformAdmin, TenantOwner, TenantAdmin)
- **MFA-02**: Usuario puede registrar dispositivo TOTP como segundo factor
- **MFA-03**: Usuario puede registrar clave WebAuthn/FIDO2 como segundo factor
- **MFA-04**: OTP via email/SMS como fallback de MFA
- **MFA-05**: AutenticaciÃ³n adaptativa basada en riesgo (IP, geolocalizaciÃ³n, comportamiento)

### Feature Flags Avanzados

- **FLAG-07**: Rollout porcentual â€” activaciÃ³n gradual de flag para porcentaje configurable de usuarios

### Client Management

- **CLNT-01**: TenantAdmin puede crear clientes tipo Persona con datos bÃ¡sicos, idioma y paÃ­s
- **CLNT-02**: TenantAdmin puede crear clientes tipo Empresa con whitelabel propio
- **CLNT-03**: CompanyAdmin puede gestionar usuarios internos de su empresa
- **CLNT-04**: Whitelabel de empresa hereda y sobrescribe whitelabel del tenant (segundo nivel)

### LocalizaciÃ³n Avanzada

- **LOCL-01**: LocalizaciÃ³n configurable por Plataforma, Tenant, Empresa y Usuario
- **LOCL-02**: ResoluciÃ³n de localizaciÃ³n: Empresa > Tenant > Plataforma > Usuario
- **LOCL-03**: Labels y mensajes personalizados por nivel

### Observabilidad

- **OBS-01**: Dashboard con KPI cards (Active Tenants, Total Products, System Health)
- **OBS-02**: SecciÃ³n de eventos, alertas y notificaciones en tiempo real
- **OBS-03**: SLA/SLO monitoring con health checks activos cada 15s

---

## Out of Scope

Exclusiones explÃ­citas para prevenir scope creep.

| Feature | Reason |
|---------|--------|
| mui-clients (Company Management UI) | v1.2 â€” requiere client management backend primero |
| mui-observability (SLA/SLO Dashboard) | v1.2 â€” requiere datos de telemetrÃ­a en producciÃ³n primero |
| Experimentos A/B | v2.0 â€” funcionalidad diferenciadora, no core |
| Integraciones externas | v2.0 â€” scope separado |
| Mobile app | Web-first strategy, mÃ³vil posterior |
| Real-time notifications UI (push) | v1.2 â€” no bloqueante para v1.1 |
| Redis pub/sub para WS multi-worker | v1.2 upgrade path â€” in-memory registry suficiente para MVP2 |

---

## Traceability

QuÃ© fases cubren quÃ© requerimientos. Actualizado durante creaciÃ³n del roadmap.

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

### v1.1 (Pending â€” phases 7+)

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROD-01 | Phase 7 | Complete |
| PROD-02 | Phase 7 | Complete |
| PROD-03 | Phase 7 | Complete |
| PROD-04 | Phase 7 | Complete |
| PROD-05 | Phase 7 | Complete |
| PROD-06 | Phase 7 | Complete |
| SEG-01 | Phase 8 | Complete |
| SEG-02 | Phase 8 | Complete |
| SEG-03 | Phase 8 | Complete |
| SEG-04 | Phase 8 | Complete |
| SEG-05 | Phase 8 | Complete |
| SDK-01 | Phase 8 | Complete |
| SDK-02 | Phase 8 | Complete |
| SDK-03 | Phase 8 | Complete |
| SDK-04 | Phase 8 | Complete |
| MUI-01 | Phase 9 | Pending |
| MUI-02 | Phase 9 | Pending |
| MUI-03 | Phase 9 | Pending |
| MUI-04 | Phase 10 | Complete |
| MUI-05 | Phase 10 | Complete |
| MUI-06 | Phase 11 | Complete |
| SDK-05 | Phase 11 | Complete |
| SDK-06 | Phase 11 | Complete |
| SDK-07 | Phase 11 | Pending |
| SDK-08 | Phase 11 | Pending |
| SDK-09 | Phase 11 | Pending |
| SDK-10 | Phase 11 | Pending |
| SDK-11 | Phase 11 | Pending |
| SDK-12 | Phase 11 | Pending |

**Coverage v1.1:**
- v1.1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0 âœ“

---
*Requirements defined: 2026-06-06*
*Last updated: 2026-06-07 â€” v1.1 MVP2 requirements added (29 new: MUI-01..06, PROD-01..06, SEG-01..05, SDK-01..12)*
