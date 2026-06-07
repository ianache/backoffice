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
        proxyReq.setHeader('X-User-Sub', req.user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', (req.user?.roles ?? []).join(','))
        proxyReq.setHeader('X-User-Tenant-Id', req.user?.tenantId ?? '')
      },
    },
  })
)
