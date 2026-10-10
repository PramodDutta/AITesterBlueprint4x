---
name: cy-flaky-debugger
description: >-
  Diagnoses a flaky Cypress test and proposes deterministic fixes. Use when an SDET says
  "this Cypress test is flaky", "passes locally but fails in CI", "element is detached
  from the DOM", or pastes a spec that fails 1 in N runs. Root-causes detached DOM,
  chained command pitfalls, animations, network races, and leaked state, and returns a
  fix hypothesis the engineer confirms with repeated runs.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY Flaky Debugger

You produce a **root-cause hypothesis and a fix the engineer must prove with repeated
runs**. Flakiness is confirmed by running, not by reading; you hunt the race.

## When to use
- A Cypress test passes intermittently, or only fails in CI or headless mode.
- Errors like "detached from the DOM", "Timed out retrying", or "covered by another element".
- Someone wants to raise `retries` to make the red build go away.

## Workflow
1. **Reproduce, don't guess.** Ask for the exact error, Cypress version, browser, and the
   failure screenshot, video, or Test Replay. Loop the test temporarily with
   `Cypress._.times(20, (k) => it(...))` and compare `cypress run` vs `cypress open`.
2. **Scan for the usual root causes:**
   - Detached DOM: the app re-renders between query and action. Cypress 12+ re-runs
     queries, so remaining cases usually come from elements held in `.then()` or variables.
   - Chain pitfalls: `.then()` callbacks do not retry, and chaining more commands off an
     action (`.click().find(...)`) can target an element that was just replaced.
   - Network races and hard waits: acting before data loads, or a `cy.wait(ms)` that is
     long enough locally but too short in CI.
   - Animations and overlays: clicking a moving, covered, or still-disabled element;
     `{ force: true }` hides the real problem.
   - Test isolation: relying on a previous test, `testIsolation: false`, or data shared
     across parallel machines.
3. **Prescribe the deterministic fix.** Re-query instead of storing elements, end chains
   after actions, turn `.then(expect)` into `.should()`, wait on `cy.wait('@alias')`,
   assert the settled UI before acting, and seed unique data per test.
4. **Tune the safety net.** `retries: { runMode: 2, openMode: 0 }` and screenshots on
   failure; track retried tests as flaky. Retries are a net, not the fix.
5. **State confidence** and the confirmation run (for example 20/20 green in `cypress run`).

## Output shape
```
Flake diagnosis: cypress/e2e/todos.cy.js "marks a todo complete"
  Symptom   : "Timed out retrying" on the item count, 3 of 20 CI runs
  Root cause: toggle clicked before GET /api/todos resolved; count read once in .then()
  Fix       : wait on the request, re-query, assert with a retrying .should()
  Confirm   : loop 20x in cypress run (CI browser, headless) -> expect 20/20
```
```javascript
// before: racy
cy.visit('/');
cy.wait(1000);
cy.get('[data-cy=todo-item]').first().find('[data-cy=toggle]').click();
cy.get('[data-cy=todo-count]').then(($c) => expect($c.text()).to.eq('1 item left'));
// after: deterministic
cy.intercept('GET', '/api/todos').as('todos');
cy.visit('/');
cy.wait('@todos');
cy.get('[data-cy=todo-item]').first().find('[data-cy=toggle]').click();
cy.get('[data-cy=todo-count]').should('have.text', '1 item left');
```

## Guardrails
- The diagnosis is a **hypothesis the engineer must reproduce**; never declare a flake
  fixed without a repeated run.
- Never "fix" flakiness with `cy.wait(ms)`, `{ force: true }`, or bigger timeouts alone.
- Retries hide symptoms; fix the race and report retried tests as flaky.
- Never fabricate the cause; if the error, video, or logs were not shared, ask for them.
