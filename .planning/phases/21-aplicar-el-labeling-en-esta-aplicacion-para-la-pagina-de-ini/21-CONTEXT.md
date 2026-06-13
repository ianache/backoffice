# Phase 21: Login Localization via Labeling SDK - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply the Phase 20 Localization White Label Engine to the Portal `/login` authentication panel. Initialize labels before the initial login render, use the existing SDK `$t` integration and hot reload, and preserve a fully usable login when labels, SDK, BFF, or WebSocket are unavailable.

The right-side dashboard preview, branding customization, hostname-based tenant discovery, and new authentication capabilities are outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Locale Selection
- **D-01:** Detect locale from the browser on every `/login` load. Browser locales matching `es-*` resolve to `es_PE`; every other locale resolves to `en_US`.
- **D-02:** Do not show a locale selector on the login page.
- **D-03:** Do not persist the detected locale in local or session storage.
- **D-04:** Use `en_US` as the fallback for unsupported or unavailable browser locales.

### Pre-Authentication Label Context
- **D-05:** Resolve the pre-auth tenant from `VITE_BO_TENANT_ID`, with `platform` as the fallback when it is absent.
- **D-06:** Send tenant plus product context to `LabelClient`; product comes from `VITE_BO_PRODUCT_ID` with `backoffice` as the default.
- **D-07:** Do not send company context before authentication.
- **D-08:** Reuse the existing `VITE_BO_SDK_KEY` approach for pre-auth SDK access in this phase.

### Login Content Coverage
- **D-09:** Localize only the left authentication panel in this phase. Keep the right-side metrics, announcements, and hero content unchanged.
- **D-10:** Keep the `BackOffice CC` product name fixed and outside the labeling engine.
- **D-11:** Keep technical values outside the labeling engine: application version, email placeholder, and proper names such as Keycloak.
- **D-12:** Map known authentication failures to label keys. Unknown failures use a generic localized error label rather than exposing backend text.

### Startup and Failure Behavior
- **D-13:** Before the initial login render, wait for label initialization for at most 1 second.
- **D-14:** During that wait, show a minimal neutral loading screen with no label-dependent text.
- **D-15:** If the 1-second limit expires or initialization fails, render the complete usable login with bundled local fallback strings.
- **D-16:** If labels arrive after fallback render, update the visible login in place.
- **D-17:** Continue applying `INVALIDATE_NAMESPACE` hot reload after initialization. SDK, BFF, label bootstrap, missing-key reporting, and WebSocket failures must never block login access.

### the agent's Discretion
- Exact namespace name and label-key naming convention for the login panel.
- Exact bundled fallback-string module shape and known-auth-error mapping structure.
- Loading indicator implementation, provided it remains minimal, neutral, and accessible.
- Test organization and timeout implementation details consistent with existing Portal and SDK patterns.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Contract and Label Engine
- `.planning/ROADMAP.md` - Phase 21 goal and dependency on Phase 20.
- `.planning/phases/20-localization-white-label-engine/20-CONTEXT.md` - locked SDK, locale, inheritance, missing-key, and hot-reload decisions.
- `sdk/sdk-js/src/labels.ts` - existing `LabelClient`, `$t` plugin, bootstrap, fallback, missing-report, and WebSocket behavior.
- `backend/app/domains/sdk/router.py` - existing label bootstrap, prefetch, and missing-label endpoints.
- `backend/alembic/versions/g002_seed_common_namespace_labels.py` - current eager namespace seed convention and dogfooding tenant selection.

### Portal Login Integration
- `portal/src/main.ts` - Portal initialization order before router registration and mount.
- `portal/src/views/LoginView.vue` - current Google Stitch login layout and hardcoded authentication copy.
- `portal/src/stores/auth.ts` - Keycloak and local-login behavior plus existing error surface.
- `portal/src/composables/useBoFlags.ts` - existing fail-open SDK initialization pattern and Portal environment variables.
- `portal/tests/visual/login.spec.ts` - current login visual and error-state coverage.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LabelClient` and `createLabelPlugin` from `@backoffice/sdk-js` already provide reactive `$t`, eager bootstrap, missing-key reports, and `INVALIDATE_NAMESPACE` handling.
- `portal/src/composables/useBoFlags.ts` demonstrates a module-scoped, idempotent, fail-open SDK integration using `VITE_BO_TENANT_ID`, `VITE_BO_SDK_KEY`, and BFF base URL.
- `portal/src/views/LoginView.vue` already contains the approved Google Stitch login design and authentication state transitions.

### Established Patterns
- Portal initializes cross-cutting services in `main.ts` before router registration and `app.mount()`.
- Cross-cutting SDK failures are caught and treated fail-open so they do not block the Portal.
- Phase 20 supports exactly `es_PE` and `en_US`, uses SDK-key-authenticated BFF routes, and broadcasts namespace invalidation over the existing WebSocket.

### Integration Points
- Add label initialization and plugin registration to the Portal bootstrap path before mounting.
- Replace authentication-panel copy and known auth errors in `LoginView.vue` with `$t` calls backed by bundled fallbacks.
- Add login label seed data through the existing Alembic label-seeding conventions.
- Extend Portal unit and Playwright coverage for locale mapping, timeout fallback, late hydration, and hot reload.

</code_context>

<specifics>
## Specific Ideas

- Preserve the current login layout exactly; this phase changes text sourcing and startup behavior, not the visual design.
- The initial loading state must not require labels to explain itself.
- A late successful bootstrap should visibly replace bundled fallback strings without requiring reload or authentication.

</specifics>

<deferred>
## Deferred Ideas

- Resolve the pre-auth tenant from hostname, subdomain, or custom domain in a future phase.

</deferred>

---

*Phase: 21-login-localization-via-labeling-sdk*
*Context gathered: 2026-06-13*
