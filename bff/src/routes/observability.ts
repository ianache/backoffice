import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { requireRole } from '../middleware/roles.js'
import { config } from '../config/index.js'

export const observabilityRouter = Router()

observabilityRouter.use(
  requireAuth,
  requireRole('PlatformAdmin', 'TenantOwner', 'TenantAdmin'),
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips the '/observability' mount prefix from req.url before passing to this
    // middleware, so we must add it back so the backend sees the correct path.
    // The backend observability router is mounted at /observability.
    pathRewrite: (path) => `/observability${path}`,
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
