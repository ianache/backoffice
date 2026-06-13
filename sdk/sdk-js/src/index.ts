/**
 * Public entrypoint for @backoffice/sdk-js.
 */
export { FeatureFlagClient } from './client'
export type { InitOptions } from './client'
export { evaluateRule, evaluateFlag } from './evaluator'
export { ReconnectingSocket } from './websocket'
export { TelemetryBatcher } from './telemetry'
export type { TelemetryBatcherOptions } from './telemetry'
export type {
  RuleSchema,
  BootstrapSegment,
  FlagEntry,
  BootstrapResponse,
  UserContext,
  EvalEventItem,
} from './types'

import { FeatureFlagClient, type InitOptions } from './client'

/**
 * Convenience factory: creates a FeatureFlagClient, calls initialize(), and returns it.
 * Equivalent to `const client = new FeatureFlagClient(opts); await client.initialize()`.
 */
export async function initialize(opts: InitOptions): Promise<FeatureFlagClient> {
  const client = new FeatureFlagClient(opts)
  await client.initialize()
  return client
}

export { LabelClient, createLabelPlugin } from './labels'
export type { LabelClientOptions, LabelNamespace, LabelBootstrapResponse, Locale } from './labels'

import { LabelClient, type LabelClientOptions } from './labels'

/**
 * Convenience factory: creates a LabelClient, calls initialize(), and returns it.
 * Equivalent to `const client = new LabelClient(opts); await client.initialize()`.
 */
export async function initializeLabels(opts: LabelClientOptions): Promise<LabelClient> {
  const client = new LabelClient(opts)
  await client.initialize()
  return client
}
