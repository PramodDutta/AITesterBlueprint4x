---
name: test-estimation-calculator
description: >-
  Estimate test effort with a work breakdown structure (WBS) and three-point PERT
  estimates, with explicit assumptions and buffer. Use when a QA lead says
  "estimate the testing effort", "how many days do we need to test this",
  "give me a PERT estimate", or pastes a scope or feature list. Produces a WBS table with
  O/M/P/E per task, totals, a confidence range and a commit number, as a draft that stops
  for human review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Planning
  version: 1.0.0
---

# Test Estimation Calculator

You give **an estimate with its assumptions showing**, never a single magic number. The
range and the assumptions are what make the estimate defensible when scope moves.

## When to use
- A sprint, release or SOW needs a testing effort figure.
- A manager asks "how long will testing take?" and the answer must survive challenge.
- Scope changed and the old estimate needs a traceable re-calculation.

## Workflow
1. **Confirm scope and inputs.** Ask for features in scope, case counts or complexity,
   environments, team size and productive hours per day. Never invent a case count.
2. **Build the WBS.** Break work into tasks: requirement review, planning, design, data and
   environment setup, execution cycles, defect retest, regression, reporting and closure.
3. **Get three points per task.** Optimistic (O), most likely (M) and pessimistic (P), in
   hours. Prefer the tester's own numbers or past actuals over your defaults.
4. **Compute PERT.** E = (O + 4M + P) / 6 and SD = (P - O) / 6 per task. Total E is the
   sum of E; total SD = sqrt(sum of SD squared), assuming tasks are independent.
5. **Add the buffer explicitly.** Report the range E +/- 2 SD (about 95%) and commit near
   the upper end. Add a separate risk buffer only for named risks, never a hidden padding.
6. **Convert to calendar time.** Divide by productive hours per day and headcount, then
   note dependencies (environment ready, build drops) that can shift dates.
7. **HUMAN REVIEW GATE (mandatory).** Present the estimate as a draft with every assumption
   numbered. Ask the lead to confirm inputs before the number is shared or committed.

## Output shape
```markdown
# Test Estimate - Loyalty Points v2 (40 test cases, 1 tester)
| WBS | Task                          | O  | M  | P  | E = (O+4M+P)/6 | SD   |
|-----|-------------------------------|----|----|----|----------------|------|
| 1.1 | Requirement review + plan     | 4  | 6  | 14 | 7.0            | 1.67 |
| 1.2 | Test case design (40 cases)   | 12 | 16 | 26 | 17.0           | 2.33 |
| 1.3 | Test data + environment setup | 4  | 8  | 18 | 9.0            | 2.33 |
| 1.4 | Execution cycle 1             | 10 | 14 | 24 | 15.0           | 2.33 |
| 1.5 | Defect retest + regression    | 6  | 10 | 20 | 11.0           | 2.33 |
| 1.6 | Reporting + closure           | 2  | 4  | 6  | 4.0            | 0.67 |
Total E = 63.0 h | Total SD = sqrt(25.0) = 5.0 h | Range (E +/- 2 SD): 53 to 73 h
Commit: 73 h = about 12.2 working days at 6 productive h/day
Risk buffer (named, not included): +8 h if shared staging is down more than 1 day (A3)
Assumptions:
  A1 40 cases at medium complexity; A2 one execution cycle plus one retest cycle
  A3 staging shared with team B; A4 build delivered by <TBD date>
--- HUMAN REVIEW GATE ---
Confirm case count, productive hours and A3 before this goes to the plan.
```

## Guardrails
- Never fabricate historical actuals, velocity or case counts; ask or mark as assumed.
- Show the formula and every input so anyone can recompute the total.
- Keep buffer visible and tied to named risks; never pad individual tasks silently.
- Re-estimate when scope changes instead of stretching the old number.
- The estimate is a draft until the QA lead confirms the inputs and assumptions.
