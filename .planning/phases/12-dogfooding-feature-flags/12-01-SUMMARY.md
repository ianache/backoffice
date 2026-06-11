---
phase: 12-dogfooding-feature-flags
plan: 01
subsystem: portal
tags: [vue, sdk, federation, infrastructure]

requires: []
provides:
  - "useBoFlags composable wrapping @backoffice/sdk-js"
  - "Workspace dependency linkage for portal"
  - "Federation exposure of ./boFlags"
  - "TypeScript definitions for shell/boFlags remote module"
  - "Initialization block in portal/src/main.ts"
affects: [12-02, 12-03]

tech-stack:
  added: ["@backoffice/sdk-js (workspace dependency)"]
  patterns:
    - "Module-level singleton state in useBoFlags.ts with fail-open defaults (true refs)"
    - "WS invalidate() hook re-fetching from remote to update Vue ref dynamically"

key-files:
  created:
    - portal/src/composables/useBoFlags.ts
  modified:
    - portal/package.json
    - portal/.env
    - portal/vite.config.ts
    - microuis/mui-feature-flags/src/env.d.ts
    - portal/src/main.ts

key-decisions:
  - "Fail-open design where refs default to true so admin UI is never locked out on initialization error"
  - "Live WS reactivity by overriding FeatureFlagClient.invalidate() to run evaluateRemote() and update refs"

requirements-completed: [DOGF-01, DOGF-02, DOGF-03]

duration: 10min
completed: 2026-06-11
---

# Phase 12 Plan 01: useBoFlags Composable + Infrastructure Summary

Established the foundational infrastructure for dogfooding feature flags in the BackOffice portal, integrating the custom SDK, configuring environment variables, exposing the composable via Module Federation, and initializing the client.

## Accomplishments
- Added `@backoffice/sdk-js` as a workspace dependency to `portal/package.json` and ran `pnpm install` to link.
- Added `VITE_BO_SDK_KEY`, `VITE_BO_TENANT_ID`, and `VITE_BO_ENVIRONMENT` variables to `portal/.env`.
- Created `portal/src/composables/useBoFlags.ts` implementing a module-scoped singleton Vue composable.
- Configured Module Federation in `portal/vite.config.ts` to expose the composable as `./boFlags`.
- Added module declaration for `shell/boFlags` in `microuis/mui-feature-flags/src/env.d.ts` for type safety in remote MUIs.
- Integrated non-blocking, fire-and-forget initialization of the composable in `portal/src/main.ts` after successful Keycloak authentication.
