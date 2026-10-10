---
name: cy-test-generator
description: >-
  Generates Cypress E2E specs from a manual test case or user story. Use when an SDET
  says "write a Cypress test for this", "automate this test case in Cypress", "convert
  these steps to a cy spec", or pastes test steps with expected results. Produces a spec
  with data-cy selectors and retry-able assertions (no cy.wait(ms)), a draft the
  engineer runs against the real app before merging.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY Test Generator

You turn a test case into a **Cypress spec that waits on app state, never on the clock**.
Every step becomes a command chain and every expected result a retry-able assertion.

## When to use
- A manual test case or acceptance criteria needs an automated Cypress E2E spec.
- An existing spec is full of `cy.wait(2000)` and brittle CSS selectors.
- A new feature needs a smoke spec before the release cut.

## Workflow
1. **Read the case.** Extract preconditions, steps, test data, and each expected result.
   If the URL, role, or data is missing, ask; do not invent routes or accounts.
2. **Map selectors.** Use `[data-cy=...]` first, then `data-testid`, then `cy.contains()`
   for user-visible text. If the attribute is missing, list it as an app change instead
   of falling back to CSS classes, `nth-child`, or XPath.
3. **Set up state fast.** Seed data and log in with `cy.request` or a `cy.session`-based
   command in `beforeEach`; drive the UI only for the flow under test.
4. **Assert with retries.** Use `.should()` chains, which Cypress retries until the
   timeout. Wait for network with `cy.intercept(...).as('x')` plus `cy.wait('@x')`,
   never `cy.wait(<ms>)`.
5. **Keep tests independent.** One behavior per `it`, no dependence on test order, and
   no state passed between `it` blocks through variables.
6. **List assumptions** for the engineer: baseUrl, test user, seeded data, custom
   commands used, and every `data-cy` attribute the app must add.

## Output shape
```javascript
// cypress/e2e/checkout/apply-coupon.cy.js
describe('Checkout - apply coupon', () => {
  beforeEach(() => {
    cy.login(Cypress.env('USER_EMAIL'), Cypress.env('USER_PASSWORD')); // cy.session command
    cy.intercept('POST', '/api/cart/coupon').as('applyCoupon');
    cy.visit('/checkout');
  });

  it('applies a valid coupon and shows the discount', () => {
    cy.get('[data-cy=coupon-input]').type('SAVE10');
    cy.get('[data-cy=apply-coupon]').click();
    cy.wait('@applyCoupon').its('response.statusCode').should('eq', 200);
    cy.get('[data-cy=discount-row]').should('be.visible').and('contain', '10%');
  });

  it('rejects an expired coupon', () => {
    cy.get('[data-cy=coupon-input]').type('EXPIRED2024');
    cy.get('[data-cy=apply-coupon]').click();
    cy.wait('@applyCoupon').its('response.statusCode').should('eq', 422);
    cy.get('[data-cy=coupon-error]').should('be.visible');
  });
});
```

## Guardrails
- The spec is a **draft the engineer must run** against the real app; never claim it passes.
- Never fabricate selectors, routes, status codes, error copy, or test data; ask instead.
- No `cy.wait(<ms>)`: wait on an aliased request or a `.should()` assertion.
- Never assign command results to variables (`const btn = cy.get(...)`); use aliases or `.then()`.
- Keep credentials in `Cypress.env()` and CI secrets, never hard-coded in the spec.
