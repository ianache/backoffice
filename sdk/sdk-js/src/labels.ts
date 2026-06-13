/**
 * LabelClient — core SDK client for the White Labeling Engine (@backoffice/sdk-js).
 *
 * - initialize(): fetches /labels/bootstrap (eager namespaces, e.g. 'common') and
 *   populates a reactive in-memory cache (LBL-08).
 * - prefetch(namespaces): fetches /labels/prefetch for lazy namespaces not yet loaded.
 * - translate(path, vars): cache-only lookup with {var} interpolation; on cache-miss
 *   returns '[sys.<key>]' and calls reportMissingLabel() (best-effort).
 * - Own ReconnectingSocket to /sdk/ws/flags/{tenantId}: filters for
 *   { type: 'INVALIDATE_NAMESPACE', namespace }, re-fetches that namespace via
 *   prefetch(); ignores 'flag_updated' and 'ping' (decoupled from FeatureFlagClient).
 *
 * Reactivity (Pitfall 5): `cache` is wrapped in Vue's reactive() so that `$t` reads
 * inside <template> expressions participate in render-effect tracking — when
 * invalidateNamespace() reloads a namespace, components using {{ $t(...) }}
 * automatically re-render.
 */
import { reactive } from 'vue'
import type { App } from 'vue'
import { ReconnectingSocket } from './websocket'

export type Locale = 'es_PE' | 'en_US'

export interface LabelClientOptions {
  tenantId: string
  companyId?: string
  productId?: string
  locale: Locale
  apiBaseUrl: string
  sdkKey: string
}

export type LabelNamespace = Record<string, string>
export type LabelBootstrapResponse = { namespaces: Record<string, LabelNamespace>; locale: string }

export class LabelClient {
  /** namespace -> { key: value }. Reactive for Vue template tracking (Pitfall 5). */
  private cache: Record<string, LabelNamespace> = reactive({})
  private loadedNamespaces = new Set<string>()
  private socket?: ReconnectingSocket

  constructor(private opts: LabelClientOptions) {}

  /** Two-phase hydration, phase 1: fetches eager namespaces (e.g. 'common') and opens the WS. */
  async initialize(): Promise<void> {
    const res = await fetch(this._url('/labels/bootstrap'), { headers: this._headers() })
    if (!res.ok) {
      throw new Error(`labels bootstrap failed: HTTP ${res.status}`)
    }
    const data: LabelBootstrapResponse = await res.json()
    Object.entries(data.namespaces).forEach(([ns, labels]) => {
      this.cache[ns] = labels
      this.loadedNamespaces.add(ns)
    })

    const wsBaseUrl = this.opts.apiBaseUrl.replace(/^http/, 'ws')
    this.socket = new ReconnectingSocket(
      `${wsBaseUrl}/sdk/ws/flags/${encodeURIComponent(this.opts.tenantId)}`,
      this.opts.sdkKey,
      (msg) => {
        if (msg?.type === 'INVALIDATE_NAMESPACE' && typeof msg.namespace === 'string') {
          this.invalidateNamespace(msg.namespace)
        }
        // 'flag_updated' and 'ping' messages are ignored — fully decoupled from FeatureFlagClient
      },
    )
  }

  /** Two-phase hydration, phase 2: loads any namespaces not already cached. */
  async prefetch(namespaces: string[]): Promise<void> {
    const missing = namespaces.filter((ns) => !this.loadedNamespaces.has(ns))
    if (missing.length === 0) return
    const res = await fetch(this._url('/labels/prefetch', { namespaces: missing.join(',') }), {
      headers: this._headers(),
    })
    if (!res.ok) {
      throw new Error(`labels prefetch failed: HTTP ${res.status}`)
    }
    const data: LabelBootstrapResponse = await res.json()
    Object.entries(data.namespaces).forEach(([ns, labels]) => {
      this.cache[ns] = labels
      this.loadedNamespaces.add(ns)
    })
  }

  /**
   * Cache-only lookup with `{var}` interpolation. `path` is `"namespace.label_key"`.
   * On cache-miss, returns `"[sys.<key>]"` and fires reportMissingLabel() (best-effort).
   */
  translate(path: string, variables?: Record<string, unknown>): string {
    const [namespace, key] = path.split('.')
    const label = this.cache[namespace]?.[key]
    if (label === undefined) {
      this.reportMissingLabel(namespace, key)
      return `[sys.${key}]`
    }
    if (!variables) return label
    return Object.entries(variables).reduce(
      (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
      label,
    )
  }

  /** Drops a namespace from the cache and reloads it in the background (hot-reload). */
  invalidateNamespace(namespace: string): void {
    delete this.cache[namespace]
    this.loadedNamespaces.delete(namespace)
    void this.prefetch([namespace])
  }

  /** RF-06: best-effort POST to /labels/missing, like TelemetryBatcher. */
  reportMissingLabel(namespace: string, labelKey: string): void {
    void fetch(`${this.opts.apiBaseUrl}/sdk/labels/missing`, {
      method: 'POST',
      headers: { ...this._headers(), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: this.opts.tenantId,
        company_id: this.opts.companyId ?? null,
        product_id: this.opts.productId ?? null,
        namespace,
        label_key: labelKey,
        locale: this.opts.locale,
      }),
    }).catch(() => {})
  }

  /** Returns the current cache as a read-only view (for debugging/tests). */
  getCache(): Readonly<Record<string, LabelNamespace>> {
    return this.cache
  }

  /** Tears down the WS connection (clean shutdown / SPA unmount). */
  destroy(): void {
    this.socket?.close()
  }

  private _headers(): Record<string, string> {
    return { Authorization: `Bearer ${this.opts.sdkKey}` }
  }

  private _url(path: string, extraQuery: Record<string, string> = {}): string {
    const qs = this._query(extraQuery)
    return `${this.opts.apiBaseUrl}/sdk${path}${qs ? `?${qs}` : ''}`
  }

  private _query(extra: Record<string, string> = {}): string {
    const params = new URLSearchParams({
      tenant_id: this.opts.tenantId,
      locale: this.opts.locale,
      ...(this.opts.companyId ? { company_id: this.opts.companyId } : {}),
      ...(this.opts.productId ? { product_id: this.opts.productId } : {}),
      ...extra,
    })
    return params.toString()
  }
}

// ---------------------------------------------------------------------------
// Vue plugin factory
// ---------------------------------------------------------------------------

export function createLabelPlugin(
  client: LabelClient,
  fallbackResolver?: (path: string, variables: Record<string, unknown> | undefined, translated: string) => string
) {
  return {
    install(app: App) {
      app.config.globalProperties.$t = (path: string, vars?: Record<string, unknown>) => {
        const translated = client.translate(path, vars)
        if (fallbackResolver) {
          return fallbackResolver(path, vars, translated)
        }
        return translated
      }
    },
  }
}

