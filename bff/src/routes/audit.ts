import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { config } from '../config/index.js'

export const auditRouter = Router()

auditRouter.use(
  requireAuth,
  // No requireRole() restriction — PlatformAdmin/TenantOwner/TenantAdmin/ProductManager/
  // ProductDeveloper/ProductQA all have read access to audit logs (PRD §3); the backend
  // scopes results by tenant_id via X-User-Tenant-Id for non-PlatformAdmin roles.
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips the '/audit-logs' mount prefix from req.url before passing to this
    // middleware, so we must add it back so the backend sees the correct path.
    pathRewrite: (path) => `/audit-logs${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Email', (req as any).user?.email ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
        proxyReq.setHeader('X-User-Tenant-Id', (req as any).user?.tenantId ?? '')
      },
    },
  })
)
