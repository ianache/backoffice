---
phase: 21
slug: aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini
status: approved
shadcn_initialized: false
preset: google-stitch-material-3-existing
created: 2026-06-13
---

# Phase 21 - UI Design Contract

> Visual and interaction contract for applying the Labeling SDK to the existing Portal login.

## Design Intent

This phase is a text-source and startup-state change, not a redesign.

- Preserve the current Google Stitch split-screen login composition, DOM hierarchy, dimensions, controls, icons, image, animations, and right-side preview.
- Localize only the left authentication panel copy identified below.
- Add one neutral pre-mount loading state while labels receive their maximum 1-second startup opportunity.
- Never show SDK diagnostic sentinels such as `[sys.key]`, raw backend errors, or an unavailable/blocked login.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing project design system; no shadcn |
| Preset | Google Stitch / Material 3 existing login |
| Component library | Material Web custom elements plus existing `StitchTextField.vue` |
| Icon library | Material Symbols Outlined |
| Font | Inter via `--font-family-sans` |
| Source of truth | `portal/src/views/LoginView.vue`, `portal/src/assets/theme.css`, `portal/tailwind.config.js` |

No new component library, icon family, font, color token, spacing token, or visual pattern may be introduced.

## Layout Contract

### Login screen

- Keep `main` as full-height/full-width flex layout.
- Keep left panel at `w-[30%] min-w-[400px]`, with `p-xl`, right border, and its current three vertical zones: branding, authentication, footer.
- Keep right preview at `w-[70%]`, `p-xl`, scroll behavior, cards, announcements, and hero image unchanged.
- Keep `AuthLayout.vue` as `h-screen w-full overflow-hidden`.
- Do not add a locale selector, language indicator, label-status badge, retry button, warning banner, toast, or skeleton inside the login.
- Do not change responsive behavior in this phase. Existing Playwright snapshots remain the visual baseline.

### Pre-mount loading state

- Loading state occupies the full viewport and uses existing `background` / `on-background` theme tokens.
- Display one centered indeterminate Material progress indicator or equivalent existing-system spinner.
- No visible loading text, logo, brand copy, progress percentage, or error message.
- The indicator must have an accessible name such as `aria-label="Loading login"` even though no visible text is rendered.
- The loader disappears atomically when Vue mounts after label initialization settles or the 1-second deadline expires. No fade, layout shift, or intermediate partially-rendered login.

## Spacing Scale

Use the existing project tokens only:

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon and compact inline gaps |
| sm | 8px | Authentication control grouping |
| md | 16px | Button padding and default gaps |
| lg | 24px | Authentication section gaps |
| xl | 32px | Panel padding and major layout gaps |

Exceptions: Existing literal dimensions and sizes already present in `LoginView.vue` remain unchanged. Do not introduce new spacing exceptions.

## Typography

| Role | Existing contract | Usage |
|------|-------------------|-------|
| Product name | 28px, semibold, tight tracking | Fixed `BackOffice CC`; never localized |
| Auth heading | 22px, semibold, 28px line height | Localized welcome heading |
| Body/help | Existing `text-sm` / `text-[11px]` classes | Localized descriptions and support copy |
| Buttons | Existing `text-base font-medium` | Localized button/loading labels |
| Technical footer | Existing `text-xs font-semibold` | Fixed version; never localized |

Localized strings may wrap naturally within the existing `max-w-sm` authentication column. Do not reduce font size, truncate, clamp, or widen the panel to accommodate translations.

## Color

Use existing semantic tokens only.

| Role | Token | Usage |
|------|-------|-------|
| Dominant surfaces | `background`, `surface-container-lowest` | Existing page and left panel |
| Primary action | `primary`, `on-primary` | Existing Keycloak and submit actions |
| Secondary action | `outline`, `on-surface` | Existing local-admin toggle |
| Supporting text | `on-surface-variant` | Existing descriptions/help |
| Error | `error-container`, `on-error-container` | Existing inline authentication error |
| Loader | `primary` on `background` | Neutral pre-mount indicator |

Both light and dark themes must continue to derive from `theme.css`; no literal phase-specific colors.

## Localized Copy Contract

Use namespace `login`. English bundled fallback is the baseline copy; Spanish fallback communicates the same intent.

| Key | en_US fallback | es_PE fallback | Surface |
|-----|----------------|----------------|---------|
| `login.brand_tagline` | Control Center & Multi-tenant Administration | Centro de Control y Administracion Multi-tenant | Branding description only |
| `login.welcome_title` | Welcome back | Bienvenido nuevamente | Auth heading |
| `login.welcome_body` | Access your administrative dashboard using enterprise credentials. | Accede a tu panel administrativo usando credenciales empresariales. | Auth description |
| `login.sso_action` | Sign in with Keycloak | Iniciar sesion con Keycloak | Primary SSO button |
| `login.sso_connecting` | Connecting... | Conectando... | SSO loading state |
| `login.divider_or` | or | o | Divider |
| `login.local_action` | Local Admin Login | Acceso de administrador local | Local form toggle |
| `login.email_label` | Email | Correo electronico | Field label |
| `login.password_label` | Password | Contrasena | Field label |
| `login.submit_action` | Sign In | Iniciar sesion | Local submit button |
| `login.submit_loading` | Signing in... | Iniciando sesion... | Local submit loading state |
| `login.help_prompt` | Trouble signing in? | Problemas para iniciar sesion? | Support prompt |
| `login.help_action` | Contact Support | Contactar soporte | Support link |
| `login.error_invalid_credentials` | Invalid email or password. | Correo o contrasena invalidos. | Known credential failure |
| `login.error_authentication_failed` | Authentication could not be completed. Please try again. | No se pudo completar la autenticacion. Intenta nuevamente. | Known post-exchange failure |
| `login.error_generic` | Sign-in failed. Please try again or contact support. | El inicio de sesion fallo. Intenta nuevamente o contacta a soporte. | Unknown failure |

### Fixed copy outside Labeling

The following must remain literal and unchanged:

- `BackOffice CC`
- `Keycloak` proper name within localized sentences
- `admin@backoffice.dev` email placeholder
- `v2.4.12-stable`
- Right-side metrics, announcement copy, tags, hero heading/body, image alt text, and all preview data
- Material icon names

## Interaction States

| State | Visual and interaction contract |
|-------|---------------------------------|
| Pre-mount labels pending | Full-viewport neutral spinner; no login controls visible; maximum duration 1 second |
| Labels loaded before deadline | Mount complete login once using resolved labels |
| Labels timeout/failure | Mount complete login using bundled locale fallbacks; no warning or disabled controls |
| Labels arrive after mount | Replace fallback copy in place through reactive cache; preserve focus, typed credentials, open local form, and loading states |
| Namespace invalidated | Refresh visible copy in place; preserve all user interaction state |
| Missing label | Render bundled fallback, report miss best-effort, never render `[sys.key]` |
| Keycloak action pending | Preserve existing disabled primary button and circular progress; use localized connecting label |
| Local login pending | Preserve existing disabled submit button and circular progress; use localized signing-in label |
| Known auth error | Existing inline error container with mapped localized error |
| Unknown auth error | Existing inline error container with generic localized error; never raw exception/backend copy |

## Accessibility Contract

- Preserve semantic button elements, disabled states, field labels, and existing keyboard behavior.
- Localized text must remain available to assistive technology as ordinary rendered text.
- Pre-mount spinner must expose an accessible name but no visible label-dependent copy.
- Late hydration and hot reload must not move focus, clear input values, collapse the local form, or announce raw diagnostic keys.
- Existing color-token contrast behavior in light/dark mode remains the source of truth.

## Visual Regression Contract

- Existing light, dark, and error-state snapshots in `portal/tests/visual/login.spec.ts` remain the layout baseline.
- Test assertions must become locale-aware without weakening visibility or role-based assertions.
- Add coverage proving fallback-rendered and remotely-hydrated copy occupy the same existing surfaces.
- Any intentional snapshot update must show text-only differences in the left authentication panel or the neutral pre-mount loader; right-side preview and overall geometry must remain unchanged.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Existing project components | `StitchTextField`, Material Web progress/icon elements | Reuse only |
| shadcn official | None | Not applicable |
| Third-party registries | None | No additions permitted |

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS - exact fallback copy, exclusions, and error language are specified.
- [x] Dimension 2 Visuals: PASS - existing split layout is locked; only neutral loader and text sourcing change.
- [x] Dimension 3 Color: PASS - all states use existing semantic theme tokens.
- [x] Dimension 4 Typography: PASS - current classes and wrapping behavior are locked.
- [x] Dimension 5 Spacing: PASS - current spacing scale and geometry are locked.
- [x] Dimension 6 Registry Safety: PASS - no new registry blocks or libraries.

**Approval:** approved 2026-06-13
