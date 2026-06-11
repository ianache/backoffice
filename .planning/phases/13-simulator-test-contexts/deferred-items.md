# Deferred Items — Phase 13 (Simulator Test Contexts)

## REQUIREMENTS.md missing SIM-* requirement IDs

- **Found during:** 13-02 execution (`requirements mark-complete SIM-03`)
- **Issue:** `.planning/REQUIREMENTS.md` does not contain `SIM-01`/`SIM-03`/etc. requirement IDs from Phase 13's plan frontmatter (`requirements: [SIM-03]`). `requirements mark-complete SIM-03` returned `not_found`. The same gap existed for Plan 13-01 (`requirements-completed: [SIM-01]`), so this is pre-existing — not caused by 13-02's changes.
- **Scope:** Out of scope for 13-02 (no files this plan touches relate to REQUIREMENTS.md structure).
- **Suggested fix:** When Phase 13 was added to ROADMAP.md (2026-06-11), the corresponding SIM-01..SIM-04 requirement entries should also have been added to REQUIREMENTS.md's traceability table. A future plan or manual edit should backfill these entries so `requirements mark-complete` can check them off.
