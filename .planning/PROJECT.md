# BackOffice Multi-Tenant Platform

## What This Is

Plataforma empresarial de administración multi-tenant que permite gestionar tenants, usuarios por tenant y feature flags jerárquicos con evaluación determinista. Incluye un rule builder visual con drag & drop, evaluación en tiempo real, e interfaz alineada al design system de Google Stitch (Material 3). Diseñada para operar en entornos multi-producto, multi-país y multi-idioma. Stack: Vue 3 + Pinia / Node.js BFF / Python FastAPI / MySQL / Keycloak.

## Core Value

Los feature flags jerárquicos con evaluación determinista deben funcionar — sin esto, los tenants no pueden controlar su funcionalidad y el sistema no tiene razón de existir.

## Requirements

### Validated (v1.0)

- ✓ PlatformAdmin puede crear, editar, suspender y eliminar tenants — v1.0
- ✓ Tenant almacena: name, country, language, currency, units, whitelabel_config, status — v1.0
- ✓ PlatformAdmin puede asociar productos habilitados a un tenant — v1.0
- ✓ TenantAdmin puede gestionar usuarios (crear, editar, activar/desactivar, resetear MFA) — v1.0
- ✓ Roles asignables: TenantOwner, TenantAdmin, TenantViewer, ProductManager, ProductDeveloper, ProductQA — v1.0
- ✓ Toda acción de usuario genera entrada en audit log — v1.0
- ✓ Autenticación via Keycloak con PKCE y ROPC — v1.0
- ✓ Feature flags configurables en 3 niveles: Global → Tenant → Producto — v1.0
- ✓ Resolución jerárquica: Producto > Tenant > Global — v1.0
- ✓ Operadores de evaluación: equals, in, notIn, contains, regex — v1.0
- ✓ Segmentos reutilizables en múltiples flags y niveles — v1.0
- ✓ Rule Builder visual: crear/editar reglas sin código — v1.0
- ✓ Drag & drop para prioridad de reglas — v1.0
- ✓ Live simulator: previsualización de evaluación con JSON de contexto — v1.0
- ✓ UI alineada a Google Stitch (Material 3, Nav Rail, high-density) — v1.0
- ✓ Soporte Light/Dark mode persistente — v1.0

### Active (v1.1+)

#### Client Management
- [ ] TenantAdmin puede crear clientes tipo Persona y Empresa
- [ ] Doble whitelabel: Empresa hereda y sobrescribe configuración de Tenant

#### Feature Flags Avanzados
- [ ] Rollout porcentual — activación gradual de flag para porcentaje configurable de usuarios
- [ ] Nivel Empresa en jerarquía de flags (Empresa > Producto > Tenant > Global)

#### Dashboard & Observabilidad
- [ ] KPI cards en dashboard (Active Tenants, Total Products, System Health)
- [ ] Sección de eventos, alertas y notificaciones en tiempo real

#### MFA Avanzado
- [ ] MFA obligatorio para roles críticos (PlatformAdmin, TenantOwner, TenantAdmin)
- [ ] TOTP, WebAuthn/FIDO2, OTP como fallback

### Out of Scope

- Localización avanzada (idioma, moneda, formatos por nivel) — diferido v2.0
- Experimentos A/B — diferido v2.0
- Mobile app — web-first strategy
- Integraciones externas — diferido v2.0

## Context

**v1.0 shipped 2026-06-08** — 7 fases, 29 planes, ~8,016 LOC (5,882 TS/Vue + 1,629 Python + 505 Node.js).

El PRD completo está en `PRD.md` en la raíz del proyecto. Contiene el modelo de datos completo (15+ tablas), ADRs, ICD (Interface Control Document) con todas las rutas Web→BFF→Backend→Keycloak, y el modelo de permisos detallado.

El diseño UX/UI vive en Google Stitch: https://stitch.withgoogle.com/u/1/projects/5651761190718398526

**Reglas estrictas del proyecto (de PRD.md §22):**
1. No crear patrones nuevos cuando ya existen patrones establecidos
2. Preferir editar archivos existentes sobre crear nuevos
3. Soluciones aburridas, legibles y seguras para producción
4. Explicar POR QUÉ antes de generar cambios grandes

**Deuda técnica conocida:**
- Visual baselines de `portal/tests/visual/internal.spec.ts` no generadas (4/5 faltantes) — nav timing issue en Playwright, infra E2E lista en `portal/.env.playwright`

## Constraints

- **Stack**: Vue 3 + Pinia / Node.js BFF / Python FastAPI / MySQL / Keycloak — cerrado
- **Multi-tenant**: Aislamiento lógico (no físico) — decisión de arquitectura
- **Performance**: Evaluación local flags < 1ms, remota < 50ms, health checks < 100ms
- **Disponibilidad**: 99.9% uptime target
- **Seguridad**: Zero Trust, MFA obligatorio para roles críticos, auditoría completa

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Vue 3 + Pinia para Web App | Ecosistema reactivo moderno, composición flexible | ✓ Funcionó bien — tipado con composables limpio |
| Node.js BFF como capa intermedia | Desacopla Web de Backend, permite transformación de datos | ✓ Proxy pattern con jose JWT validation probado |
| Python FastAPI Backend | Stack elegido para lógica de negocio y servicios internos | ✓ SQLAlchemy + Alembic migrations sólido |
| Keycloak como IdP | Solución enterprise para auth + MFA + roles | ✓ PKCE + ROPC ambos funcionales en QA |
| MySQL (no PostgreSQL) | Decisión de infra del cliente | ✓ Alembic migrations compatibles |
| Multi-tenant lógico | Simplifica operaciones frente a aislamiento físico | ✓ tenant_id en JWT claims propagado a toda la stack |
| Feature Flags como core value | Sin evaluación determinista, el sistema no diferencia | ✓ Jerarquía 3 niveles + segmentos reutilizables |
| Evaluación jerárquica: Producto > Tenant > Global | Permite personalización granular sin conflictos | ✓ TypeScript port de Python en rule builder verified |
| Google Stitch (Material 3) como design system | Coherencia visual con Google Cloud Console style | ✓ Nav Rail 72px + high-density table + M3 tokens |
| vuedraggable@next para rule builder | Única lib drag-and-drop compatible con Vue 3 | ✓ Funcionó con handle=".drag-handle" |
| VITE_E2E_SKIP_AUTH para Playwright E2E | Evita Keycloak init en tests visuales | ⚠️ Infra lista, snapshots pendientes de generar |

---
*Last updated: 2026-06-08 after v1.0 milestone*
