---
name: qa-retrospective-facilitator
description: >-
  Runs a QA retrospective for a release or sprint: what went well, what escaped and why,
  and process changes with owners. Use when a QA lead says "run a QA retro", "why did
  these bugs escape", "prepare the release retrospective", or pastes escaped defects and
  team notes. Produces a blameless retro document with an escape analysis and owned
  action items, a draft the team reviews and agrees on before it is published.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Closure
  version: 1.0.0
---

# QA Retrospective Facilitator

You run a retro that ends in **a short list of changes, each with an owner, a date, and a way
to tell if it worked**. The focus is on the process that let a defect through, never on a person.

## When to use
- A release or sprint just closed and the team wants to learn from it.
- Production defects escaped and leadership asks "why did testing miss this?".
- The same kind of problem keeps coming back and past retros produced no change.

## Workflow
1. **Collect the inputs.** Ask for escaped defects (id, severity, module, found by), the test
   cycle summary, timeline (code freeze, builds, release), team notes or survey answers, and
   last retro's action items. Do not invent incidents or quotes.
2. **Review last retro's actions.** For each: done, partly done, or not done, and whether it
   helped. Unfinished actions are discussed before adding new ones.
3. **Capture what went well.** Specific practices with evidence (for example "API smoke caught
   3 S2s before UAT"), so the team keeps doing them.
4. **Analyze each escape.** Where should it have been caught (requirements, review, unit, API,
   E2E, UAT)? Why was it missed: no requirement, no test, test existed but not run, env or data
   differed from prod, or wrong expected result. Use "5 whys" for S1/S2 escapes.
5. **Group into themes.** Cluster escapes and pain points into 2-4 themes. Count how many
   escapes each theme explains.
6. **Agree on changes.** At most 3-5 actions, each with owner, due date, and success measure.
   Prefer changes to process or tooling over "be more careful".
7. **HUMAN REVIEW GATE (mandatory).** Present the retro as a draft. List missing inputs,
   escapes with unclear root cause, and proposed owners not yet confirmed. Ask the team to
   agree before it is published.

## Output shape
```
# QA Retro - Release 4.2 (2026-09-15 to 2026-10-08)
Last retro actions: 2 done, 1 not done ("seed data script", carried over)
Went well:
  - API smoke on every PR caught 3 S2s before UAT
  - Daily triage kept S1 age under 1 day
Escapes (4):
| Defect  | Sev | Should be caught at | Why missed                         | Theme          |
|---------|-----|---------------------|------------------------------------|----------------|
| PAY-901 | S1  | API                 | refund path had no test case       | Coverage gap   |
| SRCH-77 | S2  | E2E                 | staging had 1k records, prod 2M    | Env/data drift |
| PRF-12  | S3  | Requirements        | timezone rule not in the story     | Req clarity    |
| PAY-905 | S2  | API                 | test existed, skipped since 4.0    | Coverage gap   |
Actions:
  1. Add refund + partial refund API tests | owner: payments SDET | due 10-20 | measure: in CI
  2. Report skipped tests weekly, max age 14 days | owner: QA lead | due 10-17
  3. Prod-like search dataset in staging | owner: DevOps | due 11-01
--- HUMAN REVIEW GATE ---
Owners for actions 2 and 3 not yet confirmed. Agree as a team before publishing.
```

## Guardrails
- Never fabricate a defect, quote, root cause, or action-item status.
- Blameless: describe gaps in process, tools, and information, never name a person as the cause.
- Cap actions at 3-5; an action without an owner and date is a wish, not a change.
- Root causes are hypotheses until the team agrees on them in the retro.
- The document is a draft until the team reviews it.
