import { describe, it, expect, vi, beforeEach } from 'vitest'

const { MockClient, mockInitialize, mockEvaluate, mockEvaluateRemote, mockDestroy } = vi.hoisted(() => {
  const mockInitialize = vi.fn()
  const mockEvaluate = vi.fn()
  const mockDestroy = vi.fn()
  const mockEvaluateRemote = vi.fn()

  const MockClient = vi.fn().mockImplementation(() => ({
    initialize: mockInitialize,
    evaluate: mockEvaluate,
    evaluateRemote: mockEvaluateRemote,
    invalidate: vi.fn(),
    destroy: mockDestroy,
  }))

  return { MockClient, mockInitialize, mockEvaluate, mockEvaluateRemote, mockDestroy }
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
    mockEvaluate.mockImplementation((flagKey) => {
      if (flagKey === 'bo.features') return true
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

  it('init is idempotent — second call is a no-op', async () => {
    mockInitialize.mockResolvedValue(undefined)
    mockEvaluate.mockReturnValue(true)

    await composable.init({ sub: 'user1' })
    await composable.init({ sub: 'user2' })

    expect(MockClient).toHaveBeenCalledTimes(1)
  })
})
