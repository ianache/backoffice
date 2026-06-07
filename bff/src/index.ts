import express from 'express'
import cors from 'cors'
import { config } from './config/index.js'
import { authRouter } from './routes/auth.js'
import { tenantsRouter } from './routes/tenants.js'

const app = express()

app.use(cors({
  origin: config.frontendUrl,
  credentials: true,
}))
app.use(express.json())

// Health check — no auth required
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'backoffice-bff' })
})

// Auth routes: /auth/me, etc.
app.use('/auth', authRouter)

// Tenant management: proxied to backend
app.use('/tenants', tenantsRouter)

app.listen(config.port, () => {
  console.log(`BFF running on http://localhost:${config.port}`)
  console.log(`Keycloak: ${config.keycloak.url}/realms/${config.keycloak.realm}`)
})
