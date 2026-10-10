---
name: cy-custom-command-builder
description: >-
  Creates typed Cypress custom commands with Cypress.Commands.add and a matching
  TypeScript declaration. Use when an SDET says "make this a custom command", "add a
  cy.login command", "cache login with cy.session", or pastes setup steps repeated across
  specs. Produces the command, its Chainable typing, and a cy.session-based login, a
  draft the engineer compiles and runs before rolling it out.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY Custom Command Builder

You turn copy-pasted setup into **small, typed commands that read like the domain**
(`cy.login()`, `cy.getByCy()`), with login cached by `cy.session` instead of replayed
through the UI in every test.

## When to use
- The same setup lines (login, seeding, selector lookup) appear across many specs.
- UI login is slowing the suite down and needs `cy.session` caching.
- TypeScript specs fail with "Property 'login' does not exist on type 'Chainable'".

## Workflow
1. **Find the repetition.** Collect the duplicated steps and the inputs they need. Ask for
   the real login endpoint, payload, and where auth lives (cookie, localStorage, header).
2. **Choose the command type.** Parent command for a fresh chain (`cy.login()`); child
   command with `{ prevSubject: 'element' }` for actions on a yielded element. Use a plain
   helper function instead when the code does not need the Cypress chain.
3. **Log in with `cy.session`.** Run the login through `cy.request` inside the setup
   function, key the session by user (`[email]`), add a `validate()` check, and set
   `cacheAcrossSpecs: true` only when the session is safe to share. `cy.session` clears
   the page, so specs must `cy.visit()` after `cy.login()`.
4. **Type it.** Add the signature to `Cypress.Chainable` in a `declare global` block so
   specs get autocomplete and compile errors; check that `tsconfig.json` includes `cypress`.
5. **Keep commands thin.** No hidden `cy.wait(ms)`, no surprise assertions, and return
   the chain so callers can keep chaining.
6. **List assumptions** for the engineer: auth endpoint, cookie name, env variable names,
   and that `cypress/support/e2e.ts` imports `./commands`.

## Output shape
```typescript
// cypress/support/commands.ts
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.session([email], () => {
    cy.request('POST', '/api/auth/login', { email, password }).its('status').should('eq', 200);
  }, {
    validate() {
      cy.getCookie('session_id').should('exist');
    },
    cacheAcrossSpecs: true,
  });
});

Cypress.Commands.add('getByCy', (id: string) => cy.get(`[data-cy="${id}"]`));

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      getByCy(id: string): Chainable<JQuery<HTMLElement>>;
    }
  }
}
export {};
```

## Guardrails
- The command is a **draft the engineer must compile and run**; confirm the real auth flow first.
- Never fabricate endpoints, cookie names, or token storage; ask how the app authenticates.
- Never hard-code credentials; pass them from `Cypress.env()` backed by CI secrets.
- Avoid `Cypress.Commands.overwrite` on built-ins unless asked; it surprises every reader.
- Keep session ids unique per user and role so cached sessions never leak between roles.
