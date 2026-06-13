# Phase 21: Login Localization via Labeling SDK - Research

**Researched:** 2026-06-13
**Domain:** Pre-auth Vue localization using the existing White Labeling SDK
**Confidence:** HIGH

## Summary

Phase 21 should integrate the already-built `LabelClient` into the Portal bootstrap and localize only the authentication panel of `LoginView.vue`. No new backend endpoint or localization library is needed. The main implementation challenge is preserving the approved fail-open behavior while still allowing missing-key reporting, reactive late hydration, and WebSocket hot reload.

The recommended shape is:

1. Seed a dedicated eager `login` namespace for `es_PE` and `en_US` through a new additive Alembic revision after the current labels head.
2. Add a Portal-owned singleton login-label service/composable that constructs `LabelClient` before mount, detects browser locale, exposes a fallback-aware translation function, and retains the initialization promise after the 1-second render deadline.
3. Register the SDK Vue plugin before mounting, preserve the current login layout, replace only authentication-panel copy, and map known auth errors to stable label keys.
4. Verify backend seed/bootstrap behavior, composable timeout/late-hydration/fallback behavior, and the visible login flow.

## Existing Contracts

### LabelClient behavior

- `LabelClient.initialize()` fetches all eager namespaces and opens its own `ReconnectingSocket` only after bootstrap succeeds.
- Its cache is Vue `reactive()`, so reads through `translate()` re-render after namespace updates.
- Missing translations return `[sys.<key>]` and trigger best-effort `POST /sdk/labels/missing`.
- `INVALIDATE_NAMESPACE` deletes and re-prefetches the namespace.
- Initialization errors reject; WebSocket failures after successful initialization reconnect independently.

### Portal bootstrap behavior

- `portal/src/main.ts` creates the app and Pinia, initializes auth, loads remote routes, then mounts.
- Cross-cutting feature flags use an idempotent singleton composable and fail-open defaults.
- `portal/index.html` currently contains an empty `#app`, so a neutral pre-mount loading state requires a small static loader or equivalent bootstrap-owned markup.

### Backend label behavior

- `/api/v1/sdk/labels/bootstrap` returns every eager namespace for `tenant_id + locale` plus optional company/product.
- Product-level resolution is only applied when both `company_id` and `product_id` are present in the current resolver. Because Phase 21 explicitly sends no company before authentication, login labels must have tenant-level values; product context may still be sent for forward compatibility but will not override tenant labels under the current resolver.
- SDK routes require `Authorization: Bearer <VITE_BO_SDK_KEY>`.
- Current `g002` seeds only `common`; the current migration head includes the uncommitted repair revision `g003`, so the Phase 21 seed must be created after the actual head discovered at execution time and must not rewrite published migrations.

## Recommended Architecture

### Dedicated eager namespace

Use a dedicated eager namespace named `login`, rather than expanding `common`.

Reasons:
- It keeps authentication copy grouped and administrable.
- Eager bootstrap already supports multiple eager namespaces.
- Hot reload can invalidate only `login`.
- Missing-key diagnostics remain easy to understand.

Seed tenant-level values for the dogfooding tenant lookup convention used by `g002`: prefer tenant id `5`, then the first tenant, and no-op when no tenant exists. Seed both locales with stable keys for authentication-panel headings, descriptions, buttons, field labels, help copy, loading text states, and known/generic authentication errors. Keep `BackOffice CC`, version, email placeholder, and `Keycloak` proper name out of the seed.

### Portal login-label service

Create a Portal-owned singleton, following `useBoFlags.ts`, responsible for:

- `detectLoginLocale(language = navigator.language)`: `es-*` to `es_PE`, otherwise `en_US`.
- Constructing one `LabelClient` using:
  - `tenantId: VITE_BO_TENANT_ID ?? 'platform'`
  - `productId: VITE_BO_PRODUCT_ID ?? 'backoffice'`
  - no `companyId`
  - detected locale
  - `apiBaseUrl: VITE_BFF_URL ?? 'http://localhost:3000'`
  - `sdkKey: VITE_BO_SDK_KEY ?? 'dev-sdk-secret-change-in-prod'`
- A fallback-aware translation function. It must call `client.translate('login.<key>', vars)` first so missing keys are reported; when the return value is the SDK sentinel `[sys.<key>]`, return the bundled locale-specific fallback instead.
- A startup method that starts initialization once and exposes a promise suitable for a 1-second race without cancelling the underlying initialization.
- Fail-open state: rejection is swallowed/logged and fallback translations remain available.

The local fallback catalog is required because the SDK's built-in fallback is diagnostic (`[sys.key]`), not user-facing. Keep the fallback catalog in Portal code because it is the login availability contract.

### Startup sequencing

Register `createLabelPlugin(client)` before `app.mount()`. Start label initialization before auth/router work and await only a 1-second deadline before mounting. Do not cancel or replace the original initialization promise after timeout; if it later succeeds, the reactive SDK cache replaces fallbacks automatically.

Use a minimal neutral pre-mount loading indicator in `portal/index.html` or another bootstrap-owned surface. It must not depend on labels and should disappear when Vue mounts.

### LoginView integration

Preserve layout and right-side content. Replace only authentication-panel text with the fallback-aware translator. Keep technical values fixed. Avoid displaying raw exception messages: map known local-login failures to label keys and use the generic localized error for unknown failures.

## Key Pitfalls

1. **Using raw `$t` directly exposes `[sys.key]`.** The Portal wrapper must translate sentinel results to bundled fallbacks after allowing the SDK to report the miss.
2. **Cancelling or discarding initialization at timeout breaks late hydration.** Race only the render deadline; retain the real initialization.
3. **Waiting for auth before labels defeats pre-auth localization.** Initialize login labels independently of `authStore.isAuthenticated`.
4. **Opening multiple LabelClients creates duplicate WebSockets and missing reports.** Use one module-scoped singleton with idempotent initialization.
5. **Product override assumptions are unsafe without company context.** Seed login copy at tenant level; current resolver applies product overrides only with company plus product.
6. **Raw backend authentication errors can bypass localization and leak detail.** Map known errors and use a generic localized unknown-error key.
7. **Changing right-side content or layout expands scope.** Visual design and preview content remain unchanged.

## Requirements Derived for Planning

- **LOGIN-LBL-01:** A dedicated eager `login` namespace contains tenant-level `es_PE` and `en_US` authentication-panel labels.
- **LOGIN-LBL-02:** Portal resolves browser locale on every load (`es-*` to `es_PE`, otherwise `en_US`) without selector or persistence.
- **LOGIN-LBL-03:** Portal creates one pre-auth `LabelClient` using environment tenant/product context, no company, and the existing SDK key.
- **LOGIN-LBL-04:** Portal waits at most 1 second before rendering login, shows a neutral pre-mount loader, and never blocks access on label infrastructure failure.
- **LOGIN-LBL-05:** Authentication-panel text and known/generic auth errors use SDK translation with bundled local fallback; excluded technical/brand text and right-side preview remain unchanged.
- **LOGIN-LBL-06:** Late bootstrap and `INVALIDATE_NAMESPACE` update visible login translations without reload.
- **LOGIN-LBL-07:** Missing login keys are reported through the existing SDK endpoint while user-facing text remains usable.
- **LOGIN-LBL-08:** Automated tests cover seed/bootstrap, locale/context resolution, timeout/failure fallback, late hydration, missing-key fallback/reporting, hot reload, and visible login behavior.

## Validation Architecture

### Test layers

| Layer | Existing infrastructure | Phase 21 coverage |
|---|---|---|
| Backend | `pytest`, FastAPI `TestClient`, async SQLite fixtures | login eager seed/bootstrap returns both locales and tenant-level values |
| SDK/Portal unit | Vitest with mocked `@backoffice/sdk-js`, fake timers, Vue reactivity | locale mapping, client options, idempotence, 1-second deadline, failure fallback, sentinel fallback, late hydration |
| Portal build | `vue-tsc` + Vite build | plugin/types/template integration |
| Browser | Playwright login visual specs | localized authentication panel remains usable and right-side layout remains stable |

### Fast feedback commands

- Portal unit: `pnpm --filter @backoffice/portal test -- --run`
- Portal build: `pnpm --filter @backoffice/portal build`
- SDK labels regression: `pnpm --filter @backoffice/sdk-js test -- tests/labels.test.ts`
- Backend focused: `backend/venv/Scripts/python.exe -m pytest backend/tests/test_labels_sdk_router.py -q`
- Browser focused: `pnpm --filter @backoffice/portal exec playwright test tests/visual/login.spec.ts`

### Sampling guidance

- Run focused unit tests after every Portal task.
- Run backend focused tests after seed/bootstrap work.
- Run Portal build after integration/template changes.
- Run SDK regression plus Playwright login spec after the final integration wave.

## Planning Recommendation

Use three plans:

1. Backend seed and bootstrap regression coverage for the eager `login` namespace.
2. Portal login-label singleton, fallback catalog, locale/context resolution, one-second startup deadline, and unit tests.
3. `LoginView.vue` translation/error mapping integration plus build, SDK regression, and Playwright coverage.

Plans 1 and 2 can run in parallel. Plan 3 depends on Plan 2 and should consume the seeded key contract from Plan 1.

## RESEARCH COMPLETE

