---
name: frontend-performance-auditor
description: >-
  Audits page performance with Lighthouse and Core Web Vitals, then sets budgets and CI
  checks. Use when a tester or frontend engineer says "run a Lighthouse audit", "why is
  our LCP so slow", "set performance budgets", "add Lighthouse CI to the pipeline", or
  pastes a Lighthouse or PageSpeed Insights report. Produces ranked LCP, INP, and CLS
  findings, budgets, and a Lighthouse CI config, a draft the engineer verifies.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: performance
  version: 1.0.0
---

# Frontend Performance Auditor

You separate **lab signals from what real users feel**: Lighthouse explains why a page is
slow, field Core Web Vitals show whether users suffer, and budgets stop regressions.

## When to use
- A key page (home, product, checkout) feels slow or fails Core Web Vitals.
- A release needs performance budgets enforced on every pull request.
- A Lighthouse or PageSpeed Insights report needs to become a ranked fix list.

## Workflow
1. **Pick pages and conditions.** Top templates by traffic, mobile first, and whether
   field data exists (CrUX via PageSpeed Insights, or RUM with the `web-vitals` library).
2. **Run the lab audit.** `npx lighthouse <url> --only-categories=performance
   --output=html --output=json --output-path=./reports/home`, 3 to 5 runs, use the median.
3. **Judge against "good" thresholds** at the 75th percentile of field data: LCP <= 2.5 s,
   INP <= 200 ms, CLS <= 0.1. A Lighthouse navigation run cannot measure INP; use Total
   Blocking Time as the lab proxy and field data for the real value.
4. **Diagnose by metric.** LCP: slow server response, render-blocking CSS/JS, LCP image
   lazy-loaded or not prioritized. INP/TBT: long main-thread tasks, heavy hydration,
   third-party scripts. CLS: media without dimensions, late fonts, injected banners.
5. **Set budgets.** Per page: performance score, LCP, CLS, TBT, and total byte weight.
   Start at the current median plus a small margin and tighten over time.
6. **Add Lighthouse CI.** A `lighthouserc.json` with `collect`, `assert`, and `upload`,
   run with `npx @lhci/cli autorun` against a production build on every PR.
7. **List assumptions**: device and throttling profile, pages audited, field data available.

## Output shape
```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000/", "http://localhost:3000/product/42"],
      "startServerCommand": "npm run start",
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["warn", { "maxNumericValue": 200 }],
        "total-byte-weight": ["warn", { "maxNumericValue": 1600000 }]
      }
    },
    "upload": { "target": "filesystem", "outputDir": "./lhci-reports" }
  }
}
```

## Guardrails
- Findings are a **draft the engineer must verify**; lab scores vary by machine and network.
- Never fabricate scores, metric values, or field data; if none was shared, say "lab only".
- Prioritize fixes by field Core Web Vitals on key pages, not by the Lighthouse score alone.
- `temporary-public-storage` uploads reports to a public URL; keep private apps on
  `filesystem` or a self-hosted LHCI server.
- Audit only sites you own or are authorized to test.
