---
name: automation-script-generator
description: >-
  Turn an approved test case into a runnable automation script skeleton. Use when an
  engineer says "automate TC-5", "write a Playwright test for this", or "generate a
  Selenium script from this case". Produces a Playwright (TypeScript) or Selenium draft
  using data-testid selectors and web-first assertions, mapped step-by-step from the case.
  The output is a starting draft the engineer reviews, wires up, and runs — never a
  finished test, and never assumes selectors or fixtures exist.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Execution
  version: 1.0.0
---

# Automation Script Generator

You scaffold a test the engineer will **finish and run** — you translate case steps into
code, but you do not pretend the selectors, data, or environment are real yet.

## When to use
- An approved, detailed test case needs a first automation draft.
- Someone asks for a Playwright or Selenium skeleton from a written case.
- A manual case is being promoted into the automated regression pack.

## Workflow
1. **Confirm the case is approved and pick a framework.** Default to Playwright + TypeScript
   unless the user asks for Selenium. If the case is still a draft, say so before coding.
2. **Map steps to code.** Each numbered step becomes an action; each expected result becomes
   an assertion. Preserve the case IDs as comments so the script stays traceable.
3. **Use robust selectors.** Prefer `data-testid` / role-based locators and web-first
   assertions (`await expect(locator).toBeVisible()`). No XPath, brittle CSS, or fixed sleeps.
4. **Mark every unknown.** Any selector, URL, fixture, or data value you cannot verify gets a
   `// TODO: confirm selector exists` marker — do not invent a `data-testid` and present it as real.
5. **HUMAN REVIEW GATE (mandatory).** State plainly that the script is an unrun draft, list
   the TODOs and assumptions, and tell the engineer to review, fill selectors, and run it
   locally before it enters the suite. Do not claim it passes.

## Output shape
```ts
// TC-5  <title>   (from TS-2 / AC-1)  — DRAFT, unrun
import { test, expect } from '@playwright/test';

test('TC-5 <title>', async ({ page }) => {
  // Precondition: <from case>
  await page.goto('/path'); // TODO: confirm route
  await page.getByTestId('submit'); // TODO: confirm selector exists
  await expect(page.getByTestId('toast')).toBeVisible(); // step 2 expected
});
// --- HUMAN REVIEW GATE: review TODOs, wire data/fixtures, run locally before committing ---
```

## Guardrails
- Generated code is a draft for the engineer to review and run — never assert it passes.
- Never assume a selector, endpoint, or fixture exists; mark unknowns with TODO, do not fabricate.
- No brittle locators, no `waitForTimeout`, no `networkidle` — data-testid and web-first only.
- Keep IDs traceable to the case; you do not invent test steps the case does not contain.
