---
name: Stitch Console
colors:
  surface: '#f6faff'
  surface-dim: '#d6dadf'
  surface-bright: '#f6faff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f4f9'
  surface-container: '#eaeef3'
  surface-container-high: '#e5e8ee'
  surface-container-highest: '#dfe3e8'
  on-surface: '#181c20'
  on-surface-variant: '#414754'
  inverse-surface: '#2c3135'
  inverse-on-surface: '#edf1f6'
  outline: '#727785'
  outline-variant: '#c1c6d6'
  surface-tint: '#005bc0'
  primary: '#005bbf'
  on-primary: '#ffffff'
  primary-container: '#1a73e8'
  on-primary-container: '#ffffff'
  inverse-primary: '#adc7ff'
  secondary: '#5b5f64'
  on-secondary: '#ffffff'
  secondary-container: '#dde0e6'
  on-secondary-container: '#5f6368'
  tertiary: '#9e4300'
  on-tertiary: '#ffffff'
  tertiary-container: '#c55500'
  on-tertiary-container: '#0e0200'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc7ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#dfe3e8'
  secondary-fixed-dim: '#c3c7cc'
  on-secondary-fixed: '#181c20'
  on-secondary-fixed-variant: '#43474c'
  tertiary-fixed: '#ffdbcb'
  tertiary-fixed-dim: '#ffb691'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#783100'
  background: '#f6faff'
  on-background: '#181c20'
  surface-variant: '#dfe3e8'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  title-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
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
  label-lg:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.5px
  label-md:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
  code:
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
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin: 32px
  max-width: 1440px
---

## Brand & Style
The design system is engineered for precision, reliability, and enterprise-grade scalability. It targets DevOps engineers and Product Managers who require a high-density, low-friction interface to manage complex deployment logic.

The aesthetic follows a **Corporate / Modern** movement, heavily influenced by Google’s latest Material 3 evolution. It prioritizes clarity through:
- **Functional Minimalism:** Removing unnecessary visual noise to focus on logic and status.
- **Systematic Order:** High structural alignment using consistent grids.
- **Trust-Driven Clarity:** Using subtle elevation and high-quality typography to make mission-critical data (like production toggles) feel secure and deliberate.

## Colors
The palette is rooted in a professional "Enterprise Blue" that signals stability. 

- **Primary:** Used for the main action buttons, active toggle states, and primary navigation highlights.
- **Surface & Backgrounds:** The main application background is `#F8F9FA`. Content sits on white (`#FFFFFF`) containers to create clear separation.
- **Status Tints:** For state indicators (Online/Offline, Success/Failure), use the semantic colors. In high-density tables, use low-opacity background tints (10-15%) with full-saturation text for high legibility without visual fatigue.
- **Border Palette:** Use `#DADCE0` for standard component borders and separators.

## Typography
This design system utilizes **Inter** for all UI elements to ensure maximum legibility across high-density data tables. 

- **Headlines:** Use `headline-lg` for page titles and `headline-md` for major section headers.
- **Body:** `body-md` is the workhorse for all descriptions and table data.
- **Labels:** Use `label-lg` in all-caps for small metadata headers or overlines.
- **Monospace:** For feature flag keys, environment variables, or rule logic, use **JetBrains Mono** to distinguish technical strings from UI labels.

## Layout & Spacing
The layout follows a **Fixed-Fluid hybrid grid**. The side navigation is fixed at 256px, while the main content area expands to a maximum of 1440px, centering itself on ultra-wide displays.

- **Grid:** Use a 12-column grid for dashboard views.
- **Rhythm:** All spacing must be a multiple of 4px. Use `16px` (md) for standard padding within cards and `24px` (lg) for gutters between major layout blocks.
- **Density:** Provide a "Compact" toggle for data tables that reduces vertical cell padding from 12px to 8px for power users.

## Elevation & Depth
Depth is used sparingly to signify interactivity and layering. This system avoids heavy shadows in favor of **Tonal Layers** and subtle "Google-style" elevation.

- **Level 0 (Background):** `#F8F9FA` - The base canvas.
- **Level 1 (Surface):** `#FFFFFF` with a 1px border of `#DADCE0`. Used for cards and main content areas.
- **Level 2 (Interaction):** A soft shadow `0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15)`. Used for buttons on hover and active dropdowns.
- **Level 3 (Overlays):** Used for modals and flyouts. These should have a more pronounced shadow to separate them from the logic beneath.

## Shapes
The design system uses a consistent **Rounded** language to feel approachable yet professional.

- **Standard Containers:** Cards and rule blocks use `12px` (rounded-lg).
- **Small Components:** Buttons, input fields, and chips use `8px` (standard).
- **Large Components:** Modals and large empty-state containers use `16px` (rounded-xl).
- **Toggle Tracks:** Must be fully rounded (pill-shaped) to clearly distinguish them from other interactive elements.

## Components
Consistent implementation of these components ensures a "Stitch" feel across the console:

- **The Switch (Toggle):** The primary component. Inactive: gray track with white thumb. Active: Blue track (`#1A73E8`) with white thumb. Add a "Deliberate Action" delay or confirmation for Production environment toggles.
- **Rule Blocks:** Nestable cards with a light-blue left border highlight. Logic connectors (AND/OR) should be rendered as small, pill-shaped chips floating on the connecting line between blocks.
- **KPI Cards:** Display flag health (e.g., "99.9% Success Rate"). Use a `title-md` for the metric and a small sparkline for 24h trend data.
- **Environment Tabs:** Use a sub-navigation bar with a bottom indicator. Each environment (Dev, QA, Prod) should have a distinct colored dot next to the label (Gray, Amber, Red respectively) to prevent accidental edits in the wrong scope.
- **Data Tables:** White background, thin horizontal separators. The "Flag Name" should be `primary_color_hex` and clickable.
- **Buttons:**
    - *Primary:* Solid Blue background.
    - *Secondary:* Outlined with `#DADCE0`.
    - *Danger:* Outlined with Red text for "Delete Flag" actions.