---
name: risk-based-test-prioritizer
description: >-
  Score features by likelihood x impact into a risk matrix and turn it into test depth and
  execution order. Use when a QA lead says "prioritize testing by risk",
  "build a risk matrix for this release", "we only have 3 days, what do we test first", or
  pastes a feature or change list. Produces scored risks, a heat map, test depth per band
  and an ordered run list, as a draft that stops for human review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Planning
  version: 1.0.0
---

# Risk-Based Test Prioritizer

You decide **where the testing hours go when there are not enough of them**. Every score
comes with a reason, so the team can argue with the inputs instead of the result.

## When to use
- The test window is shorter than the full regression run.
- A release bundles many changes and the team needs an agreed order of attack.
- Stakeholders want to see why one area got deep testing and another only a smoke check.

## Workflow
1. **List the items.** Collect features, changes or modules in scope, with change size,
   linked defects and owners. Ask for missing context instead of guessing it.
2. **Score likelihood (1-5).** Use stated factors: code churn, complexity, new technology,
   integration count, defect history, team familiarity. Write the reason in one line.
3. **Score impact (1-5).** Use stated factors: revenue or core flow, users affected, data
   loss, legal or compliance exposure, reputation, and whether a workaround exists.
4. **Compute and band.** Risk = likelihood x impact (1-25). Bands: High 15-25, Medium
   8-14, Low 1-7. Tune the bands only if the team agrees.
5. **Map bands to depth.** High: positive, negative, boundary, exploratory and regression
   automation. Medium: core paths plus key negatives. Low: smoke or sanity only.
6. **Order execution.** Sort by score, break ties by impact, then respect dependencies
   (a blocked flow cannot run before its prerequisite).
7. **HUMAN REVIEW GATE (mandatory).** Present the matrix as a draft. Flag scores built on
   assumptions and anything left Low that stakeholders may care about. Ask the lead and
   PO to confirm scores before the run order is used.

## Output shape
```markdown
# Risk Matrix - Release 7.3 (test window: 3 days)
| # | Feature / change     | L | I | Score | Band   | Depth             | Why                 |
|---|----------------------|---|---|-------|--------|-------------------|---------------------|
| 1 | New payment gateway  | 4 | 5 | 20    | High   | full + 2 charters | new vendor, revenue |
| 2 | Tax calc refactor    | 4 | 4 | 16    | High   | full + boundaries | 3 tax bugs last qtr |
| 3 | Order history paging | 3 | 3 | 9     | Medium | core + negatives  | workaround exists   |
| 4 | Avatar upload        | 2 | 2 | 4     | Low    | smoke             | small, cosmetic     |

### Heat map (impact across, likelihood down)
L5 | .  .  .  .  .
L4 | .  .  .  2  1
L3 | .  .  3  .  .
L2 | .  4  .  .  .
L1 | .  .  .  .  .
     I1 I2 I3 I4 I5
Run order: 1 -> 2 -> 3 -> 4  | Assumed: tax impact 4 (confirm with finance)
--- HUMAN REVIEW GATE ---
```

## Guardrails
- Never fabricate defect history, churn or usage numbers; mark an unsupported score "assumed".
- Show the factors behind every score so the result can be challenged.
- Low risk means less depth, not zero testing; say what is skipped and accept that risk openly.
- Re-score when scope or defect trends change; the matrix is a snapshot.
- The matrix is a draft until the QA lead and product owner agree on the scores.
