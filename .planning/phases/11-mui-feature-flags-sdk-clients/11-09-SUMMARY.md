---
phase: 11-mui-feature-flags-sdk-clients
plan: 09
subsystem: sdk
tags: [python, httpx, pytest, pytest-asyncio, feature-flags, sdk]

# Dependency graph
requires:
  - phase: 11-mui-feature-flags-sdk-clients
    provides: "Plan 01 backend OPERATORS/_evaluate_rule canonical spec; Plan 06 bootstrap members[] schema and sdk-js evaluator.ts reference"
provides:
  - "Standalone pip-installable backoffice-sdk Python package (sdk/sdk-python)"
  - "evaluate_rule()/evaluate_flag()/OPERATORS - Python port of canonical 7-operator evaluation engine"
  - "FeatureFlagClient with async initialize() (httpx bootstrap fetch + cache), sync evaluate(), async evaluate_remote()"
affects: ["11-10 (SDK WS reconnect builds on FeatureFlagClient cache)"]

# Tech tracking
tech-stack:
  added: ["httpx==0.27.2", "websockets>=12.0", "pytest==8.3.3", "pytest-asyncio==0.24.0"]
  patterns:
    - "sdk/sdk-python is a standalone package (own pyproject.toml + .venv), NOT part of pnpm workspace"
    - "evaluate_flag() operates on bootstrap-cache FlagEntry dicts (DB-free), mirroring sdk-js evaluator.ts any-match segment semantics"
    - "FeatureFlagClient: single async initialize() call; evaluate() synchronous cache-only; evaluate_remote() async fallback via httpx.AsyncClient"

key-files:
  created:
    - sdk/sdk-python/pyproject.toml
    - sdk/sdk-python/.gitignore
    - sdk/sdk-python/src/backoffice_sdk/__init__.py
    - sdk/sdk-python/src/backoffice_sdk/evaluator.py
    - sdk/sdk-python/src/backoffice_sdk/client.py
    - sdk/sdk-python/tests/test_evaluator.py
    - sdk/sdk-python/tests/test_client.py
  modified: []

key-decisions:
  - "Created dedicated sdk/sdk-python/.venv instead of installing into the global Python environment, to avoid downgrading globally-installed httpx/pytest/pytest-asyncio (which conflicted with google-genai/litellm)"
  - "evaluator.py evaluate_flag() takes a single bootstrap FlagEntry dict + user dict (Plan 06/sdk-js shape), distinct from backend service.py evaluate_flag() which takes a list of ORM flags + scope context - both share the same OPERATORS/_evaluate_rule core"

patterns-established:
  - "Pattern: sdk-python tests mock httpx.AsyncClient.get/.post via unittest.mock.patch.object + AsyncMock, no respx dependency needed"

requirements-completed: [SDK-11]

# Metrics
duration: 16min
completed: 2026-06-10
---

# Phase 11 Plan 09: sdk-python evaluator + FeatureFlagClient Summary

**Standalone `backoffice-sdk` Python package with a 7-operator evaluator (parity with backend OPERATORS and sdk-js evaluator.ts) and an async `FeatureFlagClient` (httpx bootstrap fetch, sync cache evaluate, async remote evaluate fallback)**

## Performance

- **Duration:** 16 min
- **Started:** 2026-06-10T13:00:00Z
- **Completed:** 2026-06-10T13:16:01Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- `sdk/sdk-python` scaffolded as a standalone, pip-installable package (`pip install -e ".[dev]"` in its own `.venv`), outside the pnpm workspace
- `evaluator.py`: `OPERATORS` dict with 7 entries (equals/in/notIn/contains/regex/greaterThan/lessThan), `evaluate_rule()` and `evaluate_flag()` ported from `backend/app/domains/feature_flags/service.py` and `sdk-js/src/evaluator.ts`, including manual segment `members[]` and rule_based segment any-match semantics
- `FeatureFlagClient`: `async initialize()` (httpx bootstrap fetch -> cache), synchronous cache-only `evaluate()`, `async evaluate_remote()` (POST `/sdk/evaluate`), plus `invalidate()`/`replace_cache()` helpers for Plan 10's WS reconnect
- 40 pytest tests (33 evaluator + 7 client) all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold sdk-python package** - `69c97d4` (chore)
2. **Task 2: Implement evaluator.py (RED)** - `61c755a` (test)
2. **Task 2: Implement evaluator.py (GREEN)** - `983107b` (feat) *(see Deviations - commit message attribution affected by parallel-execution race)*
3. **Task 3: Implement client.py (RED)** - `e99d4d0` (test)
3. **Task 3: Implement client.py (GREEN)** - `82210d5` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `sdk/sdk-python/pyproject.toml` - Standalone package definition (httpx, websockets deps; pytest/pytest-asyncio dev extras; pytest asyncio_mode=auto)
- `sdk/sdk-python/.gitignore` - Excludes `.venv/`, `__pycache__/`, `.pytest_cache/`
- `sdk/sdk-python/src/backoffice_sdk/__init__.py` - Exports `FeatureFlagClient`, `evaluate_rule`, `evaluate_flag`, `OPERATORS`
- `sdk/sdk-python/src/backoffice_sdk/evaluator.py` - 7-operator `OPERATORS` dict, `evaluate_rule()`, `evaluate_flag()` (bootstrap-cache entry evaluation)
- `sdk/sdk-python/src/backoffice_sdk/client.py` - `FeatureFlagClient` with `initialize()`/`evaluate()`/`evaluate_remote()`/`invalidate()`/`replace_cache()`
- `sdk/sdk-python/tests/test_evaluator.py` - 33 tests covering all 7 operators (ported from `backend/tests/test_feature_flags_eval.py`) and `evaluate_flag` segment/rule cases
- `sdk/sdk-python/tests/test_client.py` - 7 tests covering `initialize()`/`evaluate()`/`evaluate_remote()`/`invalidate()`/`replace_cache()` with mocked httpx

## Decisions Made
- Used a dedicated `sdk/sdk-python/.venv` (created via `python -m venv`) rather than installing into the global Python environment. The first `pip install -e ".[dev]"` attempt (no venv) downgraded globally-installed `httpx` 0.28.1->0.27.2 and `pytest`/`pytest-asyncio`, breaking `google-genai`/`litellm` dependency constraints. Restored global versions, then created an isolated venv for sdk-python — matches the project's existing `backend/venv` convention.
- `evaluate_flag(entry, user)` in sdk-python operates on a single bootstrap `FlagEntry` dict (Plan 06/sdk-js shape: `{enabled, rules, segments, default_val, scope}`), NOT the backend's `evaluate_flag(flags: list, context: dict)` which does scope-priority winner selection across multiple ORM flags. Both share identical `OPERATORS`/`_evaluate_rule` semantics — this is the documented spec in the plan interfaces (sdk-js `evaluateFlag` is the direct template).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Global pip install conflict avoided via dedicated venv**
- **Found during:** Task 1
- **Issue:** `pip install -e ".[dev]"` against the global Python 3.14 environment downgraded `httpx`/`pytest`/`pytest-asyncio` to versions pinned by `pyproject.toml`, producing dependency-resolver conflicts with `google-genai` and `litellm` (unrelated globally-installed tools).
- **Fix:** Restored global package versions (`pip install --upgrade httpx==0.28.1 pytest==9.0.3 pytest-asyncio==1.3.0`), then created `sdk/sdk-python/.venv` and reinstalled `backoffice-sdk` there in editable mode. All subsequent verification (`pytest`, `import backoffice_sdk`) run via `.venv/Scripts/python.exe`.
- **Files modified:** none (environment-only change); `sdk/sdk-python/.gitignore` added to exclude `.venv/`
- **Commit:** `69c97d4`

### Process Note (not a code deviation)

**Concurrent execution git index race with Plan 11-07**

Plan 11-09 ran in parallel with Plan 11-07 (per orchestrator wave plan), both operating on the same git working tree/index. During Task 2's commit, the parallel 11-07 executor's staged final-docs files (`.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `11-07-SUMMARY.md`) were transiently present in the shared index alongside this plan's `evaluator.py` change. After a `git reset --soft HEAD~1` + `git restore --staged` to separate the two plans' changes, a second race occurred: the 11-07 executor's own commit (`983107b`, message "docs(11-07): complete FeatureFlagClient core plan") ended up containing this plan's `evaluator.py` diff instead of 11-07's intended `.planning/*` diff (which 11-07 then re-committed separately as `8811a86`).

Net effect: `evaluator.py`'s implementation IS correctly committed and present in the repo (verified via `git diff HEAD -- sdk/sdk-python/` = empty, `git log -- sdk/sdk-python/src/backoffice_sdk/evaluator.py` shows it). Only the commit *message* attribution for that one diff is "docs(11-07)..." instead of "feat(11-09)...". No code or `.planning/*` content was lost — both plans' final states are correct on disk and in history. Subsequent commits (Task 3) used `git commit --only <file>` to avoid repeating the race.

---

**Total deviations:** 1 auto-fixed (1 blocking - environment isolation), 1 process note (no code/data impact)
**Impact on plan:** No impact on deliverables - all 40 tests pass, package is correctly pip-installable, pnpm-workspace.yaml unchanged. The git history has one commit with a mismatched message (983107b) but correct content.

## Issues Encountered
- pytest-asyncio 0.24.0 emits `DeprecationWarning` for `asyncio.get_event_loop_policy`/`set_event_loop_policy` under Python 3.14 (pre-existing version-pin from backend/requirements.txt, matches the spec's pinned versions; out of scope per scope boundary - tests pass, warnings only).

## User Setup Required
None - no external service configuration required. `sdk/sdk-python/.venv` is local and gitignored; CI/other environments should run `python -m venv .venv && .venv/Scripts/python.exe -m pip install -e ".[dev]"` (or `bin/activate` on POSIX) from `sdk/sdk-python`.

## Next Phase Readiness
- `FeatureFlagClient` cache (`self.cache`, `replace_cache()`, `invalidate()`) is ready for Plan 10's WebSocket reconnect to push live updates.
- `evaluator.py` OPERATORS/evaluate_rule/evaluate_flag are verified at parity with backend (Plan 01) and sdk-js (Plan 06) for the 4-way consistency requirement (backend, sdk-js, sdk-python, frontend RuleSimulator).
- No blockers.

---
*Phase: 11-mui-feature-flags-sdk-clients*
*Completed: 2026-06-10*

## Self-Check: PASSED

All 7 created files found on disk; all 5 referenced commits (69c97d4, 61c755a, 983107b, e99d4d0, 82210d5) found in git history.
