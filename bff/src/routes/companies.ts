import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { config } from '../config/index.js'

export const companiesRouter = Router()

companiesRouter.use(
  requireAuth,
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips '/companies' prefix; rewrite to /companies so backend sees correct path
    // (backend mounts companies_router at /companies, same convention as /products)
    pathRewrite: (path) => `/companies${path}`,
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
