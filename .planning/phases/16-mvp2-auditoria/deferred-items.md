# Deferred Items: Phase 16 MVP2 Auditoria

## REQUIREMENTS.md registration gap (AUD-01 through AUD-06)

`node gsd-tools.cjs requirements mark-complete AUD-01 AUD-02 AUD-03` returned `not_found` for
all three IDs during 16-01 execution — `AUD-01`/`AUD-02`/`AUD-03` (and presumably AUD-04/05/06)
are not present in `.planning/REQUIREMENTS.md`. This matches the registration gap already noted
in `ROADMAP.md` for Phase 16 ("registration gap vs REQUIREMENTS.md noted in phase
deferred-items.md, same as Phases 14/15").

**Status:** Pre-existing condition, out of scope for 16-01 (Rule: SCOPE BOUNDARY — only auto-fix
issues directly caused by the current task's changes).

**Action needed:** Add AUD-01 through AUD-06 to `.planning/REQUIREMENTS.md` traceability table
(separately, likely during a later plan or a dedicated requirements-sync pass), then re-run
`requirements mark-complete AUD-01 AUD-02 AUD-03` for 16-01's completed requirements.
