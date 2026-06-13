---
phase: 21
slug: aplicar-el-labeling-en-esta-aplicacion-para-la-pagina-de-ini
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-13
---

# Phase 21 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest + pytest + Playwright |
| **Config file** | `portal/package.json`, `sdk/sdk-js/package.json`, `portal/playwright.config.ts` |
| **Quick run command** | `pnpm --filter @backoffice/portal test -- --run` |
| **Full suite command** | `pnpm --filter @backoffice/portal build && pnpm --filter @backoffice/sdk-js test -- tests/labels.test.ts` |
| **Estimated runtime** | ~60 seconds excluding Playwright |

## Sampling Rate

- **After every task commit:** Run the task's focused Vitest or pytest command.
- **After every plan wave:** Run `pnpm --filter @backoffice/portal build`.
- **Before `$gsd-verify-work`:** Portal build, SDK labels regression, backend focused tests, and login Playwright spec must be green.
- **Max feedback latency:** 90 seconds for automated unit/build feedback.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | LOGIN-LBL-01, LOGIN-LBL-08 | T-21-01 | Seed uses existing tenant lookup and contains no credential data | integration | `backend/venv/Scripts/python.exe -m pytest backend/tests/test_labels_sdk_router.py -q` | Yes | pending |
| 21-02-01 | 02 | 1 | LOGIN-LBL-02, LOGIN-LBL-03, LOGIN-LBL-04 | T-21-02 | Missing env and network failures cannot block login | unit | `pnpm --filter @backoffice/portal test -- --run` | Yes | pending |
| 21-02-02 | 02 | 1 | LOGIN-LBL-06, LOGIN-LBL-07 | T-21-03 | Late hydration and missing reports do not expose SDK sentinel to users | unit | `pnpm --filter @backoffice/portal test -- --run` | Yes | pending |
| 21-03-01 | 03 | 2 | LOGIN-LBL-05, LOGIN-LBL-08 | T-21-04 | Raw backend auth errors are not rendered | build/unit | `pnpm --filter @backoffice/portal build` | Yes | pending |
| 21-03-02 | 03 | 2 | LOGIN-LBL-04, LOGIN-LBL-06, LOGIN-LBL-08 | T-21-05 | Login remains usable when SDK/BFF/WS are unavailable | e2e | `pnpm --filter @backoffice/portal exec playwright test tests/visual/login.spec.ts` | Yes | pending |

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

## Manual-Only Verifications

All phase behaviors have automated verification. Final visual comparison may be reviewed when Playwright snapshots change intentionally.

## Validation Sign-Off

- [x] All tasks have automated verification or existing infrastructure.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing references.
- [x] No watch-mode flags.
- [x] Feedback latency target is under 90 seconds.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved 2026-06-13
