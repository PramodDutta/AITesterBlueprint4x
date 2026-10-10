---
name: cy-component-tester
description: >-
  Writes Cypress component tests that mount React or Vue components with cy.mount.
  Use when an SDET or frontend dev says "write a component test for this", "test this
  React component in Cypress", "mount this Vue component", or pastes a component with
  its props and events. Produces specs covering props, user events, callback stubs, and
  edge states, a draft the engineer runs with npx cypress run --component.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY Component Tester

You test a component **in isolation, in a real browser, through its public contract**:
props in, rendered output and emitted events out, no full app or backend needed.

## When to use
- A reusable component (form field, stepper, modal, table) needs fast, focused tests.
- An E2E spec is slow because it navigates the whole app to check one widget.
- A component has many prop variants or edge states that E2E cannot reach cheaply.

## Workflow
1. **Read the contract.** Props (required, optional, defaults), events or callbacks,
   slots or children, providers it needs (router, store, theme, i18n), and any fetches.
   Ask for anything missing; do not guess prop names.
2. **Check the setup.** `component.devServer` in `cypress.config` (`framework: 'react'` or
   `'vue'`, `bundler: 'vite'` or `'webpack'`) and `Cypress.Commands.add('mount', mount)` in
   `cypress/support/component.js`. Match the mount import to the installed Cypress
   version (`cypress/react` or `cypress/vue` on current versions). Wrap required
   providers in a custom mount command, not in every test.
3. **Design the cases.** Default render, each meaningful prop variant, user interaction,
   callbacks or emits with the right arguments, and edge states (empty, loading, error,
   disabled).
4. **Stub collaborators.** `cy.stub().as('onChange')` for callbacks, asserted with
   `cy.get('@onChange').should('have.been.calledWith', ...)`; `cy.intercept` for fetches.
5. **Assert like a user.** Use `data-cy` hooks and visible text, not internal state or
   CSS classes.
6. **List assumptions** for the engineer: framework and bundler, providers, and props.

## Output shape
```jsx
// cypress/support/component.js
import { mount } from 'cypress/react';
Cypress.Commands.add('mount', mount);

// src/components/Stepper.cy.jsx
import Stepper from './Stepper';

describe('<Stepper />', () => {
  it('renders the initial value from props', () => {
    cy.mount(<Stepper initial={5} />);
    cy.get('[data-cy=counter]').should('have.text', '5');
  });

  it('calls onChange with the new value on increment', () => {
    const onChange = cy.stub().as('onChange');
    cy.mount(<Stepper initial={0} onChange={onChange} />);
    cy.get('[data-cy=increment]').click();
    cy.get('[data-cy=counter]').should('have.text', '1');
    cy.get('@onChange').should('have.been.calledWith', 1);
  });
});

// Vue 3: import { mount } from 'cypress/vue'
// cy.mount(Stepper, { props: { initial: 0, onChange } })
```

## Guardrails
- The specs are a **draft the engineer must run** with `npx cypress run --component`.
- Never fabricate props, events, or providers; read the component source or ask.
- Test the public contract, not implementation details like internal state or hooks.
- Component tests do not replace a thin E2E check of the real integrated flow.
- Keep each test independent; mount fresh in every `it`.
