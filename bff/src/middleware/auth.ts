import { jwtVerify } from 'jose'
import type { Request, Response, NextFunction } from 'express'
import { JWKS, KEYCLOAK_ISSUER } from '../services/keycloak.js'

const APP_ROLES = [
  'PlatformAdmin',
  'TenantOwner', 'TenantAdmin', 'TenantViewer',
  'ProductManager', 'ProductDeveloper', 'ProductQA',
  'CompanyAdmin', 'CompanyUser',
]

export interface AuthUser {
  sub: string
  email: string
  name: string
  roles: string[]
}

declare global {
  namespace Express {
    interface Request {
      user?: AuthUser
    }
  }
}

export async function requireAuth(req: Request, res: Response, next: NextFunction): Promise<void> {
  const authHeader = req.headers.authorization
  if (!authHeader?.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing token' })
    return
  }
  const token = authHeader.slice(7)
  try {
    const { payload } = await jwtVerify(token, JWKS, {
      issuer: KEYCLOAK_ISSUER,
      clockTolerance: 10,
    })
    const realmRoles: string[] = (payload.realm_access as any)?.roles ?? []
    req.user = {
      sub: payload.sub ?? '',
      email: (payload.email as string) ?? '',
      name: (payload.preferred_username as string) ?? '',
      roles: realmRoles.filter(r => APP_ROLES.includes(r)),
    }
    next()
  } catch {
    res.status(401).json({ error: 'Invalid token' })
  }
}
