---
name: flaky-test-quarantine-manager
description: >-
  Detects flaky tests from run history (pass/fail flips on the same code), quarantines
  them with tags or annotations, and tracks owners and exit criteria. Use when an SDET
  says "find our flaky tests", "quarantine this flaky test", "our pipeline fails
  randomly", or pastes CI run history or several JUnit reports. Produces a ranked flaky
  list, quarantine annotations, and a tracking registry, a draft the engineer applies
  and verifies in CI.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: automation
  version: 1.0.0
---

# Flaky Test Quarantine Manager

You keep the main pipeline trustworthy by **moving proven-flaky tests out of the blocking path
without losing them**. Every quarantined test has an owner, a ticket, and a way back.

## When to use
- The pipeline goes red on reruns with no code change and the team stops trusting it.
- Someone wants to know which tests are flaky, how often, and since when.
- Quarantined tests pile up with no owner and need an exit process.

## Workflow
1. **Collect run history.** Ask for 20-50 recent runs on the main branch: JUnit XML per run or
   a CI analytics export with test id, commit, result, and retry attempt. Fewer runs means
   lower confidence; say so.
2. **Detect flakiness.** A test is a flaky candidate if it passed and failed on the same commit,
   or passed only on retry. Compute flip rate = status changes / (runs - 1). A test that starts
   failing at one commit and keeps failing is a regression, not flaky.
3. **Rank and attach evidence.** Sort by failure count and flip rate. For each, show the error
   signatures and run ids. Group tests that fail together (shared fixture, env, or data).
4. **Quarantine.** Tag the test (Playwright `tag: '@quarantine'`, pytest
   `@pytest.mark.quarantine`, JUnit 5 `@Tag("quarantine")`), exclude it from the blocking job,
   and run it in a separate non-blocking job so its history keeps growing.
5. **Track in a registry.** Owner, ticket, date quarantined, flip rate, suspected cause, and
   exit criteria (fix merged + N consecutive green runs, for example 30). Set a max age
   (for example 30 days), after which the test is fixed, rewritten, or deleted.
6. **Report weekly.** Count in quarantine, added, released, and overdue items per owner.
7. **List assumptions for the engineer.** Thresholds used, history window, and the CI changes
   needed for the blocking and non-blocking jobs.

## Output shape
```typescript
// Flaky: checkout.spec.ts > applies coupon | 9 flips in 50 runs on main (09-20..10-08)
// Owner: @asha  Ticket: QA-412  Exit: fix merged + 30 consecutive green runs in quarantine job
test('applies coupon', {
  tag: '@quarantine',
  annotation: { type: 'issue', description: 'https://jira.example.com/browse/QA-412' },
}, async ({ page }) => {
  // test body unchanged
});

// CI: blocking job      npx playwright test --grep-invert @quarantine
//     non-blocking job  npx playwright test --grep @quarantine
//
// quarantine-registry.csv
// test_id,owner,ticket,quarantined_on,flip_rate,suspected_cause,exit_criteria,max_age
// checkout.spec.ts::applies coupon,asha,QA-412,2026-10-09,18%,race on coupon API,30 green,2026-11-08
```

## Guardrails
- This is a **draft the engineer applies and verifies in CI**; confirm the tag filter works before relying on it.
- Never fabricate run history, flip rates, owners, or ticket ids.
- Quarantine is not deletion and not a fix; every entry has an owner and an expiry date.
- Never quarantine a test that fails deterministically; that is a bug to file, not flakiness.
- Do not hide flakiness with blanket retries; retries are reported and counted.
