import { describe, it, expect, vi, afterEach } from 'vitest'
import { FeatureFlagClient } from '../src/client'
import type { BootstrapResponse } from '../src/types'

const BOOTSTRAP_FIXTURE: BootstrapResponse = {
  my_flag: {
    enabled: true,
    rules: [{ attribute: 'country', operator: 'equals', value: 'PE', result: true }],
    segments: [],
    default_val: false,
    scope: 'global',
  },
}

const OPTS = {
  tenantId: 'tenant-1',
  productId: 'product-1',
  environment: 'production',
  apiBaseUrl: 'https://bff.example.com',
  sdkKey: 'sdk-secret-key',
}

describe('FeatureFlagClient cache performance', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('evaluate() averages under 1ms per call for a cached flag (SDK-06)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        json: async () => BOOTSTRAP_FIXTURE,
      }),
    )

    const client = new FeatureFlagClient(OPTS)
    await client.initialize()

    const ITERATIONS = 1000
    const user = { country: 'PE' }

    const start = performance.now()
    for (let i = 0; i < ITERATIONS; i++) {
      client.evaluate('my_flag', user)
    }
    const end = performance.now()

    const avgMs = (end - start) / ITERATIONS
    expect(avgMs).toBeLessThan(1)
  })
})
