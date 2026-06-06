import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Request, Response, NextFunction } from 'express'

// Mock the keycloak service module before importing auth middleware
vi.mock('../services/keycloak.js', () => ({
  JWKS: vi.fn(),
  KEYCLOAK_ISSUER: 'http://localhost:8080/realms/backoffice',
}))

// Mock jose jwtVerify
vi.mock('jose', () => ({
  jwtVerify: vi.fn(),
}))

import { requireAuth } from './auth.js'
import { jwtVerify } from 'jose'

const mockJwtVerify = vi.mocked(jwtVerify)

function makeReq(headers: Record<string, string> = {}): Request {
  return { headers } as unknown as Request
}

function makeRes(): { res: Response; status: ReturnType<typeof vi.fn>; json: ReturnType<typeof vi.fn> } {
  const json = vi.fn()
  const status = vi.fn().mockReturnValue({ json })
  const res = { status, json } as unknown as Response
  return { res, status, json }
}

describe('requireAuth middleware', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 401 with {error: "Missing token"} when Authorization header is absent', async () => {
    const req = makeReq()
    const { res, status, json } = makeRes()
    const next = vi.fn()

    await requireAuth(req, res, next as NextFunction)

    expect(status).toHaveBeenCalledWith(401)
    expect(json).toHaveBeenCalledWith({ error: 'Missing token' })
    expect(next).not.toHaveBeenCalled()
  })

  it('returns 401 with {error: "Missing token"} when Authorization header does not start with Bearer', async () => {
    const req = makeReq({ authorization: 'Basic sometoken' })
    const { res, status, json } = makeRes()
    const next = vi.fn()

    await requireAuth(req, res, next as NextFunction)

    expect(status).toHaveBeenCalledWith(401)
    expect(json).toHaveBeenCalledWith({ error: 'Missing token' })
    expect(next).not.toHaveBeenCalled()
  })

  it('returns 401 with {error: "Invalid token"} when jwtVerify throws', async () => {
    const req = makeReq({ authorization: 'Bearer invalid.token.here' })
    const { res, status, json } = makeRes()
    const next = vi.fn()

    mockJwtVerify.mockRejectedValueOnce(new Error('Token expired'))

    await requireAuth(req, res, next as NextFunction)

    expect(status).toHaveBeenCalledWith(401)
    expect(json).toHaveBeenCalledWith({ error: 'Invalid token' })
    expect(next).not.toHaveBeenCalled()
  })

  it('calls next() and populates req.user when token is valid', async () => {
    const req = makeReq({ authorization: 'Bearer valid.token.here' }) as Request & { user?: unknown }
    const { res } = makeRes()
    const next = vi.fn()

    mockJwtVerify.mockResolvedValueOnce({
      payload: {
        sub: 'user-uuid-123',
        email: 'admin@backoffice.dev',
        preferred_username: 'admin',
        realm_access: {
          roles: ['PlatformAdmin', 'offline_access', 'uma_authorization'],
        },
        iss: 'http://localhost:8080/realms/backoffice',
        exp: 9999999999,
      },
      protectedHeader: { alg: 'RS256' },
    } as any)

    await requireAuth(req, res, next as NextFunction)

    expect(next).toHaveBeenCalledOnce()
    expect(req.user).toEqual({
      sub: 'user-uuid-123',
      email: 'admin@backoffice.dev',
      name: 'admin',
      roles: ['PlatformAdmin'], // offline_access and uma_authorization filtered out
    })
  })

  it('filters realm_access.roles to only APP_ROLES', async () => {
    const req = makeReq({ authorization: 'Bearer valid.token.here' }) as Request & { user?: unknown }
    const { res } = makeRes()
    const next = vi.fn()

    mockJwtVerify.mockResolvedValueOnce({
      payload: {
        sub: 'user-uuid-456',
        email: 'tenant@backoffice.dev',
        preferred_username: 'tenant_user',
        realm_access: {
          roles: ['TenantAdmin', 'offline_access', 'uma_authorization', 'default-roles-backoffice'],
        },
        iss: 'http://localhost:8080/realms/backoffice',
        exp: 9999999999,
      },
      protectedHeader: { alg: 'RS256' },
    } as any)

    await requireAuth(req, res, next as NextFunction)

    expect(next).toHaveBeenCalledOnce()
    expect((req as any).user?.roles).toEqual(['TenantAdmin'])
  })

  it('handles missing realm_access gracefully (empty roles array)', async () => {
    const req = makeReq({ authorization: 'Bearer valid.token.here' }) as Request & { user?: unknown }
    const { res } = makeRes()
    const next = vi.fn()

    mockJwtVerify.mockResolvedValueOnce({
      payload: {
        sub: 'user-uuid-789',
        email: 'norolls@backoffice.dev',
        preferred_username: 'noroles',
        // no realm_access
        iss: 'http://localhost:8080/realms/backoffice',
        exp: 9999999999,
      },
      protectedHeader: { alg: 'RS256' },
    } as any)

    await requireAuth(req, res, next as NextFunction)

    expect(next).toHaveBeenCalledOnce()
    expect((req as any).user?.roles).toEqual([])
  })
})
