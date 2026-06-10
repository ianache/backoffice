/**
 * Public entrypoint for @backoffice/sdk-js.
 */
export { FeatureFlagClient } from './client'
export type { InitOptions } from './client'
export { evaluateRule, evaluateFlag } from './evaluator'
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
