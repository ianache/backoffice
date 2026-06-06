import { describe, it, expect, vi } from 'vitest'
import type { Request, Response, NextFunction } from 'express'
import { requireRole } from './roles.js'
import type { AuthUser } from './auth.js'

function makeReq(user?: AuthUser): Request {
  return { user } as unknown as Request
}

function makeRes(): { res: Response; status: ReturnType<typeof vi.fn>; json: ReturnType<typeof vi.fn> } {
  const json = vi.fn()
  const status = vi.fn().mockReturnValue({ json })
  const res = { status, json } as unknown as Response
  return { res, status, json }
}

describe('requireRole middleware factory', () => {
  it('calls next() when user has the required role', () => {
    const req = makeReq({ sub: 'u1', email: 'a@b.com', name: 'Alice', roles: ['PlatformAdmin'] })
    const { res } = makeRes()
    const next = vi.fn()

    requireRole('PlatformAdmin')(req, res, next as NextFunction)

    expect(next).toHaveBeenCalledOnce()
  })

  it('returns 403 when user does not have the required role', () => {
    const req = makeReq({ sub: 'u2', email: 'b@b.com', name: 'Bob', roles: ['TenantViewer'] })
    const { res, status, json } = makeRes()
    const next = vi.fn()

    requireRole('PlatformAdmin')(req, res, next as NextFunction)

    expect(status).toHaveBeenCalledWith(403)
    expect(json).toHaveBeenCalledWith({ error: 'Insufficient permissions' })
    expect(next).not.toHaveBeenCalled()
  })

  it('returns 403 when req.user is undefined', () => {
    const req = makeReq(undefined)
    const { res, status, json } = makeRes()
    const next = vi.fn()

    requireRole('PlatformAdmin')(req, res, next as NextFunction)

    expect(status).toHaveBeenCalledWith(403)
    expect(json).toHaveBeenCalledWith({ error: 'Insufficient permissions' })
    expect(next).not.toHaveBeenCalled()
  })

  it('calls next() when user has any one of multiple accepted roles', () => {
    const req = makeReq({ sub: 'u3', email: 'c@b.com', name: 'Carol', roles: ['TenantAdmin'] })
    const { res } = makeRes()
    const next = vi.fn()

    requireRole('PlatformAdmin', 'TenantAdmin')(req, res, next as NextFunction)

    expect(next).toHaveBeenCalledOnce()
  })

  it('returns 403 when user has none of multiple accepted roles', () => {
    const req = makeReq({ sub: 'u4', email: 'd@b.com', name: 'Dave', roles: ['CompanyUser'] })
    const { res, status, json } = makeRes()
    const next = vi.fn()

    requireRole('PlatformAdmin', 'TenantAdmin')(req, res, next as NextFunction)

    expect(status).toHaveBeenCalledWith(403)
    expect(json).toHaveBeenCalledWith({ error: 'Insufficient permissions' })
    expect(next).not.toHaveBeenCalled()
  })
})
