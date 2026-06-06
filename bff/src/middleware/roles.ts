import type { Request, Response, NextFunction } from 'express'

export function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const userRoles = req.user?.roles ?? []
    if (!roles.some(r => userRoles.includes(r))) {
      res.status(403).json({ error: 'Insufficient permissions' })
      return
    }
    next()
  }
}
