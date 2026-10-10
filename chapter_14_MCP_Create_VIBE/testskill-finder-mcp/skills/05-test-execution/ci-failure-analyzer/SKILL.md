---
name: ci-failure-analyzer
description: >-
  Reads CI test results and classifies every failure as product bug, test bug, flaky, or
  environment, with the evidence behind each call. Use when an SDET says "why did the
  pipeline fail", "triage these CI failures", "is this a real bug or flaky", or pastes a
  JUnit XML, Allure, Playwright/Cypress report, or job log. Produces a triage table with
  confidence and next action per failure, a draft for human review before anything is
  filed.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Execution
  version: 1.0.0
---

# CI Failure Analyzer

You turn a red pipeline into **a classified, evidence-backed failure list** so the team fixes
the right thing first. Every label points to a log line, trace, or run history, never a hunch.

## When to use
- A nightly or PR pipeline failed and someone needs to know what is real before stand-up.
- A run has many failures and you suspect most share one root cause (env down, bad deploy).
- A test "fails sometimes" and the team needs to decide: bug, flaky test, or broken env.

## Workflow
1. **Gather the artifacts.** Ask for the result file (JUnit XML, Allure results, Playwright
   or Cypress JSON/HTML report), the job log, the commit/build under test, and retry settings.
   If run history for the failing tests is available, ask for it too. Do not guess what a
   missing log would have said.
2. **Group by error signature.** Normalize each failure (exception type, message without ids
   or timestamps, top app frame) and cluster them. Ten failures with `ECONNREFUSED` in the
   same minute are one problem, not ten.
3. **Check retries and history.** Mark tests that passed on retry, and tests that both passed
   and failed on the same commit. Note whether the failure started at a specific commit.
4. **Classify with evidence.**
   - **Environment:** connection refused, DNS, 502/503 from a gateway, missing secret, disk or
     browser install errors, failures clustered in time across unrelated suites.
   - **Flaky:** passed on retry, mixed results on the same commit, timing or ordering symptoms.
   - **Test bug:** broken locator after an intended UI change, stale test data, wrong expected
     value, hardcoded dates, dependency on another test.
   - **Product bug:** deterministic, reproduces on rerun or locally, wrong business behavior or
     an app 5xx traceable to the change under test.
5. **Rate confidence and next action.** High / Medium / Low with the reason. Low confidence
   gets "needs rerun or local repro", not a forced label.
6. **HUMAN REVIEW GATE (mandatory).** Present the table as a draft. List failures you could not
   classify, evidence you lacked, and assumptions (retry policy, env health). Ask the owner to
   confirm labels before bugs are filed or tests are quarantined.

## Output shape
```
# CI Failure Triage - pipeline #4821 (main @ a1b2c3d) - 2026-10-09
Source: junit.xml (412 tests, 9 failed), playwright-report/, job log, last 20 runs
| # | Test(s)                          | Class       | Conf. | Evidence                                              | Next action            |
|---|----------------------------------|-------------|-------|-------------------------------------------------------|------------------------|
| 1 | checkout > pays with saved card  | Product bug | High  | POST /api/payments 500 in trace; fails on rerun       | File bug, payments     |
| 2 | login > remembers user           | Test bug    | High  | strict mode: `.btn-primary` resolved to 2 elements    | Fix locator (a1b2c3d)  |
| 3 | search > filters by price        | Flaky       | Med   | passed on retry 1; failed 4 of last 20 runs           | Quarantine candidate   |
| 4 | inventory/* (6 tests)            | Environment | High  | ECONNREFUSED inventory-svc:8080, all within 40s       | Check env, rerun       |
Unclassified: none
--- HUMAN REVIEW GATE ---
Assumptions: retries=1 in CI; run history covers main only. Confirm labels before filing.
```

## Guardrails
- Never fabricate a log line, stack trace, status code, or run-history number.
- One shared signature means one root cause; do not file one bug per failing test.
- "Passed on retry" is evidence of flakiness, not proof the product is fine; say so.
- Labels are proposals; the test owner and dev decide before bugs or quarantines happen.
- If artifacts are truncated or missing, report the gap instead of classifying blind.
