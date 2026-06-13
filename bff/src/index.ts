import express from 'express'
import cors from 'cors'
import { config } from './config/index.js'
import { authRouter } from './routes/auth.js'
import { tenantsRouter } from './routes/tenants.js'
import { usersRouter } from './routes/users.js'
import { flagsRouter } from './routes/flags.js'
import { sdkRouter } from './routes/sdk.js'
import { productsRouter } from './routes/products.js'
import { companiesRouter } from './routes/companies.js'
import { auditRouter } from './routes/audit.js'

const app = express()

app.use(cors({
  origin: config.frontendUrl,
  credentials: true,
}))

// Health check — no auth required
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'backoffice-bff' })
})

// Auth routes: /auth/me, etc.
// express.json() only on non-proxy routes — proxy middleware needs the raw body stream
app.use('/auth', express.json(), authRouter)

// Tenant management: proxied to backend
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/tenants', tenantsRouter)

// User management: proxied to backend, TenantAdmin/TenantOwner only
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/users', usersRouter)

// Feature flags management: proxied to backend, multi-role (PlatformAdmin | TenantAdmin | TenantOwner | ProductManager)
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/flags', flagsRouter)

// SDK endpoints: proxied to backend /api/v1/sdk/*, no Keycloak auth (SDK key auth handled by backend)
// WebSocket connections to /sdk/ws/flags/:tenant_id are upgraded and forwarded to backend /ws/flags/:tenant_id
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/sdk', sdkRouter)

// Products catalog and tenant subscriptions: proxied to backend /api/v1/products/*
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/products', productsRouter)

// Companies catalog: proxied to backend /api/v1/companies/*, role + tenant isolation enforced backend-side
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/companies', companiesRouter)

// Audit log timeline: proxied to backend /audit-logs/*, read-only (no PATCH/DELETE — PRD §10.2)
// NOTE: express.json() is intentionally NOT applied here; the proxy streams the raw body
app.use('/audit-logs', auditRouter)

app.listen(config.port, () => {
  console.log(`BFF running on http://localhost:${config.port}`)
  console.log(`Keycloak: ${config.keycloak.url}/realms/${config.keycloak.realm}`)
})
