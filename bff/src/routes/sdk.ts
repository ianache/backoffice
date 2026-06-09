import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { config } from '../config/index.js'

// NOTE: No requireAuth/requireRole middleware here — SDK endpoints use their own
// Authorization: Bearer <sdk_key> auth validated by the backend (not Keycloak JWT).
// NOTE: WebSocket /ws/flags/{tenant_id} is NOT proxied through BFF in Phase 8.
// SDK clients connect directly to backend. BFF WebSocket proxy (ws: true) deferred to Phase 10.

export const sdkRouter = Router()

sdkRouter.use(
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    // Express strips the '/sdk' mount prefix from req.url before passing to this
    // middleware, so we must rewrite to /api/v1/sdk so the backend sees the correct path.
    pathRewrite: (path) => `/api/v1/sdk${path}`,
  })
)
