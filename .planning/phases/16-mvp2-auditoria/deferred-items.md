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

**16-03 update:** `requirements mark-complete AUD-05` also returned `not_found` during 16-03
execution, confirming the same gap. AUD-05 (users/tenants/companies write-path instrumentation)
is functionally complete per 16-03-SUMMARY.md; only the REQUIREMENTS.md traceability entry is
missing.

**16-04 update:** `requirements mark-complete AUD-06` also returned `not_found` during 16-04
execution, confirming the same gap. AUD-06 (Activity Timeline + Diff Viewer frontend) is
functionally complete per 16-04-SUMMARY.md — Phase 16 MVP2 Auditoria is now fully delivered
end-to-end; only the REQUIREMENTS.md traceability entries (AUD-01 through AUD-06) remain to be
added in a dedicated requirements-sync pass.

**16-05 update:** `requirements mark-complete AUD-03 AUD-06` also returned `not_found` during
16-05 execution (gap-closure plan), confirming the same pre-existing condition. AUD-03 (frontend
consumption of the diff endpoint) and AUD-06 (Diff Viewer blocking gap) are now functionally
complete per 16-05-SUMMARY.md — Phase 16 MVP2 Auditoria is fully delivered end-to-end with no
remaining blocking gaps per 16-VERIFICATION.md. The REQUIREMENTS.md traceability entries
(AUD-01 through AUD-06) still remain to be added in a dedicated requirements-sync pass.
