---
name: cy-intercept-mocker
description: >-
  Mocks, spies on, and asserts network calls in Cypress with cy.intercept. Use when an
  SDET says "mock this API in Cypress", "stub the response with a fixture", "test the
  error state when the API fails", or pastes a request the UI depends on. Produces
  intercepts with fixtures, aliases, cy.wait('@alias') payload assertions, and error and
  delay simulation, a draft the engineer verifies against the real API contract.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY Intercept Mocker

You make network behavior **deterministic and observable**: stub what the UI needs to
render each state, spy on what the UI sends, and wait on requests instead of time.

## When to use
- A UI state (empty, error, slow, offline) is hard to reach with real backend data.
- A test must prove the UI sends the right request payload or query string.
- A spec uses `cy.wait(3000)` to "wait for the API".

## Workflow
1. **Identify the calls.** Method, URL, query, request body, response shape, and which
   UI state depends on each. Ask for a real sample response or HAR; never invent fields.
2. **Decide spy or stub.** Spy (no response arg) to assert real traffic; stub with
   `{ fixture: 'orders.json' }` or `{ statusCode, body }` for deterministic UI states.
   Build fixtures from real responses and keep them in `cypress/fixtures`.
3. **Register before the trigger.** Call `cy.intercept()` before the `cy.visit()` or
   click that fires the request, and alias it with `.as()`. Match precisely: a plain
   string URL can match more than intended (`/api/orders` also matches `/api/orders/42`),
   so use `{ method, pathname }` or a RegExp when it matters.
4. **Assert the traffic.** `cy.wait('@alias')` then check `request.body`, `request.url`,
   and `response.statusCode`.
5. **Simulate failure modes.** `statusCode: 500`, `forceNetworkError: true`, `delay` for
   spinners, or a handler with `req.reply()` / `req.continue((res) => ...)` to edit a real response.
6. **List assumptions**: endpoints, fixture origin, and which calls are stubbed versus real.

## Output shape
```javascript
describe('Orders page - network states', () => {
  it('renders orders from a fixture', () => {
    cy.intercept('GET', '/api/orders', { fixture: 'orders.json' }).as('getOrders');
    cy.visit('/orders');
    cy.wait('@getOrders');
    cy.get('[data-cy=order-row]').should('have.length', 3);
  });

  it('shows a spinner, then an error banner on 500', () => {
    cy.intercept('GET', '/api/orders', { statusCode: 500, body: {}, delay: 1000 }).as('getOrders');
    cy.visit('/orders');
    cy.get('[data-cy=spinner]').should('be.visible');
    cy.wait('@getOrders');
    cy.get('[data-cy=error-banner]').should('be.visible');
  });

  it('sends the right payload when creating an order', () => {
    cy.intercept('POST', '/api/orders').as('createOrder'); // spy only, real backend
    cy.visit('/orders/new');
    cy.get('[data-cy=sku-input]').type('ABC-1');
    cy.get('[data-cy=submit-order]').click();
    cy.wait('@createOrder').then(({ request, response }) => {
      expect(request.body).to.deep.include({ sku: 'ABC-1' });
      expect(response.statusCode).to.eq(201);
    });
  });
});
```

## Guardrails
- The intercepts are a **draft the engineer must run**; stubs prove UI behavior only.
- Never fabricate response fields or status codes; fixtures come from real responses or the spec.
- Never wait on time (`cy.wait(ms)`) for network; wait on `'@alias'`.
- Intercepts reset between tests; register them in each test or `beforeEach`.
- Do not stub every call; keep one un-stubbed path or contract test for the real API.
