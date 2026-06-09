import { Router } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { config } from '../config/index.js'

// NOTE: No requireAuth/requireRole middleware here — SDK endpoints use their own
// Authorization: Bearer <sdk_key> auth validated by the backend (not Keycloak JWT).

export const sdkRouter = Router()

sdkRouter.use(
  createProxyMiddleware({
    target: config.backendUrl,
    changeOrigin: true,
    ws: true,
    // Express strips '/sdk' prefix. HTTP SDK calls rewrite to /api/v1/sdk.
    // WebSocket connections to /sdk/ws/flags/:tenant_id rewrite to /ws/flags/:tenant_id on backend.
    pathRewrite: (path) => {
      if (path.startsWith('/ws/')) return path  // WS paths: /sdk/ws/... -> /ws/...
      return `/api/v1/sdk${path}`               // HTTP paths: /sdk/... -> /api/v1/sdk/...
    },
  })
)
