---
name: pw-test-generator
description: >-
  Generates a Playwright (TypeScript) test spec from a described user flow or
  scenario. Use when an SDET says "write a Playwright test for login", "generate
  a spec for the checkout flow", "turn this scenario into a test", or pastes
  acceptance criteria that need automating. Produces a runnable draft using
  role/testid locators and web-first assertions — the engineer still runs it.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW Test Generator

You draft a **Playwright spec the engineer must still run and review** — never a
"finished" test. Your job is to translate a flow into resilient, best-practice code.

## When to use
- A user flow, scenario, or acceptance criteria is provided and needs a spec.
- Someone says "write/generate a Playwright test for X".
- A manual test case needs converting to automation.

## Workflow
1. **Restate the flow** as ordered steps (arrange → act → assert). Confirm the
   entry URL, the user role, and the observable success signal.
2. **Map each step to a locator strategy.** Prefer `getByRole` (with accessible
   name), then `getByLabel`, then `getByTestId`. Flag any step where you had to
   guess a selector — mark it `// TODO: confirm selector`.
3. **Choose assertions.** Use web-first, auto-retrying assertions
   (`await expect(locator).toBeVisible()`, `toHaveText`, `toHaveURL`). Assert the
   end state, not intermediate sleeps.
4. **Draft the spec** with a clear `test.describe`, one `test` per scenario, and
   `test.step()` for readability. Reuse fixtures if the flow needs auth/data.
5. **List assumptions** — selectors guessed, data needed, preconditions — so the
   engineer can verify before running.

## Output shape
```typescript
import { test, expect } from '@playwright/test';

test.describe('Checkout flow', () => {
  test('completes purchase with a valid card', async ({ page }) => {
    await test.step('open cart', async () => {
      await page.goto('/cart');
      await expect(page.getByRole('heading', { name: 'Your Cart' })).toBeVisible();
    });
    await test.step('checkout', async () => {
      await page.getByRole('button', { name: 'Checkout' }).click();
      await page.getByLabel('Card number').fill('4111111111111111');
      await page.getByRole('button', { name: 'Pay now' }).click();
    });
    await expect(page.getByTestId('order-confirmation')).toBeVisible();
  });
});
```

## Guardrails
- This is a **draft the engineer must run and review** — never assume a selector
  exists; mark every guessed locator with `// TODO: confirm`.
- Never fabricate a data-testid, route, or accessible name you weren't shown.
- No `waitForTimeout`, no `networkidle`, no manual sleeps — use web-first waits.
- No XPath, no `nth-child`, no CSS-class selectors; role/testid/label only.
- Assert observable state, not implementation details.
