import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock the @backoffice/sdk-js package
const { MockLabelClient, mockInitialize, mockTranslate, mockDestroy, mockPrefetch } = vi.hoisted(() => {
  const mockInitialize = vi.fn()
  const mockTranslate = vi.fn()
  const mockDestroy = vi.fn()
  const mockPrefetch = vi.fn()

  const MockLabelClient = vi.fn().mockImplementation((opts) => ({
    opts,
    initialize: mockInitialize,
    translate: mockTranslate,
    destroy: mockDestroy,
    prefetch: mockPrefetch,
  }))

  return {
    MockLabelClient,
    mockInitialize,
    mockTranslate,
    mockDestroy,
    mockPrefetch,
  }
})

vi.mock('@backoffice/sdk-js', () => ({
  LabelClient: MockLabelClient,
  createLabelPlugin: vi.fn().mockImplementation((client, resolver) => ({
    install(app: any) {
      app.config.globalProperties.$t = (path: string, vars?: any) => {
        const translated = client.translate(path, vars)
        if (resolver) {
          return resolver(path, vars, translated)
        }
        return translated
      }
    }
  }))
}))

import { useLoginLabels, detectLoginLocale, CATALOG_FALLBACK } from './useLoginLabels'

describe('useLoginLabels', () => {
  let composable: ReturnType<typeof useLoginLabels>

  beforeEach(() => {
    vi.useFakeTimers()
    composable = useLoginLabels()
    composable._reset()
    MockLabelClient.mockClear()
    mockInitialize.mockReset()
    mockTranslate.mockReset()
    mockDestroy.mockReset()
    mockPrefetch.mockReset()
    mockPrefetch.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('detectLoginLocale', () => {
    it('maps es/es-* to es_PE and other/empty to en_US', () => {
      expect(detectLoginLocale('es')).toBe('es_PE')
      expect(detectLoginLocale('es-PE')).toBe('es_PE')
      expect(detectLoginLocale('ES-AR')).toBe('es_PE')
      expect(detectLoginLocale('en-US')).toBe('en_US')
      expect(detectLoginLocale('fr-FR')).toBe('en_US')
      expect(detectLoginLocale('')).toBe('en_US')
      expect(detectLoginLocale(undefined)).toBe('en_US')
    })
  })

  describe('LabelClient initialization and configuration', () => {
    it('creates client with default environment values and no company context', () => {
      // Accessing client getter triggers instantiation after mockClear
      const clientInstance = composable.client as any
      expect(MockLabelClient).toHaveBeenCalled()
      expect(clientInstance.opts.productId).toBe('backoffice')
      expect(clientInstance.opts.companyId).toBeUndefined()
    })
  })

  describe('initialize()', () => {
    it('is idempotent and starts initialization only once', async () => {
      mockInitialize.mockResolvedValue(undefined)
      const p1 = composable.initialize()
      const p2 = composable.initialize()

      expect(p1).toBe(p2)
      await p1
      expect(mockInitialize).toHaveBeenCalledTimes(1)
      expect(composable.initialized.value).toBe(true)
    })

    it('swallows and logs initialization failures (fail-open)', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      mockInitialize.mockRejectedValue(new Error('Network failure'))

      await expect(composable.initialize()).resolves.not.toThrow()
      expect(composable.initialized.value).toBe(false)
      expect(warnSpy).toHaveBeenCalled()
      warnSpy.mockRestore()
    })
  })

  describe('waitForInitialLabels()', () => {
    it('resolves after 1000ms deadline even if client is still pending', async () => {
      let resolveInit: any
      const initPromise = new Promise<void>((resolve) => {
        resolveInit = resolve
      })
      mockInitialize.mockReturnValue(initPromise)

      const waitPromise = composable.waitForInitialLabels(1000)

      // Advance timers by 999ms - should still be pending
      await vi.advanceTimersByTimeAsync(999)
      
      // Advance to 1000ms - should resolve
      await vi.advanceTimersByTimeAsync(1)
      await expect(waitPromise).resolves.not.toThrow()
      
      expect(composable.initialized.value).toBe(false)

      // Resolve original initialize now
      resolveInit()
      
      // Await initialize() to allow composable state to update and settle
      await composable.initialize()
      expect(composable.initialized.value).toBe(true)
    })
  })

  describe('translate fallback logic (t)', () => {
    it('returns catalog fallback for missing keys or when not initialized', () => {
      // client.translate returns [sys.key] on missing
      mockTranslate.mockReturnValue('[sys.welcome_title]')

      const val = composable.t('login.welcome_title')
      // Make it locale-independent based on what locale actually got detected
      const currentLocale = composable.locale.value
      expect(val).toBe(CATALOG_FALLBACK[currentLocale].welcome_title)
    })

    it('passes through remote value if found in cache', () => {
      mockTranslate.mockReturnValue('Welcome Back (Remote)')

      const val = composable.t('login.welcome_title')
      expect(val).toBe('Welcome Back (Remote)')
    })
  })
})
