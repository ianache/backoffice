---
phase: 06-stitch-ui-implementation
verified: 2026-06-06T23:00:00Z
status: gaps_found
score: 2/3 must-haves verified
gaps:
  - truth: "Todas las páginas internas (excepto login) se ajustan al diseño de 'Tenant Management' de Google Stitch (node-id: acc51e...)"
    status: partial
    reason: "La implementación de los componentes Stitch en páginas internas está completa, pero 4 de 5 snapshots de regresión visual de internal.spec.ts no existen ni están committed. El test suite no tiene baselines para tenants-view-light, tenant-drawer-create, tenant-drawer-whitelabel, y tenant-drawer-dark. Además, UI-04 permanece sin marcar como completado en REQUIREMENTS.md."
    artifacts:
      - path: "portal/tests/visual/internal.spec.ts-snapshots/"
        issue: "Solo existe tenants-view-dark-chromium-win32.png (untracked). Faltan 4 de 5 baselines: tenants-view-light, tenant-drawer-create, tenant-drawer-whitelabel, tenant-drawer-dark."
      - path: ".planning/REQUIREMENTS.md"
        issue: "UI-04 marcado como [ ] (incompleto) cuando la implementacion esta presente en codigo."
    missing:
      - "Ejecutar los 5 tests de internal.spec.ts para generar todos los snapshots baseline"
      - "Commitear portal/tests/visual/internal.spec.ts-snapshots/ con los 5 PNG generados"
      - "Actualizar REQUIREMENTS.md: cambiar '- [ ] **UI-04**' a '- [x] **UI-04**'"
      - "Agregar UI-03 y UI-04 a la tabla de Traceability en REQUIREMENTS.md con Phase 6"
---

# Phase 6: Stitch UI Implementation — Verification Report

**Phase Goal:** Implementar la página de login y ajustar todas las páginas internas siguiendo los diseños de Google Stitch para asegurar coherencia visual completa
**Verified:** 2026-06-06T23:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | La página de login refleja fielmente el diseño de Google Stitch | VERIFIED | LoginView.vue usa StitchTextField + StitchButton + md-icon + error container con tokens Stitch. 3 snapshots baseline committed (login-light, login-dark, login-error). Auth store tiene `loginWithCredentials` via ROPC. |
| 2 | Todas las páginas internas se ajustan al diseño de 'Tenant Management' de Google Stitch | PARTIAL | Implementación completa en código (Nav Rail 72px, high-density table, status chips, M3 state-layer, drawer con ARIA), pero 4 de 5 visual baseline snapshots no existen ni están en git. UI-04 sin marcar en REQUIREMENTS.md. |
| 3 | El flujo de autenticación y la funcionalidad de negocio se mantienen intactos | VERIFIED | LoginView -> authStore.loginWithCredentials() -> router.push('/dashboard'). Router guards siguen funcionando. TenantsView mantiene CRUD completo (create/edit/delete/suspend). |

**Score:** 2/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `portal/tailwind.config.js` | Tailwind configurado con tokens de theme.css | VERIFIED | Mapea 40+ variables CSS (surface, primary, secondary, error, etc.) a clases Tailwind. Incluye borderRadius y spacing desde tokens. |
| `portal/src/components/ui/StitchButton.vue` | Wrapper atómico para md-filled-button | VERIFIED | Soporta variantes filled/outlined/text, type, disabled. Slots para icon y contenido. Usa tokens --rounded-lg y --font-family-sans. |
| `portal/src/components/ui/StitchTextField.vue` | Wrapper atómico para md-outlined-text-field | VERIFIED | Soporta v-model (update:modelValue), label, type, placeholder, error, errorText, supportingText, leading/trailing icon slots. |
| `portal/src/components/layout/MainLayout.vue` | Layout con Nav Rail y App Bar | VERIFIED | Nav Rail 72px con md-navigation-tab para Tenants/Users/Audit/Settings. App Bar con theme toggle (uiStore.toggleTheme), user profile, logout. Reactivo a route.meta.title. |
| `portal/src/components/layout/AuthLayout.vue` | Layout simplificado para auth | VERIFIED | Centra contenido en pantalla completa, muestra logo/branding BackOffice, usa surface-container con border-outline-variant. |
| `portal/src/views/LoginView.vue` | Página de login con diseño Stitch | VERIFIED | Usa StitchTextField (email + password con md-icon), StitchButton submit, md-checkbox "remember me", error container con bg-error-container, md-circular-progress durante loading. Llama authStore.loginWithCredentials. |
| `portal/src/views/TenantsView.vue` | Vista de Tenants refactorizada con Stitch | VERIFIED | page-title (1.375rem/400) + page-subtitle (0.8125rem), usa TenantTable + TenantDrawer + StitchButton. |
| `portal/src/components/tenants/TenantTable.vue` | Tabla high-density con componentes Stitch | VERIFIED | colgroup con anchos fijos, filas 36px (h-9/py-0), md-checkbox, status-chip con variantes active/suspended, product-chip, M3 state-layer hover (color-mix 8% primary), md-menu con positioning="popover". |
| `portal/src/components/tenants/TenantDrawer.vue` | Drawer con patrones M3 | VERIFIED | role="dialog" aria-modal="true" :aria-label, drawer-title + drawer-subtitle, md-tabs, scrollbar thin, box-shadow M3 elevation level 3, border-left outline-variant, footer 52px. |
| `portal/src/components/tenants/TenantForm.vue` | Formulario con secciones Stitch | VERIFIED | 3 secciones (Identity, Localization, Product Access) con form-section-label (0.6875rem/600/uppercase). StitchTextField + md-outlined-select + md-checkbox. |
| `portal/src/components/tenants/WhitelabelForm.vue` | Formulario whitelabel con secciones Stitch | VERIFIED | 3 secciones (Domain & Branding, Color Palette, Typography) con form-section-label. preview-card con preview-title + preview-body. StitchTextField para domain y logo_url. |
| `portal/tests/visual/login.spec.ts` | Tests de regresión visual para Login | VERIFIED | 3 tests: Light Mode, Dark Mode, Error State. Verifica h2 'Welcome back', md-outlined-text-field, md-filled-button. Snapshots committed (3 PNG). |
| `portal/tests/visual/internal.spec.ts` | Tests de regresión visual para páginas internas | PARTIAL | 5 tests declarados (tenants-light, tenants-dark, drawer-create, drawer-whitelabel, drawer-dark). Solo 1 snapshot existe localmente (tenants-view-dark, untracked). Los otros 4 no existen. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| App.vue | MainLayout / AuthLayout | `route.meta.layout === 'auth'` | WIRED | Router declara `layout: 'auth'` para /login y `layout: 'main'` para rutas internas. App.vue computa el layout correcto. |
| LoginView.vue | authStore.loginWithCredentials | `import { useAuthStore }` + `await authStore.loginWithCredentials(email, password)` | WIRED | Wiring completo: form onSubmit -> handleLogin -> loginWithCredentials -> router.push('/dashboard'). |
| authStore.loginWithCredentials | Keycloak ROPC endpoint | `fetch(...protocol/openid-connect/token)` + response.json() + keycloak.init() | WIRED | POST con grant_type=password, respuesta usada para inicializar Keycloak con tokens, _populate() llamado al autenticarse. |
| MainLayout.vue | uiStore.toggleTheme | `import { useUIStore }` + `@click="uiStore.toggleTheme"` | WIRED | Toggle conectado al store. |
| TenantsView.vue | tenantsStore | `import { useTenantsStore }` + onMounted fetchTenants | WIRED | Carga datos en mount, operaciones CRUD completas. |
| TenantTable.vue | StitchTextField | `import StitchTextField` | WIRED | Usado en toolbar de búsqueda. |
| TenantDrawer.vue | TenantForm + WhitelabelForm | `import TenantForm` + `import WhitelabelForm` | WIRED | Tab 0 = TenantForm, Tab 1 = WhitelabelForm. v-model=formData en ambos. |
| main.ts | tailwind.css + material.ts | `import './assets/tailwind.css'` + `import './plugins/material'` | WIRED | Ambas importaciones presentes. material.ts carga 32 componentes @material/web incluyendo labs/navigationtab. |
| internal.spec.ts | snapshot baselines | `toHaveScreenshot(...)` con archivos PNG | NOT_WIRED | Solo tenants-view-dark existe localmente y sin commit. 4 baselines ausentes impiden que los tests pasen en CI. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UI-03 | 06-03-PLAN.md | Login page sigue diseño Stitch node-id 501bb1... | SATISFIED | LoginView.vue completamente reimplementado con StitchTextField, StitchButton, error display con tokens Stitch. 3 visual baselines committed. |
| UI-04 | 06-02-PLAN.md, 06-04-PLAN.md | Páginas internas siguen diseño Tenant Management node-id acc51e... | PARTIAL | Implementación en código es completa y fiel al diseño (Nav Rail, high-density table, M3 patterns). Pero REQUIREMENTS.md aún marca UI-04 como `[ ]` y 4 de 5 visual baselines no existen. |

**Orphaned in REQUIREMENTS.md traceability table:** UI-03 y UI-04 no aparecen en la tabla de Traceability de REQUIREMENTS.md. Solo los requirements de fases 1-5 están mapeados. Phase 6 requirements (UI-03, UI-04) están ausentes de la tabla.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `portal/tests/visual/internal.spec.ts-snapshots/` | N/A | 4 de 5 snapshot baselines ausentes (directorio untracked) | WARNING | Tests de regresión visual pasarán en modo --update-snapshots pero fallarán en CI al ejecutar contra baselines inexistentes. No bloquea funcionalidad pero bloquea validación visual automatizada. |
| `.planning/REQUIREMENTS.md` line 24 | 24 | `- [ ] **UI-04**` marcado como incomplete | INFO | Discrepancia administrativa — la implementación existe pero el tracker no se actualizó. |

No se encontraron stubs de implementación (return null, return {}, console.log-only handlers, placeholder templates).

### Human Verification Required

#### 1. Fidelidad visual al diseño de Google Stitch (Login)

**Test:** Navegar a `/login` con el portal en ejecución (`pnpm --filter portal dev`). Comparar visualmente contra el diseño Stitch node-id `501bb1c4dfdb456d9cd2672135daee2d`.
**Expected:** Card centrado con logo, campos email/password con md-outlined-text-field, botón Sign In con md-filled-button, checkbox "Remember me", enlace "Forgot password?". Tokens de color Stitch aplicados correctamente.
**Why human:** La fidelidad a un diseño Figma/Stitch específico (proporción, spacing exacto, colores de marca) no se puede verificar programáticamente desde el código fuente.

#### 2. Fidelidad visual al diseño de Google Stitch (Tenant Management interno)

**Test:** Iniciar sesión y navegar a `/tenants`. Comparar contra diseño Stitch node-id `acc51e9c26554064a2e0a45864688b85`.
**Expected:** Nav Rail 72px visible a la izquierda, App Bar con título "Tenant Management", tabla high-density con filas compactas 36px, status chips, menú de acciones por fila. Abrir Create Tenant y verificar el drawer lateral con tabs General Info / Whitelabel y secciones agrupadas.
**Why human:** El diseño Stitch especifica proporciones, densidad visual y distribución de elementos que solo son verificables visualmente contra el mockup original.

#### 3. Flujo de autenticación completo con ROPC

**Test:** En el portal, ingresar credenciales de un usuario válido de Keycloak QA. Verificar que el login funciona sin redirigir a la página de Keycloak.
**Expected:** El usuario se autentica directamente en el portal, queda en la SPA sin redirección, y aparece su nombre/rol en el App Bar.
**Why human:** El flujo ROPC requiere conexión activa a Keycloak QA (oauth2.qa.comsatel.com.pe). No se puede verificar sin el servidor externo activo.

### Gaps Summary

La fase 6 logró su objetivo principal de implementación: todos los componentes Stitch están creados, el sistema de layout Auth/Main funciona, la página de login usa componentes Material 3 con tokens Stitch, y las páginas internas tienen la densidad visual y patrones de Google Cloud Console definidos en el diseño Stitch.

**El gap específico es de validación, no de implementación:**

1. **Visual baselines de internal.spec.ts incompletas:** Los 5 tests de regresión visual para páginas internas existen como código pero 4 de 5 screenshots PNG de referencia no se generaron ni se commitearon. El directorio `internal.spec.ts-snapshots/` está untracked en git. Para que la suite de tests de regresión visual funcione como safety net en futuras iteraciones (su propósito declarado), los 5 baselines deben existir y estar versionados.

2. **REQUIREMENTS.md desactualizado:** UI-04 permanece marcado como `[ ]` y ninguno de los dos requirements del fase (UI-03, UI-04) aparece en la tabla de traceability. Esto es un gap documental que deja el tracker de estado del proyecto inconsistente con el código.

Para cerrar estos gaps se necesita: ejecutar `pnpm --filter portal exec playwright test portal/tests/visual/internal.spec.ts --update-snapshots` para generar los 5 baselines, commitear el directorio de snapshots, y actualizar REQUIREMENTS.md.

---

_Verified: 2026-06-06T23:00:00Z_
_Verifier: Claude (gsd-verifier)_
