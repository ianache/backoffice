import { describe, it, expect } from 'vitest'
import { OPERATORS, evaluateRule, evaluateFlag } from '../src/evaluator'
import type { FlagEntry } from '../src/types'

describe('OPERATORS', () => {
  it('has exactly 8 entries matching backend semantics', () => {
    expect(Object.keys(OPERATORS).sort()).toEqual(
      ['anyOf', 'contains', 'equals', 'greaterThan', 'in', 'lessThan', 'notIn', 'regex'].sort(),
    )
  })
})

describe('evaluateRule', () => {
  it('equals: true case', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'equals', value: 'PE' }, { country: 'PE' })).toBe(true)
  })

  it('equals: false case', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'equals', value: 'PE' }, { country: 'US' })).toBe(false)
  })

  it('in: true case', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'in', value: ['PE', 'AR'] }, { country: 'PE' })).toBe(true)
  })

  it('in: false case', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'in', value: ['PE', 'AR'] }, { country: 'US' })).toBe(false)
  })

  it('notIn: true case', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'notIn', value: ['US'] }, { country: 'PE' })).toBe(true)
  })

  it('notIn: false case', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'notIn', value: ['US'] }, { country: 'US' })).toBe(false)
  })

  it('contains: true case', () => {
    expect(evaluateRule({ attribute: 'email', operator: 'contains', value: '@acme' }, { email: 'john@acme.com' })).toBe(true)
  })

  it('contains: false case', () => {
    expect(evaluateRule({ attribute: 'email', operator: 'contains', value: '@acme' }, { email: 'john@other.com' })).toBe(false)
  })

  it('regex: true case', () => {
    expect(evaluateRule({ attribute: 'email', operator: 'regex', value: '^admin' }, { email: 'admin@co.com' })).toBe(true)
  })

  it('regex: false case', () => {
    expect(evaluateRule({ attribute: 'email', operator: 'regex', value: '^admin' }, { email: 'user@co.com' })).toBe(false)
  })

  it('greaterThan: true case', () => {
    expect(evaluateRule({ attribute: 'ltv', operator: 'greaterThan', value: 500 }, { ltv: 600 })).toBe(true)
  })

  it('greaterThan: false case', () => {
    expect(evaluateRule({ attribute: 'ltv', operator: 'greaterThan', value: 500 }, { ltv: 400 })).toBe(false)
  })

  it('greaterThan: numeric strings via Number() coercion', () => {
    expect(evaluateRule({ attribute: 'ltv', operator: 'greaterThan', value: '500' }, { ltv: '600' })).toBe(true)
  })

  it('greaterThan: NaN comparisons fail closed (false)', () => {
    expect(evaluateRule({ attribute: 'plan', operator: 'greaterThan', value: 500 }, { plan: 'enterprise' })).toBe(false)
  })

  it('lessThan: true case', () => {
    expect(evaluateRule({ attribute: 'ltv', operator: 'lessThan', value: 500 }, { ltv: 100 })).toBe(true)
  })

  it('lessThan: false case', () => {
    expect(evaluateRule({ attribute: 'ltv', operator: 'lessThan', value: 500 }, { ltv: 600 })).toBe(false)
  })

  it('missing attribute returns false', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'equals', value: 'PE' }, {})).toBe(false)
  })

  it('unknown operator returns false', () => {
    expect(evaluateRule({ attribute: 'country', operator: 'bogus', value: 'PE' }, { country: 'PE' })).toBe(false)
  })

  it('anyOf: list context intersecting returns true', () => {
    expect(evaluateRule({ attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin', 'TenantOwner'] }, { roles: ['TenantOwner', 'viewer'] })).toBe(true)
  })

  it('anyOf: list context disjoint returns false', () => {
    expect(evaluateRule({ attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin', 'TenantOwner'] }, { roles: ['viewer'] })).toBe(false)
  })

  it('anyOf: scalar context member returns true', () => {
    expect(evaluateRule({ attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin', 'TenantOwner'] }, { roles: 'PlatformAdmin' })).toBe(true)
  })

  it('anyOf: scalar context non-member returns false', () => {
    expect(evaluateRule({ attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin', 'TenantOwner'] }, { roles: 'guest' })).toBe(false)
  })

  it('anyOf: empty expected array returns false', () => {
    expect(evaluateRule({ attribute: 'roles', operator: 'anyOf', value: [] }, { roles: ['x'] })).toBe(false)
  })

  it('anyOf: case-sensitive returns false', () => {
    expect(evaluateRule({ attribute: 'roles', operator: 'anyOf', value: ['PlatformAdmin'] }, { roles: ['platformadmin'] })).toBe(false)
  })

  it('anyOf: non-array expected with scalar actual returns false (fail-closed)', () => {
    expect(evaluateRule({ attribute: 'role', operator: 'anyOf', value: 'admin' }, { role: 'admin' })).toBe(false)
  })
})

describe('evaluateFlag', () => {
  const baseEntry: FlagEntry = {
    enabled: true,
    rules: [],
    segments: [],
    default_val: false,
    scope: 'global',
  }

  it('disabled flag returns false regardless of rules', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      enabled: false,
      rules: [{ attribute: 'country', operator: 'equals', value: 'PE', result: true }],
      default_val: true,
    }
    expect(evaluateFlag(entry, { country: 'PE' })).toBe(false)
  })

  it('matching rule with result:true returns true', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      rules: [{ attribute: 'country', operator: 'equals', value: 'PE', result: true }],
      default_val: false,
    }
    expect(evaluateFlag(entry, { country: 'PE' })).toBe(true)
  })

  it('no matching rule returns default_val', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      rules: [{ attribute: 'country', operator: 'equals', value: 'PE', result: true }],
      default_val: false,
    }
    expect(evaluateFlag(entry, { country: 'US' })).toBe(false)
  })

  it('rule_based segment with matching conditions returns true (any-match)', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      default_val: false,
      segments: [
        {
          id: 1,
          type: 'rule_based',
          conditions: [{ attribute: 'country', operator: 'equals', value: 'PE' }],
          members: [],
        },
      ],
    }
    expect(evaluateFlag(entry, { country: 'PE' })).toBe(true)
  })

  it('manual segment with members[] including user.id returns true', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      default_val: false,
      segments: [
        {
          id: 2,
          type: 'manual',
          conditions: [],
          members: ['user-uuid-001', 'user-uuid-002'],
        },
      ],
    }
    expect(evaluateFlag(entry, { id: 'user-uuid-001' })).toBe(true)
  })

  it('manual segment matches via user.sub when user.id absent', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      default_val: false,
      segments: [
        {
          id: 2,
          type: 'manual',
          conditions: [],
          members: ['user-uuid-555'],
        },
      ],
    }
    expect(evaluateFlag(entry, { sub: 'user-uuid-555' })).toBe(true)
  })

  it('manual segment matches via user.user_id when id/sub absent', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      default_val: false,
      segments: [
        {
          id: 2,
          type: 'manual',
          conditions: [],
          members: ['user-uuid-777'],
        },
      ],
    }
    expect(evaluateFlag(entry, { user_id: 'user-uuid-777' })).toBe(true)
  })

  it('no rule/segment match returns default_val', () => {
    const entry: FlagEntry = {
      ...baseEntry,
      default_val: true,
      rules: [{ attribute: 'country', operator: 'equals', value: 'PE', result: true }],
      segments: [
        {
          id: 1,
          type: 'rule_based',
          conditions: [{ attribute: 'country', operator: 'equals', value: 'AR' }],
          members: [],
        },
        {
          id: 2,
          type: 'manual',
          conditions: [],
          members: ['someone-else'],
        },
      ],
    }
    expect(evaluateFlag(entry, { country: 'US', id: 'user-uuid-001' })).toBe(true)
  })

  describe('company-scope target guard (TGT-03)', () => {
    it('company-scoped entry with matching user.company_id falls through to default_val', () => {
      const entry: FlagEntry = {
        ...baseEntry,
        enabled: true,
        scope: 'company',
        company_id: 'acme',
        rules: [],
        segments: [],
        default_val: true,
      }
      expect(evaluateFlag(entry, { company_id: 'acme' })).toBe(true)
    })

    it('company-scoped entry with non-matching user.company_id returns false', () => {
      const entry: FlagEntry = {
        ...baseEntry,
        enabled: true,
        scope: 'company',
        company_id: 'acme',
        rules: [],
        segments: [],
        default_val: true,
      }
      expect(evaluateFlag(entry, { company_id: 'other' })).toBe(false)
    })

    it('company-scoped entry with user missing company_id returns false', () => {
      const entry: FlagEntry = {
        ...baseEntry,
        enabled: true,
        scope: 'company',
        company_id: 'acme',
        rules: [],
        segments: [],
        default_val: true,
      }
      expect(evaluateFlag(entry, {})).toBe(false)
    })

    it('legacy company-scoped entry with null company_id skips guard regardless of user', () => {
      const entry: FlagEntry = {
        ...baseEntry,
        enabled: true,
        scope: 'company',
        company_id: null,
        rules: [],
        segments: [],
        default_val: true,
      }
      expect(evaluateFlag(entry, { company_id: 'anything' })).toBe(true)
      expect(evaluateFlag(entry, {})).toBe(true)
    })

    it('non-company scopes are unaffected by the guard', () => {
      const entry: FlagEntry = {
        ...baseEntry,
        enabled: true,
        scope: 'product',
        product_id: 'p1',
        rules: [],
        segments: [],
        default_val: true,
      }
      expect(evaluateFlag(entry, {})).toBe(true)
    })
  })
})
