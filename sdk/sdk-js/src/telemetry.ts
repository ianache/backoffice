/**
 * TelemetryBatcher — batches evaluate() results and reports them back to the
 * BFF without external dependencies.
 *
 * Dual-trigger flush:
 * - `track()` flushes immediately once the queue reaches 100 events.
 * - A timer-based flush runs every 60s, but only STARTS after a randomized
 *   startup jitter (`Math.random() * 30000`, i.e. 0-30s) to avoid a
 *   thundering herd of flush requests across all SDK instances right after
 *   a deploy (per 11-RESEARCH.md / STATE.md decision).
 *
 * On `window`'s `beforeunload` event, any queued events are flushed via
 * `navigator.sendBeacon()` — the only mechanism guaranteed to complete
 * during page unload. `sendBeacon()` cannot set custom headers (no
 * `Authorization`), so the SDK key is passed as a `?sdk_key=` query param,
 * relying on the `verify_sdk_secret` query-param fallback added in Plan 06.
 */
import type { EvalEventItem } from './types'

export interface TelemetryBatcherOptions {
  apiBaseUrl: string
  sdkKey: string
  productId: string
}

export class TelemetryBatcher {
  private queue: EvalEventItem[] = []
  private flushTimer: ReturnType<typeof setInterval> | null = null

  constructor(private opts: TelemetryBatcherOptions) {
    setTimeout(() => {
      this.flushTimer = setInterval(() => {
        void this.flush()
      }, 60000)
    }, Math.random() * 30000)

    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.flushBeacon())
    }
  }

  /** Queues an evaluation event; flushes immediately once the queue reaches 100 events. */
  track(event: EvalEventItem): void {
    this.queue.push(event)
    if (this.queue.length >= 100) {
      void this.flush()
    }
  }

  /**
   * POSTs all queued events to {apiBaseUrl}/sdk/eval-events with the SDK key
   * as a Bearer token. No-op if the queue is empty.
   *
   * Known tradeoff: if the request fails (network error, non-2xx response),
   * the events are NOT re-queued and are lost. Acceptable for telemetry —
   * losing a batch of evaluation analytics is preferable to unbounded queue
   * growth or retry storms.
   */
  async flush(): Promise<void> {
    if (this.queue.length === 0) return
    const events = this.queue.splice(0, this.queue.length)
    try {
      await fetch(`${this.opts.apiBaseUrl}/sdk/eval-events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.opts.sdkKey}`,
        },
        body: JSON.stringify({ events, product_id: this.opts.productId }),
      })
    } catch {
      // telemetry is best-effort — swallow network errors
    }
  }

  /**
   * Flushes all queued events via navigator.sendBeacon(), used on
   * 'beforeunload' since fetch() may be cancelled mid-flight during unload.
   * No-op if the queue is empty.
   */
  flushBeacon(): void {
    if (this.queue.length === 0) return
    const events = this.queue.splice(0, this.queue.length)
    const payload = JSON.stringify({ events, product_id: this.opts.productId })
    navigator.sendBeacon(
      `${this.opts.apiBaseUrl}/sdk/eval-events?sdk_key=${encodeURIComponent(this.opts.sdkKey)}`,
      payload,
    )
  }

  /** Stops the interval-based flush timer. */
  destroy(): void {
    if (this.flushTimer) clearInterval(this.flushTimer)
  }
}
