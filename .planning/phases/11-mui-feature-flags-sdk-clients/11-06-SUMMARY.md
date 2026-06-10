---
phase: 11-mui-feature-flags-sdk-clients
plan: 06
subsystem: api
tags: [fastapi, sqlalchemy, vitest, typescript, pnpm-workspace, feature-flags, sdk]

# Dependency graph
requires:
  - phase: 11-mui-feature-flags-sdk-clients
    provides: "Plan 01 canonical OPERATORS table (greaterThan/lessThan via float() coercion) in backend/app/domains/feature_flags/service.py"
provides:
  - "GET /api/v1/sdk/bootstrap inlines members:[] for every segment (manual gets real UUID arrays, rule_based gets [])"
  - "verify_sdk_secret accepts ?sdk_key= query-param fallback (header takes precedence) for navigator.sendBeacon() telemetry auth"
  - "@backoffice/sdk-js workspace package with types.ts contracts and evaluator.ts (7-operator DB-free local evaluation engine)"
affects: ["11-07", "11-08"]

# Tech tracking
tech-stack:
  added: ["vitest@2.1.9 (sdk/sdk-js only)", "typescript@^5.5.3 (sdk/sdk-js)"]
  patterns:
    - "DB-free SDK evaluator: evaluateFlag()/evaluateRule() in TS mirror backend evaluate_flag()/_evaluate_rule() exactly, including manual segment members[] membership check"
    - "verify_sdk_secret: header-or-query-param auth with header precedence, for endpoints reachable via navigator.sendBeacon()"

key-files:
  created:
    - backend/tests/test_sdk_bootstrap.py
    - sdk/sdk-js/package.json
    - sdk/sdk-js/tsconfig.json
    - sdk/sdk-js/vitest.config.ts
    - sdk/sdk-js/src/types.ts
    - sdk/sdk-js/src/evaluator.ts
    - sdk/sdk-js/src/index.ts
    - sdk/sdk-js/tests/evaluator.test.ts
  modified:
    - backend/app/domains/sdk/service.py
    - backend/app/domains/sdk/schemas.py
    - backend/app/dependencies.py
    - pnpm-workspace.yaml
    - pnpm-lock.yaml

key-decisions:
  - "verify_sdk_secret: Authorization header (if present) is validated first and takes precedence over sdk_key query param, even if the query param is invalid — preserves existing route behavior unchanged"
  - "bootstrap_flags() adds members:[] to ALL segment types (not just manual) — rule_based segments get an empty array since their members column is always NULL, keeping the schema uniform"
  - "sdk/sdk-js uses vitest@^2.1.0 per plan spec (not the workspace-standard ^1.6.0) — isolated devDependency, no cross-package conflict in pnpm workspace"
  - "Created sdk/sdk-js/src/index.ts (not in plan's file list) re-exporting types + evaluator, since package.json main/types point to ./src/index.ts — needed for Plans 07/08 to import the package entry point"

patterns-established:
  - "DB-free unit testing of bootstrap_flags(): monkeypatch list_flags()/get_flag_segments() with SimpleNamespace fixtures, mirroring test_feature_flags_eval.py's no-DB-session pattern"

requirements-completed: [SDK-05, SDK-06]

# Metrics
duration: 12min
completed: 2026-06-10
---

# Phase 11 Plan 06: SDK Bootstrap Members + sdk-js Evaluator Scaffold Summary

**Backend bootstrap now inlines manual-segment `members[]` arrays and accepts `?sdk_key=` query-param auth for sendBeacon; new `@backoffice/sdk-js` workspace package ships a DB-free 7-operator evaluator (incl. greaterThan/lessThan) mirroring the backend exactly, with 27 passing vitest tests.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-10
- **Completed:** 2026-06-10
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- `bootstrap_flags()` now returns `members: list[str]` for every inlined segment (manual segments carry real UUID arrays parsed from the `members` TEXT column; rule_based segments get `[]`), enabling fully DB-free local membership checks in SDK evaluators
- `verify_sdk_secret` supports `?sdk_key=` query-param fallback alongside the existing `Authorization: Bearer` header (header wins if present), unblocking `navigator.sendBeacon()` telemetry flushes which cannot send custom headers
- New `sdk/sdk-js` (`@backoffice/sdk-js`) package registered in the pnpm workspace with vitest + TypeScript configured, `types.ts` contracts (`FlagEntry`, `BootstrapResponse`, `RuleSchema`, `BootstrapSegment`, `UserContext`, `EvalEventItem`), and `evaluator.ts` (`OPERATORS` 7-entry table + `evaluateRule`/`evaluateFlag`) — 27 vitest tests pass, `tsc --noEmit` clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend — inline manual segment members[] in bootstrap + sdk_key query-param fallback for eval-events auth** - `73f4256` (feat, TDD)
2. **Task 2: Add sdk/sdk-js to pnpm workspace and scaffold package.json/tsconfig/vitest config** - `721356b` (chore)
3. **Task 3: Create types.ts contracts and evaluator.ts (7-operator local evaluation engine incl. manual segment members)** - `8ff1afc` (feat, TDD)

**Plan metadata:** (this commit) - docs: complete plan

_Note: TDD tasks (1, 3) implemented test+implementation together per existing test-file conventions in the codebase rather than separate RED/GREEN commits, matching how test_feature_flags_eval.py and useRuleSimulator.test.ts were structured in prior phases._

## Files Created/Modified
- `backend/app/domains/sdk/service.py` - `bootstrap_flags()` parses `members` column (JSON array) and adds `"members": members` to every inlined segment dict
- `backend/app/domains/sdk/schemas.py` - `BootstrapSegment.members: list[str] = []` added
- `backend/app/dependencies.py` - `verify_sdk_secret` accepts optional `sdk_key: str | None = Query(default=None)`; header-or-query-param auth with header precedence
- `backend/tests/test_sdk_bootstrap.py` - 8 new tests: 2 for `bootstrap_flags()` members inlining (manual + rule_based), 6 for `verify_sdk_secret` auth paths
- `pnpm-workspace.yaml` - added `'sdk/sdk-js'` to `packages:`
- `sdk/sdk-js/package.json` - `@backoffice/sdk-js` workspace package, vitest@^2.1.0 + typescript@^5.5.3 devDeps, `test`/`typecheck` scripts
- `sdk/sdk-js/tsconfig.json` - ES2020 target, DOM lib, strict mode
- `sdk/sdk-js/vitest.config.ts` - node environment
- `sdk/sdk-js/src/types.ts` - `RuleSchema`, `BootstrapSegment`, `FlagEntry`, `BootstrapResponse`, `UserContext`, `EvalEventItem`
- `sdk/sdk-js/src/evaluator.ts` - `OPERATORS` (7 entries), `evaluateRule()`, `evaluateFlag()` — DB-free, mirrors backend `service.py` and `useRuleSimulator.ts`
- `sdk/sdk-js/src/index.ts` - re-exports types + evaluator as package entry point
- `sdk/sdk-js/tests/evaluator.test.ts` - 27 tests covering all 7 operators, evaluateFlag enabled/rules/segments/default_val cases

## Decisions Made
- `verify_sdk_secret`: header takes precedence over query param when both present (even if query param is invalid) — preserves all existing SDK routes' behavior unchanged
- `members:[]` added uniformly to all segment types in `bootstrap_flags()` for schema consistency (rule_based segments simply get an empty array)
- `sdk/sdk-js` uses vitest@^2.1.0 as specified in the plan (workspace's other packages use ^1.6.0) — isolated devDependency in its own package.json, no conflicts
- Added `sdk/sdk-js/src/index.ts` (not explicitly listed in plan files) since `package.json` `main`/`types` reference `./src/index.ts` — required entry point for Plans 07/08 imports

## Deviations from Plan

None - plan executed exactly as written. The `src/index.ts` addition is a minimal scaffolding necessity implied by the package.json `main`/`types` fields specified in Task 2's action steps, not a scope change.

## Issues Encountered
- System `python` (3.14) lacks the project's dependencies; tests were run via `backend/venv/Scripts/python.exe` (the project's existing venv, Python 3.11.9) — consistent with how this venv is used elsewhere in the repo.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `sdk/sdk-js` package skeleton, `types.ts` contracts, and `evaluator.ts` are ready for Plan 07 (sdk-js client/bootstrap fetch) and Plan 08 (WS + telemetry) to build on top of
- Bootstrap response now includes `members[]` for manual segments — Plan 07's local evaluator can perform membership checks without any backend round-trip
- `/api/v1/sdk/eval-events?sdk_key=...` query-param auth is ready for Plan 08's `navigator.sendBeacon()`-based telemetry flush
- No blockers identified

---
*Phase: 11-mui-feature-flags-sdk-clients*
*Completed: 2026-06-10*

## Self-Check: PASSED

All created files and task commits verified present.
