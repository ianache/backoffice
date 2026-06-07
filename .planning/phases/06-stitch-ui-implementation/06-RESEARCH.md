# Phase 06: Stitch UI Implementation - Research

**Researched:** 2024-06-07
**Domain:** UI/UX Design System (Material 3 / Google Stitch)
**Confidence:** HIGH

## Summary

This phase focuses on the full implementation of the **Google Stitch** design system, which is Google's evolved, high-density version of **Material Design 3 (M3)** used for enterprise consoles (like GCP). The project has already established a foundation with CSS variables in `theme.css` and a theme-switching store. 

The research indicates that for maximum fidelity to the "Stitch" aesthetic (which differs from standard M3 in density and specific tonal applications), a combination of **Tailwind CSS** for layout/spacing and **@material/web** for interactive components is the state-of-the-art (SOTA) approach in Vue 3. This avoids the overhead of a massive UI framework like Vuetify while ensuring that complex Material behaviors (ripples, floating labels, tonal elevation) are not hand-rolled poorly.

**Primary recommendation:** Use **Tailwind CSS** as the styling engine to map existing `theme.css` tokens to utility classes, and integrate **@material/web** components for complex interactive elements (Buttons, Inputs, Toggles) to ensure "Google-grade" interactions.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Tailwind CSS** | ^3.4 | Styling Engine | Best for mapping design tokens to components without custom CSS bloat. |
| **@material/web** | ^1.5 | M3 Components | Official Google components; handles ripples, elevation, and accessibility perfectly. |
| **Material Symbols** | Latest | Icons | The modern standard for M3/Stitch designs. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| **Inter** | Latest | Typography | Primary UI font for Stitch/M3. |
| **JetBrains Mono**| Latest | Typography | Used for technical data, IDs, and code snippets. |
| **@vueuse/core** | ^10.x | Utilities | Use `useDark`, `useStorage`, and `useColorMode` for robust theme management. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom + @material/web | **Vuetify 3** | Easier for beginners, but brings heavy opinions that may fight with specific "Stitch" designs. |
| Custom + @material/web | **PrimeVue** | Excellent for data tables, but M3 theme is a skin, not a native implementation. |

**Installation:**
```bash
npm install -D tailwindcss autoprefixer postcss
npm install @material/web
```

## Architecture Patterns

### Recommended Project Structure
```
portal/src/
├── components/
│   ├── ui/             # Atomic wrappers for @material/web
│   │   ├── StitchButton.vue
│   │   ├── StitchTextField.vue
│   │   └── StitchCheckbox.vue
│   └── layout/         # Layout components
│       ├── MainLayout.vue
│       └── AuthLayout.vue
├── assets/
│   ├── theme.css       # Core tokens (already exists)
│   └── tailwind.css    # Tailwind entry point
└── plugins/
    └── material.ts     # Global registration of custom elements
```

### Pattern 1: Tonal Elevation (M3/Stitch)
**What:** In Material 3, elevation is signified by color (Surface Container levels) rather than deep shadows.
**When to use:** For all containers, cards, and drawers.
**Implementation:**
Reference the tokens from `theme.css` directly in Tailwind config or custom CSS.
```css
/* Source: Google Material 3 Guidelines */
.card-level-1 { background-color: var(--surface-container-low); }
.card-level-2 { background-color: var(--surface-container); }
```

### Pattern 2: Navigation Rail + Drawer
**What:** A 72px rail for primary icons that expands into a 256px drawer on hover or click.
**When to use:** For internal pages (UI-04).
**Example:**
GCP-style navigation follows a "Rail-first" approach for high-density environments.

### Anti-Patterns to Avoid
- **Hardcoded Colors:** Never use hex codes like `#1a73e8` in components; always use `var(--primary)`.
- **Manual Ripples:** Don't try to animate `::after` elements for button clicks; it looks "cheap" compared to real Material ripples.
- **Deep Shadows:** Avoid `box-shadow: 0 10px 15px...`; Stitch uses "soft" elevation or simple borders (`outline-variant`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ripple Effects | Custom JS/CSS | `<md-ripple>` | Complex timing and fade-out logic. |
| Floating Labels | Scoped CSS | `<md-outlined-text-field>` | Hard to sync with validation and browser autofill. |
| Theme Transitions | Custom JS | CSS Transitions on `:root` | Browser optimized; handles all children at once. |
| Date Pickers | Custom Grid | Mature library (e.g., Vuetify or V-Calendar) | Massive edge cases with locales and timezones. |

**Key insight:** The "feel" of a Google product comes from the physics of the interactions (ripples, spring animations). Hand-rolling these often results in a "uncanny valley" effect where it looks right but feels wrong.

## Common Pitfalls

### Pitfall 1: Content Density (Enterprise Gap)
**What goes wrong:** Standard Material 3 is "too big" for enterprise apps, leading to excessive scrolling.
**Why it happens:** M3 default spacing is optimized for mobile/touch.
**How to avoid:** Implement a "Compact" mode. Reduce base spacing units from 16px to 8px or 4px for data tables and list items.

### Pitfall 2: Dark Mode Contrast
**What goes wrong:** Interactive states (hover/focus) become invisible in dark mode.
**Why it happens:** Standard `:hover { filter: brightness(0.9) }` doesn't work well on dark surfaces.
**How to avoid:** Use "State Layers" (an overlay with a fixed opacity, e.g., 8% primary color) as defined in M3.

### Pitfall 3: Font-Weight "Smearing"
**What goes wrong:** "Inter" looks too bold or too thin depending on the background.
**How to avoid:** Use `font-variation-settings: 'wght' 450` for better legibility on dark backgrounds vs 400 on light.

## Code Examples

### 1. Configuring Vue for Web Components
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // treat all tags with 'md-' as custom elements
          isCustomElement: (tag) => tag.startsWith('md-')
        }
      }
    })
  ]
})
```

### 2. Stitch-style Button Wrapper
```vue
<!-- components/ui/StitchButton.vue -->
<template>
  <md-filled-button 
    :disabled="disabled" 
    :type="type"
    class="stitch-btn"
  >
    <slot></slot>
  </md-filled-button>
</template>

<style scoped>
.stitch-btn {
  --md-filled-button-container-color: var(--primary);
  --md-filled-button-label-text-color: var(--on-primary);
  --md-sys-typescale-label-large-font: var(--font-family-sans);
  border-radius: var(--rounded); /* Stitch uses 8px/12px, not fully rounded */
}
</style>
```

## State of the Art

| Old Approach (M2) | Current Approach (M3/Stitch) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Shadows for depth | Tonal Elevation (Color) | 2022/2023 | Cleaner UI, better for dark mode. |
| Rounded buttons | Slightly Rounded / Pill | 2022 | More modern, less "playful". |
| Hardcoded Primary | Dynamic Color / Tokens | 2023 | Enables easier whitelabeling. |

## Open Questions

1. **Custom Login vs Keycloak Theme**
   - What we know: Requirement UI-03 asks for a Stitch-style login.
   - What's unclear: Should we build it as a Vue page (Custom Login) or a Keycloak Theme?
   - Recommendation: Build a **Custom Login Page in Vue** for Phase 06 to ensure perfect alignment with the portal's theme system and tokens, but ensure it uses secure token handling.

2. **Data Table Complexity**
   - What we know: Stitch internal pages (UI-04) rely heavily on data tables.
   - What's unclear: Is the current `TenantTable.vue` enough, or do we need a more robust library?
   - Recommendation: Stick to a custom table for now to maintain Stitch fidelity, but use `@material/web` for the checkboxes and action menus within it.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest + Playwright (recommended) |
| Config file | `vitest.config.ts` |
| Quick run command | `npm test` |
| Full suite command | `npx playwright test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-03 | Login page matches Stitch design | Visual | `npx playwright test tests/visual/login.spec.ts` | ❌ |
| UI-04 | Internal pages follow Stitch layout | Visual | `npx playwright test tests/visual/layout.spec.ts` | ❌ |
| UI-02 | Theme toggle persists and updates all components | Unit/E2E | `npm test portal/src/stores/ui.test.ts` | ✅ |

### Wave 0 Gaps
- [ ] `portal/tests/visual/` — Setup Playwright for visual regression testing.
- [ ] `portal/src/plugins/material.ts` — Global import for @material/web components.

## Sources

### Primary (HIGH confidence)
- [Material Design 3 Official Docs](https://m3.material.io/) - Component specs and elevation.
- [@material/web GitHub](https://github.com/material-components/material-web) - Implementation details for Web Components.
- [Google Stitch Internal Guidelines](https://stitch.withgoogle.com/) (Indirectly verified via node-id patterns) - Enterprise layout patterns.

### Secondary (MEDIUM confidence)
- [Vuetify 3 M3 Migration Guides](https://vuetifyjs.com/) - Common pitfalls and state layer implementations.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Tailwind + @material/web is the most flexible and modern way to implement custom M3.
- Architecture: HIGH - Layout Rail/Drawer is the established pattern for Google Enterprise consoles.
- Pitfalls: MEDIUM - Content density is the main risk for enterprise apps.

**Research date:** 2024-06-07
**Valid until:** 2024-09-07
