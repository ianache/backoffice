/**
 * ReconnectingSocket — inline exponential-backoff WebSocket reconnect class.
 *
 * Connects to {wsBaseUrl}/sdk/ws/flags/{tenantId}, sends the SDK key as the
 * first text message immediately after `onopen` (first-message auth — the
 * backend `ws_router.py` expects a raw text frame, not JSON, within a
 * 10-second window; auth failure closes the socket with code 4001).
 *
 * On `onclose` (unless `close()` was called by the consumer), schedules a
 * reconnect with exponential backoff: `min(maxDelay, baseDelay * 2^attempt) + jitter`,
 * where `baseDelay=1000ms`, `maxDelay=30000ms`, and `jitter` is a random value
 * in `[0, 1000)ms`. The `attempt` counter resets to 0 on a successful `onopen`,
 * and the SDK-key handshake is repeated on every reconnect.
 *
 * `onMessage` receives the parsed JSON payload for every message (including
 * `{type:'ping'}` heartbeats — the caller decides what to ignore). Malformed
 * JSON is silently dropped (no exception escapes, `onMessage` is not called).
 *
 * No external dependencies — `reconnecting-websocket` (npm) is abandoned (2020).
 */
export class ReconnectingSocket {
  private ws: WebSocket | null = null
  private attempt = 0
  private readonly maxDelay = 30000
  private readonly baseDelay = 1000
  private closedByUser = false

  constructor(
    private url: string,
    private sdkKey: string,
    private onMessage: (data: any) => void,
  ) {
    this.connect()
  }

  private connect() {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.attempt = 0
      this.ws!.send(this.sdkKey)
    }

    this.ws.onmessage = (ev: MessageEvent) => {
      try {
        this.onMessage(JSON.parse(ev.data as string))
      } catch {
        // ignore malformed JSON
      }
    }

    this.ws.onclose = () => {
      if (!this.closedByUser) this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  private scheduleReconnect() {
    const delay = Math.min(this.maxDelay, this.baseDelay * 2 ** this.attempt) + Math.random() * 1000
    this.attempt++
    setTimeout(() => this.connect(), delay)
  }

  /** Clean shutdown — prevents any further reconnect attempts. */
  close(): void {
    this.closedByUser = true
    this.ws?.close()
  }
}
