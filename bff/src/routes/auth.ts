import { Router } from 'express'
import { requireAuth } from '../middleware/auth.js'

export const authRouter = Router()

// GET /auth/me — returns authenticated user identity and roles
// Called by the Vue frontend after successful Keycloak login to hydrate Pinia store
authRouter.get('/me', requireAuth, (req, res) => {
  res.json({
    sub: req.user!.sub,
    email: req.user!.email,
    name: req.user!.name,
    roles: req.user!.roles,
  })
})
