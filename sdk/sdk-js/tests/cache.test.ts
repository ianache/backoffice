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

/**
 * Minimal mock of the browser WebSocket API so initialize()'s
 * `new ReconnectingSocket(...)` call doesn't open a real connection.
 */
class MockWebSocket {
  url: string
  send = vi.fn()
  close = vi.fn()
  onopen: (() => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(url: string) {
    this.url = url
  }
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
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
    vi.stubGlobal('navigator', { sendBeacon: vi.fn() })
    vi.stubGlobal('window', { addEventListener: vi.fn() })

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
