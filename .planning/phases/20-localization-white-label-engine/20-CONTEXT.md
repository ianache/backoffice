# Phase 20: Localization White Label Engine - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the multi-tenant White Labeling Engine end to end:
- `localized_labels` table with 3-level inheritance (Tenant → Company → Product, "override by proximity")
- BFF/backend resolver with caching, namespace-based lazy loading (`common` eager, `page_*`/`form_*` lazy)
- Two-phase hydration (`/bootstrap` critical namespaces, `/prefetch` background namespaces)
- Hot-reload invalidation (`INVALIDATE_NAMESPACE` broadcast on label update)
- Vue 3 SDK integration (`$t` plugin with interpolation + missing-key reporting)
- BackOffice admin module (per `docs/prd_namespaces_keys_management.md`) for managing namespaces, keys/translations, overrides, and diagnostics

Delivered as ONE phase with many sequenced plans/waves (not split into sub-phases).

</domain>

<decisions>
## Implementation Decisions

### MVP Scope Slice
- Single Phase 20, broken into multiple plans/waves by the planner — covers engine + admin UI + SDK together.
- Admin UI must-have RFs for v1: RF-01 (Workspace Context Selector), RF-02 (Namespace sidebar + CRUD), RF-03 (Key matrix + filters), RF-04 (Key editor + parameter validation), RF-05 (Inheritance tree + restore override), RF-08 (Dark mode).
- Vue 3 `$t` plugin + missing-key reporting is added to the existing `sdk/sdk-js` package (new "labels" module alongside the flag evaluator) — not a separate package, not portal-only.
- Hot-reload (WS `INVALIDATE_NAMESPACE`) is IN SCOPE for v1. Reuse the existing in-process `ConnectionManager` + per-tenant WebSocket pattern (`backend/app/ws/connection_manager.py`, `backend/app/domains/sdk/ws_router.py`) — do NOT wait for Phase 19's Redis pub/sub.

### Locales & Seed Content
- v1 supports exactly two locales: `es_PE` and `en_US` (matches design doc examples).
- Seed the `common` namespace (eager-load) with realistic nav/button labels (e.g., `btn_aceptar`/`btn_cancelar`) for an existing tenant, PLUS 1-2 company-level overrides to demonstrate the inheritance cascade in the UI.
- Seed data targets EXISTING tenant/company/product records already in the dev DB (from Phases 2 and 7) — do not fabricate a new demo hierarchy.
- Namespaces are fully admin-creatable from day one (RF-02: create via modal with id/strategy/description, unique-ID validation) — no hardcoded namespace list. `common` is seeded as starter data but the create flow works identically for new namespaces.

### Roles & Permissions
- Add a new Keycloak role `UXWriter`. Backend enforces that `UXWriter` can only update `label_value` on existing keys (no namespace CRUD, no key/structure creation) — matches PRD §4 row exactly.
- For PlatformAdmin / TenantAdmin (TenantOwner) / ProductManager, mirror the existing scope-checking pattern from `backend/app/domains/feature_flags/router.py` (the `allowed_scopes` / role-based authorization helper) applied to namespaces and labels endpoints.
- "Their own" tenant/company/product for non-PlatformAdmin roles comes from Keycloak token claims, same as the existing tenants/feature_flags domains — restricts Workspace Context Selector options accordingly.

### Diagnostics & Import/Export (RF-06 / RF-07)
- RF-06 (Missing Keys panel) ships in v1 via a SELF-CONTAINED `missing_label_reports`-style table/endpoint — independent of Phase 18's telemetry pipeline (which has 0 plans / not built).
- Miss trigger: the SDK `$t` plugin calls `reportMissingLabel(namespace, key)` (per design doc §5A), which posts to a BFF/backend endpoint. Repeated misses increment a hit counter; panel shows namespace, missing key, hits, last reported (per PRD RF-06).
- `quickCreateMissing()` flow (pre-fill create-key form from a missing-key row) is part of RF-06 v1.
- RF-07 v1 = EXPORT ONLY (JSON for SDK bootstrap shape + CSV for translators), for the active Workspace Context. Import (drag-and-drop, overwrite/skip conflict resolution) is DEFERRED to a follow-up.

### Claude's Discretion
- Exact `localized_labels` schema details beyond what's specified (indexes, version field type) — follow PRD §7 (optimistic concurrency via `version`) and existing model conventions (MySQL 5.6-safe TEXT for JSON-ish fields like `params`).
- Cache implementation details (in-memory vs Redis-backed per design doc §3) — design doc shows Redis; confirm what's already available in this environment and adapt accordingly.
- Exact shape of the `missing_label_reports` table and dedup/hit-counting mechanism.
- Micro-UI module name/location and Shell nav placement for the new admin module — follow the `mui-feature-flags`/`mui-tenants` Module Federation pattern.
- BFF route naming/structure for labels endpoints — follow `bff/src/routes/flags.ts` / `tenants.ts` conventions.

</decisions>

<specifics>
## Specific Ideas

- The HTML prototype at `design/stitch/labeling - namespaces_keys_management.html` is the visual reference the PRD was written against — use it directly for the admin UI's layout, IDs, and interactions (12-column grid: sidebar col-span-3, matrix col-span-6, translation/inheritance panel col-span-3).
- Inheritance tree visualization (RF-05) should show the cascade with "Hereda de Tenant" / "Hereda de Company / Tenant" connector text per PRD §5, with a "Restaurar" action that deletes the override row at the active context level.
- Audit requirement from PRD §7 is strict: every insert/update/delete on `localized_labels` must write to `audit_log` with `entity_type: localized_label`, before/after payloads — follow the existing audit domain pattern (relevant to recently-completed Phase 16 audit work).
- Concurrency conflict UX from PRD §9.2 PI-02: second concurrent editor gets a toast — "La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios."

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/domains/feature_flags/models.py`: tenant_id/company_id/product_id nullable scoping columns (String(100), nullable, indexed) — directly mirrors the `localized_labels` hierarchy columns needed.
- `backend/app/domains/feature_flags/router.py`: role/scope authorization helper (PlatformAdmin/TenantAdmin/TenantOwner/ProductManager checks) — reuse pattern for namespace/label endpoints and the new UXWriter role.
- `backend/app/ws/connection_manager.py` + `backend/app/domains/sdk/ws_router.py`: in-process per-tenant WebSocket manager with first-message auth — reuse directly for `INVALIDATE_NAMESPACE` broadcast (no Redis dependency needed for v1).
- `sdk/sdk-js/src/` (client.ts, evaluator.ts, websocket.ts, telemetry.ts): existing SDK package structure — add a labels module (`$t`, interpolation, `reportMissingLabel`) following the same conventions as the flag evaluator/telemetry modules.
- `microuis/mui-feature-flags`, `microuis/mui-tenants`: Module Federation micro-UI pattern to follow for the new labels admin module.
- `design/stitch/labeling - namespaces_keys_management.html`: ready-made interactive prototype matching the PRD — direct visual/structural reference.

### Established Patterns
- Audit logging: all CRUD on domain entities writes to `audit_log` (entity_type, before/after payload, user) — Phase 16 just completed the audit timeline/diff viewer for this.
- MySQL 5.6-safe JSON-as-TEXT columns (`tags`, `rules` in feature_flags) — apply same approach for any JSON-shaped fields (e.g., interpolation `params`).
- `version` field with `onupdate=func.now()` style optimistic concurrency already used in feature_flags — extend for `localized_labels`.

### Integration Points
- `bff/src/routes/`: add `labels.ts` mirroring `tenants.ts`/`flags.ts` structure, proxying to new backend endpoints.
- `backend/app/domains/sdk/router.py`: extend with `/labels/bootstrap` and `/labels/prefetch` endpoints alongside existing `/bootstrap`/`/evaluate`.
- Portal/Shell navigation: new menu entry for the labels admin micro-UI, gated by role (PlatformAdmin/TenantAdmin/ProductManager/UXWriter visibility per PRD §4).
- Existing tenant/company/product records (Phases 2, 7) provide the seed-data targets for the Workspace Context Selector demo.

</code_context>

<deferred>
## Deferred Ideas

- RF-07 Import (drag-and-drop JSON/CSV upload with overwrite/skip conflict resolution) — follow-up phase once export is proven.
- Flutter `LabelEngine` (offline-capable SDK with shared_preferences) from design doc §5B — no Flutter codebase exists in this project; out of scope unless a Flutter client is introduced later.
- Full integration of missing-key diagnostics with Phase 18's telemetry/aggregation pipeline — v1 uses a self-contained log; unify with Phase 18 once that pipeline is built.
- Redis-backed distributed cache + Redis pub/sub for hot-reload (Phase 19 scope) — v1 hot-reload uses the existing in-process WS pattern; multi-instance scaling remains Phase 19's concern.

</deferred>

---

*Phase: 20-localization-white-label-engine*
*Context gathered: 2026-06-13*
