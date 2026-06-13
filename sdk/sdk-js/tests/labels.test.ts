import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { isReactive } from 'vue'

// Mock ./websocket entirely so LabelClient never opens a real WebSocket.
// Capture the onMessage callback passed to ReconnectingSocket's constructor
// so tests can simulate incoming WS messages (INVALIDATE_NAMESPACE/flag_updated/ping).
let capturedOnMessage: ((data: any) => void) | undefined
const mockSocketClose = vi.fn()

vi.mock('../src/websocket', () => ({
  ReconnectingSocket: vi.fn().mockImplementation((_url: string, _key: string, onMessage: (data: any) => void) => {
    capturedOnMessage = onMessage
    return { close: mockSocketClose }
  }),
}))

import { LabelClient, createLabelPlugin } from '../src/labels'

const OPTS = {
  tenantId: 'tenant-1',
  locale: 'es_PE' as const,
  apiBaseUrl: 'https://bff.example.com',
  sdkKey: 'sdk-secret-key',
}

const BOOTSTRAP_FIXTURE = {
  namespaces: {
    common: { btn_aceptar: 'Aceptar' },
  },
  locale: 'es_PE',
}

describe('LabelClient', () => {
  beforeEach(() => {
    capturedOnMessage = undefined
    mockSocketClose.mockClear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('initialize()', () => {
    it('fetches /labels/bootstrap and populates the cache', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new LabelClient(OPTS)
      await client.initialize()

      const [url] = fetchMock.mock.calls[0]
      expect(url).toContain(`${OPTS.apiBaseUrl}/sdk/labels/bootstrap`)
      expect(url).toContain('tenant_id=tenant-1')
      expect(url).toContain('locale=es_PE')

      expect(client.translate('common.btn_aceptar')).toBe('Aceptar')
    })
  })

  describe('translate()', () => {
    it('interpolates {var} placeholders', async () => {
      const fixture = {
        namespaces: {
          common: { msg_bienvenida: 'Hola {name}, bienvenido a {app}' },
        },
        locale: 'es_PE',
      }
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok: true,
          json: async () => fixture,
        }),
      )

      const client = new LabelClient(OPTS)
      await client.initialize()

      expect(client.translate('common.msg_bienvenida', { name: 'Ana', app: 'BackOffice' })).toBe(
        'Hola Ana, bienvenido a BackOffice',
      )
    })

    it('returns [sys.key] and reports missing label for unknown key', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new LabelClient(OPTS)
      await client.initialize()

      fetchMock.mockClear()
      fetchMock.mockResolvedValue({ ok: true, json: async () => ({}) })

      const result = client.translate('common.unknown_key')

      expect(result).toBe('[sys.unknown_key]')

      // reportMissingLabel is a best-effort fire-and-forget fetch — flush microtasks
      await Promise.resolve()
      await Promise.resolve()

      const missingCall = fetchMock.mock.calls.find(([url]) => String(url).includes('/labels/missing'))
      expect(missingCall).toBeDefined()
      const [url, init] = missingCall!
      expect(url).toBe(`${OPTS.apiBaseUrl}/sdk/labels/missing`)
      expect(init.method).toBe('POST')
      const body = JSON.parse(init.body)
      expect(body.namespace).toBe('common')
      expect(body.label_key).toBe('unknown_key')
      expect(body.locale).toBe(OPTS.locale)
    })
  })

  describe('prefetch()', () => {
    it('loads only missing namespaces', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new LabelClient(OPTS)
      await client.initialize()

      fetchMock.mockClear()
      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => ({ namespaces: { page_dashboard: { title: 'Dashboard' } }, locale: 'es_PE' }),
      })

      await client.prefetch(['common', 'page_dashboard'])

      expect(fetchMock).toHaveBeenCalledTimes(1)
      const [url] = fetchMock.mock.calls[0]
      expect(url).toContain('/labels/prefetch')
      expect(url).toContain('namespaces=page_dashboard')
      expect(url).not.toContain('common')

      expect(client.translate('page_dashboard.title')).toBe('Dashboard')
    })
  })

  describe('WS hot-reload', () => {
    it('INVALIDATE_NAMESPACE triggers re-fetch of that namespace', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new LabelClient(OPTS)
      await client.initialize()

      expect(capturedOnMessage).toBeDefined()

      fetchMock.mockClear()
      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => ({ namespaces: { common: { btn_aceptar: 'Aceptar (actualizado)' } }, locale: 'es_PE' }),
      })

      capturedOnMessage!({ type: 'INVALIDATE_NAMESPACE', namespace: 'common' })

      // cache cleared synchronously
      expect((client as any).cache.common).toBeUndefined()

      // prefetch is async — flush microtasks
      await Promise.resolve()
      await Promise.resolve()
      await Promise.resolve()

      expect(fetchMock).toHaveBeenCalledTimes(1)
      const [url] = fetchMock.mock.calls[0]
      expect(url).toContain('/labels/prefetch')
      expect(url).toContain('namespaces=common')

      expect(client.translate('common.btn_aceptar')).toBe('Aceptar (actualizado)')
    })

    it('flag_updated message is ignored', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new LabelClient(OPTS)
      await client.initialize()

      fetchMock.mockClear()

      capturedOnMessage!({ type: 'flag_updated', flag_key: 'x' })

      await Promise.resolve()
      await Promise.resolve()

      expect(fetchMock).not.toHaveBeenCalled()
      expect(client.translate('common.btn_aceptar')).toBe('Aceptar')
    })
  })

  describe('reactive cache', () => {
    it('cache is a Vue reactive() object', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok: true,
          json: async () => BOOTSTRAP_FIXTURE,
        }),
      )

      const client = new LabelClient(OPTS)
      await client.initialize()

      expect(isReactive((client as any).cache)).toBe(true)
    })
  })

  describe('createLabelPlugin', () => {
    it('installs $t as a global property', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok: true,
          json: async () => BOOTSTRAP_FIXTURE,
        }),
      )

      const client = new LabelClient(OPTS)
      await client.initialize()

      const plugin = createLabelPlugin(client)
      const app = { config: { globalProperties: {} as any } } as any
      plugin.install(app)

      expect(typeof app.config.globalProperties.$t).toBe('function')
      expect(app.config.globalProperties.$t('common.btn_aceptar')).toBe('Aceptar')
    })

    it('uses fallbackResolver when provided', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => BOOTSTRAP_FIXTURE,
      })
      vi.stubGlobal('fetch', fetchMock)

      const client = new LabelClient(OPTS)
      await client.initialize()

      const resolver = vi.fn().mockImplementation((path, vars, translated) => {
        if (translated.startsWith('[sys.')) {
          return 'Fallback copy'
        }
        return translated
      })

      const plugin = createLabelPlugin(client, resolver)
      const app = { config: { globalProperties: {} as any } } as any
      plugin.install(app)

      expect(app.config.globalProperties.$t('common.btn_aceptar')).toBe('Aceptar')
      expect(resolver).toHaveBeenCalledWith('common.btn_aceptar', undefined, 'Aceptar')

      // Cache miss test case
      fetchMock.mockClear()
      fetchMock.mockResolvedValue({ ok: true, json: async () => ({}) })
      const val = app.config.globalProperties.$t('common.missing_key')
      expect(val).toBe('Fallback copy')
      expect(resolver).toHaveBeenCalledWith('common.missing_key', undefined, '[sys.missing_key]')

      // reportMissingLabel is fire-and-forget — flush microtasks
      await Promise.resolve()
      await Promise.resolve()
      const missingCall = fetchMock.mock.calls.find(([url]) => String(url).includes('/labels/missing'))
      expect(missingCall).toBeDefined()
    })
  })
})

