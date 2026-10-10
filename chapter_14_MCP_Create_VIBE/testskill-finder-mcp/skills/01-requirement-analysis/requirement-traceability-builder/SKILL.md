---
name: requirement-traceability-builder
description: >-
  Build a requirements traceability matrix (RTM) that links requirements and acceptance
  criteria to scenarios, test cases and defects. Use when a QA lead says
  "build an RTM for this release", "which requirements have no tests",
  "find orphan test cases", or pastes requirement and test case exports. Produces the
  matrix, untraced requirements, orphan tests and a coverage summary, as a draft that
  stops for human review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Requirement Analysis
  version: 1.0.0
---

# Requirement Traceability Builder

You prove **every requirement has a test and every test has a reason to exist**. The
matrix is only as honest as its links, so you never invent one.

## When to use
- A release or audit needs evidence that each requirement was tested.
- Someone asks "what is not covered?" or "why do we still run this test?".
- Requirements changed mid-sprint and the team needs to see which tests are now stale.

## Workflow
1. **Collect the sources.** Ask for exports of requirements or stories with their ACs,
   scenarios, test cases (with any "covers" or link field), latest execution results and
   defects. Keep original IDs; never reconstruct an ID from memory.
2. **Normalize to one row per requirement or AC.** Keep many-to-many links: one AC can
   map to several cases, and one case can cover several ACs.
3. **Link forward and backward.** Use explicit links first (issue links, tags, a
   "Requirement" column). Title-similarity matches go in a separate "suggested" list and
   are never merged into the matrix without confirmation.
4. **Surface the gaps.** List untraced requirements (no scenario or case), orphan tests
   (no requirement), requirements whose cases were never executed, requirements with open
   defects, and tests still linked to retired or changed requirements.
5. **Summarize coverage.** Compute counts and percentages from the rows themselves, and
   attach a risk note to each gap so the lead can decide what to fix first.
6. **HUMAN REVIEW GATE (mandatory).** Present the RTM as a draft. List suggested links,
   missing exports and any data you could not reconcile. Ask the lead to confirm before
   the matrix is shared as release or audit evidence.

## Output shape
```markdown
# Requirements Traceability Matrix - Release 4.2 (Checkout)
| Req ID  | Requirement / AC    | Scenario | Test cases     | Result  | Defects | Status       |
|---------|---------------------|----------|----------------|---------|---------|--------------|
| REQ-101 | AC-1 Valid coupon   | SC-01    | TC-011, TC-012 | Pass    | -       | Covered      |
| REQ-101 | AC-2 Expired coupon | SC-02    | TC-013         | Fail    | BUG-877 | Covered, bug |
| REQ-102 | Guest checkout      | -        | -              | -       | -       | UNTRACED     |
| REQ-103 | AC-1 Save card      | SC-04    | TC-020         | Not run | -       | Not executed |

### Untraced requirements
- REQ-102 Guest checkout: no scenario or case. Risk: High (revenue path).
### Orphan tests
- TC-045 "Verify banner color": no requirement. Link it, retire it, or keep as regression.
### Suggested links (not yet in matrix)
- TC-031 "Coupon stacking" may cover REQ-101 AC-3 (title match only).
### Coverage summary
Requirement rows: 4 | Traced: 3 (75%) | Executed: 2 of 3 | Rows with open defects: 1
--- HUMAN REVIEW GATE ---
Missing: defect export for sprint 40. Confirm suggested links before I publish.
```

## Guardrails
- Never fabricate a link, test case ID, result or defect; an unknown cell stays empty.
- Fuzzy or title-based matches are suggestions until a human confirms them.
- Calculate every percentage from the rows shown, never from an estimate.
- Report orphan tests neutrally; retiring a test is the team's decision, not yours.
- The matrix is a draft until the QA lead confirms it.
