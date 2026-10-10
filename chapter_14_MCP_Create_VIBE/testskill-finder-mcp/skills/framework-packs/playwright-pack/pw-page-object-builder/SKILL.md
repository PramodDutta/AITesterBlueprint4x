---
name: pw-page-object-builder
description: >-
  Builds a Playwright Page Object Model class from a page or URL. Use when an
  SDET says "make a page object for the login page", "build a POM for the
  dashboard", "extract locators into a page class", or wants to refactor inline
  selectors into a reusable class. Produces locators-as-methods (getByTestId/
  getByRole), action methods, and a static PATH — a draft to review.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW Page Object Builder

You draft a **Page Object class the engineer must wire up and verify** — never a
finished, guaranteed-correct class. You encode resilient locators and clear actions.

## When to use
- A page/URL/screenshot is described and needs a reusable POM.
- Inline locators in a spec should be extracted into a class.
- Someone says "build/make a page object for X".

## Workflow
1. **Identify the page's role** and its stable entry path → `static readonly PATH`.
2. **Inventory the elements** the tests interact with. Group into logical clusters
   (header, form, table). If it exceeds ~50 locators, split into sub-page classes
   and say so — one bloated POM is a smell.
3. **Express each locator as a method** returning a `Locator`, preferring
   `getByRole`/`getByLabel`/`getByTestId`. Never store a resolved element; return
   the locator lazily so it re-queries.
4. **Add action methods** that orchestrate locators (e.g. `login(user, pass)`),
   with explicit return types. Keep assertions out of the POM; expose state.
5. **Flag guessed selectors** with `// TODO: confirm` and list them for review.

## Output shape
```typescript
import { type Page, type Locator } from '@playwright/test';

export class LoginPage {
  static readonly PATH = '/login';
  constructor(private readonly page: Page) {}

  usernameInput = (): Locator => this.page.getByLabel('Username');
  passwordInput = (): Locator => this.page.getByLabel('Password');
  submitButton = (): Locator => this.page.getByRole('button', { name: 'Sign in' });
  errorBanner = (): Locator => this.page.getByTestId('login-error');

  async goto(): Promise<void> {
    await this.page.goto(LoginPage.PATH);
  }

  async login(username: string, password: string): Promise<void> {
    await this.usernameInput().fill(username);
    await this.passwordInput().fill(password);
    await this.submitButton().click();
  }
}
```

## Guardrails
- This is a **draft the engineer must run and review** — never assume a selector,
  testid, or PATH exists; mark guesses with `// TODO: confirm`.
- Never fabricate accessible names or data-testids you weren't shown.
- Locators return `Locator` (lazy) — never cache resolved elements or `ElementHandle`.
- No XPath / `nth-child` / CSS-class selectors. No assertions inside the POM.
- Cap at ~50 locators per class; split into sub-pages when larger.
