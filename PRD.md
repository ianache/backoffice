📘 PRD INTEGRADO FINAL — Plataforma BackOffice Multi‑Tenant
(Product Requirements Document — versión consolidada)

---

1. Visión General del Producto

La Plataforma BackOffice Multi‑Tenant es un sistema empresarial diseñado para operar en entornos:

- Multi‑tenant (múltiples clientes corporativos)  
- Multi‑producto  
- Multi‑país  
- Multi‑idioma  
- Multi‑whitelabel  
- Multi‑nivel de personalización  

El BackOffice permite gestionar:

- Tenants  
- Usuarios por tenant  
- Clientes finales (personas y empresas)  
- Whitelabel multinivel (tenant → empresa)  
- Localización avanzada (idioma, moneda, unidades, mensajes)  
- Feature Flags jerárquicos  
- Observabilidad con SLA/SLO  
- MFA moderno  
- Auditoría y telemetría  

---

2. Objetivos del Producto

2.1 Objetivos funcionales
- Centralizar la administración de tenants, usuarios, clientes y productos.  
- Permitir personalización visual y funcional a dos niveles (tenant y empresa).  
- Soportar operación global (países, idiomas, monedas, unidades).  
- Controlar funcionalidades mediante Feature Flags jerárquicos.  
- Monitorear salud de servicios y alertar por degradación.  
- Garantizar seguridad empresarial con MFA y Zero Trust.

2.2 Objetivos técnicos
- Arquitectura desacoplada Web + BFF + Backend.  
- Seguridad con Keycloak y MFA.  
- Evaluación determinista de Feature Flags.  
- Observabilidad integrada.  
- Escalabilidad horizontal.  

---

3. Usuarios y Roles

3.1 Roles globales
- PlatformAdmin — controla toda la plataforma.

3.2 Roles por tenant
- TenantOwner  
- TenantAdmin  
- TenantViewer

3.3 Roles por producto dentro del tenant
- ProductManager  
- ProductDeveloper  
- ProductQA

3.4 Roles por cliente empresa
- CompanyAdmin  
- CompanyUser

3.5 Autenticación y MFA
- Keycloak como IdP.  
- MFA obligatorio para roles críticos.  
- Factores soportados:
  - TOTP  
  - WebAuthn / FIDO2  
  - Biométricos  
  - OTP (fallback)  
- Autenticación adaptativa basada en riesgo.

---

4. Gestión de Tenants

Funcionalidades
- Crear, editar, suspender, eliminar tenants.  
- Configurar whitelabel del tenant.  
- Configurar idioma, moneda, unidades.  
- Asociar productos habilitados.  
- Gestionar usuarios del tenant.  
- Gestionar clientes del tenant.  

Datos del tenant
- name  
- country  
- default_language  
- default_currency  
- default_units  
- whitelabel_config  
- status  

---

5. Gestión de Usuarios por Tenant

Funcionalidades
- Crear usuarios.  
- Asignar roles por tenant y por producto.  
- Activar/desactivar usuarios.  
- Resetear MFA.  
- Registrar auditoría.

Datos del usuario
- email  
- name  
- roles  
- mfa_devices  
- status  

---

6. Gestión de Clientes (Personas y Empresas)

6.1 Personas naturales
- Datos básicos.  
- Idioma y país.  
- Preferencias opcionales.

6.2 Empresas
- Whitelabel propio (segundo nivel).  
- Idioma, moneda, unidades.  
- Mensajes personalizados.  
- Usuarios internos.  

Datos del cliente empresa
- name  
- country  
- default_language  
- default_currency  
- default_units  
- company_whitelabel  
- custom_labels  
- custom_messages  

---

7. Doble Whitelabel (Tenant + Empresa)

7.1 Whitelabel del Tenant
- Logo  
- Colores  
- Tipografía  
- Dominio  
- Mensajes base  

7.2 Whitelabel de Empresa
- Logo propio  
- Colores propios  
- Dominio propio  
- Mensajes propios  

7.3 Resolución jerárquica
`
Plataforma → Tenant → Empresa → Usuario
`

---

8. Localización Avanzada

Configurable por:
- Plataforma  
- Tenant  
- Empresa  
- Usuario  

Elementos
- Idioma  
- Moneda  
- Unidades  
- Formatos  
- Labels  
- Mensajes  

Resolución
`
Empresa > Tenant > Plataforma > Usuario
`

---

9. Feature Flags Jerárquicos

Niveles
1. Global  
2. Tenant  
3. Producto  
4. Empresa  

Atributos
- name  
- default  
- complex  
- ttl  
- enabled  
- environment  

Resolución
`
Empresa > Producto > Tenant > Global
`

Reglas
- equals  
- in  
- notIn  
- contains  
- regex  
- rollout porcentual  

Segmentos
- Reutilizables  
- Jerárquicos  

---

10. Rule Builder

Funcionalidades
- Crear reglas visualmente.  
- Ordenar reglas (drag & drop).  
- Evaluación determinista.  
- Previsualización de resultados.  

---

11. Observabilidad, SLA y SLO

11.1 Servicios monitoreados
- APIs internas  
- Backend Python  
- BFF  
- PostgreSQL  
- Keycloak  
- Servicios externos  

11.2 Health checks
- Frecuencia configurable  
- Latencia  
- Estado UP/DOWN/DEGRADED  

11.3 Métricas
- Uptime  
- Latencia p95/p99  
- Error rate  

11.4 Alertas
- SLA incumplido  
- SLO degradado  
- Error rate alto  

11.5 Dashboard
- Estado actual  
- Tendencias  
- Impacto en Feature Flags  

---

12. Seguridad y MFA

Factores soportados
- TOTP  
- WebAuthn / FIDO2  
- Biométricos  
- OTP (fallback)  

Políticas
- MFA obligatorio para roles críticos.  
- MFA configurable por tenant.  
- MFA configurable por empresa.  
- Autenticación adaptativa.  

---

13. Requerimientos No Funcionales

Seguridad
- Keycloak  
- MFA  
- Zero Trust  
- Auditoría obligatoria  

Performance
- Evaluación local < 1ms  
- Evaluación remota < 50ms  
- Health checks < 100ms  

Escalabilidad
- Backend stateless  
- Cache distribuida  

Disponibilidad
- 99.9% uptime  

---

14. Modelo de Permisos Multi‑Tenant

| Rol | Alcance | Permisos |
|-----|---------|----------|
| PlatformAdmin | Global | CRUD tenants, whitelabels, flags globales |
| TenantOwner | Tenant | CRUD productos, whitelabel, usuarios |
| TenantAdmin | Tenant | CRUD usuarios, productos, flags |
| TenantViewer | Tenant | Solo lectura |
| ProductManager | Producto | CRUD flags, reglas, segmentos |
| ProductDeveloper | Producto | CRUD reglas técnicas |
| ProductQA | Producto | Cambiar flags en dev/qa |
| CompanyAdmin | Empresa | Gestiona whitelabel y usuarios internos |
| CompanyUser | Empresa | Acceso a productos |

---

15. Arquitectura del Sistema

Componentes
- Web App (Vue + Pinia)  
- BFF Node.js  
- Backend Python  
- PostgreSQL  
- Keycloak  
- WebSocket Hub  

Servicios internos
- TenantService  
- UserManagementService  
- ClientManagementService  
- WhiteLabelService  
- LocalizationService  
- FeatureFlagService  
- EvaluationEngine  
- HealthCheckEngine  
- AuditService  
- TelemetryService  

---

16. ADR — Architecture Decision Records

Incluye decisiones sobre:

- Arquitectura Web + BFF + Backend  
- Keycloak como IdP  
- MFA obligatorio  
- Evaluación local + remota  
- PostgreSQL  
- WebSocket  
- Multi‑tenant lógico  
- Whitelabel multinivel  
- Localización jerárquica  
- Health checks activos  
- SLA/SLO configurables  

---

17. ICD — Interface Control Document

Web → BFF
- /bff/tenants  
- /bff/tenant/{id}/users  
- /bff/tenant/{id}/clients  
- /bff/tenant/{id}/product/{pid}/flags  
- /bff/health/services  

BFF → Backend
- /api/flags  
- /api/evaluate  
- /api/clients  
- /api/localization  
- /api/health/services  

BFF → Keycloak
- Crear usuario  
- Asignar roles  
- Resetear MFA  

---

18. Modelo de Datos

Incluye tablas:

- tenants  
- tenant_users  
- tenantuserroles  
- clients  
- client_whitelabels  
- localization_profiles  
- products  
- flags  
- rules  
- segments  
- servicehealthsamples  
- servicehealthmetrics  
- audit_log  
- usermfadevices  
- usermfaevents  

---

19. Roadmap

Fase 1
- Tenants  
- Usuarios  
- Feature Flags  

Fase 2
- Clientes empresa  
- Doble whitelabel  
- Localización  

Fase 3
- Observabilidad  
- SLA/SLO  
- Alertas  

Fase 4
- MFA avanzado  
- Experimentos A/B  
- Integraciones externas  

---

20. Glosario

- Tenant: cliente corporativo.  
- Cliente Empresa: organización dentro del tenant.  
- Cliente Persona: usuario final individual.  
- Whitelabel: personalización visual.  
- Feature Flag: interruptor de funcionalidad.  
- SLA: Service Level Agreement.  
- SLO: Service Level Objective.  
- MFA: Multi‑Factor Authentication.  
- Health Check: verificación de estado.  

---

🔗 Navegación rápida (Guided Links)

- Feature Flags  
- Whitelabel multinivel  
- Localización avanzada  
- MFA moderno  
- Observabilidad SLA/SLO  
- Modelo de permisos  

---

21. UX/UI

El diseño de UX/UI se encuentra en Google Stitch https://stitch.withgoogle.com/u/1/projects/5651761190718398526?pli=1

22. Reglas Estrictas (Harness)
Se debe colocar en AGENT.md, CLAUDE.md y GEMINI.md.

1. Do not create new patterns when existing ones already exist
2. Prefer editing existing files over creating new ones.
3. Keep solutions boring, readable, and production-safe
4. Explain WHY before generating large changes
