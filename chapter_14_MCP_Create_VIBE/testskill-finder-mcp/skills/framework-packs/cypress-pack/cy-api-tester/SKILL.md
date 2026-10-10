---
name: cy-api-tester
description: >-
  Writes API tests in Cypress with cy.request and combines API setup with UI checks.
  Use when an SDET says "write API tests in Cypress", "test this endpoint with
  cy.request", "create the data through the API and check it in the UI", or pastes an
  endpoint spec or curl command. Produces happy-path, auth, and negative tests asserting
  status, headers, and body, a draft the engineer runs against a real environment.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY API Tester

You draft **API checks that run in milliseconds and set up UI tests without clicking
through forms**, covering the happy path and the failures testers forget.

## When to use
- An endpoint or OpenAPI snippet needs fast coverage inside an existing Cypress project.
- A UI test spends most of its time creating data that one API call could create.
- A UI action should be verified by checking backend state through the API.

## Workflow
1. **Extract the contract.** Method, path, auth scheme, request body, status codes, and
   response shape. If any of it is unknown, ask; do not invent fields or endpoints.
2. **Design the case matrix.** Happy path, auth (missing or expired token -> 401/403),
   validation (bad body -> 400/422), unknown id -> 404, and boundary values.
3. **Call `cy.request` correctly.** Pass an options object (`method`, `url`, `headers`,
   `body`, `qs`). `cy.request` fails the test on non-2xx/3xx responses, so set
   `failOnStatusCode: false` for every expected error case.
4. **Assert precisely.** Status, `content-type` header, and body shape; check presence
   and type for generated ids and timestamps instead of exact values.
5. **Combine API and UI.** Create data with `cy.request`, then `cy.visit` and assert it
   renders; or act in the UI and confirm backend state with a follow-up request. Use
   unique data per test and clean up what you create.
6. **List assumptions**: baseUrl, token source (`Cypress.env`), seed data, cleanup route.

## Output shape
```javascript
const auth = () => ({ Authorization: `Bearer ${Cypress.env('API_TOKEN')}` });

describe('API: /api/orders', () => {
  it('creates an order', () => {
    cy.request({ method: 'POST', url: '/api/orders', headers: auth(), body: { sku: 'ABC-1', qty: 2 } })
      .then((res) => {
        expect(res.status).to.eq(201);
        expect(res.headers['content-type']).to.include('application/json');
        expect(res.body).to.have.property('id').that.is.a('string');
        expect(res.body).to.include({ sku: 'ABC-1', qty: 2 });
      });
  });

  it('rejects a request without a token', () => {
    cy.request({ method: 'POST', url: '/api/orders', body: { sku: 'ABC-1' }, failOnStatusCode: false })
      .its('status').should('eq', 401);
  });

  it('shows an API-created order in the UI', () => {
    const sku = `UI-${Date.now()}`;
    cy.request({ method: 'POST', url: '/api/orders', headers: auth(), body: { sku, qty: 1 } })
      .its('body.id')
      .then((id) => {
        cy.login(Cypress.env('USER_EMAIL'), Cypress.env('USER_PASSWORD'));
        cy.visit(`/orders/${id}`);
        cy.get('[data-cy=order-sku]').should('have.text', sku);
      });
  });
});
```

## Guardrails
- This is a **draft the engineer must run against a real environment**; confirm status
  codes and fields against the actual contract.
- Never fabricate endpoints, fields, or auth schemes; a missing spec is a question.
- Never hard-code tokens or passwords; read them from `Cypress.env()` backed by CI secrets.
- Assert type and shape for volatile fields, not exact generated values.
- Clean up created records, and never point destructive tests at production.
