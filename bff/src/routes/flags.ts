import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const flagsRouter = Router()

flagsRouter.use(
  requireAuth,
  requireRole('PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips the '/flags' mount prefix from req.url before passing to this
    // middleware, so we must add it back so the backend sees the correct path.
    pathRewrite: (path) => `/flags${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
        proxyReq.setHeader('X-User-Tenant-Id', (req as any).user?.tenantId ?? '')
      },
    },
  })
)
