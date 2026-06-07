---
name: Bold Precision
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#5d3f3b'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#926f6a'
  outline-variant: '#e7bdb7'
  surface-tint: '#c0000f'
  primary: '#a9000b'
  on-primary: '#ffffff'
  primary-container: '#d41117'
  on-primary-container: '#ffe6e3'
  inverse-primary: '#ffb4aa'
  secondary: '#5f5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e2dfde'
  on-secondary-container: '#636262'
  tertiary: '#00529d'
  on-tertiary: '#ffffff'
  tertiary-container: '#006ac8'
  on-tertiary-container: '#e4ecff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad5'
  primary-fixed-dim: '#ffb4aa'
  on-primary-fixed: '#410001'
  on-primary-fixed-variant: '#930008'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474746'
  tertiary-fixed: '#d5e3ff'
  tertiary-fixed-dim: '#a7c8ff'
  on-tertiary-fixed: '#001b3c'
  on-tertiary-fixed-variant: '#004789'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

This design system is built for high-stakes professional environments where clarity and decisive action are paramount. It blends **Minimalism** with **Corporate Modern** sensibilities, utilizing a high-energy primary red to signal importance and momentum against a restrained, systematic backdrop.

The target audience consists of power users in finance, technology, or enterprise operations who require a tool that feels both authoritative and efficient. The emotional response is one of confidence, urgency, and precision. Every element is designed to reduce cognitive load while highlighting critical paths through the strategic use of its signature primary hue.

## Colors

The palette is anchored by a high-chroma **Bold Red**, used specifically for primary actions, active navigation states, and critical alerts. This is balanced by a sophisticated set of cool grays and a stark white surface strategy to maintain a clean, professional aesthetic.

- **Primary:** Used for the main "Call to Action" buttons, active icons, and progress indicators.
- **Secondary:** Deep charcoal for text and structural elements to ensure high legibility.
- **Neutral:** Slate tones for borders, secondary text, and disabled states.
- **Surface/Background:** A layered approach using pure white for content containers and a very light gray for the base canvas to provide subtle contrast.

## Typography

The design system utilizes **Inter** exclusively to leverage its systematic, neutral, and highly legible characteristics. The type hierarchy is strictly defined to ensure information architecture is clear at a glance.

Headlines use tighter letter spacing and heavier weights to command attention. Body text prioritizes a comfortable line height for sustained reading. Labels and utility text often utilize medium or semi-bold weights to remain distinct even at smaller scales. Use the `display-lg` style sparingly for hero sections or key data points.

## Layout & Spacing

The design system employs a **12-column fluid grid** for desktop and a **4-column grid** for mobile. The spacing rhythm is strictly based on an **8px linear scale**, ensuring mathematical harmony across all components.

- **Desktop:** 12 columns with 24px gutters and 40px side margins. Max-width for content is 1440px.
- **Tablet:** 8 columns with 24px gutters and 32px side margins.
- **Mobile:** 4 columns with 16px gutters and 16px side margins. 

Internal component padding should always use multiples of 4px, though the overall layout should stick to the 8px increments (8, 16, 24, 32, 48, 64) for vertical rhythm.

## Elevation & Depth

This design system uses a **Tonal Layering** approach combined with **Low-Contrast Outlines**. Depth is communicated through subtle changes in surface color and thin, purposeful borders rather than heavy shadows.

- **Level 0 (Background):** #F8FAFC - The base canvas.
- **Level 1 (Surface):** #FFFFFF - Primary containers, cards, and navigation bars.
- **Level 2 (Raised):** Surface color with a very soft, 10% opacity neutral shadow (0px 4px 12px) used exclusively for floating elements like dropdowns and modals.

Borders are 1px thick, using a soft #E2E8F0 color for most containers, creating a "clean-cut" appearance that feels structural and organized.

## Shapes

The shape language is defined by the **Rounded Eight** principle. This creates a professional look that is approachable but remains disciplined and architectural.

- **Standard (Base):** 0.5rem (8px) for buttons, input fields, and small cards.
- **Large (LG):** 1rem (16px) for main content containers and modals.
- **Extra Large (XL):** 1.5rem (24px) for featured promotional sections.

All interactive elements must maintain these consistent radii to ensure a cohesive visual signature across the entire interface.

## Components

### Buttons
- **Primary:** Solid #D41117 background with white text. On hover, transition to #D72429.
- **Secondary:** White background with a 1px #E2E8F0 border. Text is #1A1A1A.
- **Tertiary/Ghost:** No background or border. Text is #D41117.

### Navigation
- **Active State:** Navigation links use a 2px solid #D41117 bottom border (or left border for sidebars) and a semi-bold weight. Icons in active states are tinted with the primary red.

### Input Fields
- Use an 8px corner radius. Focus states should lose the neutral border and gain a 2px solid #D41117 ring with a 4px soft outer glow.

### Cards
- Pure white background with a 1px #E2E8F0 border. Use 16px (rounded-lg) corners for cards containing complex data or nested components.

### Chips & Tags
- For active or selected tags, use a light tint of the primary red (#FEE2E2) with #D41117 text to maintain the brand identifier without overwhelming the UI.