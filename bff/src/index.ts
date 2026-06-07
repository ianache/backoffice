import express from 'express'
import cors from 'cors'
import { config } from './config/index.js'
import { authRouter } from './routes/auth.js'
import { tenantsRouter } from './routes/tenants.js'
import { usersRouter } from './routes/users.js'
import { flagsRouter } from './routes/flags.js'

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

app.listen(config.port, () => {
  console.log(`BFF running on http://localhost:${config.port}`)
  console.log(`Keycloak: ${config.keycloak.url}/realms/${config.keycloak.realm}`)
})
