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
    // Express strips '/products' prefix; rewrite to /products so backend sees correct path
    // (backend mounts products_router at /products, same convention as /tenants)
    pathRewrite: (path) => `/products${path}`,
    on: {
      proxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-Internal-Secret', config.internalSecret)
        proxyReq.setHeader('X-User-Sub', (req as any).user?.sub ?? '')
        proxyReq.setHeader('X-User-Roles', ((req as any).user?.roles ?? []).join(','))
      },
    },
  })
)
