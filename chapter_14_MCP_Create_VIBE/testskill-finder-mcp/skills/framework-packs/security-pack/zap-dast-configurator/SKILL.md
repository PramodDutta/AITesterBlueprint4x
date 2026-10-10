---
name: zap-dast-configurator
description: >-
  Configures OWASP ZAP baseline and full scans in CI with the ZAP Docker image, a rules
  file to tune alerts, and report artifacts, then triages the findings. Use when a QA or
  DevSecOps engineer says "add a ZAP scan to our pipeline", "set up DAST in CI", "tune
  these ZAP alerts", or pastes a ZAP report. Produces a CI job, a rules file, and a triage
  table for authorized scans of your own app, a draft the engineer runs and verifies.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: security
  version: 1.0.0
---

# ZAP DAST Configurator

You wire **a ZAP scan into CI that the team trusts**: tuned rules, clear pass/fail, reports
kept as artifacts, and every alert triaged instead of ignored.

## When to use
- A web app or API needs automated DAST on each pull request or nightly build.
- An existing ZAP job is noisy, always red, or always ignored.
- Someone pastes a ZAP HTML/JSON report and asks which alerts are real.

## Workflow
1. **Confirm target and authorization.** A staging URL the team owns, written approval, and a
   scan window. Choose the scan: `zap-baseline.py` (spider plus passive rules, safe for shared
   envs), `zap-full-scan.py` (active attacks, dedicated test env only, never production), or
   `zap-api-scan.py -f openapi` for an API with a spec.
2. **Generate the rules file.** Run the baseline once with `-g rules.tsv` to list every rule,
   then set each line (tab-separated: rule id, action, name) to `IGNORE`, `INFO`, `WARN`, or
   `FAIL`, e.g. `10010 FAIL (Cookie No HttpOnly Flag)`. Pass it back with `-c rules.tsv`.
3. **Wire the CI job.** Mount a writable folder at `/zap/wrk`, write `-r` HTML, `-J` JSON and
   `-w` Markdown reports, cap spidering with `-m`, add `-j` for SPAs (Ajax spider), and upload
   reports with `if: always()`. Exit codes: 0 pass, 1 a FAIL rule fired, 2 warnings only, 3 error.
4. **Roll out in stages.** Start with `-I` (warnings do not fail the build) and only
   high-confidence rules on FAIL; promote rules from WARN to FAIL as each issue is fixed.
5. **Handle authentication.** Baseline scans run unauthenticated; for logged-in areas ask the
   engineer for a ZAP context file (`-n`) or an Automation Framework plan
   (`zap.sh -cmd -autorun /zap/wrk/plan.yaml`) and a dedicated scan account.
6. **Triage every alert.** Per alert: rule id, risk and confidence, affected URLs, reproduce on
   the target, then decide: bug (ticket), accepted risk (IGNORE with reason and ticket in a
   `#` comment line in the rules file), or false positive (evidence attached).
7. **List assumptions.** Target URL, auth approach, scan duration, and who owns triage.

## Output shape
```yaml
name: zap-baseline
on: [pull_request]
jobs:
  zap:
    runs-on: ubuntu-latest
    env:
      TARGET_URL: ${{ vars.ZAP_TARGET_URL }}   # staging only, authorized under SEC-142
    steps:
      - uses: actions/checkout@v4
      - name: Prepare work dir (ZAP runs as a non-root user)
        run: mkdir -p zap && cp .zap/rules.tsv zap/ && chmod -R a+w zap
      - name: ZAP baseline scan
        run: |
          docker run --rm -v "$PWD/zap:/zap/wrk/:rw" ghcr.io/zaproxy/zaproxy:stable \
            zap-baseline.py -t "$TARGET_URL" -c rules.tsv \
            -r zap-report.html -J zap-report.json -w zap-report.md -m 3 -I
      - name: Upload ZAP reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: zap-reports
          path: zap/zap-report.*
```

## Guardrails
- Only test systems you own or are explicitly authorized to test; active scans
  (`zap-full-scan.py`) only on a dedicated test environment.
- Never fabricate alerts, rule ids, or triage outcomes; quote the report and mark unverified items.
- Every IGNORE needs a written reason and an owner; never silence a rule just to turn CI green.
- This is a draft pipeline the engineer must run and verify; a clean baseline scan is not a pen test.
