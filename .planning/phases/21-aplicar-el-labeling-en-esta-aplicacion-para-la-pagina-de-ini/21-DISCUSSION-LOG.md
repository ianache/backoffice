# Phase 21: Login Localization via Labeling SDK - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 21-login-localization-via-labeling-sdk
**Areas discussed:** Locale selection, pre-authentication context, content coverage, failure behavior

---

## Locale Selection

- Selected browser detection on every load: `es-*` maps to `es_PE`; all others map to `en_US`.
- Rejected fixed Spanish and environment-only locale selection.
- Selected no visible locale selector and no persistence.
- Selected `en_US` fallback for unsupported locales.

## Pre-Authentication Context

- Selected `VITE_BO_TENANT_ID` with `platform` fallback.
- Selected tenant plus `VITE_BO_PRODUCT_ID`, defaulting product to `backoffice`; no company context.
- Selected reuse of `VITE_BO_SDK_KEY`.
- Deferred hostname/domain tenant discovery.

## Content Coverage

- Selected authentication panel only; right-side preview remains unchanged.
- Selected fixed `BackOffice CC` branding.
- Selected technical values outside labels: version, email placeholder, Keycloak proper name.
- Selected localized known-error mapping plus generic localized fallback for unknown errors.

## Failure Behavior

- Selected a maximum 1-second initialization wait.
- Selected a minimal neutral loading screen during the wait.
- Selected bundled local fallback strings after timeout or failure.
- Selected late in-place hydration and continued `INVALIDATE_NAMESPACE` hot reload.
- Locked fail-open behavior: label infrastructure must never block login access.

## the agent's Discretion

- Namespace and key naming.
- Bundled fallback and error-mapping module structure.
- Accessible loading-indicator implementation.
- Test and timeout implementation details.

## Deferred Ideas

- Resolve pre-auth tenant from hostname, subdomain, or custom domain.
