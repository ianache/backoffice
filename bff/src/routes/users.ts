import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const usersRouter = Router()

usersRouter.use(
  requireAuth,
  requireRole('TenantAdmin', 'TenantOwner'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    pathRewrite: (path) => `/users${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
        // tenant_id from JWT claim — requires Keycloak protocol mapper for tenant_id attribute
        // auth.ts AuthUser shape: { sub, email, name, roles } — no tenantId yet
        // Once the protocol mapper is configured, this will populate automatically
        const user = (req as any).user ?? {}
        const tenantId = user.tenantId ?? user.attributes?.tenant_id?.[0] ?? ''
        proxyReq.setHeader('X-User-Tenant-Id', tenantId)
      },
    },
  })
)
