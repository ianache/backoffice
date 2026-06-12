import { describe, it, expect } from 'vitest'
import { validateFlagTarget, buildTargetFields } from './flagFormModel'

// ---------------------------------------------------------------------------
// validateFlagTarget — required-target validation per scope (TGT-01/TGT-02)
// ---------------------------------------------------------------------------

describe('validateFlagTarget', () => {
  it('global scope: no target required -> null', () => {
    expect(validateFlagTarget('global', { tenantId: '', productId: '', companyId: '' })).toBe(null)
  })

  it('product scope: empty productId -> error mentioning product', () => {
    const err = validateFlagTarget('product', { tenantId: '', productId: '', companyId: '' })
    expect(err).not.toBe(null)
    expect(err?.toLowerCase()).toContain('product')
  })

  it('tenant scope: empty tenantId -> error', () => {
    const err = validateFlagTarget('tenant', { tenantId: '', productId: '', companyId: '' })
    expect(err).not.toBe(null)
    expect(err?.toLowerCase()).toContain('tenant')
  })

  it('company scope: empty companyId -> error', () => {
    const err = validateFlagTarget('company', { tenantId: '', productId: '', companyId: '' })
    expect(err).not.toBe(null)
    expect(err?.toLowerCase()).toContain('company')
  })

  it('product scope: productId selected -> null', () => {
    expect(validateFlagTarget('product', { tenantId: '', productId: 'backoffice', companyId: '' })).toBe(null)
  })
})

// ---------------------------------------------------------------------------
// buildTargetFields — mutual exclusivity payload (explicit nulls)
// ---------------------------------------------------------------------------

describe('buildTargetFields', () => {
  it('product scope: only product_id survives, others explicitly null', () => {
    expect(buildTargetFields('product', { tenantId: 't1', productId: 'p1', companyId: 'c1' })).toEqual({
      tenant_id: null,
      product_id: 'p1',
      company_id: null,
    })
  })

  it('global scope: all three null', () => {
    expect(buildTargetFields('global', { tenantId: 't1', productId: 'p1', companyId: 'c1' })).toEqual({
      tenant_id: null,
      product_id: null,
      company_id: null,
    })
  })

  it('tenant scope: only tenant_id survives', () => {
    expect(buildTargetFields('tenant', { tenantId: '12', productId: '', companyId: '' })).toEqual({
      tenant_id: '12',
      product_id: null,
      company_id: null,
    })
  })

  it('company scope: only company_id survives', () => {
    expect(buildTargetFields('company', { tenantId: '', productId: '', companyId: 'acme' })).toEqual({
      tenant_id: null,
      product_id: null,
      company_id: 'acme',
    })
  })
})
