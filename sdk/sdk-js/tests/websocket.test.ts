import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ReconnectingSocket } from '../src/websocket'

/**
 * Minimal mock of the browser WebSocket API. Stores the constructor URL,
 * exposes `send`/`close` spies, and provides `triggerOpen()`/`triggerMessage(data)`/
 * `triggerClose()` helpers to manually invoke the handlers assigned by
 * ReconnectingSocket.
 */
class MockWebSocket {
  static instances: MockWebSocket[] = []

  url: string
  send = vi.fn()
  close = vi.fn()
  onopen: (() => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  triggerOpen() {
    this.onopen?.()
  }

  triggerMessage(data: string) {
    this.onmessage?.({ data })
  }

  triggerClose() {
    this.onclose?.()
  }

  triggerError() {
    this.onerror?.()
  }
}

describe('ReconnectingSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('opens a WebSocket to the given URL on construction', () => {
    new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

    expect(MockWebSocket.instances).toHaveLength(1)
    expect(MockWebSocket.instances[0].url).toBe('wss://example.com/ws/flags/tenant-1')
  })

  it('sends the sdk key as a raw text message on open (first-message auth)', () => {
    new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

    const ws = MockWebSocket.instances[0]
    ws.triggerOpen()

    expect(ws.send).toHaveBeenCalledTimes(1)
    expect(ws.send).toHaveBeenCalledWith('sdk-key')
  })

  it('parses JSON messages and forwards the parsed object to onMessage', () => {
    const onMessage = vi.fn()
    new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', onMessage)

    const ws = MockWebSocket.instances[0]
    ws.triggerMessage(JSON.stringify({ type: 'flag_updated', flag_key: 'my_flag' }))

    expect(onMessage).toHaveBeenCalledTimes(1)
    expect(onMessage).toHaveBeenCalledWith({ type: 'flag_updated', flag_key: 'my_flag' })
  })

  it('forwards ping messages to onMessage without filtering', () => {
    const onMessage = vi.fn()
    new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', onMessage)

    const ws = MockWebSocket.instances[0]
    ws.triggerMessage(JSON.stringify({ type: 'ping' }))

    expect(onMessage).toHaveBeenCalledTimes(1)
    expect(onMessage).toHaveBeenCalledWith({ type: 'ping' })
  })

  it('does not call onMessage and does not throw on malformed JSON', () => {
    const onMessage = vi.fn()
    new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', onMessage)

    const ws = MockWebSocket.instances[0]
    expect(() => ws.triggerMessage('{not valid json')).not.toThrow()
    expect(onMessage).not.toHaveBeenCalled()
  })

  describe('reconnect with exponential backoff + jitter', () => {
    it('schedules the 1st reconnect with delay in [1000, 2000)ms', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0)
      new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

      const ws = MockWebSocket.instances[0]
      ws.triggerClose()

      // Not yet reconnected just before delay
      vi.advanceTimersByTime(999)
      expect(MockWebSocket.instances).toHaveLength(1)

      // Reconnects at ~1000ms (base * 2^0 + jitter*0)
      vi.advanceTimersByTime(1)
      expect(MockWebSocket.instances).toHaveLength(2)

      vi.restoreAllMocks()
    })

    it('schedules the 2nd reconnect with delay in [2000, 3000)ms after a 2nd close without reopening', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0)
      new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

      // 1st close -> attempt becomes 1, reconnect after ~1000ms
      MockWebSocket.instances[0].triggerClose()
      vi.advanceTimersByTime(1000)
      expect(MockWebSocket.instances).toHaveLength(2)

      // 2nd close (without onopen, so attempt is still 1) -> reconnect after ~2000ms
      MockWebSocket.instances[1].triggerClose()
      vi.advanceTimersByTime(1999)
      expect(MockWebSocket.instances).toHaveLength(2)
      vi.advanceTimersByTime(1)
      expect(MockWebSocket.instances).toHaveLength(3)

      vi.restoreAllMocks()
    })

    it('schedules the 3rd reconnect with delay in [4000, 5000)ms', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0)
      new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

      MockWebSocket.instances[0].triggerClose() // attempt 0 -> 1, delay ~1000
      vi.advanceTimersByTime(1000)
      MockWebSocket.instances[1].triggerClose() // attempt 1 -> 2, delay ~2000
      vi.advanceTimersByTime(2000)
      MockWebSocket.instances[2].triggerClose() // attempt 2 -> 3, delay ~4000
      vi.advanceTimersByTime(3999)
      expect(MockWebSocket.instances).toHaveLength(3)
      vi.advanceTimersByTime(1)
      expect(MockWebSocket.instances).toHaveLength(4)

      vi.restoreAllMocks()
    })

    it('caps the reconnect delay at maxDelay=30000ms for high attempt counts', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0)
      new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

      // Drive attempt counter up: 1000, 2000, 4000, 8000, 16000 -> attempt=5, next delay capped at 30000
      let idx = 0
      const delays = [1000, 2000, 4000, 8000, 16000]
      for (const delay of delays) {
        MockWebSocket.instances[idx].triggerClose()
        vi.advanceTimersByTime(delay)
        idx++
      }
      expect(MockWebSocket.instances).toHaveLength(idx + 1)

      // attempt is now 5 -> base*2^5 = 32000, capped at 30000
      MockWebSocket.instances[idx].triggerClose()
      vi.advanceTimersByTime(29999)
      expect(MockWebSocket.instances).toHaveLength(idx + 1)
      vi.advanceTimersByTime(1)
      expect(MockWebSocket.instances).toHaveLength(idx + 2)

      vi.restoreAllMocks()
    })

    it('resets the attempt counter to 0 on successful open, so a subsequent close reconnects after ~1000ms again', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0)
      new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())

      // 1st close -> attempt 0->1, reconnect after 1000ms
      MockWebSocket.instances[0].triggerClose()
      vi.advanceTimersByTime(1000)
      expect(MockWebSocket.instances).toHaveLength(2)

      // Successful open resets attempt to 0
      MockWebSocket.instances[1].triggerOpen()

      // 2nd close after successful open -> reconnect after ~1000ms again (not 2000ms)
      MockWebSocket.instances[1].triggerClose()
      vi.advanceTimersByTime(999)
      expect(MockWebSocket.instances).toHaveLength(2)
      vi.advanceTimersByTime(1)
      expect(MockWebSocket.instances).toHaveLength(3)

      vi.restoreAllMocks()
    })
  })

  describe('close()', () => {
    it('prevents reconnection after a subsequent onclose', () => {
      const rs = new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())
      const ws = MockWebSocket.instances[0]

      rs.close()
      ws.triggerClose()
      vi.advanceTimersByTime(60000)

      expect(MockWebSocket.instances).toHaveLength(1)
    })

    it('calls ws.close() on the underlying socket', () => {
      const rs = new ReconnectingSocket('wss://example.com/ws/flags/tenant-1', 'sdk-key', vi.fn())
      const ws = MockWebSocket.instances[0]

      rs.close()

      expect(ws.close).toHaveBeenCalledTimes(1)
    })
  })
})
