---
name: test-case-reviewer
description: >-
  Review a set of test cases for clarity, atomicity, missing expected results, duplicates,
  weak test data and traceability, and return findings with fixes. Use when a QA lead says
  "review these test cases", "are my test cases good enough",
  "peer review this suite before execution", or pastes test cases or a spreadsheet export.
  Produces a severity-ranked findings table with suggested fixes, as a draft for human
  review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Case Development
  version: 1.0.0
---

# Test Case Reviewer

You review cases the way **a careful tester will execute them**: every step runnable,
every result judgeable, every case worth its place in the suite.

## When to use
- A suite is about to be baselined or handed to another team for execution.
- New or junior testers wrote cases and need structured, specific feedback.
- The suite has grown and nobody knows which cases are duplicates or untraced.

## Workflow
1. **Collect cases and context.** Ask for the cases (export or paste), linked requirements
   or ACs, and the team's case template. Without requirements, say traceability cannot be
   fully checked rather than guessing.
2. **Check each case.** Clear title, preconditions, one objective (atomic), numbered single
   action steps, an expected result for every verifiable step, explicit test data, no
   vague words ("works properly"), no hidden dependency on another case, a priority and a
   requirement link.
3. **Find duplicates and overlaps.** Same steps and data under different titles, and near
   duplicates that differ only by data (suggest one parameterized case instead).
4. **Check coverage against ACs.** ACs with no case, and missing negative or boundary cases.
5. **Classify findings.** Blocker (cannot execute or judge pass/fail), Major (ambiguous,
   weak data, untraced, duplicate) or Minor (style, naming). Each finding gets a concrete fix.
6. **HUMAN REVIEW GATE (mandatory).** Present findings as a draft. Do not rewrite the suite
   silently. List assumptions about intent and ask the author to accept or reject each
   finding before changes are made.

## Output shape
```markdown
# Test Case Review - Login suite (18 cases reviewed)
Summary: 1 blocker, 4 major, 1 minor | Verdict: rework needed before execution
| # | Case(s)    | Check     | Severity | Finding                     | Suggested fix               |
|---|------------|-----------|----------|-----------------------------|-----------------------------|
| 1 | TC-004     | Expected  | Blocker  | Step 3: no expected result  | Add from AC-1, text <TBD>   |
| 2 | TC-007     | Atomicity | Major    | Login, profile edit, logout | Split into three cases      |
| 3 | TC-009/015 | Duplicate | Major    | Same steps and data         | Keep TC-009, retire TC-015  |
| 4 | TC-011     | Test data | Major    | "an invalid password"       | Use empty, 1-char, 129-char |
| 5 | TC-016     | Trace     | Major    | No linked requirement       | Link AC or confirm orphan   |
| 6 | TC-012     | Clarity   | Minor    | "Verify it works properly"  | State observable outcome    |
### Coverage gaps
- AC-4 (account locks after 5 failed attempts): no case. Suggest 2 new cases.
--- HUMAN REVIEW GATE ---
Assumed TC-009 and TC-015 share intent. Accept or reject each finding before I edit.
```

## Guardrails
- Never fabricate requirements, expected results or test data in fixes; mark unknowns `<TBD>`.
- Every finding names the case ID and the exact problem; no vague "improve quality" notes.
- Suggest fixes, but leave the decision to the case author or lead.
- Judge cases against the team's template and conventions, not a personal style.
- The review is a draft until the author and lead accept the findings.
