# Deferred Items — Phase 14

## From Plan 14-03

- **REQUIREMENTS.md does not contain LST-02/TGT-03 entries** — `requirements mark-complete LST-02 TGT-03` returned `not_found`. Same pre-existing planning gap as LST-01/CMP-01 noted below (Plans 14-01/14-04). Left unmarked; flagged here for phase-completion verification to register/reconcile LST-02/TGT-03 (and LST-01/CMP-01) in REQUIREMENTS.md.

## From Plan 14-04

- **REQUIREMENTS.md does not contain LST-01/LST-02 entries** — `requirements mark-complete LST-01 LST-02` returned `not_found`. These requirement IDs are referenced in 14-04-PLAN.md frontmatter but were not registered in `.planning/REQUIREMENTS.md` during phase planning.
  - Action: out of scope for 14-04 (pre-existing planning gap). Left unmarked; flagged here for phase-completion verification to register/reconcile LST-01/LST-02 in REQUIREMENTS.md.

## From Plan 14-01

- **`backend/tests/test_feature_flags_router.py` fails to collect** — `ImportError: cannot import name '_validate_update_target' from 'app.domains.feature_flags.router'`.
  - Cause: pre-existing uncommitted working-tree changes to `backend/app/domains/feature_flags/router.py` and `backend/tests/test_feature_flags_router.py` (out of scope for 14-01 — these files are not in 14-01's `files_modified` list).
  - Verified: on a clean tree (changes stashed), this test file passes (8/8).
  - Action: out of scope for 14-01, not fixed. Likely belongs to an in-progress later plan (14-03+ context). Full backend suite excluding this file: 117/117 passed (includes new `test_companies_router.py`, 15/15).

- **REQUIREMENTS.md does not contain a CMP-01 entry** — `requirements mark-complete CMP-01` returned `not_found`. CMP-01 is referenced in 14-01-PLAN.md and 14-06-PLAN.md frontmatter but was not registered in `.planning/REQUIREMENTS.md` during phase planning (same pre-existing planning gap as LST-01/LST-02, see 14-04 entry above).
  - Action: out of scope for 14-01, not fixed. Left unmarked; flagged here for phase-completion verification to register/reconcile CMP-01 (and LST-01/LST-02) in REQUIREMENTS.md.
