import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { requireAuth } from '../middleware/auth.js'
import { config } from '../config/index.js'

export const productsRouter = Router()

productsRouter.use(
  requireAuth,
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips '/products' prefix; rewrite to /api/v1/products so backend sees correct path
    pathRewrite: (path) => `/api/v1/products${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
      },
    },
  })
)
