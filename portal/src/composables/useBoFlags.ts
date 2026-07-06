/**
 * useBoFlags - Singleton composable for BackOffice dogfooding feature flags.
 *
 * Wraps @backoffice/sdk-js to evaluate three gating flags:
 * - `bo.feature` / `bo.features` -> Feature Flags + Segments nav menu visibility
 * - `bo.feature.create` -> Create Flag button + Clone action visibility
 * - `bo.feature.update` -> Edit pencil action visibility
 *
 * Fail-open design: all refs default to `true`. If the SDK fails to
 * initialize (bad key, network error, backend down), the admin UI
 * remains fully functional.
 *
 * Live WS reactivity: after init, the SDK's WebSocket receives
 * `flag_updated` messages. We intercept `invalidate()` to re-fetch
 * the updated flag via `evaluateRemote()` and update the Vue ref.
 */
import { ref, readonly, type Ref } from 'vue'
import { FeatureFlagClient } from '@backoffice/sdk-js'

const boFeature = ref(true)
const boFeatureCreate = ref(true)
const boFeatureUpdate = ref(true)
const initialized = ref(false)

let client: FeatureFlagClient | null = null
let userCtx: Record<string, unknown> = {}

type FlagGroup = {
  keys: string[]
  ref: Ref<boolean>
}

const FLAG_GROUPS: FlagGroup[] = [
  { keys: ['bo.feature', 'bo.features'], ref: boFeature },
  { keys: ['bo.feature.create'], ref: boFeatureCreate },
  { keys: ['bo.feature.update'], ref: boFeatureUpdate },
]

const FLAG_GROUP_BY_KEY = new Map<string, FlagGroup>(
  FLAG_GROUPS.flatMap((group) => group.keys.map((key) => [key, group] as const)),
)

function syncFlag(group: FlagGroup) {
  if (!client) return
  if (group.ref === boFeature) {
    group.ref.value = true
    return
  }
  const cache = client.getCache()
  const activeKey = group.keys.find((key) => cache[key] !== undefined)
  if (!activeKey) return
  group.ref.value = client.evaluate(activeKey, userCtx)
}

export function useBoFlags() {
  async function init(context: Record<string, unknown>): Promise<void> {
    if (initialized.value) return
    userCtx = context

    try {
      client = new FeatureFlagClient({
        tenantId: import.meta.env.VITE_BO_TENANT_ID ?? 'platform',
        productId: 'backoffice',
        environment: import.meta.env.VITE_BO_ENVIRONMENT ?? 'production',
        apiBaseUrl: import.meta.env.VITE_BFF_URL ?? 'http://localhost:3000',
        sdkKey: import.meta.env.VITE_BO_SDK_KEY ?? 'dev-sdk-secret-change-in-prod',
      })

      await client.initialize()

      FLAG_GROUPS.forEach(syncFlag)

      const originalInvalidate = client.invalidate.bind(client)
      client.invalidate = (flagKey: string) => {
        originalInvalidate(flagKey)
        const group = FLAG_GROUP_BY_KEY.get(flagKey)
        if (group) {
          if (group.ref === boFeature) {
            boFeature.value = true
            return
          }
          syncFlag(group)
          return
        }
        client!.evaluateRemote(flagKey, userCtx).catch(() => {
          /* fail-open: keep current ref value */
        })
      }

      initialized.value = true
    } catch (e) {
      console.warn('[bo-flags] SDK init failed, using fail-open defaults', e)
    }
  }

  function destroy(): void {
    client?.destroy()
    client = null
    initialized.value = false
  }

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
    boFeature: readonly(boFeature),
    boFeatureCreate: readonly(boFeatureCreate),
    boFeatureUpdate: readonly(boFeatureUpdate),
    initialized: readonly(initialized),
    init,
    destroy,
    _reset,
  }
}
