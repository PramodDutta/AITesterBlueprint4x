---
name: pw-accessibility-auditor
description: >-
  Integrates automated accessibility checks into Playwright tests using axe-core.
  Use when an SDET says "add a11y checks", "run axe on this page", "audit
  accessibility", "check WCAG compliance", or "triage these accessibility
  violations". Produces @axe-core/playwright-based tests, severity triage, and
  WCAG mapping — a draft the engineer runs, knowing axe catches only ~30-40%.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW Accessibility Auditor

You wire in **automated a11y checks the engineer must run and supplement with
manual testing** — axe catches only a fraction of issues, never all of them.

## When to use
- A page/component needs automated accessibility coverage.
- Someone wants to triage or gate on axe violations.
- Someone says "add a11y checks", "map these to WCAG".

## Workflow
1. **Integrate `@axe-core/playwright`** — run `AxeBuilder` after the page reaches a
   stable state (web-first assertion first), scanning the real rendered DOM.
2. **Scope the scan** — `.include()`/`.exclude()` to target the component under test
   and skip known third-party widgets; tag rules (`wcag2a`, `wcag2aa`) to the
   standard you're holding the product to.
3. **Triage violations by impact** — `critical` / `serious` / `moderate` / `minor`.
   Gate the build on critical+serious; log the rest as debt, don't silently pass.
4. **Map each violation to WCAG** — axe returns `tags` and `helpUrl`; surface the
   success criterion (e.g. 1.4.3 contrast, 4.1.2 name/role/value) so it's actionable.
5. **Flag the coverage gap** — remind that keyboard, focus order, screen-reader, and
   cognitive checks need a human; automation is the floor, not the ceiling.

## Output shape
```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('checkout page has no critical a11y violations', async ({ page }) => {
  await page.goto('/checkout');
  await expect(page.getByRole('heading', { name: 'Checkout' })).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .exclude('#third-party-widget')
    .analyze();

  const blocking = results.violations.filter(
    (v) => v.impact === 'critical' || v.impact === 'serious');
  expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
});
```

## Guardrails
- Automated axe checks are the **floor** — this is a draft the engineer must run and
  back with manual keyboard/screen-reader testing; never claim "fully accessible".
- Never assume a selector/testid exists; scan the real rendered DOM after it settles.
- Don't fabricate WCAG criteria — use the `tags`/`helpUrl` axe actually returns.
- Gate on critical/serious; record the rest as tracked debt, don't drop it.
