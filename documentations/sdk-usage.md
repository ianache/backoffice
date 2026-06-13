# `@backoffice/sdk-js` Usage & Integration Guide

This document provides a detailed technical guide on how the BackOffice Feature Flag SDK (`@backoffice/sdk-js`) is integrated internally within the BackOffice Portal (Dogfooding) and how it can be incorporated into external, third-party projects.

---

## 1. SDK Architecture Overview

The `@backoffice/sdk-js` is a lightweight, high-performance client-side library designed to fetch, evaluate, and synchronize feature flags.

```
┌────────────────────────────────────────────────────────┐
│                   BackOffice Control Plane             │
└───────────────────────────┬────────────────────────────┘
                            │ (Bootstrap / WebSockets)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 @backoffice/sdk-js                     │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Bootstrap Cache  │  │ WS Client    │  │Telemetry │  │
│  └────────┬─────────┘  └──────┬───────┘  └────▲─────┘  │
└───────────┼───────────────────┼───────────────┼────────┘
            │ evaluate()        │ invalidate()  │ track()
            ▼                   ▼               │
┌────────────────────────────────────────────────────────┐
│                   Consumer Application                 │
└────────────────────────────────────────────────────────┘
```

### Key SDK Capabilities:
* **Bootstrap cache:** Upon initialization, it fetches all targeting rules and flags from the BFF (`/sdk/bootstrap`) in a single network request.
* **Sub-millisecond Evaluation:** Evaluation is synchronous and cache-only (`client.evaluate(flagKey, context)`), avoiding network hops in critical rendering paths.
* **WebSocket Semicolon Sync:** Establishes a reconnecting WebSocket connection. Whenever a flag changes, a `flag_updated` event is sent to invalidate that specific cache entry.
* **Telemetry & Reporting:** Evaluated flags automatically queue up evaluation metadata sent back in batches for analytics and impressions.
* **Fail-Open Philosophy:** If the SDK fails to boot (network issues, incorrect key, Control Plane down), evaluations degrade gracefully without blocking user interaction.

---

## 2. Dogfooding in the BackOffice Portal (Internal)

Within the BackOffice project, the Portal serves as the primary "dogfooding" consumer of the feature flag system.

### A. The Composable Singleton: `useBoFlags.ts`
Path: `portal/src/composables/useBoFlags.ts`

The composable wraps the SDK inside a module-scoped singleton, ensuring only one instance of the client and WS connection is shared across all Vue components.

```typescript
import { ref, readonly, type Ref } from 'vue'
import { FeatureFlagClient } from '@backoffice/sdk-js'

// Singleton reactive state
const boFeature       = ref(true) // Gating of menus
const boFeatureCreate = ref(true) // Gating of creation / clone
const boFeatureUpdate = ref(true) // Gating of edit/update actions
const initialized     = ref(false)

let client: FeatureFlagClient | null = null
let userCtx: Record<string, unknown> = {}

const FLAG_MAP: Record<string, Ref<boolean>> = {
  'bo.features':       boFeature,
  'bo.feature.create': boFeatureCreate,
  'bo.feature.update': boFeatureUpdate,
}

export function useBoFlags() {
  async function init(context: Record<string, unknown>): Promise<void> {
    if (initialized.value) return
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

      // Initial Evaluation
      for (const [flagKey, flagRef] of Object.entries(FLAG_MAP)) {
        flagRef.value = client.evaluate(flagKey, userCtx)
      }

      // Live WebSocket Reactivity
      const originalInvalidate = client.invalidate.bind(client)
      client.invalidate = (flagKey: string) => {
        originalInvalidate(flagKey)
        // Re-fetch remotely when invalidated and update matching Ref
        client!.evaluateRemote(flagKey, userCtx)
          .then((result) => {
            const r = FLAG_MAP[flagKey]
            if (r) r.value = result
          })
          .catch(() => { /* Fail-open: retain last value */ })
      }

      initialized.value = true
    } catch (e) {
      console.warn('[bo-flags] SDK init failed, using fail-open defaults', e)
    }
  }

  function destroy() {
    client?.destroy()
    client = null
    initialized.value = false
  }

  return {
    boFeature:       readonly(boFeature),
    boFeatureCreate: readonly(boFeatureCreate),
    boFeatureUpdate: readonly(boFeatureUpdate),
    initialized:     readonly(initialized),
    init,
    destroy,
  }
}
```

### B. Startup Initialization
Path: `portal/src/main.ts`

The SDK initializes as soon as Keycloak authentication is established. Crucially, the initialization is **non-blocking** (using fire-and-forget `.catch()`), preventing the application loading sequence from stalling if the SDK backend is unreachable.

```typescript
import { useBoFlags } from './composables/useBoFlags'

// Initialize flags only after authentication is confirmed
if (authStore.isAuthenticated) {
  useBoFlags().init({ sub: authStore.user?.email ?? '', roles: authStore.roles })
    .catch(() => {}) // Fail-open: do not block app load
}
```

### C. Module Federation Exposure
Path: `portal/vite.config.ts`

Since the Portal uses a micro-frontend architecture with Module Federation, the Shell exposes the `useBoFlags` composable so that federated Micro UIs (remotes) can access the exact same state without initializing their own clients.

```typescript
exposes: {
  './boFlags': './src/composables/useBoFlags.ts',
}
```

---

## 3. Integration Guide for Third-Party Products

If an external application or product wants to implement BackOffice Feature Flags, they can incorporate the SDK by following these integration steps.

### Step 1: Install the SDK Package

First, add `@backoffice/sdk-js` to your product's dependencies.

```bash
# npm
npm install @backoffice/sdk-js

# pnpm
pnpm add @backoffice/sdk-js

# yarn
yarn add @backoffice/sdk-js
```

### Step 2: Configure Environment Variables

Configure the required environmental keys. Each environment (dev, staging, production) must have its respective SDK Secret Key generated from the BackOffice Admin Console.

```env
VITE_BO_API_BASE_URL=https://flags.mycompany.com/sdk
VITE_BO_SDK_KEY=sdk_secret_prod_abc123xyz
VITE_BO_TENANT_ID=enterprise-tenant-a
VITE_BO_ENVIRONMENT=production
```

### Step 3: Initialize the SDK Client

Call the `initialize` helper when booting your application. Make sure to define the unique `productId` that corresponds to your application in BackOffice.

```typescript
import { initialize, type FeatureFlagClient } from '@backoffice/sdk-js'

let flagClient: FeatureFlagClient | null = null

export async function bootstrapFeatureFlags(user: { id: string; email: string; roles: string[] }) {
  try {
    flagClient = await initialize({
      tenantId:    import.meta.env.VITE_BO_TENANT_ID,
      productId:   'e-commerce-portal', // Your custom registered Product ID
      environment: import.meta.env.VITE_BO_ENVIRONMENT,
      apiBaseUrl:  import.meta.env.VITE_BO_API_BASE_URL,
      sdkKey:      import.meta.env.VITE_BO_SDK_KEY,
    })
    console.log('Feature Flags SDK initialized successfully')
  } catch (error) {
    console.warn('Failed to initialize feature flags. Falling back to default states.', error)
  }
}
```

### Step 4: Synchronous Evaluation

In your application logic or rendering loops, perform evaluations synchronously using `flagClient.evaluate()`. Provide the current user's context so the engine can check targeting rules (e.g. email domains, roles, percentages).

```typescript
import { getFlagClient } from './my-flag-wrapper'

function showNewFeature() {
  const client = getFlagClient()
  if (!client) return false // fallback if SDK failed to initialize
  
  const userContext = {
    id: currentUser.id,
    email: currentUser.email,
    roles: currentUser.roles,
  }

  // Evaluates instantly from the local cache
  return client.evaluate('checkout.redesign-2026', userContext)
}
```

### Step 5: Clean Shutdown / SPA Unmounting

When the SPA unmounts, hot-reloads, or the user logs out, call `destroy()` to properly terminate websocket connections and flush telemetry queues.

```typescript
export function terminateFeatureFlags() {
  if (flagClient) {
    flagClient.destroy()
    flagClient = null
  }
}
```
