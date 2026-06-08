# Retrospective: BackOffice Multi-Tenant Platform

## Milestone: v1.0 — BackOffice MVP

**Shipped:** 2026-06-08
**Phases:** 7 (1, 2, 2.1, 3, 4, 5, 6) | **Plans:** 29 | **LOC:** ~8,016

### What Was Built

- Auth layer: Keycloak PKCE + ROPC, JWT validation en BFF, guards en Vue Router
- Tenant management: CRUD completo con whitelabel config (logo, colores, tipografía, dominio)
- User management: Keycloak admin API, roles multi-nivel, audit log, MFA reset
- Feature flags: jerarquía 3 niveles, 5 operadores de evaluación, segmentos reutilizables
- Rule builder: drag & drop visual, live simulator TypeScript port del motor Python
- Stitch UI: Material 3 (Nav Rail 72px, high-density table, M3 tokens), Light/Dark mode

### What Worked

- GSD wave-based execution con subagents paralelos — phases 4 y 5 en múltiples waves ejecutaron en paralelo sin conflictos
- Checkpoint plans (`autonomous: false`) para E2E verification humana — protocolo claro y efectivo
- TypeScript port del engine Python para rule builder — verificado contra el backend con mismos operadores
- Stack cerrado desde el inicio — no hubo debates de tecnología durante ejecución

### What Was Inefficient

- Phase 2 perdió su header en ROADMAP.md — herramienta de análisis no pudo parsear la fase
- Visual baselines de Playwright no generadas — Keycloak init interfiere con auth injection; requirió infra E2E adicional que no resolvió completamente el problema en esta sesión
- Phase 6 marcada complete antes de generar snapshots — gap descubierto en verificación post-facto

### Patterns Established

- `VITE_E2E_SKIP_AUTH` + `.env.playwright` para bypass de Keycloak en tests visuales
- Pinia `pinia-plugin-persistedstate` key = store ID — mock auth via `sessionStorage.setItem('auth', ...)`
- Commit atómico por tarea con `feat({phase}-{plan}):` prefix — git log filtreable por fase
- SUMMARY.md con frontmatter estructurado en cada plan — permite análisis automatizado

### Key Lessons

- Los tests visuales con Playwright requieren `page.waitForURL()` explícito — `waitForLoadState('networkidle')` no garantiza que el router haya completado la navegación inicial
- Keycloak `check-sso` en Playwright: aunque `addInitScript` setea sessionStorage antes de cualquier script, `keycloak.init()` en `main.ts` sobreescribe el estado — el flag `VITE_E2E_SKIP_AUTH` es la solución correcta
- Phase headers en ROADMAP.md son críticos para el tooling — una fase sin `### Phase N:` header queda invisible para `roadmap analyze`

### Cost Observations

- Model mix: 100% Sonnet (executor + verifier + orchestrator)
- Sessions: ~8 conversaciones para completar v1.0
- Notable: subagents con 200k context fresh cada uno — orchestrator se mantuvo lean (~15%)

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | LOC | Timeline |
|-----------|--------|-------|-----|----------|
| v1.0 MVP | 7 | 29 | ~8,016 | 2026-06-06 → 2026-06-08 |
