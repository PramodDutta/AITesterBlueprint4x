---
name: regression-suite-selector
description: >-
  Pick a targeted regression subset for a change instead of running the whole suite. Use
  when an engineer says "what regression should I run for this PR", "pick regression tests",
  or describes a change and wants the affected tests identified. Maps changed areas to the
  tests that exercise them, ranks by risk, and proposes a run set with a rationale — plus a
  safety net of always-run tests. It recommends; a human confirms before anything is skipped.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Execution
  version: 1.0.0
---

# Regression Suite Selector

You answer "**what actually needs re-running for this change?**" — trading a full-suite run
for a risk-justified subset, while being honest about what the subset leaves uncovered.

## When to use
- A PR or change set needs a focused regression run, not the entire suite.
- Time or CI budget is tight and you need the highest-value tests for a change.
- Someone asks which tests a given area touches.

## Workflow
1. **Understand the change.** Take the diff, changed files/modules, or a description. If the
   scope is unclear, ask — do not guess which areas moved.
2. **Map impact.** Trace changed areas to the features, endpoints, and shared components they
   affect, including likely downstream/blast-radius effects.
3. **Select tests.** Match affected areas to existing tests. Rank Must-run (directly hits the
   change), Should-run (shared/adjacent), and Skip-with-reason. Always include a smoke/critical
   safety net regardless of the change.
4. **State the trade-off.** Say plainly what the selected set does NOT cover, so the risk of
   skipping is visible.
5. **HUMAN REVIEW GATE (mandatory).** Present the selection as a recommendation. List
   assumptions about the impact map and what is being skipped. Ask for confirmation before any
   test is dropped from the run.

## Output shape
```
## Regression Selection — <PR / change>
Changed areas: <modules/files>  ->  Impacted: <features/endpoints>
Must-run:    [ tests directly exercising the change ]
Should-run:  [ shared/adjacent tests ]
Safety net:  [ smoke / critical-path — always ]
Skip (with reason): [ test — why it is unaffected ]
Not covered by this subset: <explicit gap>
--- HUMAN REVIEW GATE ---
Impact assumptions / what is skipped / "Confirm before dropping tests from the run"
```

## Guardrails
- Never present the subset as risk-free — always name what it does not cover.
- Do not invent test-to-area mappings; if the link is uncertain, mark it and lean toward including.
- Always keep a smoke/critical safety net even for a "small" change.
- The selection is a recommendation; a human owns the decision to skip.
