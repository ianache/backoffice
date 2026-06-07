---
name: Stitch Console Dark
colors:
  surface: '#0b141c'
  surface-dim: '#0b141c'
  surface-bright: '#313a43'
  surface-container-lowest: '#060f16'
  surface-container-low: '#141c24'
  surface-container: '#182028'
  surface-container-high: '#222b33'
  surface-container-highest: '#2d363e'
  on-surface: '#dae3ee'
  on-surface-variant: '#c1c6d5'
  inverse-surface: '#dae3ee'
  inverse-on-surface: '#29313a'
  outline: '#8b919e'
  outline-variant: '#414753'
  surface-tint: '#abc7ff'
  primary: '#abc7ff'
  on-primary: '#002f65'
  primary-container: '#4d94ff'
  on-primary-container: '#002c60'
  inverse-primary: '#005cba'
  secondary: '#a2c9ff'
  on-secondary: '#00315c'
  secondary-container: '#0071c7'
  on-secondary-container: '#f0f4ff'
  tertiary: '#67df70'
  on-tertiary: '#00390d'
  tertiary-container: '#2eab44'
  on-tertiary-container: '#00360c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d7e3ff'
  primary-fixed-dim: '#abc7ff'
  on-primary-fixed: '#001b3f'
  on-primary-fixed-variant: '#00458e'
  secondary-fixed: '#d3e4ff'
  secondary-fixed-dim: '#a2c9ff'
  on-secondary-fixed: '#001c38'
  on-secondary-fixed-variant: '#004882'
  tertiary-fixed: '#83fc89'
  tertiary-fixed-dim: '#67df70'
  on-tertiary-fixed: '#002105'
  on-tertiary-fixed-variant: '#005317'
  background: '#0b141c'
  on-background: '#dae3ee'
  surface-variant: '#2d363e'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-margin: 24px
  gutter: 16px
---

## Brand & Style
The design system is a high-performance, developer-centric interface designed for deep focus and technical clarity. The brand personality is systematic, precise, and authoritative, catering to engineers and data scientists who require long-duration interface interaction without eye strain.

The design style is **Corporate Modern with a Technical Edge**. It utilizes a "Dark Mode First" philosophy, moving away from pure blacks to deep navy-charcoal tones to reduce high-contrast glare while maintaining a sense of infinite depth. The aesthetic is characterized by sharp typography, subtle tonal layering instead of heavy shadows, and high-visibility accent points that guide the user's attention to critical actions and system status.

## Colors
This design system utilizes a structured dark palette optimized for technical consoles. 

- **Surface Layers:** Use `#0b0e14` as the base canvas. Background elements like sidebars or secondary panels use the slightly lighter `#161b22` to create a "container" effect. 
- **Interaction States:** Primary actions use a vibrant `#4d94ff` blue. For secondary actions and subtle accents, a softer `#79c0ff` is preferred.
- **Typography Contrast:** Primary text is an off-white `#e6edf3` to prevent the "vibrating" effect of pure white on black. Secondary metadata and labels use `#8b949e`.
- **Borders:** Outlines are critical in dark mode. Use `#30363d` for standard component borders to define shape without excessive contrast.

## Typography
Typography is optimized for legibility and information density. 

- **Primary Font:** **Inter** is the workhorse for the entire system, providing a clean, neutral, and highly readable sans-serif experience.
- **Label & Data Font:** **Geist** is introduced for labels and small UI elements to provide a modern, technical feel with slightly increased tracking for clarity at small sizes.
- **Code & Monospace:** For CLI outputs, logs, and configuration snippets, use **JetBrains Mono**.
- **Scale:** Keep body text at `14px` for standard dashboard density, dropping to `12px` for secondary metadata and status labels.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. Navigation and sidebars are fixed-width (typically 240px or 64px collapsed), while the main content area is fluid to maximize data visualization real estate.

- **Grid:** A 12-column grid is used for dashboard layouts, though individual cards and modules often rely on internal flexbox/auto-layout logic using the 4px base unit.
- **Rhythm:** Standard spacing between related elements is `8px` (sm), while distinct sections or cards are separated by `24px` (lg).
- **Safe Areas:** Maintain a minimum `24px` margin on the left and right edges of the viewport on desktop, reducing to `16px` on mobile.

## Elevation & Depth
In this dark mode system, depth is communicated through **Tonal Elevation** rather than physical shadows. 

- **Level 0 (Base):** `#0b0e14` - The primary background.
- **Level 1 (Surface):** `#161b22` - Cards, navigation bars, and secondary panels.
- **Level 2 (Overlay):** `#21262d` - Modals, dropdown menus, and hovered states.
- **Outlines:** Every elevated surface should have a subtle 1px border using the `outline` token (`#30363d`) to ensure separation when one dark surface overlaps another.
- **Shadows:** If used for modals, they should be deep, wide, and low-opacity (Black @ 50% opacity, 20px blur) to provide a soft ambient glow that suggests the object is floating above the base.

## Shapes
The design system utilizes the **ROUND_EIGHT** principle for a balanced, professional appearance. 

- **Standard Components:** Buttons, input fields, and small cards use a `0.5rem` (8px) corner radius.
- **Large Containers:** Dashboard cards and modals use `1rem` (16px) for a softer, more modern framing.
- **Strict Elements:** Data grid cells and inline tags may use a reduced `4px` radius for maximum space efficiency.

## Components

- **Buttons:**
  - **Primary:** Background `#4d94ff`, Text `#051d3b` (High contrast).
  - **Secondary:** Transparent background with `#30363d` outline, Text `#e6edf3`.
  - **Ghost:** No background or border, Text `#8b949e`, transitions to `#e6edf3` on hover.

- **Inputs:**
  - Fields use the `#0b0e14` background with a `#30363d` border.
  - Active/Focus state: Border changes to `#4d94ff` with a subtle outer glow (2px).

- **Chips & Tags:**
  - Use a subtle fill (`#161b22`) and high-contrast text. 
  - Status indicators (e.g., "Active", "Error") use low-opacity versions of their semantic colors (e.g., Success green at 15% opacity background with 100% opacity text).

- **Cards:**
  - Background: `surface-container` (`#161b22`).
  - Border: 1px solid `outline` (`#30363d`).
  - Header: Separated by a 1px divider for complex data views.

- **Lists & Data Grids:**
  - Use `outline-variant` (`#21262d`) for row separators.
  - Hover state: Background shifts to `#21262d` to provide clear row-level feedback.