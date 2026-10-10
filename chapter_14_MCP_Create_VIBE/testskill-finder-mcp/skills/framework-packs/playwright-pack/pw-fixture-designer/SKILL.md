---
name: pw-fixture-designer
description: >-
  Designs custom Playwright test fixtures (auth/session, seeded data, page
  objects) with correct setup/teardown and scope. Use when an SDET says "create
  an auth fixture", "I need a logged-in page fixture", "set up test data
  fixtures", "share a page object via fixture", or wants to stop repeating login
  in every test. Produces a typed fixtures module — a draft to wire in and run.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW Fixture Designer

You design **fixtures the engineer must wire into the config and run** — never a
guaranteed-working setup. You pick the right scope, and always tear down cleanly.

## When to use
- Login/setup is duplicated across specs and should become a fixture.
- Tests need seeded data, a pre-authenticated context, or shared page objects.
- Someone says "design/create a fixture for X".

## Workflow
1. **Classify each fixture's scope.** Per-`test` for isolation (fresh data, a page
   object); `worker`-scoped for expensive shared setup (a storage-state login once
   per worker). Default to test scope unless reuse is safe and read-only.
2. **Prefer `storageState` for auth** — authenticate once (global setup or a worker
   fixture), persist state, and inject it, rather than logging in through the UI in
   every test.
3. **Split setup from teardown** with the `use()` pattern: arrange before `await
   use(value)`, clean up after. Every created resource (DB row, temp user) gets
   deleted or reset.
4. **Type the fixtures** via `test.extend<MyFixtures>()` so consumers get IntelliSense.
5. **List preconditions** — env vars, API endpoints, seed scripts the engineer must
   supply — and mark anything you assumed.

## Output shape
```typescript
import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

type Fixtures = { loginPage: LoginPage; seededOrderId: string };

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));            // test-scoped, fresh per test
  },
  seededOrderId: async ({ request }, use) => {
    const res = await request.post('/api/orders', { data: { sku: 'ABC' } });
    const { id } = await res.json();
    await use(id);                              // arrange
    await request.delete(`/api/orders/${id}`);  // teardown — always clean up
  },
});
export { expect };
```

## Guardrails
- This is a **draft the engineer must wire into `playwright.config.ts` and run** —
  never assume an API route, seed script, or env var exists; list what's required.
- Never fabricate endpoints or credentials; flag them as inputs the team provides.
- Always tear down created resources — a fixture that leaks state causes flakiness.
- Do not put auth in a UI-login-per-test; use `storageState`. No `waitForTimeout`.
