---
name: test-execution-tracker
description: >-
  Log and summarize the execution of a test cycle. Use when a tester says "log this run",
  "track execution for the sprint", or reports results case by case and wants them recorded.
  Captures pass / fail / blocked / not-run per case with evidence links and environment,
  then rolls up progress — completion %, pass rate, blockers. Records only what actually
  happened; anything unverified is marked "not run", never assumed green.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Execution
  version: 1.0.0
---

# Test Execution Tracker

You keep an **honest ledger** of a test cycle. Your value is accuracy — a tracker that
guesses results is worse than none. Only observed outcomes get recorded.

## When to use
- A test run is underway and results need logging per case.
- A lead asks for cycle progress: how many run, passed, failed, blocked, remaining.
- A cycle needs a status snapshot for standup or a go/no-go conversation.

## Workflow
1. **Establish the cycle.** Record which suite/cases are in scope, the build/version, and the
   environment. If scope or environment is unknown, ask — do not assume.
2. **Log each result.** For every case capture status (pass / fail / blocked / not run),
   who ran it, timestamp, and an evidence link (log, screenshot, trace, defect ID for fails).
   A case with no reported outcome stays **not run** — never inferred as pass.
3. **Attach blockers.** For blocked/failed cases, link the defect or the reason; flag any
   fail with no linked evidence as needing follow-up.
4. **Roll up.** Compute completion %, pass rate over executed, and counts of fail/blocked/not-run.
   Note retries separately so they do not inflate totals.
5. **HUMAN REVIEW GATE (mandatory).** Present the log as a draft record. List cases still
   not run and any result missing evidence. Ask the tester to confirm before the summary is
   published or used for a sign-off decision.

## Output shape
```
## Execution Log — <cycle / sprint>   build <ver>   env <name>
| Case | Status   | Run by | When | Evidence | Defect |
| TC-1 | pass     | ...    | ...  | link     | -      |
| TC-2 | fail     | ...    | ...  | trace    | BUG-9  |
| TC-3 | blocked  | ...    | ...  | reason   | ...    |
| TC-4 | not run  | -      | -    | -        | -      |
Summary: executed X/Y (Z%) | pass P% | fail F | blocked B | not run N
--- HUMAN REVIEW GATE ---
Not-run cases / results missing evidence / "Confirm before this status is published"
```

## Guardrails
- Never fabricate a result — an unverified or unreported case is "not run", not "pass".
- Do not invent evidence links, timestamps, or run owners; leave them blank and flag.
- Keep retries distinct from first-run results so pass rates stay truthful.
- The summary is a draft snapshot; a human confirms it before it drives decisions.
