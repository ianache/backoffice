/**
 * FeatureFlagClient — core SDK client for @backoffice/sdk-js.
 *
 * - initialize(): fetches the SDK bootstrap snapshot from the BFF and populates
 *   an in-memory cache (SDK-05).
 * - evaluate(): synchronous, cache-only, sub-millisecond evaluation using
 *   evaluator.ts's evaluateFlag() (SDK-06). Cache-miss returns false without
 *   throwing or making a network call.
 * - evaluateRemote(): async fallback calling POST {apiBaseUrl}/sdk/evaluate (SDK-07).
 *
 * Extension points for Plan 08 (WS cache invalidation + telemetry):
 * - getCache() / invalidate() / replaceCache() for WS-driven cache updates.
 * - setEvaluationListener() for telemetry batching (no-op if unset).
 */
import { evaluateFlag } from './evaluator'
import type { BootstrapResponse, UserContext, EvalEventItem } from './types'

export interface InitOptions {
  tenantId: string
  productId: string
  environment: string
  apiBaseUrl: string
  sdkKey: string
}

export class FeatureFlagClient {
  private cache: BootstrapResponse = {}
  private evaluationListener?: (event: EvalEventItem) => void

  constructor(private opts: InitOptions) {}

  /**
   * Fetches the bootstrap snapshot from {apiBaseUrl}/sdk/bootstrap and
   * populates the in-memory cache. Must be called before evaluate()/evaluateRemote()
   * for evaluate() to return non-default results.
   */
  async initialize(): Promise<void> {
    const url = `${this.opts.apiBaseUrl}/sdk/bootstrap?tenant_id=${encodeURIComponent(this.opts.tenantId)}&product_id=${encodeURIComponent(this.opts.productId)}&environment=${encodeURIComponent(this.opts.environment)}`
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${this.opts.sdkKey}` },
    })
    this.cache = await res.json()
  }

  /**
   * Synchronous, cache-only evaluation. Returns `false` on cache-miss without
   * throwing or making a network call. Calls the optional evaluation listener
   * (set via setEvaluationListener) AFTER computing the result.
   */
  evaluate(flagKey: string, user: UserContext): boolean {
    const entry = this.cache[flagKey]
    const result = entry ? evaluateFlag(entry, user) : false
    if (this.evaluationListener) {
      this.evaluationListener({
        flag_key: flagKey,
        result,
        evaluated_at: new Date().toISOString(),
        user_id: String(user.id ?? user.sub ?? user.user_id ?? 'anonymous'),
      })
    }
    return result
  }

  /**
   * Async remote fallback: POSTs to {apiBaseUrl}/sdk/evaluate and resolves
   * to the boolean `result` field of the response.
   */
  async evaluateRemote(flagKey: string, user: UserContext): Promise<boolean> {
    const res = await fetch(`${this.opts.apiBaseUrl}/sdk/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.opts.sdkKey}`,
      },
      body: JSON.stringify({ flag_key: flagKey, user }),
    })
    const data = await res.json()
    return Boolean(data.result)
  }

  /** Returns the current cache as a read-only view. */
  getCache(): Readonly<BootstrapResponse> {
    return this.cache
  }

  /** Removes a single flag entry from the cache (Plan 08 WS invalidation). */
  invalidate(flagKey: string): void {
    delete this.cache[flagKey]
  }

  /** Replaces the entire cache (Plan 08 WS full-refresh). */
  replaceCache(newCache: BootstrapResponse): void {
    this.cache = newCache
  }

  /** Registers a listener invoked after every evaluate() call (Plan 08 telemetry). */
  setEvaluationListener(fn: (event: EvalEventItem) => void): void {
    this.evaluationListener = fn
  }

  /** Returns the InitOptions used to construct this client. */
  getOptions(): Readonly<InitOptions> {
    return this.opts
  }
}
