---
name: pw-visual-regression
description: >-
  Sets up Playwright visual/screenshot regression testing. Use when an SDET says
  "add visual regression", "snapshot this component", "set up toHaveScreenshot",
  "mask the dynamic parts of this page", or "manage baselines". Produces snapshot
  tests with masking, thresholds, and a baseline strategy — a draft the engineer
  runs to generate and review the first baselines.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW Visual Regression

You set up **snapshot tests whose first baselines the engineer must generate and
eyeball** — never trust an auto-approved baseline. You make snapshots deterministic.

## When to use
- A page or component needs pixel/visual regression coverage.
- Flaky snapshot diffs need masking or threshold tuning.
- Someone says "add visual regression", "manage/update baselines".

## Workflow
1. **Pick the smallest stable target** — prefer a component locator over a full
   page; less surface means fewer false diffs.
2. **Neutralize non-determinism before snapping:** `mask` dynamic regions (dates,
   avatars, ads), disable animations (`animations: 'disabled'`), freeze data, and
   pin viewport + a consistent font/rendering environment (ideally Docker in CI).
3. **Configure tolerances** deliberately — `maxDiffPixelRatio` / `threshold` in
   config, not sprinkled ad hoc. Tight enough to catch real regressions.
4. **Establish baselines** via `--update-snapshots`, then **review each PNG by eye**
   before committing — a wrong baseline locks in the bug.
5. **Document the update flow** so baselines are refreshed intentionally, per platform.

## Output shape
```typescript
import { test, expect } from '@playwright/test';

test('dashboard card matches baseline', async ({ page }) => {
  await page.goto('/dashboard');
  const card = page.getByTestId('summary-card');
  await expect(card).toBeVisible();                       // web-first: wait for render
  await expect(card).toHaveScreenshot('summary-card.png', {
    animations: 'disabled',
    mask: [page.getByTestId('last-updated')],             // hide volatile timestamp
    maxDiffPixelRatio: 0.01,
  });
});
```
```
# generate/refresh baselines, then review the PNGs before committing
npx playwright test --update-snapshots
```

## Guardrails
- Baselines are **generated then human-reviewed** — never auto-approve; a bad
  baseline turns a bug green forever. Never assume a locator/testid exists.
- Mask every dynamic region and disable animations, or diffs will be flaky.
- Pin viewport, OS, and fonts; snapshots taken on different platforms won't match —
  generate per-project baselines in the CI environment, not just locally.
- No `waitForTimeout` before snapping; wait on a web-first assertion instead.
