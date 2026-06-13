import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const labelsRouter = Router()

labelsRouter.use(
  requireAuth,
  requireRole('PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager', 'UXWriter'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips the '/labels' mount prefix from req.url before passing to this
    // middleware, so we must add it back so the backend sees the correct path.
    // The backend labels router is mounted at /api/v1/labels (unlike flags, which is
    // mounted directly at /flags without an /api/v1 prefix).
    pathRewrite: (path) => `/api/v1/labels${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
        proxyReq.setHeader('X-User-Tenant-Id', (req as any).user?.tenantId ?? '')
        proxyReq.setHeader('X-User-Email', (req as any).user?.email ?? '')
      },
    },
  })
)
