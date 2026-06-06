# Phase 1: Foundation & Auth - Research

**Researched:** 2026-06-06
**Domain:** Keycloak + Vue 3 + Pinia + Node.js BFF authentication
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Stack (Locked — PRD §15)**
- Frontend: Vue 3 + Pinia
- BFF: Node.js
- Backend: Python
- Auth/IdP: Keycloak
- Tokens: JWT emitidos por Keycloak

**Arquitectura Auth (Locked — PRD §3.5, §15, §17)**
- Keycloak es el único IdP — no hay auth custom
- El BFF actúa como intermediario: recibe tokens de Keycloak, los valida, extrae roles
- El frontend Vue obtiene el JWT via BFF (no habla directamente con Keycloak en producción)
- Las rutas BFF relevantes según PRD ICD: BFF → Keycloak para crear usuario, asignar roles, resetear MFA

**Roles (Locked — PRD §3)**
Los roles que deben propagarse al frontend en Phase 1:
- Global: PlatformAdmin
- Por tenant: TenantOwner, TenantAdmin, TenantViewer
- Por producto: ProductManager, ProductDeveloper, ProductQA
- Por empresa: CompanyAdmin, CompanyUser

**Autenticación Simple (Locked — decisión de scope)**
- Solo email/password para v1
- No MFA obligatorio en Phase 1
- Sesión persiste con JWT válido (refresh token incluido)

**Reglas estrictas del proyecto (Locked — PRD §22)**
1. No crear patrones nuevos cuando ya existen
2. Preferir editar archivos existentes sobre crear nuevos
3. Soluciones aburridas, legibles y seguras para producción
4. Explicar POR QUÉ antes de generar cambios grandes

### Claude's Discretion

Los siguientes aspectos de implementación no están prescritos en el PRD y quedan a criterio técnico:
- Estructura del store Pinia para auth (token, user, roles)
- Estrategia de refresh de JWT (interceptor axios, vue-router guard)
- Implementación de route guards en Vue Router
- Cómo el BFF valida el JWT de Keycloak (middleware, biblioteca)
- Estructura de carpetas del proyecto (frontend y BFF)
- Manejo de errores de autenticación en el frontend

### Deferred Ideas (OUT OF SCOPE)

- **MFA (PRD §3.5, §12):** TOTP, WebAuthn/FIDO2, OTP fallback, biométrico — Fase 2 (v2 MFA)
- **Autenticación adaptativa por riesgo** (IP, geolocalización, comportamiento) — Fase 2
- **MFA obligatorio para roles críticos** — Fase 2 (cuando MFA está implementado)
- **Configuración de MFA por tenant y empresa** — Fase 2+
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | Usuario puede autenticarse con email/password via Keycloak como IdP | Keycloak redirect flow via keycloak-js; `login-required` onLoad triggers Keycloak hosted login page; BFF OIDC code exchange |
| AUTH-02 | Sesión persiste con tokens JWT emitidos por Keycloak | pinia-plugin-persistedstate for token storage; keycloak.updateToken() for refresh; axios request interceptor pattern |
| AUTH-03 | Roles del usuario se propagan desde Keycloak al BFF y respetados en el frontend | realm_access.roles claim in JWT decoded by BFF; BFF passes roles in session/user endpoint; Pinia stores roles; Vue Router meta.roles guards |
</phase_requirements>

---

## Summary

This phase implements the full authentication layer: Keycloak as the sole Identity Provider, a Node.js BFF that exchanges authorization codes and validates JWTs, and a Vue 3 frontend that stores auth state in Pinia and enforces route guards. The architecture is a standard OIDC Authorization Code flow where the frontend delegates to the BFF rather than talking directly to Keycloak in production.

The key design decision (already locked) is that the Vue frontend talks to the BFF, not directly to Keycloak. In practice this means the BFF handles the OIDC redirect, token exchange, JWT validation, role extraction, and exposes a `/auth/me` endpoint. The frontend holds the access token in Pinia state (with `pinia-plugin-persistedstate`) and sends it to the BFF on every request; the BFF validates the token on every request (Zero Trust, per PRD §13).

The critical pitfall to avoid is the `keycloak-nodejs-connect` package: it carries a deprecation notice (no removal date yet, but the Keycloak team officially added it ~3 years ago). Use `jose` for JWT verification on the BFF instead — it is ESM-native, actively maintained, works across all runtimes, and is the community-accepted replacement.

**Primary recommendation:** Initialize Keycloak in `main.ts` before `app.mount()`, use `keycloak-js` with `check-sso` on the frontend, validate tokens on the BFF with `jose` + `createRemoteJWKSet`, persist auth state with `pinia-plugin-persistedstate`, and protect routes with Vue Router `beforeEach` guards that read `meta.requiresAuth` and `meta.roles`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| keycloak-js | ^26.0.0 | Official Keycloak JS adapter; handles OIDC redirect, token lifecycle | Official Keycloak client; matches server version |
| pinia | ^2.2.0 | Auth state management (isAuthenticated, user, token, roles) | Vue 3 official state manager; replaces Vuex |
| vue-router | ^4.4.0 | Client-side routing with navigation guards | Official Vue 3 router |
| pinia-plugin-persistedstate | ^4.x | Persists auth store to localStorage/sessionStorage across page reloads | AUTH-02 requirement: session persists across reloads |
| jose | ^5.x | JWT verification on BFF using Keycloak JWKS endpoint | keycloak-nodejs-connect is deprecated; jose is the community-accepted replacement |
| express | ^4.x | BFF HTTP server | Established Node.js framework; BFF stack decision |
| express-session | ^1.18.x | Server-side session storage (optional enhancement over stateless JWT) | Needed if BFF stores tokens server-side (BFF pattern) |
| axios | ^1.x | HTTP client on frontend; supports request interceptors for token refresh | Standard Vue HTTP client; interceptor pattern for token refresh |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @dsb-norge/vue-keycloak-js | ^3.0.7 | Vue 3 plugin wrapping keycloak-js with Composition API | If you want `useKeycloak()` composable and reactive state rather than managing raw keycloak-js |
| connect-redis | ^8.x | Redis session store for express-session | Production: multi-instance BFF needs shared session store |
| cors | ^2.x | CORS middleware on BFF | Required for Vue dev server → BFF cross-origin requests |
| dotenv | ^16.x | Environment variable management | Keycloak URL, realm, client ID from env |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| keycloak-js (direct) | @dsb-norge/vue-keycloak-js | The wrapper adds Vue 3 composable API; use raw keycloak-js if you want minimal dependencies and full control via Pinia store |
| jose (BFF JWT verify) | jsonwebtoken + jwks-rsa | Both work; `jose` is ESM-native, more modern, single package; `jsonwebtoken` is older CJS but extremely battle-tested |
| Stateless JWT on BFF | HttpOnly cookie + server session | Cookie+session is more secure against XSS; stateless JWT is simpler. PRD §13 says Zero Trust roles verified each request — stateless JWT satisfies this |

**Installation (Frontend):**
```bash
npm install keycloak-js pinia pinia-plugin-persistedstate vue-router axios
```

**Installation (BFF):**
```bash
npm install express jose express-session cors dotenv
```

---

## Architecture Patterns

### Recommended Project Structure

**Frontend (Vue 3):**
```
src/
├── main.ts              # Keycloak init before app.mount()
├── plugins/
│   └── keycloak.ts      # Keycloak instance singleton
├── stores/
│   └── auth.ts          # Pinia auth store (token, user, roles, isAuthenticated)
├── router/
│   └── index.ts         # Vue Router + beforeEach guards
├── composables/
│   └── useAuth.ts       # useAuth() composable exposing store + authenticatedFetch
├── services/
│   └── api.ts           # Axios instance with request interceptor (token refresh)
├── views/
│   ├── LoginView.vue    # Redirects to Keycloak if unauthenticated
│   └── UnauthorizedView.vue
└── layouts/
    └── AuthLayout.vue   # Wraps protected pages
```

**BFF (Node.js/Express):**
```
src/
├── index.ts             # Express app entry
├── middleware/
│   ├── auth.ts          # JWT verification middleware (jose)
│   └── roles.ts         # Role enforcement middleware
├── routes/
│   ├── auth.ts          # /auth/callback, /auth/me, /auth/logout
│   └── proxy.ts         # Proxied routes to Python backend
├── services/
│   └── keycloak.ts      # JWKS client (createRemoteJWKSet) singleton
└── config/
    └── index.ts         # Env vars (KEYCLOAK_URL, REALM, CLIENT_ID, CLIENT_SECRET)
```

---

### Pattern 1: Keycloak Init Before App Mount

**What:** Initialize keycloak-js and populate Pinia auth store before `app.mount()` so the app never renders in an unknown auth state.
**When to use:** Always — prevents flash of unauthenticated content and race conditions.

```typescript
// src/main.ts
// Source: https://skycloak.io/blog/keycloak-vue-js-authentication-guide/
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)
app.use(router)

const authStore = useAuthStore()
authStore.init().then(() => {
  app.mount('#app')
})
```

---

### Pattern 2: Pinia Auth Store

**What:** Centralized auth state with `init()`, `login()`, `logout()`, `hasRole()` actions.
**When to use:** Single source of truth for auth state across the app.

```typescript
// src/stores/auth.ts
// Source: https://skycloak.io/blog/keycloak-vue-js-authentication-guide/
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import keycloak from '../plugins/keycloak'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const token = ref<string | null>(null)
  const user = ref<{ name: string; email: string } | null>(null)
  const roles = ref<string[]>([])
  const isLoading = ref(true)

  const hasRole = (role: string) => roles.value.includes(role)

  async function init() {
    isLoading.value = true
    try {
      const authenticated = await keycloak.init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
      })
      if (authenticated) {
        isAuthenticated.value = true
        token.value = keycloak.token ?? null
        roles.value = keycloak.realmAccess?.roles ?? []
        user.value = {
          name: keycloak.tokenParsed?.preferred_username ?? '',
          email: keycloak.tokenParsed?.email ?? '',
        }
        // Token refresh every 30 seconds
        setInterval(async () => {
          const refreshed = await keycloak.updateToken(60)
          if (refreshed) token.value = keycloak.token ?? null
        }, 30000)
      }
    } finally {
      isLoading.value = false
    }
  }

  function login() { keycloak.login() }
  function logout() { keycloak.logout() }

  return { isAuthenticated, token, user, roles, isLoading, hasRole, init, login, logout }
}, {
  persist: {
    paths: ['token', 'user', 'roles', 'isAuthenticated'],
    storage: sessionStorage, // sessionStorage is safer than localStorage for tokens
  }
})
```

---

### Pattern 3: Vue Router Navigation Guards

**What:** `beforeEach` guard checking `meta.requiresAuth` and `meta.roles` on every navigation.
**When to use:** All protected routes.

```typescript
// src/router/index.ts
// Source: https://router.vuejs.org/guide/advanced/navigation-guards.html
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('../views/LoginView.vue') },
    { path: '/unauthorized', component: () => import('../views/UnauthorizedView.vue') },
    {
      path: '/dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      component: () => import('../views/AdminView.vue'),
      meta: { requiresAuth: true, roles: ['PlatformAdmin'] }
    },
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  // Wait for Keycloak init
  if (authStore.isLoading) return true
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    authStore.login()
    return false
  }
  const requiredRoles = to.meta.roles as string[] | undefined
  if (requiredRoles?.length && !requiredRoles.some(r => authStore.hasRole(r))) {
    return { path: '/unauthorized' }
  }
  return true
})

export default router
```

---

### Pattern 4: BFF JWT Validation Middleware (jose)

**What:** Express middleware that validates Keycloak JWT on every protected BFF route using JWKS endpoint.
**When to use:** Every BFF route that proxies to the Python backend.

```typescript
// src/middleware/auth.ts
// Source: https://github.com/panva/jose + Keycloak JWKS endpoint
import { createRemoteJWKSet, jwtVerify } from 'jose'
import type { Request, Response, NextFunction } from 'express'

const JWKS = createRemoteJWKSet(
  new URL(`${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}/protocol/openid-connect/certs`)
)

export async function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing token' })
  }
  const token = authHeader.slice(7)
  try {
    const { payload } = await jwtVerify(token, JWKS, {
      issuer: `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}`,
      clockTolerance: 10,
    })
    // Attach decoded token to request for downstream use
    ;(req as any).user = {
      sub: payload.sub,
      email: payload.email,
      name: payload.preferred_username,
      roles: (payload.realm_access as any)?.roles ?? [],
    }
    next()
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' })
  }
}
```

---

### Pattern 5: Role Enforcement on BFF

**What:** Middleware factory that checks roles extracted from JWT.
**When to use:** BFF routes that require specific roles (Zero Trust: check at API layer).

```typescript
// src/middleware/roles.ts
export function requireRole(...roles: string[]) {
  return (req: any, res: any, next: any) => {
    const userRoles: string[] = req.user?.roles ?? []
    if (!roles.some(r => userRoles.includes(r))) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }
    next()
  }
}

// Usage: router.get('/tenants', requireAuth, requireRole('PlatformAdmin'), tenantsHandler)
```

---

### Pattern 6: Axios Request Interceptor (Token Refresh)

**What:** Axios instance that refreshes the Keycloak token before each API call and injects the Authorization header.
**When to use:** All frontend → BFF API calls.

```typescript
// src/services/api.ts
import axios from 'axios'
import keycloak from '../plugins/keycloak'

const api = axios.create({ baseURL: import.meta.env.VITE_BFF_URL })

api.interceptors.request.use(async (config) => {
  // Refresh if token expires within 30 seconds
  await keycloak.updateToken(30)
  config.headers.Authorization = `Bearer ${keycloak.token}`
  return config
})

api.interceptors.response.use(
  r => r,
  async (error) => {
    if (error.response?.status === 401) {
      keycloak.login()
    }
    return Promise.reject(error)
  }
)

export default api
```

---

### Pattern 7: BFF /auth/me Endpoint (Role Propagation)

**What:** Endpoint the frontend can call to hydrate auth store on startup (e.g. after page refresh, if using BFF session pattern).
**When to use:** When the frontend needs to re-hydrate user/roles from the server rather than re-decoding a stored token.

```typescript
// src/routes/auth.ts
import { requireAuth } from '../middleware/auth'

router.get('/auth/me', requireAuth, (req: any, res) => {
  res.json({
    sub: req.user.sub,
    email: req.user.email,
    name: req.user.name,
    roles: req.user.roles,
  })
})
```

---

### Anti-Patterns to Avoid

- **keycloak-nodejs-connect on BFF:** Deprecated package (Keycloak official notice, ~2023). Use `jose` instead.
- **`login-required` vs `check-sso` on init:** Using `login-required` forces immediate redirect even on public routes. Use `check-sso` for initialization; redirect to login only when accessing a protected route.
- **Decoding JWT on the frontend to extract roles:** Never parse the JWT payload directly on the frontend to make security decisions. The frontend receives roles from the Pinia store (populated by keycloak-js from `realmAccess`); the BFF independently re-validates every token.
- **Storing access tokens in localStorage:** localStorage is accessible to any JS on the page (XSS vector). Use sessionStorage if storing in browser, or the BFF server-side session pattern. PRD §13 Zero Trust means the BFF validates on every request anyway.
- **Mounting app before Keycloak init resolves:** Causes flash of unauthenticated content and race conditions with auth guards. Always `await authStore.init()` before `app.mount()`.
- **Lightweight access tokens (Keycloak 24+):** If lightweight access tokens are enabled in Keycloak realm settings, the JWT will not contain `realm_access` or `resource_access` claims, causing role propagation to silently return empty arrays. Verify this is disabled or map roles explicitly via protocol mapper.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT verification on BFF | Custom public key fetch + crypto verify | `jose` with `createRemoteJWKSet` | JWKS key rotation, clock tolerance, issuer validation — dozens of edge cases |
| Token refresh logic | Custom timer with expiry tracking | `keycloak.updateToken(minValidity)` | keycloak-js handles race conditions, token expiry math, multiple callers |
| Auth state reactivity | Custom Vue reactive wrapper around keycloak-js | Pinia auth store | Store provides reactive, persistent, testable state |
| OIDC code exchange | Manual PKCE + token endpoint calls | keycloak-js handles OIDC flow | State parameter, nonce, PKCE — critical security primitives |
| Role-based route protection | Per-component auth checks | Vue Router `meta.roles` + `beforeEach` | Centralized; impossible to miss a protected route |

**Key insight:** Keycloak's OIDC flow, JWT signing/verification, and token refresh involve security-critical edge cases that the libraries (keycloak-js, jose) have already solved. Custom implementations routinely miss clock skew, key rotation, token replay, and concurrent refresh races.

---

## Common Pitfalls

### Pitfall 1: Keycloak Init Race Condition

**What goes wrong:** Router guard checks `authStore.isAuthenticated` while `authStore.init()` is still resolving. User is redirected to login on the first load even with a valid session.
**Why it happens:** `app.mount()` is called before `authStore.init()` resolves, so the router renders routes before Keycloak confirms the session.
**How to avoid:** In `main.ts`, call `await authStore.init()` before `app.mount()`. In the router guard, check `authStore.isLoading` and return early or show a loading screen.
**Warning signs:** Page flicker on load; unauthenticated redirects on page refresh despite valid session.

---

### Pitfall 2: Roles Not Present in JWT (Lightweight Access Token)

**What goes wrong:** `keycloak.realmAccess?.roles` returns `[]` or `undefined`. BFF role checks fail for all users.
**Why it happens:** Keycloak 24+ introduced lightweight access tokens that omit role claims to reduce token size. If enabled in Realm Settings, roles are not included by default.
**How to avoid:** In Keycloak Admin → Realm Settings → Tokens: ensure "Use Lightweight Access Token" is disabled, OR configure a protocol mapper on the client to explicitly include `realm_access` roles.
**Warning signs:** User is authenticated (valid `sub`) but `roles` array is always empty; 403 on all role-protected routes.

---

### Pitfall 3: keycloak-nodejs-connect Deprecation

**What goes wrong:** Using `keycloak-connect` on BFF — it was deprecated by Keycloak team. While it may still work, it receives no security fixes.
**Why it happens:** It was the official Node.js adapter; many tutorials still reference it.
**How to avoid:** Use `jose` for JWT verification. See Pattern 4 above.
**Warning signs:** npm install warns about deprecated package; github.com/keycloak/keycloak-nodejs-connect shows deprecation notice in README.

---

### Pitfall 4: CORS Misconfiguration Between Frontend and BFF

**What goes wrong:** Browser blocks requests from Vue dev server (`localhost:5173`) to BFF (`localhost:3000`).
**Why it happens:** BFF CORS not configured to allow the frontend origin.
**How to avoid:** Add `cors` middleware on BFF with explicit `origin` set to Vue dev server URL and `credentials: true`. In Keycloak client settings, add `http://localhost:5173` to Web Origins.
**Warning signs:** `Access-Control-Allow-Origin` errors in browser console; keycloak-js fails silently on silent-check-sso.

---

### Pitfall 5: Third-Party Cookie Break for silent-check-sso

**What goes wrong:** `silent-check-sso` fails in browsers that block third-party cookies (Safari, Chrome with privacy settings enabled). The hidden iframe cannot access the Keycloak session cookie.
**Why it happens:** The iframe-based session check in keycloak-js uses a cross-site cookie that modern browsers block by default.
**How to avoid:** For Phase 1 dev, this is acceptable. `check-sso` will fall back to treating the user as unauthenticated (not logged in) rather than crashing. For production, the BFF pattern (HttpOnly session cookie, first-party) eliminates this issue. PRD already prescribes the BFF architecture.
**Warning signs:** Users appear logged out in Safari; `check-sso` never resolves as authenticated despite active Keycloak session.

---

### Pitfall 6: Token Not Refreshed Before BFF Calls

**What goes wrong:** Access token expires mid-session; BFF returns 401; user sees errors or is logged out.
**Why it happens:** Refresh logic is not applied to all API calls — developer uses `fetch` directly in some places, bypassing the axios interceptor.
**How to avoid:** All BFF calls MUST go through the centralized axios instance in `src/services/api.ts`. Never call `fetch()` directly.
**Warning signs:** Intermittent 401 errors after ~5 minutes (typical Keycloak access token TTL); errors only appear after the access token TTL elapses.

---

## Code Examples

### Keycloak Instance Singleton

```typescript
// src/plugins/keycloak.ts
// Source: https://skycloak.io/blog/keycloak-vue-js-authentication-guide/
import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
})

export default keycloak
```

### JWT Claim Structure from Keycloak

```json
// Standard Keycloak JWT payload (realm roles)
// Source: https://www.keycloak.org/docs/latest/authorization_services/index.html
{
  "sub": "user-uuid",
  "preferred_username": "user@example.com",
  "email": "user@example.com",
  "realm_access": {
    "roles": ["PlatformAdmin", "offline_access", "uma_authorization"]
  },
  "resource_access": {
    "my-client": {
      "roles": ["client-specific-role"]
    }
  },
  "iss": "https://keycloak.example.com/realms/backoffice",
  "exp": 1700000000,
  "iat": 1699996400
}
```

### Environment Variables (.env)

```bash
# Frontend .env
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=backoffice
VITE_KEYCLOAK_CLIENT_ID=backoffice-frontend
VITE_BFF_URL=http://localhost:3000

# BFF .env
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=backoffice
KEYCLOAK_CLIENT_ID=backoffice-bff
KEYCLOAK_CLIENT_SECRET=<secret>
PORT=3000
```

### silent-check-sso.html

```html
<!-- public/silent-check-sso.html -->
<!-- Required for keycloak-js check-sso initialization -->
<!doctype html>
<html>
  <body>
    <script>
      parent.postMessage(location.href, location.origin)
    </script>
  </body>
</html>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| keycloak-nodejs-connect | jose + createRemoteJWKSet | Deprecation notice added ~2023 | Must use jose for JWT verification on BFF |
| Vuex for auth state | Pinia with defineStore() | Vue 3 + Pinia became official (2022) | Simpler API, better TypeScript, no mutations |
| next() callback in router guards | Return value (true/false/path) | Vue Router 4 (2022) | Modern guard syntax; no need to call next() |
| keycloak-js check-session-iframe | BFF server-side session or graceful fallback | Third-party cookie deprecation (~2024-2025) | iframe-based SSO breaks in modern browsers; BFF is the robust fix |
| Lightweight access tokens (opt-in) | Full tokens with realm_access | Keycloak 24+ introduced opt-in | If enabled, roles disappear from JWT; must verify realm setting |

**Deprecated/outdated:**
- `keycloak-connect` npm package: deprecated by Keycloak team; no security updates
- `next()` function in Vue Router guards: replaced by return values in Vue Router 4
- `Vuex`: superseded by Pinia for Vue 3 projects

---

## Open Questions

1. **Keycloak instance location (dev vs production)**
   - What we know: PRD prescribes Keycloak as IdP; development will run Keycloak locally (Docker)
   - What's unclear: Whether a Docker Compose file for local Keycloak + realm config exists or needs to be created
   - Recommendation: Plan includes a Wave 0 task to stand up Keycloak via Docker Compose with pre-configured realm, client, and seed user

2. **BFF session strategy: stateless JWT pass-through vs HttpOnly cookie session**
   - What we know: PRD §13 requires Zero Trust (roles verified every request). Both patterns satisfy this. The CONTEXT.md leaves this to Claude's discretion.
   - What's unclear: Whether the team wants full BFF session (HttpOnly cookie, tokens server-side) or simpler stateless JWT pass-through (frontend holds access token, sends as Bearer header)
   - Recommendation: Use **stateless JWT pass-through** for Phase 1 (simpler, no Redis dependency). The frontend holds the access token in sessionStorage via Pinia. The BFF validates the JWT on every request using `jose`. Session cookies (HttpOnly) can be layered in a later phase.

3. **Keycloak realm role vs client role for custom app roles**
   - What we know: PRD §3 lists roles (PlatformAdmin, TenantAdmin, etc.); Keycloak supports both realm-scoped and client-scoped roles
   - What's unclear: Whether roles will be defined as Keycloak **realm roles** (appear in `realm_access.roles`) or **client roles** (appear in `resource_access.<clientId>.roles`)
   - Recommendation: Use **realm roles** for all application roles (PlatformAdmin, TenantAdmin, etc.). Realm roles are simpler to extract (`realm_access.roles`) and appropriate for cross-client roles in a multi-tenant platform.

---

## Sources

### Primary (HIGH confidence)
- https://skycloak.io/blog/keycloak-vue-js-authentication-guide/ — Full keycloak-js + Vue 3 + Pinia integration; package versions verified
- https://github.com/panva/jose — jose library; `createRemoteJWKSet` and `jwtVerify` patterns for BFF
- https://router.vuejs.org/guide/advanced/navigation-guards.html — Vue Router 4 `beforeEach` guard patterns; return-value syntax
- https://pinia.vuejs.org/ — Pinia official docs; store definition, persist plugin
- https://github.com/dsb-norge/vue-keycloak-js — vue-keycloak-js v3.0.7 (May 2026); Vue 3 composable wrapper

### Secondary (MEDIUM confidence)
- https://skycloak.io/blog/keycloak-backend-for-frontend-bff-pattern/ — BFF token storage, HttpOnly cookie, server-side session pattern
- https://www.keycloak.org/securing-apps/nodejs-adapter — Official Node.js adapter docs (keycloak-connect still documented but deprecation notice exists on GitHub)
- https://medium.com/@erinlim555/keycloak-authentication-with-vue3-pinia-cebae814b9db — Keycloak + Vue3 + Pinia implementation walkthrough
- Keycloak JWT claim structure (realm_access.roles): verified across multiple sources (Spring Boot, .NET, Node.js guides all consistent)

### Tertiary (LOW confidence)
- Third-party cookie / silent-check-sso breakage: multiple blog posts agree, official Keycloak FedCM migration doc referenced but not fully read
- connect-redis for production sessions: standard pattern but not verified against latest connect-redis v8 API for this specific use case

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — keycloak-js, Pinia, vue-router, jose all verified via official docs and recent sources (2025-2026)
- Architecture (BFF + Vue 3 patterns): HIGH — multiple primary sources corroborate; patterns consistent across resources
- JWT claim structure (realm_access.roles): HIGH — consistent across all Keycloak documentation and community sources
- keycloak-connect deprecation: MEDIUM — deprecation notice confirmed on GitHub; no official removal date; official docs page still shows it as current. Using jose is the safe choice regardless.
- Third-party cookie / silent-check-sso: MEDIUM — widely reported, Keycloak blog post confirms; mitigated by BFF architecture decision already locked in PRD

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (Keycloak ecosystem moves moderately fast; jose and pinia APIs are stable)
