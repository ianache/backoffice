import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
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

describe('FeatureFlagClient', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
    vi.stubGlobal('navigator', { sendBeacon: vi.fn() })
    vi.stubGlobal('window', { addEventListener: vi.fn() })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('initialize()', () => {
    let fetchMock: ReturnType<typeof vi.fn>

    beforeEach(() => {
      fetchMock = vi.fn().mockResolvedValue({
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)
    })

    it('fetches the bootstrap snapshot and populates the cache', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()

      expect(fetchMock).toHaveBeenCalledTimes(1)
      const [url, init] = fetchMock.mock.calls[0]
      expect(url).toContain(`${OPTS.apiBaseUrl}/sdk/bootstrap`)
      expect(url).toContain('tenant_id=tenant-1')
      expect(url).toContain('product_id=product-1')
      expect(url).toContain('environment=production')
      expect(init.headers.Authorization).toBe(`Bearer ${OPTS.sdkKey}`)

      expect(client.getCache()).toEqual(BOOTSTRAP_FIXTURE)
    })
  })

  describe('evaluate()', () => {
    beforeEach(() => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          json: async () => BOOTSTRAP_FIXTURE,
        }),
      )
    })

    it('returns the boolean computed by evaluateFlag for a cached flag (rule match)', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()

      expect(client.evaluate('my_flag', { country: 'PE' })).toBe(true)
    })

    it('returns default_val for a cached flag when no rule matches', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()

      expect(client.evaluate('my_flag', { country: 'US' })).toBe(false)
    })

    it('returns false on cache-miss without throwing or calling fetch again', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new FeatureFlagClient(OPTS)
      await client.initialize()
      expect(fetchMock).toHaveBeenCalledTimes(1)

      expect(() => client.evaluate('unknown_flag', {})).not.toThrow()
      expect(client.evaluate('unknown_flag', {})).toBe(false)
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('invokes the evaluation listener with the result after computing it', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()

      const listener = vi.fn()
      client.setEvaluationListener(listener)

      const result = client.evaluate('my_flag', { country: 'PE', id: 'user-42' })

      expect(result).toBe(true)
      expect(listener).toHaveBeenCalledTimes(1)
      const event = listener.mock.calls[0][0]
      expect(event.flag_key).toBe('my_flag')
      expect(event.result).toBe(true)
      expect(event.user_id).toBe('user-42')
      expect(typeof event.evaluated_at).toBe('string')
    })
  })

  describe('evaluateRemote()', () => {
    it('posts to /sdk/evaluate and resolves the boolean result', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        json: async () => ({ flag_key: 'my_flag', result: true }),
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new FeatureFlagClient(OPTS)
      const result = await client.evaluateRemote('my_flag', { country: 'PE' })

      expect(result).toBe(true)
      expect(fetchMock).toHaveBeenCalledTimes(1)
      const [url, init] = fetchMock.mock.calls[0]
      expect(url).toBe(`${OPTS.apiBaseUrl}/sdk/evaluate`)
      expect(init.method).toBe('POST')
      expect(init.headers.Authorization).toBe(`Bearer ${OPTS.sdkKey}`)
      expect(init.headers['Content-Type']).toBe('application/json')
      expect(JSON.parse(init.body)).toEqual({ flag_key: 'my_flag', user: { country: 'PE' } })
    })

    it('resolves to false when result is falsy', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          json: async () => ({ flag_key: 'my_flag', result: false }),
        }),
      )

      const client = new FeatureFlagClient(OPTS)
      const result = await client.evaluateRemote('my_flag', { country: 'US' })

      expect(result).toBe(false)
    })
  })

  describe('cache extension points', () => {
    beforeEach(() => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          json: async () => BOOTSTRAP_FIXTURE,
        }),
      )
    })

    it('getCache() returns the current cache', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()
      expect(client.getCache()).toEqual(BOOTSTRAP_FIXTURE)
    })

    it('invalidate() removes a single flag entry', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()

      client.invalidate('my_flag')
      expect(client.getCache()).toEqual({})
      expect(client.evaluate('my_flag', { country: 'PE' })).toBe(false)
    })

    it('replaceCache() replaces the entire cache', async () => {
      const client = new FeatureFlagClient(OPTS)
      await client.initialize()

      const newCache: BootstrapResponse = {
        other_flag: {
          enabled: true,
          rules: [],
          segments: [],
          default_val: true,
          scope: 'global',
        },
      }
      client.replaceCache(newCache)

      expect(client.getCache()).toEqual(newCache)
      expect(client.evaluate('my_flag', {})).toBe(false)
      expect(client.evaluate('other_flag', {})).toBe(true)
    })
  })

  describe('getOptions()', () => {
    it('returns the InitOptions used to construct the client', () => {
      const client = new FeatureFlagClient(OPTS)
      expect(client.getOptions()).toEqual(OPTS)
    })
  })
})
