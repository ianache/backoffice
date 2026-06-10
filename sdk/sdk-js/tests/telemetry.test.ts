import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { TelemetryBatcher } from '../src/telemetry'
import type { EvalEventItem } from '../src/types'

const OPTS = {
  apiBaseUrl: 'https://bff.example.com',
  sdkKey: 'sdk-secret-key',
  productId: 'product-1',
}

function makeEvent(i: number): EvalEventItem {
  return {
    flag_key: `flag_${i}`,
    result: true,
    evaluated_at: new Date().toISOString(),
    user_id: 'user-1',
  }
}

describe('TelemetryBatcher', () => {
  let addEventListenerMock: ReturnType<typeof vi.fn>
  let sendBeaconMock: ReturnType<typeof vi.fn>
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    vi.spyOn(Math, 'random').mockReturnValue(0.5)

    addEventListenerMock = vi.fn()
    sendBeaconMock = vi.fn()
    fetchMock = vi.fn().mockResolvedValue({ ok: true })

    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('navigator', { sendBeacon: sendBeaconMock })
    vi.stubGlobal('window', { addEventListener: addEventListenerMock })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  describe('track()', () => {
    it('does not flush for events 1-99', () => {
      const batcher = new TelemetryBatcher(OPTS)

      for (let i = 0; i < 99; i++) {
        batcher.track(makeEvent(i))
      }

      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('flushes immediately when the 100th event is tracked', async () => {
      const batcher = new TelemetryBatcher(OPTS)

      for (let i = 0; i < 100; i++) {
        batcher.track(makeEvent(i))
      }

      // flush() is async; allow the microtask queue to flush
      await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

      const [url, init] = fetchMock.mock.calls[0]
      expect(url).toBe(`${OPTS.apiBaseUrl}/sdk/eval-events`)
      expect(init.method).toBe('POST')
      expect(init.headers.Authorization).toBe(`Bearer ${OPTS.sdkKey}`)
      expect(init.headers['Content-Type']).toBe('application/json')

      const body = JSON.parse(init.body)
      expect(body.product_id).toBe(OPTS.productId)
      expect(body.events).toHaveLength(100)

      // queue is empty after flush
      await batcher.flush()
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })
  })

  describe('startup jitter + interval flush', () => {
    it('does not start the 60s interval immediately', () => {
      new TelemetryBatcher(OPTS)

      // Math.random mocked to 0.5 -> jitter = 15000ms
      vi.advanceTimersByTime(14999)
      // No interval started yet, so advancing further should not call flush
      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('starts the 60s interval after the jittered delay and flushes a non-empty queue', async () => {
      const batcher = new TelemetryBatcher(OPTS)
      batcher.track(makeEvent(1))

      // jitter = 15000ms, then interval = 60000ms => total 75000ms for first flush
      vi.advanceTimersByTime(15000) // jitter elapses, interval starts
      vi.advanceTimersByTime(60000) // interval fires

      await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    })
  })

  describe('flush()', () => {
    it('does not call fetch when the queue is empty', async () => {
      const batcher = new TelemetryBatcher(OPTS)
      await batcher.flush()
      expect(fetchMock).not.toHaveBeenCalled()
    })
  })

  describe('flushBeacon()', () => {
    it('calls navigator.sendBeacon with the events and ?sdk_key= query param when queue is non-empty', () => {
      const batcher = new TelemetryBatcher(OPTS)
      batcher.track(makeEvent(1))

      batcher.flushBeacon()

      expect(sendBeaconMock).toHaveBeenCalledTimes(1)
      const [url, body] = sendBeaconMock.mock.calls[0]
      expect(url).toBe(`${OPTS.apiBaseUrl}/sdk/eval-events?sdk_key=${encodeURIComponent(OPTS.sdkKey)}`)

      const parsed = JSON.parse(body)
      expect(parsed.product_id).toBe(OPTS.productId)
      expect(parsed.events).toHaveLength(1)
    })

    it('does not call sendBeacon when the queue is empty', () => {
      const batcher = new TelemetryBatcher(OPTS)
      batcher.flushBeacon()
      expect(sendBeaconMock).not.toHaveBeenCalled()
    })

    it('empties the queue after flushing', () => {
      const batcher = new TelemetryBatcher(OPTS)
      batcher.track(makeEvent(1))
      batcher.flushBeacon()

      sendBeaconMock.mockClear()
      batcher.flushBeacon()
      expect(sendBeaconMock).not.toHaveBeenCalled()
    })
  })

  describe('beforeunload', () => {
    it('registers a beforeunload listener that calls flushBeacon()', () => {
      new TelemetryBatcher(OPTS)

      expect(addEventListenerMock).toHaveBeenCalledWith('beforeunload', expect.any(Function))

      const handler = addEventListenerMock.mock.calls.find((c) => c[0] === 'beforeunload')![1]
      // queue is empty -> sendBeacon not called
      handler()
      expect(sendBeaconMock).not.toHaveBeenCalled()
    })
  })

  describe('destroy()', () => {
    it('clears the interval timer so flush() is not called after destroy', async () => {
      const batcher = new TelemetryBatcher(OPTS)
      batcher.track(makeEvent(1))

      vi.advanceTimersByTime(15000) // jitter elapses, interval starts

      batcher.destroy()

      vi.advanceTimersByTime(60000) // would have fired flush if not destroyed

      expect(fetchMock).not.toHaveBeenCalled()
    })
  })
})
