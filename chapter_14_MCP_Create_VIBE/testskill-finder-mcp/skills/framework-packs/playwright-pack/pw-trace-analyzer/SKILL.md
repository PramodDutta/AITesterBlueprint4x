---
name: pw-trace-analyzer
description: >-
  Analyzes a Playwright trace.zip or test failure to pinpoint the root cause. Use
  when an SDET says "read this trace", "why did this test fail", "analyze the
  trace.zip", "my CI run failed — what broke", or pastes an error + trace. Reads
  the timeline, isolates the failing action/assertion, and recommends the fix — a
  diagnosis the engineer confirms by re-running.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW Trace Analyzer

You turn a trace or failure into a **root-cause diagnosis the engineer must
confirm by re-running** — a trace shows what happened, not always why it's wrong.

## When to use
- A `trace.zip` or Playwright error/stack is available and needs interpreting.
- A CI failure needs triage before anyone re-runs blindly.
- Someone says "read/analyze this trace", "why did this fail".

## Workflow
1. **Open the trace** — recommend `npx playwright show-trace trace.zip` (or the CI
   report's trace link). If only an error string is provided, work from that and
   ask for the trace to go deeper.
2. **Locate the failing step** on the timeline — the last action/assertion before
   the error, its call log, and the DOM snapshot at that moment.
3. **Read the snapshot + call log** to classify the cause: element not found /
   not visible, strict-mode multi-match, navigation not settled, wrong assertion,
   backend error (check the Network tab), or a race with an animation/async render.
4. **Correlate signals** — console errors, failed requests, and the before/after
   snapshots — to separate a test bug from a genuine product bug.
5. **Recommend the fix** with confidence level, and the exact command to reproduce.

## Output shape
```
Trace analysis
  Failing step : expect(getByTestId('total')).toHaveText('$120') @ 00:07.3
  Snapshot     : element shows '$0' — cart total not yet updated
  Network      : PATCH /api/cart → 200 fired AFTER the assertion (race)
  Root cause   : assertion ran before the cart-update response settled
  Fix          : await the response, then assert (web-first already retries text)
  Reproduce    : npx playwright test cart.spec.ts --trace on --repeat-each=10
```
```typescript
// await the signal the UI depends on, then let the web-first assertion retry
await page.getByRole('button', { name: 'Add' }).click();
await page.waitForResponse((r) => r.url().includes('/api/cart') && r.ok());
await expect(page.getByTestId('total')).toHaveText('$120');
```

## Guardrails
- The diagnosis is a **hypothesis the engineer must confirm by re-running** — never
  declare it solved without a trace-backed reproduce step.
- Read the trace evidence; **never fabricate** timeline steps, snapshots, or network
  calls you weren't shown. If the trace wasn't provided, say what you'd need.
- Distinguish test bug vs. product bug — don't "fix" a real regression by loosening
  the test. Never recommend `waitForTimeout` as the remedy.
