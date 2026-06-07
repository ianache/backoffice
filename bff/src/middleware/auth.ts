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
  tenantId?: string   // populated from JWT 'tenant_id' claim when Keycloak protocol mapper is configured
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
    // Extract tenant_id from JWT claim — requires Keycloak User Attribute protocol mapper.
    // See docs/KEYCLOAK_SETUP.md for mapper configuration steps.
    const tenantId = (payload['tenant_id'] as string | undefined)
      ?? (payload['tenantId'] as string | undefined)
      ?? undefined

    if (!tenantId && process.env.NODE_ENV !== 'production') {
      console.warn(
        '[warn] X-User-Tenant-Id will be empty: JWT payload has no tenant_id claim. ' +
        'Configure the Keycloak User Attribute protocol mapper — see docs/KEYCLOAK_SETUP.md'
      )
    }

    req.user = {
      sub: payload.sub ?? '',
      email: (payload.email as string) ?? '',
      name: (payload.preferred_username as string) ?? '',
      roles: realmRoles.filter(r => APP_ROLES.includes(r)),
      tenantId,
    }
    next()
  } catch {
    res.status(401).json({ error: 'Invalid token' })
  }
}
