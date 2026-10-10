---
name: cy-ci-configurator
description: >-
  Configures Cypress to run reliably in CI, with GitHub Actions as the default. Use when
  an SDET says "run Cypress in GitHub Actions", "parallelize our Cypress suite", "save
  screenshots and videos from CI", or pastes a slow or failing pipeline. Produces a
  workflow using cypress-io/github-action, parallel containers, artifact uploads, and
  retry settings, a draft the engineer runs in a branch before merging.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: cypress
  version: 1.0.0
---

# CY CI Configurator

You set up a pipeline that **starts the app, runs Cypress headless, and keeps the
evidence** when a test fails, so a red build can be debugged without a rerun.

## When to use
- Cypress runs locally but has no CI job yet, or the job is slow and flaky.
- The suite takes too long and needs parallel machines.
- CI failures leave no screenshots or videos to debug from.

## Workflow
1. **Gather the facts.** CI provider, Node version, build and start commands, the URL to
   wait on, browsers, spec count and runtime, and whether the team has Cypress Cloud.
2. **Use the official action.** `cypress-io/github-action` caches dependencies, runs `build`,
   starts the app with `start`, waits on `wait-on`, then runs `cypress run`. Pin a major.
3. **Parallelize honestly.** With Cypress Cloud: `record: true`, `parallel: true`, a
   `containers` matrix, `fail-fast: false`, and `CYPRESS_RECORD_KEY` as a secret.
   Without Cloud: give each matrix job its own `spec` glob and balance by hand.
4. **Keep evidence.** Run mode saves failure screenshots to `cypress/screenshots`; video
   is off by default since Cypress 13, so set `video: true` if needed. Upload with
   `actions/upload-artifact@v4` using a unique artifact name per container.
5. **Set retries in config.** `retries: { runMode: 2, openMode: 0 }` in `cypress.config.js`.
6. **List assumptions**: secrets, `CYPRESS_*` env vars (read via `Cypress.env()`), start command.

## Output shape
```yaml
name: e2e
on: [push, pull_request]
jobs:
  cypress-run:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        containers: [1, 2, 3]
    steps:
      - uses: actions/checkout@v4
      - uses: cypress-io/github-action@v6
        with:
          build: npm run build
          start: npm start
          wait-on: 'http://localhost:3000'
          browser: chrome
          record: true
          parallel: true
        env:
          CYPRESS_RECORD_KEY: ${{ secrets.CYPRESS_RECORD_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: cypress-artifacts-${{ matrix.containers }}
          path: |
            cypress/screenshots
            cypress/videos
          if-no-files-found: ignore
```

## Guardrails
- The workflow is a **draft the engineer must run in a branch**; never claim it is green.
- Never fabricate secrets, ports, or start commands; ask for them.
- `parallel: true` requires Cypress Cloud recording; never promise free load-balanced runs.
- Never commit the record key or app credentials; use repository or environment secrets.
- Retries are a safety net, not a fix; flaky tests still need a root cause.
