import { describe, it, expect, vi, beforeEach } from 'vitest'

const { MockClient, mockInitialize, mockEvaluate, mockEvaluateRemote, mockDestroy, mockGetCache } = vi.hoisted(() => {
  const mockInitialize = vi.fn()
  const mockEvaluate = vi.fn()
  const mockDestroy = vi.fn()
  const mockEvaluateRemote = vi.fn()
  const mockGetCache = vi.fn()

  const MockClient = vi.fn().mockImplementation(() => ({
    initialize: mockInitialize,
    evaluate: mockEvaluate,
    evaluateRemote: mockEvaluateRemote,
    invalidate: vi.fn(),
    getCache: mockGetCache,
    destroy: mockDestroy,
  }))

  return { MockClient, mockInitialize, mockEvaluate, mockEvaluateRemote, mockDestroy, mockGetCache }
})

vi.mock('@backoffice/sdk-js', () => ({
  FeatureFlagClient: MockClient,
}))

import { useBoFlags } from './useBoFlags'

describe('useBoFlags', () => {
  let composable: ReturnType<typeof useBoFlags>

  beforeEach(() => {
    composable = useBoFlags()
    composable._reset()
    MockClient.mockClear()
    mockInitialize.mockReset()
    mockEvaluate.mockReset()
    mockEvaluateRemote.mockReset()
    mockDestroy.mockReset()
    mockGetCache.mockReset()
    mockGetCache.mockReturnValue({})
  })

  it('defaults to true (fail-open) before init', () => {
    expect(composable.boFeature.value).toBe(true)
    expect(composable.boFeatureCreate.value).toBe(true)
    expect(composable.boFeatureUpdate.value).toBe(true)
    expect(composable.initialized.value).toBe(false)
  })

  it('refs remain true when SDK init fails', async () => {
    mockInitialize.mockRejectedValue(new Error('Connection failed'))

    await expect(composable.init({ sub: 'user1' })).resolves.not.toThrow()

    expect(composable.boFeature.value).toBe(true)
    expect(composable.boFeatureCreate.value).toBe(true)
    expect(composable.boFeatureUpdate.value).toBe(true)
    expect(composable.initialized.value).toBe(false)
  })

  it('refs reflect evaluate() results after successful init', async () => {
    mockInitialize.mockResolvedValue(undefined)
    mockGetCache.mockReturnValue({
      'bo.feature': {},
      'bo.feature.create': {},
      'bo.feature.update': {},
    })
    mockEvaluate.mockImplementation((flagKey) => {
      if (flagKey === 'bo.feature') return true
      if (flagKey === 'bo.feature.create') return false
      if (flagKey === 'bo.feature.update') return true
      return false
    })

    await composable.init({ sub: 'user1' })

    expect(composable.initialized.value).toBe(true)
    expect(composable.boFeature.value).toBe(true)
    expect(composable.boFeatureCreate.value).toBe(false)
    expect(composable.boFeatureUpdate.value).toBe(true)
  })

  it('accepts the legacy bo.features alias for menu visibility', async () => {
    mockInitialize.mockResolvedValue(undefined)
    mockGetCache.mockReturnValue({
      'bo.features': {},
    })
    mockEvaluate.mockImplementation((flagKey) => flagKey === 'bo.features')

    await composable.init({ sub: 'user1' })

    expect(composable.boFeature.value).toBe(true)
  })

  it('init is idempotent — second call is a no-op', async () => {
    mockInitialize.mockResolvedValue(undefined)
    mockEvaluate.mockReturnValue(true)

    await composable.init({ sub: 'user1' })
    await composable.init({ sub: 'user2' })

    expect(MockClient).toHaveBeenCalledTimes(1)
  })
})
