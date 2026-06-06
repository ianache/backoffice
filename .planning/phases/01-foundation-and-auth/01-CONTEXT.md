# Phase 1: Foundation & Auth - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** PRD Express Path (PRD.md)

<domain>
## Phase Boundary

Phase 1 entrega la capa de autenticación completa que habilita el resto del sistema. Sin esto, ningún rol puede acceder a ninguna pantalla. El objetivo es: usuarios autorizados pueden autenticarse via Keycloak, obtener JWT, y tener sus roles propagados correctamente desde Keycloak → BFF → frontend Vue.

**In scope:**
- Login con email/password via Keycloak
- Sesión persistente con JWT
- Propagación de roles al frontend
- Guards de rutas según rol

**Out of scope (Phase 1):**
- MFA (TOTP, WebAuthn/FIDO2, OTP, biométrico) — v2
- Autenticación adaptativa por riesgo — v2
- Gestión de tenants/usuarios — Phase 2 y 3

</domain>

<decisions>
## Implementation Decisions

### Stack (Locked — PRD §15 + DrawIO architecture diagram)
- Frontend: Vue 3 + Pinia — arquitectura **micro-frontend** (ver abajo)
- BFF: Node.js + Redis (caching layer visible en drawio)
- Backend: Python / **FastAPI** (confirmado en drawio: "backend (api) [Python / FastAPI]")
- Auth/IdP: Keycloak
- Tokens: JWT emitidos por Keycloak
- DB: PostgreSQL schema: backoffice

### Arquitectura Auth (Locked — PRD §3.5, §15, §17 + DrawIO)
- Keycloak es el único IdP — no hay auth custom
- El BFF actúa como intermediario: recibe tokens de Keycloak, los valida, extrae roles
- El frontend Vue obtiene el JWT via BFF (no habla directamente con Keycloak en producción)
- Las rutas BFF relevantes según PRD ICD: BFF → Keycloak para crear usuario, asignar roles, resetear MFA
- **PKCS/PKCE flow**: DrawIO muestra conexión BFF → Keycloak etiquetada "PKCS" — usar PKCE (Proof Key for Code Exchange) como OAuth2 flow

### Arquitectura Micro-Frontend (Locked — DrawIO architecture diagram)
El sistema usa una arquitectura micro-frontend:
- `portal (shell)` [Vue + Pinia] — shell app principal, monta los micro-UIs
- `microuis` — contenedor de micro-frontends montados por el shell:
  - **`mui security`** — micro-UI de auth/seguridad (Phase 1 vive aquí)
  - `mui tenants` — gestión de tenants (Phase 2)
  - `mui feature-flags` — feature flags (Phase 4)
- El shell comunica con BFF via `http` (requests) y recibe via `ws/sse` (WebSocket/SSE para real-time)
- **Phase 1 entrega**: portal shell funcional + mui security con login + propagación de roles

### Modelo de Datos Adicional (DrawIO Página 3)
- `Tenant`: guid, name, created_at, created_by, state {active, inactive}
- `Product`: guid, name, description, created_at, created_by, state {active, inactive}
- `Product → ProductModule [+] → ProductFeature [+]` (jerarquía de módulos y features)
- Esta estructura es de Phase 2, pero informa el modelo de datos que el BFF debe conocer para propagar permisos por producto

### Roles (Locked — PRD §3)
Los roles que deben propagarse al frontend en Phase 1:
- Global: PlatformAdmin
- Por tenant: TenantOwner, TenantAdmin, TenantViewer
- Por producto: ProductManager, ProductDeveloper, ProductQA
- Por empresa: CompanyAdmin, CompanyUser

### Autenticación Simple (Locked — decisión de scope)
- Solo email/password para v1
- No MFA obligatorio en Phase 1
- Sesión persiste con JWT válido (refresh token incluido)

### Reglas estrictas del proyecto (Locked — PRD §22)
1. No crear patrones nuevos cuando ya existen
2. Preferir editar archivos existentes sobre crear nuevos
3. Soluciones aburridas, legibles y seguras para producción
4. Explicar POR QUÉ antes de generar cambios grandes

### Claude's Discretion
Los siguientes aspectos de implementación no están prescritos en el PRD/DrawIO y quedan a criterio técnico:
- Tecnología de micro-frontend federation (Module Federation / Vite Federation / monorepo con lazy-load)
- Estructura del store Pinia para auth (token, user, roles)
- Estrategia de refresh de JWT (interceptor axios, vue-router guard)
- Implementación de route guards en Vue Router (shell-level vs MUI-level)
- Cómo el BFF valida el JWT de Keycloak (middleware con `jose`)
- Estructura de carpetas del monorepo (shell + microuis)
- Manejo de errores de autenticación en el frontend

</decisions>

<specifics>
## Specific Ideas

**ICD relevante (PRD §17) — Rutas BFF → Keycloak:**
- Crear usuario en Keycloak
- Asignar roles a usuario
- Resetear MFA (diferido Phase 1, pero la integración BFF↔Keycloak debe permitirlo)

**Modelo de Roles (PRD §14) — lo que el frontend necesita recibir:**
| Rol | Alcance | Permisos clave |
|-----|---------|----------------|
| PlatformAdmin | Global | CRUD tenants, whitelabels, flags globales |
| TenantOwner | Tenant | CRUD productos, whitelabel, usuarios |
| TenantAdmin | Tenant | CRUD usuarios, productos, flags |
| TenantViewer | Tenant | Solo lectura |
| ProductManager | Producto | CRUD flags, reglas, segmentos |
| ProductDeveloper | Producto | CRUD reglas técnicas |
| ProductQA | Producto | Cambiar flags en dev/qa |
| CompanyAdmin | Empresa | Gestiona whitelabel y usuarios internos |
| CompanyUser | Empresa | Acceso a productos |

**Non-functional requirements relevantes (PRD §13):**
- Keycloak + MFA (MFA diferido pero la integración Keycloak debe estar lista para soportarlo)
- Zero Trust — roles verificados en cada request al BFF
- Auditoría obligatoria (login events deben quedar registrados)

</specifics>

<deferred>
## Deferred Ideas

Estos elementos aparecen en el PRD pero quedan diferidos a fases posteriores:

- **MFA (PRD §3.5, §12):** TOTP, WebAuthn/FIDO2, OTP fallback, biométrico — Fase 2 (v2 MFA)
- **Autenticación adaptativa por riesgo** (IP, geolocalización, comportamiento) — Fase 2
- **MFA obligatorio para roles críticos** — Fase 2 (cuando MFA está implementado)
- **Configuración de MFA por tenant y empresa** — Fase 2+

</deferred>

---

*Phase: 01-foundation-and-auth*
*Context gathered: 2026-06-06 via PRD Express Path (PRD.md)*
