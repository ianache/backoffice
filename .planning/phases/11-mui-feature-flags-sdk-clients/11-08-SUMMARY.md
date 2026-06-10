---
phase: 11-mui-feature-flags-sdk-clients
plan: 08
subsystem: sdk
tags: [websocket, telemetry, sdk-js, vitest, exponential-backoff, sendBeacon]

# Dependency graph
requires:
  - phase: 11-mui-feature-flags-sdk-clients
    provides: "Plan 06 sdk-js bootstrap/types/evaluator + Plan 07 FeatureFlagClient (initialize/evaluate/cache extension points)"
provides:
  - "ReconnectingSocket — inline exponential-backoff WebSocket reconnect with first-message SDK-key auth"
  - "TelemetryBatcher — dual-trigger (100 events OR 60s) flush with startup jitter and sendBeacon on beforeunload"
  - "FeatureFlagClient.initialize() now establishes WS sync (cache invalidation on flag_updated) and telemetry batching automatically; destroy() tears both down"
affects: [sdk-js consumers, future SPA integrations using @backoffice/sdk-js]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Inline ~70-line exponential-backoff WebSocket reconnect class (no external deps; reconnecting-websocket npm package is abandoned)"
    - "Telemetry batching with randomized startup jitter (Math.random()*30000) to avoid thundering herd across SDK instances post-deploy"
    - "navigator.sendBeacon with ?sdk_key= query param fallback for beforeunload flush (no Authorization header possible)"

key-files:
  created:
    - sdk/sdk-js/src/websocket.ts
    - sdk/sdk-js/src/telemetry.ts
    - sdk/sdk-js/tests/websocket.test.ts
    - sdk/sdk-js/tests/telemetry.test.ts
  modified:
    - sdk/sdk-js/src/client.ts
    - sdk/sdk-js/src/index.ts
    - sdk/sdk-js/tests/client.test.ts
    - sdk/sdk-js/tests/cache.test.ts

key-decisions:
  - "ReconnectingSocket attempt counter resets to 0 on successful onopen, so a stable connection that later drops restarts backoff from 1s, not from the prior peak delay"
  - "TelemetryBatcher.flush() swallows fetch errors (try/catch) — failed batches are dropped rather than retried/requeued, documented as an acceptable telemetry tradeoff"
  - "client.test.ts and cache.test.ts now stub WebSocket/navigator/window globals since initialize() constructs ReconnectingSocket and TelemetryBatcher as side effects"

patterns-established:
  - "WS URL derived from apiBaseUrl via http->ws / https->wss prefix replacement: `${apiBaseUrl.replace(/^http/, 'ws')}/sdk/ws/flags/{tenantId}`"
  - "destroy() lifecycle method on FeatureFlagClient for clean SPA-unmount teardown of socket + telemetry timer"

requirements-completed: [SDK-08, SDK-09, SDK-10]

# Metrics
duration: ~10min
completed: 2026-06-10
---

# Phase 11 Plan 08: WebSocket Reconnect + Telemetry Batching Summary

**Inline exponential-backoff `ReconnectingSocket` (first-message SDK-key auth, flag_updated cache invalidation) and `TelemetryBatcher` (100-event/60s dual-trigger flush with jittered startup + sendBeacon on beforeunload) wired into `FeatureFlagClient.initialize()`, completing sdk-js (SDK-05 through SDK-10).**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-10T13:16:00Z (approx)
- **Completed:** 2026-06-10T13:26:38Z
- **Tasks:** 3
- **Files modified:** 8 (4 created, 4 modified)

## Accomplishments
- `ReconnectingSocket` (sdk/sdk-js/src/websocket.ts): connects immediately on construction, sends raw SDK key on `onopen` (first-message auth, repeated on every reconnect), forwards parsed JSON messages to `onMessage` (ignoring malformed JSON), and reconnects on `onclose` with `min(30000, 1000 * 2^attempt) + jitter` backoff; attempt counter resets on successful open; `close()` prevents further reconnects.
- `TelemetryBatcher` (sdk/sdk-js/src/telemetry.ts): queues `EvalEventItem`s, flushes immediately at 100 events or every 60s after a `Math.random()*30000` startup jitter; `flush()` POSTs to `/sdk/eval-events` with `Authorization: Bearer <sdkKey>`; `flushBeacon()` uses `navigator.sendBeacon` with `?sdk_key=` query param on `beforeunload`; `destroy()` clears the interval.
- `FeatureFlagClient.initialize()` now opens the WS connection to `{wsBaseUrl}/sdk/ws/flags/{tenantId}` and starts the telemetry batcher after bootstrap completes; `flag_updated` messages call `invalidate(flag_key)`; `evaluate()` results are tracked automatically via `setEvaluationListener`. New `destroy()` method tears down both.
- All 61 sdk-js unit tests pass (12 new websocket, 10 new telemetry, plus existing 39 updated for global stubs); `tsc --noEmit` passes.

## Task Commits

Each task was committed atomically (TDD red/green for Tasks 1-2):

1. **Task 1: Implement ReconnectingSocket** - `d3443de` (test: failing tests), `8f6a9c9` (feat: implementation)
2. **Task 2: Implement TelemetryBatcher** - `ce8e72d` (test: failing tests), `2356e4e` (feat: implementation)
3. **Task 3: Wire into FeatureFlagClient.initialize()** - `f5eccbb` (feat: wiring + test global stubs)

**Plan metadata:** (this commit) `docs(11-08): complete websocket + telemetry plan`

## Files Created/Modified
- `sdk/sdk-js/src/websocket.ts` - `ReconnectingSocket` class: first-message auth, JSON parsing, exponential backoff + jitter reconnect
- `sdk/sdk-js/src/telemetry.ts` - `TelemetryBatcher` class: dual-trigger flush, startup jitter, sendBeacon on beforeunload
- `sdk/sdk-js/src/client.ts` - `FeatureFlagClient.initialize()` wires socket + telemetry; new `destroy()` method
- `sdk/sdk-js/src/index.ts` - exports `ReconnectingSocket`, `TelemetryBatcher`, `TelemetryBatcherOptions`
- `sdk/sdk-js/tests/websocket.test.ts` - 12 tests covering MockWebSocket-driven behavior including backoff sequence
- `sdk/sdk-js/tests/telemetry.test.ts` - 10 tests covering dual-trigger flush, jitter, sendBeacon, beforeunload, destroy
- `sdk/sdk-js/tests/client.test.ts` - added global stubs (WebSocket/navigator/window) so initialize() side effects don't leak
- `sdk/sdk-js/tests/cache.test.ts` - same global stubs added for the perf-benchmark test

## Decisions Made
- ReconnectingSocket attempt counter resets on successful `onopen`, matching the plan's interface skeleton exactly — verified via dedicated test (close after success reconnects at ~1s again, not continuing the backoff ramp).
- TelemetryBatcher.flush() wraps the fetch call in try/catch; a failed flush drops the batch rather than retrying — documented inline as an acceptable tradeoff for telemetry data.
- Existing client.test.ts/cache.test.ts updated to stub `WebSocket`, `navigator.sendBeacon`, and `window.addEventListener` globally — required because `initialize()` now has side effects (opens WS, starts telemetry timer) that would otherwise hit Node's real `undici` WebSocket implementation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stubbed WebSocket/navigator/window globals in existing client.test.ts and cache.test.ts**
- **Found during:** Task 3 (wiring ReconnectingSocket + TelemetryBatcher into initialize())
- **Issue:** After wiring, `initialize()` constructs `new ReconnectingSocket(...)` which calls `new WebSocket(wsUrl)`. In Node's vitest `environment: 'node'`, `WebSocket` is provided by `undici` and attempts a real connection to `wss://bff.example.com/...`, which fails and triggers `ws.onerror -> ws.close()` causing an uncaught `RangeError: Maximum call stack size exceeded` inside undici's close/error event dispatch. This broke `client.test.ts` and `cache.test.ts` (both call `initialize()`).
- **Fix:** Added a `MockWebSocket` class (constructor stores URL, `send`/`close` spies, no real connection) and stubbed `vi.stubGlobal('WebSocket', MockWebSocket)`, `vi.stubGlobal('navigator', { sendBeacon: vi.fn() })`, `vi.stubGlobal('window', { addEventListener: vi.fn() })` in both test files' setup.
- **Files modified:** sdk/sdk-js/tests/client.test.ts, sdk/sdk-js/tests/cache.test.ts
- **Verification:** `pnpm run test` — all 61 tests pass with zero unhandled errors; `pnpm run typecheck` passes.
- **Committed in:** f5eccbb (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary fix for Task 3's own verification step (`pnpm run test` must pass for the full suite) — no scope creep beyond the two test files directly affected by the new initialize() side effects.

## Issues Encountered
None beyond the auto-fixed blocking issue above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `sdk/sdk-js` is now functionally complete (SDK-05 through SDK-10): bootstrap caching, sync evaluation, remote evaluation fallback, WS-driven cache invalidation, and telemetry batching all implemented and unit-tested.
- `initialize()` is the single entrypoint matching ROADMAP success criterion 4.
- No blockers for downstream consumers (mui-feature-flags or future SPA integrations) wanting to adopt `@backoffice/sdk-js`.

---
*Phase: 11-mui-feature-flags-sdk-clients*
*Completed: 2026-06-10*

## Self-Check: PASSED

All created files verified present:
- sdk/sdk-js/src/websocket.ts - FOUND
- sdk/sdk-js/src/telemetry.ts - FOUND
- sdk/sdk-js/tests/websocket.test.ts - FOUND
- sdk/sdk-js/tests/telemetry.test.ts - FOUND
- .planning/phases/11-mui-feature-flags-sdk-clients/11-08-SUMMARY.md - FOUND

All commits verified present: d3443de, 8f6a9c9, ce8e72d, 2356e4e, f5eccbb
