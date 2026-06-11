/**
 * useBoFlags — Singleton composable for BackOffice dogfooding feature flags.
 *
 * Wraps @backoffice/sdk-js to evaluate three gating flags:
 * - `bo.feature`        → Feature Flags + Segments nav menu visibility
 * - `bo.feature.create` → Create Flag button + Clone action visibility
 * - `bo.feature.update` → Edit pencil action visibility
 *
 * Fail-open design: all refs default to `true`. If the SDK fails to
 * initialize (bad key, network error, backend down), the admin UI
 * remains fully functional — feature flags never block themselves.
 *
 * Live WS reactivity: after init, the SDK's WebSocket receives
 * `flag_updated` messages. We intercept `invalidate()` to re-fetch
 * the updated flag via `evaluateRemote()` and update the Vue ref.
 */
import { ref, readonly, type Ref } from 'vue'
import { FeatureFlagClient } from '@backoffice/sdk-js'

// ── Module-scoped singleton state ──────────────────────────────────────────
const boFeature       = ref(true)   // fail-open default
const boFeatureCreate = ref(true)   // fail-open default
const boFeatureUpdate = ref(true)   // fail-open default
const initialized     = ref(false)

let client: FeatureFlagClient | null = null
let userCtx: Record<string, unknown> = {}

// ── Flag key → ref mapping ─────────────────────────────────────────────────
const FLAG_MAP: Record<string, Ref<boolean>> = {
  'bo.features':       boFeature,
  'bo.feature.create': boFeatureCreate,
  'bo.feature.update': boFeatureUpdate,
}

function updateRef(flagKey: string, value: boolean) {
  const r = FLAG_MAP[flagKey]
  if (r) r.value = value
}

// ── Public composable ──────────────────────────────────────────────────────
export function useBoFlags() {
  /**
   * Initialize the SDK client and evaluate all dogfooding flags.
   * Non-blocking, fail-open: if anything throws, refs stay `true`.
   */
  async function init(context: Record<string, unknown>): Promise<void> {
    if (initialized.value) return // idempotent — only one client per app lifecycle
    userCtx = context

    try {
      client = new FeatureFlagClient({
        tenantId:    import.meta.env.VITE_BO_TENANT_ID ?? 'platform',
        productId:   'backoffice',
        environment: import.meta.env.VITE_BO_ENVIRONMENT ?? 'production',
        apiBaseUrl:  (import.meta.env.VITE_BFF_URL ?? 'http://localhost:3000') + '/sdk',
        sdkKey:      import.meta.env.VITE_BO_SDK_KEY ?? 'dev-sdk-secret-change-in-prod',
      })

      await client.initialize()

      // Initial evaluate — set refs from cache
      for (const [flagKey, flagRef] of Object.entries(FLAG_MAP)) {
        flagRef.value = client.evaluate(flagKey, userCtx)
      }

      // Hook WS reactivity: intercept invalidate() to re-evaluate from remote
      const originalInvalidate = client.invalidate.bind(client)
      client.invalidate = (flagKey: string) => {
        originalInvalidate(flagKey)
        // Re-fetch from remote and update the corresponding ref
        client!.evaluateRemote(flagKey, userCtx)
          .then((result) => updateRef(flagKey, result))
          .catch(() => { /* fail-open: keep current ref value */ })
      }

      initialized.value = true
    } catch (e) {
      console.warn('[bo-flags] SDK init failed, using fail-open defaults', e)
      // refs stay true — admin UI never blocked
    }
  }

  /** Clean shutdown — call on SPA unmount or hot reload. */
  function destroy(): void {
    client?.destroy()
    client = null
    initialized.value = false
  }

  /** Reset singleton state — used by tests only. */
  function _reset(): void {
    boFeature.value = true
    boFeatureCreate.value = true
    boFeatureUpdate.value = true
    initialized.value = false
    client?.destroy()
    client = null
    userCtx = {}
  }

  return {
    boFeature:       readonly(boFeature),
    boFeatureCreate: readonly(boFeatureCreate),
    boFeatureUpdate: readonly(boFeatureUpdate),
    initialized:     readonly(initialized),
    init,
    destroy,
    _reset,
  }
}
