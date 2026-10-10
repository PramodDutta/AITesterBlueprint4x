---
name: pw-ci-configurator
description: >-
  Generates CI configuration (GitHub Actions) for a Playwright suite. Use when an
  SDET says "set up Playwright in CI", "add a GitHub Actions workflow", "shard my
  tests across jobs", "upload traces and the HTML report", or "run browsers in a
  matrix". Produces a workflow with install, sharding, blob/HTML reporting, and
  artifacts — a draft the engineer commits and runs on their pipeline.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW CI Configurator

You draft a **CI workflow the engineer must commit and run on their runner** —
never a guaranteed-green pipeline. You wire in sharding, reporting, and artifacts.

## When to use
- A repo needs Playwright running on GitHub Actions.
- A slow suite should be sharded across parallel jobs.
- Someone wants trace/video/report artifacts on failure.

## Workflow
1. **Confirm the runtime** — Node version, package manager, and which projects/
   browsers must run. Don't assume; ask if unstated.
2. **Install correctly** — cache deps, then `npx playwright install --with-deps`
   for the browsers actually used (don't install all if only Chromium is needed).
3. **Shard for speed** — a matrix of `shardIndex/shardTotal`, each job running
   `--shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}` with the **blob**
   reporter, then a final `merge-reports` job to produce one HTML report.
4. **Persist evidence** — `trace: 'on-first-retry'`, and `upload-artifact` for the
   blob reports, merged HTML report, and any traces/videos, `if: always()`.
5. **Set CI ergonomics** — `retries: 2` and `workers` via config's `!!process.env.CI`,
   and `fail-fast: false` so one shard's failure doesn't cancel the others.

## Output shape
```yaml
name: playwright
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npx playwright test --shard=${{ matrix.shard }}/4 --reporter=blob
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: blob-${{ matrix.shard }}, path: blob-report, retention-days: 7 }
```

## Guardrails
- This is a **draft the engineer must commit and run** — never assume the Node
  version, package manager, browser set, or secret names; confirm them.
- Never hardcode credentials; reference `secrets.*`, don't invent values.
- Shards emit **blob** reports merged in a follow-up job — don't upload conflicting
  HTML reports per shard.
- Upload artifacts with `if: always()` or you lose evidence on the runs that matter.
