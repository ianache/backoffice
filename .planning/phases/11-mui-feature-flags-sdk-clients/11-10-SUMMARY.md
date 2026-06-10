---
phase: 11-mui-feature-flags-sdk-clients
plan: 10
subsystem: sdk
tags: [python, asyncio, websockets, sdk, live-sync, reconnect-backoff]

# Dependency graph
requires:
  - phase: 11-mui-feature-flags-sdk-clients
    provides: "Plan 09's FeatureFlagClient (httpx bootstrap, evaluate/evaluate_remote/invalidate/replace_cache); Plan 08's sdk-js ReconnectingSocket exponential backoff formula as architectural reference"
provides:
  - "sdk/sdk-python websocket.py: ws_reconnect_loop + compute_backoff_delay (exponential backoff with jitter, capped at 30s)"
  - "FeatureFlagClient WS live-sync: background asyncio.Task connecting to {ws_base_url}/sdk/ws/flags/{tenant_id}, first-message sdk_key auth, flag_updated cache invalidation"
  - "FeatureFlagClient async context manager (__aenter__/__aexit__) and close() for clean WS task teardown"
affects: [sdk-python-release, sdk-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Python port of sdk-js ReconnectingSocket backoff formula: delay = min(30, 1 * 2^attempt) + random.random() seconds"
    - "First-message WS auth: raw sdk_key sent as first text frame (no Authorization header), matching backend ws_router.py"
    - "asyncio.create_task background loop wired into initialize()/close()/__aenter__/__aexit__ for SDK lifecycle management"

key-files:
  created:
    - sdk/sdk-python/src/backoffice_sdk/websocket.py
    - sdk/sdk-python/tests/test_websocket.py
  modified:
    - sdk/sdk-python/src/backoffice_sdk/client.py
    - sdk/sdk-python/src/backoffice_sdk/__init__.py
    - sdk/sdk-python/tests/test_client.py

key-decisions:
  - "ws_base_url derived via simple string replace (https://->wss://, http://->ws://) rather than regex, avoiding edge cases"
  - "attempt counter resets to 0 immediately after ws.send(sdk_key) succeeds (post first-message send), matching sdk-js 'attempt resets on successful connect' rule"
  - "test_client.py gained an autouse fixture mocking ws_reconnect_loop so Plan 09's existing tests don't leak real WS-connect background tasks after initialize() was extended"

patterns-established:
  - "Pattern: SDK background WS loop is a plain async function (ws_reconnect_loop) taking url/sdk_key/on_message/stop_event, independent of FeatureFlagClient — testable in isolation via mocked websockets.connect"

requirements-completed: [SDK-12]

# Metrics
duration: 8min
completed: 2026-06-10
---

# Phase 11 Plan 10: sdk-python WebSocket Live-Sync Summary

**Reconnecting asyncio WebSocket client (`ws_reconnect_loop` + `compute_backoff_delay`) wired into `FeatureFlagClient` for first-message-auth live flag sync with exponential backoff, achieving architectural parity with sdk-js Plan 08.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-10T13:18:33Z
- **Completed:** 2026-06-10T13:26:18Z
- **Tasks:** 2
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments
- `websocket.py` provides `compute_backoff_delay(attempt)` (min(30, 2^attempt) + jitter) and `ws_reconnect_loop()` — connects via `websockets.connect`, sends `sdk_key` as the first text frame (first-message auth matching `backend/app/domains/sdk/ws_router.py`), dispatches JSON messages to a callback, reconnects with exponential backoff, resets attempt counter on successful connect, and is cleanly cancellable
- `FeatureFlagClient` derives `ws_base_url` from `api_base_url` (http->ws, https->wss, overridable), spawns a background `asyncio.Task` running `ws_reconnect_loop` at the end of `initialize()`, and invalidates cache entries on `flag_updated` messages via `_handle_ws_message`
- `close()` cancels the WS task cleanly (idempotent); `__aenter__`/`__aexit__` enable `async with FeatureFlagClient(...) as client:` usage
- `ws_reconnect_loop` and `compute_backoff_delay` exported from package root (`backoffice_sdk`)
- Full pytest suite (evaluator + client + websocket) passes: 57 tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement websocket.py — reconnecting WS loop with first-message auth and exponential backoff** - `fc6392a` (feat)
2. **Task 2: Wire ws_reconnect_loop into FeatureFlagClient — background task, cache invalidation, close()** - `53417ac` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `sdk/sdk-python/src/backoffice_sdk/websocket.py` - `compute_backoff_delay()` and `ws_reconnect_loop()` (reconnecting WS client with first-message auth and exponential backoff + jitter)
- `sdk/sdk-python/tests/test_websocket.py` - 16 tests covering backoff bounds, first-message auth, message dispatch, reconnect/backoff sequencing, cancellation, ws_base_url derivation, FeatureFlagClient WS wiring, _handle_ws_message, close(), and async context manager
- `sdk/sdk-python/src/backoffice_sdk/client.py` - added `ws_base_url` param, `_ws_task`, WS task spawn at end of `initialize()`, `_handle_ws_message`, `close()`, `__aenter__`/`__aexit__`
- `sdk/sdk-python/src/backoffice_sdk/__init__.py` - exports `ws_reconnect_loop`, `compute_backoff_delay`
- `sdk/sdk-python/tests/test_client.py` - added autouse fixture mocking `ws_reconnect_loop` to prevent dangling background tasks in Plan 09's pre-existing tests

## Decisions Made
- `ws_base_url` derivation uses `.replace('https://', 'wss://').replace('http://', 'ws://')` on `api_base_url` (or explicit override) — simple, avoids regex edge cases, matches the plan's recommended approach
- Attempt counter resets to 0 immediately after `ws.send(sdk_key)` (post first-message send), per the plan's simplification of the "reset on successful connect" rule
- `_handle_ws_message` only acts on `{"type": "flag_updated", "flag_key": ...}`; all other message types (including `ping`) are silent no-ops, mirroring sdk-js's dispatch-to-callback design

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pre-existing test_client.py tests leaked background WS-connect asyncio tasks**
- **Found during:** Task 2 (extending `initialize()` to spawn `_ws_task`)
- **Issue:** Plan 09's `test_client.py` tests call `client.initialize()` without mocking `ws_reconnect_loop`. After Task 2's change, this caused each test to spawn a real `asyncio.create_task(ws_reconnect_loop(...))` attempting an actual `websockets.connect` to a non-existent server, producing "Task was destroyed but it is pending!" warnings and unmanaged background tasks at test teardown.
- **Fix:** Added an `autouse=True` pytest fixture in `test_client.py` that patches `backoffice_sdk.client.ws_reconnect_loop` with a no-op async stand-in for the whole module, so existing tests remain network-free and leave no dangling tasks.
- **Files modified:** sdk/sdk-python/tests/test_client.py
- **Verification:** Full suite (`pytest -v`) passes 57/57 with zero "Task was destroyed" warnings
- **Committed in:** 53417ac (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary correctness fix directly caused by Task 2's `initialize()` change. No scope creep — only `test_client.py` test setup was touched, no production code changes beyond the plan's spec.

## Issues Encountered
None - both TDD tasks (RED test files written alongside implementation per plan's combined action blocks) passed on first/second iteration after one test-logic fix (stop_event timing in `test_ping_message_dispatched_without_special_handling`, and a `asyncio.sleep` recursion fix in the cancellation test).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- sdk-python's functional scope for SDK-11 (Plan 09, local cache + bootstrap) and SDK-12 (this plan, WS live-sync) is complete
- `sdk/sdk-python` now has architectural parity with `sdk/sdk-js`: bootstrap cache, sync `evaluate()`, async `evaluate_remote()` fallback, and reconnecting WS live-sync with exponential backoff
- Phase 11 is at 10/10 plans complete pending plan 11-08 (sdk-js telemetry, parallel wave, disjoint file tree) and final phase verification

---
*Phase: 11-mui-feature-flags-sdk-clients*
*Completed: 2026-06-10*

## Self-Check: PASSED

- FOUND: sdk/sdk-python/src/backoffice_sdk/websocket.py
- FOUND: sdk/sdk-python/tests/test_websocket.py
- FOUND: .planning/phases/11-mui-feature-flags-sdk-clients/11-10-SUMMARY.md
- FOUND commit: fc6392a
- FOUND commit: 53417ac
