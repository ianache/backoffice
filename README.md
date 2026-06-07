# BackOffice Platform

Multi-tenant BackOffice platform — Vue 3 portal + Node.js BFF + Keycloak (QA).

## Stack

| Componente | Tecnología | Puerto |
|------------|------------|--------|
| Portal (frontend) | Vue 3 + Vite + Pinia | 5173 |
| BFF (backend) | Node.js + Express + TypeScript | 3000 |
| Keycloak (autenticación) | QA remoto — sin instalación local | 443 |

## Prerequisitos

- **Node.js** ≥ 20 — [nodejs.org](https://nodejs.org)
- **pnpm** ≥ 9 — `npm install -g pnpm`
- Acceso a internet (el BFF valida tokens contra el Keycloak QA en `oauth2.qa.comsatel.com.pe`)

## Instalación (primera vez)

```bash
# Desde la raíz del monorepo
pnpm install
```

## Configuración de entorno

Los archivos `.env` ya están configurados para apuntar al Keycloak QA. Verifica que existan:

**`bff/.env`**
```
PORT=3000
KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
KEYCLOAK_REALM=Apps
KEYCLOAK_CLIENT_ID=backoffice-bff
KEYCLOAK_CLIENT_SECRET=Krhias4gcLDKZc7U0767dGyXauEccxva
FRONTEND_URL=http://localhost:5173
NODE_ENV=development
```

**`portal/.env`**
```
VITE_KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
VITE_KEYCLOAK_REALM=Apps
VITE_KEYCLOAK_CLIENT_ID=backoffice-portal
VITE_BFF_URL=http://localhost:3000
```

Si los archivos no existen, cópialos desde sus respectivos `.env.example`:

```bash
cp bff/.env.example bff/.env
cp portal/.env.example portal/.env
```

## Iniciar en desarrollo

### Opción A — Todos los servicios en paralelo (recomendado)

```bash
pnpm dev
```

Inicia BFF (puerto 3000) y Portal (puerto 5173) en paralelo.

### Opción B — Cada servicio por separado

Abre **dos terminales**:

**Terminal 1 — BFF:**
```bash
cd bff
pnpm dev
```

**Terminal 2 — Portal:**
```bash
cd portal
pnpm dev
```

**Terminal 3 - backend:**
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Verificar que todo funciona

### 1. BFF saludable
```bash
curl http://localhost:3000/health
# Esperado: {"status":"ok","service":"backoffice-bff"}
```

### 2. BFF rechaza sin token
```bash
curl http://localhost:3000/auth/me
# Esperado: 401 {"error":"Missing token"}
```

### 3. Portal carga
Abre [http://localhost:5173](http://localhost:5173) — deberías ser redirigido al login de Keycloak QA.

## Credenciales de prueba

| Campo | Valor |
|-------|-------|
| URL | https://oauth2.qa.comsatel.com.pe |
| Realm | Apps |
| Usuario | `bo.admin@backoffice.dev` |
| Contraseña | `Backoffice1!` |
| Rol | PlatformAdmin |

## Flujo de autenticación

```
Browser → http://localhost:5173
  └─ keycloak-js detecta sin sesión
  └─ redirige a https://oauth2.qa.comsatel.com.pe/realms/Apps/protocol/openid-connect/auth
  └─ usuario ingresa credenciales
  └─ Keycloak redirige de vuelta a http://localhost:5173 con código PKCE
  └─ keycloak-js intercambia código por tokens
  └─ Portal guarda tokens en Pinia store
  └─ Axios adjunta Bearer token en cada request al BFF
  └─ BFF valida el JWT contra JWKS y extrae roles
```

## Keycloak QA — Referencia

| Item | Valor |
|------|-------|
| URL admin | https://oauth2.qa.comsatel.com.pe/admin |
| Realm | Apps |
| Client (portal) | `backoffice-portal` — público, PKCE S256 |
| Client (bff) | `backoffice-bff` — confidencial |
| JWKS URI | `https://oauth2.qa.comsatel.com.pe/realms/Apps/protocol/openid-connect/certs` |
| Issuer | `https://oauth2.qa.comsatel.com.pe/realms/Apps` |

### Roles disponibles (BackOffice)

`PlatformAdmin` · `TenantOwner` · `TenantAdmin` · `TenantViewer`
`ProductManager` · `ProductDeveloper` · `ProductQA`
`CompanyAdmin` · `CompanyUser`

## Tests

```bash
# Todos los paquetes
pnpm test

# Solo BFF
cd bff && pnpm test

# Solo Portal
cd portal && pnpm test
```

## Build de producción

```bash
pnpm build
```

## Estructura del monorepo

```
backoffice-platform/
├── bff/                    # Node.js BFF (Express + TypeScript)
│   ├── src/
│   │   ├── config/         # Variables de entorno
│   │   ├── middleware/     # auth.ts (JWT) · roles.ts (RBAC)
│   │   ├── routes/         # auth.ts → GET /auth/me
│   │   ├── services/       # keycloak.ts (JWKS singleton)
│   │   └── index.ts        # Entry point
│   └── .env
├── portal/                 # Vue 3 frontend (Vite)
│   ├── src/
│   │   ├── plugins/        # keycloak.ts (keycloak-js)
│   │   ├── stores/         # auth.ts (Pinia)
│   │   ├── router/         # index.ts (Vue Router + guards)
│   │   ├── services/       # api.ts (Axios interceptor)
│   │   └── views/          # Login · Dashboard · Unauthorized
│   └── .env
├── microuis/
│   └── mui-security/       # Micro-frontend (fase 2+)
└── package.json            # Workspace root — pnpm workspaces
```

## Solución de problemas

**Error: CORS al llamar al BFF**
El portal corre en `localhost:5173` y el BFF tiene CORS configurado para ese origen. Si cambias el puerto del portal, actualiza `FRONTEND_URL` en `bff/.env`.

**Error: 401 en /auth/me con token válido**
Verifica que `KEYCLOAK_REALM=Apps` (con mayúscula) en `bff/.env`. El issuer del token debe coincidir exactamente.

**Error: redirect_uri_mismatch en Keycloak**
El client `backoffice-portal` tiene configurado `http://localhost:5173/*`. Si usas otro puerto, actualízalo en la consola de administración de Keycloak QA.

**Portal no redirige a Keycloak**
Verifica `VITE_KEYCLOAK_CLIENT_ID=backoffice-portal` en `portal/.env`. El client anterior `backoffice-frontend` fue reemplazado.
