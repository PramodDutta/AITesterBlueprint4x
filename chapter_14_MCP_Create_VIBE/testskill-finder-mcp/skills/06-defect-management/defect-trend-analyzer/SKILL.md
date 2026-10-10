---
name: defect-trend-analyzer
description: >-
  Analyzes defect data for trends such as density per module, leakage to production,
  reopen rate, aging, and severity mix, then recommends actions. Use when a QA lead says
  "analyze our bug trends", "which module has the most defects", "what is our defect
  leakage", or pastes a Jira/Azure DevOps defect export. Produces a metrics table, the
  notable trends, and ranked recommendations, as a draft for human review before it is
  shared.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Defect Management
  version: 1.0.0
---

# Defect Trend Analyzer

You turn a raw defect export into **a few trends that change what the team does next**. Every
metric shows its formula and sample size, so nobody acts on noise.

## When to use
- End of a sprint, release, or quarter, when the team wants to know where quality is slipping.
- Production incidents are rising and someone asks "why are bugs escaping?".
- Planning test effort and you need to know which modules deserve more coverage.

## Workflow
1. **Collect and clean the data.** Ask for the export (id, module/component, severity, status,
   created, resolved, reopened count, found-in environment, release). Drop duplicates and
   "not a bug" closures, and state how many rows were removed and why.
2. **Compute the core metrics** per module and per period, with the formula shown:
   - Density = defects / size (KLOC, story points, or test cases; say which).
   - Leakage = prod defects / (prod + pre-release defects) for the same release.
   - Reopen rate = reopened / resolved.
   - Aging = days open for open defects (median and p90), compared to the severity SLA.
   - Severity mix = share of S1/S2/S3/S4 per period.
3. **Find the trends.** Compare against the previous periods: rising, falling, or flat. Flag
   modules that are outliers on more than one metric.
4. **Check sample size and data quality.** Small counts, a change in triage practice, or a
   missing field can fake a trend. Mark those findings "low confidence".
5. **Recommend actions.** Tie each recommendation to a metric (for example, high leakage in
   payments -> add contract tests and a staging smoke for that service). Rank by impact.
6. **HUMAN REVIEW GATE (mandatory).** Present the analysis as a draft. List data gaps, rows
   excluded, size measure assumed, and low-confidence trends. Ask the lead to confirm before it
   is shared with the team or management.

## Output shape
```
# Defect Trends - Releases 4.0 to 4.2 (n = 386 after removing 22 duplicates)
| Module   | Defects | Density /KLOC | Leakage | Reopen | Open p90 age | S1+S2 |
|----------|---------|---------------|---------|--------|--------------|-------|
| Payments |   74    |     3.1       |  18%    |  14%   |   21 days    |  38%  |
| Search   |   52    |     1.2       |   4%    |   5%   |    6 days    |  12%  |
| Profile  |   19    |     0.6       |   0%    |   3%   |    4 days    |   5%  |
Trends:
  - Payments leakage 9% -> 13% -> 18% across 4.0-4.2 (rising, n = 74)
  - Payments reopen rate 14%: 6 of 10 reopens cite "partial fix", missing regression test
Recommendations (ranked):
  1. Add API contract tests for payments-gateway; owner: payments SDET
  2. Require a regression test link before resolving S1/S2 payments bugs
Low confidence: Profile (n = 19)
--- HUMAN REVIEW GATE ---
Assumed size = KLOC from repo stats 10-01. Confirm exclusions before sharing.
```

## Guardrails
- Never fabricate a defect count, rate, or trend; every number traces to the export.
- Always show the formula and n; a percentage without a denominator is not reported.
- Do not rank people or teams by bug count; analyze modules and process, not individuals.
- Correlation is not cause; phrase root causes as hypotheses to confirm with the team.
- The analysis is a draft until a human reviews it.
