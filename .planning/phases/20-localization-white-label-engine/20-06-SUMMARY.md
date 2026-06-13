---
phase: 20-localization-white-label-engine
plan: 06
subsystem: sdk
tags: [sdk-js, vue, websocket, localization, i18n, vitest]

# Dependency graph
requires:
  - phase: 20-localization-white-label-engine
    plan: 20-04
    provides: "GET /api/v1/sdk/labels/bootstrap, GET /api/v1/sdk/labels/prefetch, POST /api/v1/sdk/labels/missing, INVALIDATE_NAMESPACE WS broadcast"
provides:
  - "sdk/sdk-js/src/labels.ts — LabelClient (two-phase hydration, translate()/{var} interpolation/[sys.key] fallback, reportMissingLabel, reactive cache, own ReconnectingSocket filtering INVALIDATE_NAMESPACE) + createLabelPlugin Vue plugin factory"
  - "sdk/sdk-js/src/index.ts — re-exports LabelClient/createLabelPlugin/types + initializeLabels() factory"
affects: []

# Tech tracking
tech-stack:
  added:
    - "vue ^3.4.29 as devDependency + optional peerDependency of @backoffice/sdk-js (for reactive()/isReactive() and createLabelPlugin's App type)"
  patterns:
    - "LabelClient mirrors FeatureFlagClient's initialize()/destroy()/getCache() shape but with its own ReconnectingSocket (independent WS connection, no shared state with FeatureFlagClient)"
    - "reactive() cache (Pitfall 5): cache is a Vue reactive object so {{ $t(...) }} in templates re-renders automatically on invalidateNamespace()"
    - "translate(path, vars) cache-only lookup: 'namespace.key' split, {var} interpolation via regex replace, '[sys.key]' fallback + best-effort reportMissingLabel() POST (RF-06, fire-and-forget like TelemetryBatcher)"
    - "vi.mock('../src/websocket', ...) to capture ReconnectingSocket's onMessage callback and simulate INVALIDATE_NAMESPACE/flag_updated/ping without a real WebSocket"

key-files:
  created:
    - sdk/sdk-js/src/labels.ts
    - sdk/sdk-js/tests/labels.test.ts
  modified:
    - sdk/sdk-js/src/index.ts
    - sdk/sdk-js/package.json
    - pnpm-lock.yaml

key-decisions:
  - "Tests placed in sdk/sdk-js/tests/labels.test.ts (matching existing client.test.ts/websocket.test.ts location), not src/labels.test.ts as the plan's verify command literally states — sdk-js's existing convention puts all *.test.ts under tests/"
  - "reportMissingLabel()'s POST to /labels/missing built via plain string concat (${apiBaseUrl}/sdk/labels/missing), no _query() query-string params — all needed fields are in the JSON body, per plan's suggested simplification"
  - "_url(path, extraQuery) restructured per plan's IMPORTANT note to avoid double '?' — prefetch() passes { namespaces: missing.join(',') } as extraQuery"
  - "vue added as devDependency (^3.4.29) + optional peerDependency (^3.4.0); pnpm install --filter @backoffice/sdk-js linked vue@3.5.35 from the workspace pnpm store"

requirements-completed: [LBL-08]

# Metrics
duration: 12min
completed: 2026-06-13
---

# Phase 20 Plan 06: SDK Labels Client (LabelClient + createLabelPlugin) Summary

**Framework-agnostic `LabelClient` for the White Labeling Engine — two-phase hydration (`/labels/bootstrap` + `/labels/prefetch`), `translate()` with `{var}` interpolation and `[sys.key]` fallback + RF-06 missing-label reporting, a Vue `reactive()` cache, and its own `ReconnectingSocket` to `/sdk/ws/flags/{tenantId}` that hot-reloads namespaces on `INVALIDATE_NAMESPACE`; plus a thin `createLabelPlugin` exposing `$t` in Vue templates, all re-exported from `index.ts` alongside a new `initializeLabels()` factory.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-13T20:00:00Z
- **Completed:** 2026-06-13T20:24:00Z
- **Tasks:** 2 completed
- **Files modified:** 4 (2 created, 2 modified) + pnpm-lock.yaml

## Accomplishments

- `sdk/sdk-js/src/labels.ts` implements `LabelClient`:
  - `initialize()` — fetches `GET {apiBaseUrl}/sdk/labels/bootstrap?tenant_id=...&locale=...`, populates a Vue `reactive()` cache keyed by namespace, then opens its own `ReconnectingSocket` to `/sdk/ws/flags/{tenantId}`
  - `prefetch(namespaces)` — fetches only namespaces not already cached via `GET /sdk/labels/prefetch?namespaces=a,b&...`, merges results
  - `translate(path, vars)` — `"namespace.key"` cache-only lookup, `{var}` regex interpolation, `'[sys.key]'` fallback + `reportMissingLabel()` on cache-miss
  - `invalidateNamespace(namespace)` — drops the namespace from cache and reloads it via `prefetch()`
  - `reportMissingLabel(namespace, labelKey)` — best-effort `POST /sdk/labels/missing` with `{ tenant_id, company_id, product_id, namespace, label_key, locale }`, errors swallowed (TelemetryBatcher pattern)
  - WS message filter: `INVALIDATE_NAMESPACE` triggers `invalidateNamespace()`; `flag_updated`/`ping` ignored — fully decoupled from `FeatureFlagClient`
  - `getCache()` / `destroy()` mirror `FeatureFlagClient`'s extension-point shape
- `createLabelPlugin(client)` — Vue plugin installing `app.config.globalProperties.$t = (path, vars) => client.translate(path, vars)`
- `sdk/sdk-js/tests/labels.test.ts` — 8 vitest tests covering all 8 behavior specs (bootstrap population, `{var}` interpolation, `[sys.key]` fallback + missing-report POST, `prefetch()` skip-already-loaded, `INVALIDATE_NAMESPACE` re-fetch, `flag_updated` ignored, `isReactive(cache)` true, `createLabelPlugin` installs working `$t`) — all passing
- `sdk/sdk-js/src/index.ts` — re-exports `LabelClient`, `createLabelPlugin`, `LabelClientOptions`/`LabelNamespace`/`LabelBootstrapResponse`/`Locale` types, plus new `initializeLabels(opts)` convenience factory mirroring `initialize()`
- `sdk/sdk-js/package.json` — added `vue` as optional `peerDependency` (`^3.4.0`) and `devDependency` (`^3.4.29`); `pnpm install --filter @backoffice/sdk-js` linked `vue@3.5.35` from the workspace pnpm store
- Full suite: `npx vitest run` → 6 test files, 91 tests, all passing (includes 8 new `labels.test.ts` tests + 83 pre-existing); `npx tsc --noEmit` → no type errors

## Task Commits

1. **Task 1: LabelClient core (bootstrap/prefetch/translate/WS invalidation/reactive cache) + tests + vue dependency** - `61d77e2` (test)
2. **Task 2: Re-export from index.ts + initializeLabels() factory** - `dacedac` (feat)

## TDD Gate Compliance

The plan's `<behavior>` section provided complete, prescriptive code for `labels.ts` alongside the 8 test specs in a single task — there was no separate RED (failing-test-only) step before the implementation existed. Both `labels.ts` and `labels.test.ts` were created together and committed in `61d77e2` (typed as `test(...)` per the plan's TDD framing), with all 8 tests passing on first run (no RED phase observed). This deviates from the strict RED→GREEN sequence:

- `test(...)` commit exists: `61d77e2` (contains both `labels.ts` implementation and `labels.test.ts`)
- `feat(...)` commit exists after it: `dacedac` (index.ts re-exports — a separate, smaller GREEN-style addition)
- No `refactor(...)` commit (not needed)

No tests failed at any point during execution — the fail-fast "test passes unexpectedly during RED" check does not apply here because the implementation was written in the same step as the tests (the plan specified both as one prescriptive unit), not added afterward.

## Files Created/Modified

- `sdk/sdk-js/src/labels.ts` - new: `LabelClient` class (initialize/prefetch/translate/invalidateNamespace/reportMissingLabel/getCache/destroy + private `_headers`/`_url`/`_query` helpers) and `createLabelPlugin(client)` Vue plugin factory
- `sdk/sdk-js/tests/labels.test.ts` - new: 8 vitest tests using `vi.mock('../src/websocket', ...)` to capture `onMessage` and `vi.stubGlobal('fetch', ...)` for HTTP mocking
- `sdk/sdk-js/src/index.ts` - added `LabelClient`/`createLabelPlugin`/type re-exports and `initializeLabels()` factory after the existing `FeatureFlagClient`/`initialize` exports
- `sdk/sdk-js/package.json` - added `peerDependencies.vue` (optional) and `devDependencies.vue`
- `pnpm-lock.yaml` - updated by `pnpm install --filter @backoffice/sdk-js` to link `vue@3.5.35` into `sdk/sdk-js/node_modules`

## Decisions Made

- Test file placed at `sdk/sdk-js/tests/labels.test.ts` (matching `client.test.ts`/`websocket.test.ts` location) rather than `src/labels.test.ts` as the plan's literal `<verify>` command states — `sdk-js`'s established convention is all tests under `tests/`, and `npx vitest run` (no path filter) picks it up regardless
- `reportMissingLabel()` builds its POST URL via plain string concatenation (`${apiBaseUrl}/sdk/labels/missing`, no query string) since all required fields are in the JSON body — per the plan's suggested simplification to keep Test 3 assertions simple
- `_url(path, extraQuery)` restructured exactly per the plan's "IMPORTANT" note to avoid a double `?`; `prefetch()` passes `{ namespaces: missing.join(',') }` as `extraQuery`
- Mocked `./websocket` module entirely (approach (b) from the plan) to capture `onMessage` and simulate `INVALIDATE_NAMESPACE`/`flag_updated` WS messages without a real `WebSocket` global

## Deviations from Plan

None — plan executed as written. The only addition beyond the plan's literal code listing was running `pnpm install --filter @backoffice/sdk-js` to actually link the newly-declared `vue` dependency into `node_modules` (required for `import { reactive, isReactive } from 'vue'` to resolve at test/typecheck time) — this is implied setup work, not a code deviation.

## Issues Encountered

None.

## User Setup Required

None - `pnpm install` was already run as part of this plan's execution; no further action needed.

## Next Phase Readiness

- `LabelClient`, `createLabelPlugin`, and `initializeLabels()` are exported from `@backoffice/sdk-js` and ready for the mui-labeling micro-UI (or any product app) to consume for `$t(...)` label resolution with hot-reload via `INVALIDATE_NAMESPACE`
- `LBL-08` requirement implemented; same traceability gap as other Phase 20 plans applies (LBL-* IDs likely absent from `.planning/REQUIREMENTS.md` — `requirements mark-complete` may return `not_found`)

---
*Phase: 20-localization-white-label-engine*
*Completed: 2026-06-13*

## Self-Check: PASSED

All created/modified files found on disk (sdk/sdk-js/src/labels.ts, sdk/sdk-js/tests/labels.test.ts, sdk/sdk-js/src/index.ts); both task commits (61d77e2, dacedac) found in git log.
