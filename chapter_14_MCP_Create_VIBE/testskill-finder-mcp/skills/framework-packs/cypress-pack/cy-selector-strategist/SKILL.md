---
name: cy-selector-strategist
description: >-
  Audits Cypress selectors and migrates them toward data-cy or data-testid attributes.
  Use when an SDET says "our selectors keep breaking", "audit the selectors in this
  spec", "what selector should I use in Cypress", or pastes a spec full of CSS classes,
  nth-child, or XPath. Produces a ranked audit table, replacement selectors, and the exact
  attributes the app team must add, a proposal the engineer and devs agree on first.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY Selector Strategist

You make selectors **survive redesigns**: tests target attributes that exist only for
testing, so a CSS refactor or copy tweak never breaks the suite by accident.

## When to use
- Specs break after styling or layout changes even though the feature still works.
- A suite mixes classes, ids, `nth-child`, and XPath with no convention.
- A team is starting a Cypress project and wants a selector standard up front.

## Workflow
1. **Inventory selectors.** Scan `cy.get`, `.find`, `cy.contains`, and `.within` across
   specs and helpers; group them by component and page.
2. **Rate each against the priority:**
   - Best: `data-cy`, `data-test`, or `data-testid`, isolated from CSS and JS changes.
   - Good: `cy.contains('Place order')` when the visible text is part of the requirement.
   - Acceptable: stable `id` or `name`, but coupled to app code.
   - Avoid: classes, tag chains, `:nth-child`, `.eq(3)`, generated ids, and XPath.
3. **Propose replacements.** Name attributes `<component>-<element>` in kebab-case,
   unique per page. For lists, tag the row and narrow by text or `.within()`, not index.
4. **Write the app change list.** File, element, and attribute to add, grouped into one
   ticket for developers. Without app access, offer scoped `cy.contains` selectors as an
   interim fix and mark them temporary.
5. **Lock it in.** A `cy.getByCy()` helper and the `cypress/require-data-selectors`
   rule from `eslint-plugin-cypress` to stop regressions.
6. **List assumptions** for the engineer: component file paths and attribute names that
   still need developer confirmation.

## Output shape
```
Selector audit: cypress/e2e/checkout.cy.js (5 selectors, 3 high risk)
| Line | Current                             | Risk | Proposed                                     |
|------|-------------------------------------|------|----------------------------------------------|
| 14   | cy.get('.btn.btn-primary')          | High | cy.getByCy('checkout-submit')                |
| 22   | cy.get('ul > li:nth-child(3) span') | High | cy.getByCy('cart-item').contains('Blue Mug') |
| 31   | cy.get('#mui-42417')                | High | cy.getByCy('promo-code-input')               |
| 40   | cy.get('[name="email"]')            | Med  | keep for now, migrate to 'email-input'       |
| 47   | cy.contains('Place order')          | Low  | keep (button copy is a requirement)          |
App changes (one ticket for developers):
  CheckoutForm.tsx  <button type="submit">  add data-cy="checkout-submit"
  CartList.tsx      <li> per cart item      add data-cy="cart-item"
  PromoCode.tsx     <input>                 add data-cy="promo-code-input"
```
```jsx
// CheckoutForm.tsx (app change)
<button type="submit" data-cy="checkout-submit">Place order</button>
// cypress/support/commands.js
Cypress.Commands.add('getByCy', (id) => cy.get(`[data-cy="${id}"]`));
```

## Guardrails
- The audit is a **proposal the engineer and developers must agree on** before code changes.
- Never fabricate component names or file paths; mark unknown locations as "to confirm".
- Never invent an attribute and use it in a spec before the app actually renders it.
- Do not replace a text selector when the text itself is what the test verifies.
- Index-based selectors (`.eq()`, `nth-child`) are a last resort and must be flagged.
