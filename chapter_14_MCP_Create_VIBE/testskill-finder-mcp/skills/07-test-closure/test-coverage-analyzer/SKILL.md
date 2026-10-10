---
name: test-coverage-analyzer
description: >-
  Find the gaps between what was required and what was actually tested. Use when a lead
  says "where are our coverage gaps", "what isn't tested", or wants requirements and code
  areas checked against the executed and available tests. Builds a traceability view —
  requirements/ACs and code areas on one axis, tests on the other — and surfaces untested
  ACs, thinly covered areas, and orphan tests. Reports gaps from real artifacts, never
  assumed coverage.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Closure
  version: 1.0.0
---

# Test Coverage Analyzer

You show **what is genuinely covered versus what everyone assumed was covered**. A gap you
name before release is a bug you did not ship.

## When to use
- Before closing a cycle, to confirm requirements are actually tested.
- Someone asks which ACs, features, or code areas have no or weak coverage.
- A traceability view is needed for an audit or sign-off.

## Workflow
1. **Gather both sides.** Collect the requirements/ACs and the tests (designed and executed).
   If either list is incomplete, say so — do not assume a requirement is covered without a test.
2. **Build traceability.** Map each requirement/AC and key code area to the tests that cover it,
   and each test back to what it verifies.
3. **Surface gaps.** List: untested ACs (no test at all), thin coverage (only happy path, no
   negative/boundary), executed-but-failing coverage, and orphan tests (map to no requirement).
4. **Weigh by risk.** Rank gaps so the riskiest untested areas stand out, not just the count.
5. **HUMAN REVIEW GATE (mandatory).** Present the analysis as a draft. State what you could not
   map and any assumption made. Ask the QA lead to confirm before it informs a release decision.

## Output shape
```
## Coverage Analysis — <feature / release>
| Requirement / AC | Tests            | Status        | Gap                    |
| AC-1             | TC-1, TC-2       | covered       | -                      |
| AC-2             | TC-4 (happy only)| thin          | no negative/boundary   |
| AC-3             | -                | UNTESTED      | high risk              |
Orphan tests (map to no requirement): [ ... ]
Top gaps by risk: 1) AC-3  2) ...
--- HUMAN REVIEW GATE ---
Unmapped items / assumptions / "Confirm before this informs release sign-off"
```

## Guardrails
- Never assume coverage exists without a test to point to — an unmapped AC is a gap, not a pass.
- Do not fabricate test IDs or requirement IDs to make the matrix look complete.
- Distinguish "covered" from "covered and passing" — a failing test is not coverage.
- The analysis is a draft input to sign-off; a human owns the release decision.
