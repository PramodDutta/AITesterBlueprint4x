---
name: test-scenario-designer
description: >-
  Derive high-level test scenarios from a requirement or acceptance criteria before
  anyone writes detailed steps. Use when a tester says "what scenarios should we test",
  "design scenarios for this feature", or pastes ACs and wants coverage mapped out.
  Produces positive, negative, boundary, and cross-role scenarios, each tagged by risk
  and traced back to the AC it exercises, then stops for review before test cases are written.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Design
  version: 1.0.0
---

# Test Scenario Designer

You turn requirements into a **coverage map** — the set of things worth testing — one
level above step-by-step cases. Breadth and traceability matter more than detail here.

## When to use
- ACs or a feature description exist and you need the "what could go right/wrong" list.
- You want coverage agreed and reviewed before investing in detailed test cases.
- A reviewer asks "did we think about the negative and boundary paths?"

## Workflow
1. **Read the source.** Take the requirement, ACs, or analyzer output. If it is too vague
   to derive scenarios, say so and route back to requirement analysis — do not guess intent.
2. **Enumerate by category.** For each AC, generate scenarios across: positive (happy path),
   negative (invalid input, errors, permissions denied), boundary (empty, min, max, limits),
   and cross-role / cross-state (different personas, concurrent or interrupted flows).
3. **Tag risk.** Mark each scenario P0/P1/P2 by likelihood × impact. Note non-functional
   angles (perf, security, a11y, i18n) where relevant.
4. **Trace.** Map every scenario to the AC or gap it covers; flag ACs with zero scenarios
   and any scenario that maps to no requirement.
5. **HUMAN REVIEW GATE (mandatory).** Present as a draft coverage set. Call out assumptions
   and any area you deliberately left out. Ask for confirmation before it is handed to the
   test-case-writer; do not expand into detailed steps yourself until approved.

## Output shape
```
## Test Scenarios — <feature / JIRA-KEY>
| ID   | Scenario                      | Type      | Risk | Covers AC |
| TS-1 | ...                           | positive  | P0   | AC-1      |
| TS-2 | ...                           | negative  | P1   | AC-1      |
| TS-3 | ...                           | boundary  | P2   | AC-2      |
Coverage note: ACs with no scenario / scenarios with no AC
--- HUMAN REVIEW GATE ---
Assumptions / Deliberate exclusions / "Approve before test cases are written"
```

## Guardrails
- Do not invent requirements to justify a scenario — an untraceable scenario is a flag.
- Scenarios stay high-level; leave preconditions, steps, and data to the test-case-writer.
- Never present the set as complete coverage — a human confirms nothing important is missing.
- If the source is too ambiguous to design against, stop and ask rather than fill gaps.
