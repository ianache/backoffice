# BackOffice Multi-Tenant Platform

## What This Is

Plataforma empresarial de administración multi-tenant que permite gestionar tenants, usuarios por tenant y feature flags jerárquicos con evaluación determinista. Diseñada para operar en entornos multi-producto, multi-país y multi-idioma, con personalización whitelabel a dos niveles (tenant → empresa). La arquitectura sigue el patrón Web App (Vue + Pinia) + BFF Node.js + Backend Python + PostgreSQL + Keycloak.

## Core Value

Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.

## Requirements

### Validated

(None yet — ship to validate)

### Active

#### Tenant Management
- [ ] PlatformAdmin puede crear, editar, suspender y eliminar tenants
- [ ] Tenant almacena: name, country, default_language, default_currency, default_units, whitelabel_config, status
- [ ] PlatformAdmin puede asociar productos habilitados a un tenant

#### User Management
- [ ] TenantAdmin puede crear usuarios dentro de su tenant
- [ ] Usuarios tienen roles asignables: TenantOwner, TenantAdmin, TenantViewer, ProductManager, ProductDeveloper, ProductQA
- [ ] TenantAdmin puede activar/desactivar usuarios
- [ ] TenantAdmin puede resetear MFA de un usuario
- [ ] Toda acción de usuario genera entrada en audit log

#### Authentication & MFA
- [ ] Autenticación via Keycloak como IdP
- [ ] MFA obligatorio para roles críticos (PlatformAdmin, TenantOwner, TenantAdmin)
- [ ] Factores soportados: TOTP, WebAuthn/FIDO2, OTP (fallback)
- [ ] Autenticación adaptativa basada en riesgo

#### Feature Flags
- [ ] Feature flags configurables en 4 niveles: Global → Tenant → Producto → Empresa
- [ ] Atributos de flag: name, default, complex, ttl, enabled, environment
- [ ] Resolución jerárquica: Empresa > Producto > Tenant > Global
- [ ] Reglas de evaluación: equals, in, notIn, contains, regex, rollout porcentual
- [ ] Segmentos reutilizables y jerárquicos
- [ ] Evaluación local < 1ms, evaluación remota < 50ms

#### Rule Builder
- [ ] Crear y editar reglas visualmente
- [ ] Ordenar reglas via drag & drop
- [ ] Previsualización de resultados de evaluación

### Out of Scope

- Gestión de clientes (personas y empresas) — Fase 2
- Doble whitelabel (tenant + empresa) — Fase 2
- Localización avanzada (idioma, moneda, formatos por nivel) — Fase 2
- Observabilidad / SLA / SLO / Alertas — Fase 3
- MFA avanzado (Biométricos), Experimentos A/B — Fase 4
- Integraciones externas — Fase 4
- Mobile app — fuera de scope

## Context

El PRD completo está en `PRD.md` en la raíz del proyecto. Contiene el modelo de datos completo (15+ tablas), ADRs, ICD (Interface Control Document) con todas las rutas Web→BFF→Backend→Keycloak, y el modelo de permisos detallado.

El diseño UX/UI vive en Google Stitch: https://stitch.withgoogle.com/u/1/projects/5651761190718398526

**Reglas estrictas del proyecto (de PRD.md §22):**
1. No crear patrones nuevos cuando ya existen patrones establecidos
2. Preferir editar archivos existentes sobre crear nuevos
3. Soluciones aburridas, legibles y seguras para producción
4. Explicar POR QUÉ antes de generar cambios grandes

## Constraints

- **Stack**: Vue 3 + Pinia / Node.js BFF / Python Backend / PostgreSQL / Keycloak — cerrado, ya decidido
- **Multi-tenant**: Aislamiento lógico (no físico) — decisión de arquitectura
- **Performance**: Evaluación local flags < 1ms, remota < 50ms, health checks < 100ms
- **Disponibilidad**: 99.9% uptime target
- **Seguridad**: Zero Trust, MFA obligatorio para roles críticos, auditoría completa

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Vue 3 + Pinia para Web App | Ecosistema reactivo moderno, composición flexible | — Pending |
| Node.js BFF como capa intermedia | Desacopla Web de Backend, permite transformación de datos | — Pending |
| Python Backend | Stack elegido para lógica de negocio y servicios internos | — Pending |
| Keycloak como IdP | Solución enterprise para auth + MFA + roles | — Pending |
| Multi-tenant lógico | Simplifica operaciones frente a aislamiento físico | — Pending |
| Feature Flags como core value | Sin evaluación determinista, el sistema no diferencia | — Pending |
| Evaluación jerárquica: Empresa > Producto > Tenant > Global | Permite personalización granular sin conflictos | — Pending |

---
*Last updated: 2026-06-06 after initialization*
