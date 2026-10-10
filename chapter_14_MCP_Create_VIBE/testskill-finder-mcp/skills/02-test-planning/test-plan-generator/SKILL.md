---
name: test-plan-generator
description: >-
  Turn a JIRA ticket into a review-ready test plan. Use when a tester or QA lead
  says "write a test plan for JIRA-1234", "plan testing for this story", "what
  should we test here", or pastes an acceptance-criteria / user-story ticket.
  Fetches the ticket, analyzes it for gaps and ambiguities, fills the standard
  test-plan template, and stops for human review before anything is treated as final.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Planning
  version: 1.0.0
---

# Test Plan Generator

You produce a **test plan a human still has to approve** — never a "done" artifact.
Your job is analysis + drafting + surfacing what is missing, not silent completion.

## When to use
- A JIRA key or story text is provided and someone wants testing planned.
- Someone asks "what are the risks / edge cases / gaps in this ticket".

## Workflow (follow in order)

### 1. Fetch the ticket
- If a JIRA key is given (e.g. `VOC-1234`), fetch it. Prefer an available JIRA MCP
  tool. If none, run `scripts/fetch_jira.sh VOC-1234` (needs `JIRA_BASE_URL`,
  `JIRA_EMAIL`, `JIRA_TOKEN` env vars). If neither works, ask the user to paste the
  ticket body — **do not invent ticket content.**
- Capture: summary, description, acceptance criteria, components, linked issues,
  attachments, and the fix version / sprint.

### 2. Analyze & find the missing pieces
Run the ticket through `references/requirement-checklist.md`. For every item, mark
✅ present / ⚠️ ambiguous / ❌ missing. Explicitly list:
- Missing or vague acceptance criteria
- Undefined edge cases, error states, empty/limit/boundary conditions
- Unstated non-functional needs (perf, security, a11y, i18n, permissions/roles)
- Missing test data, environments, or dependencies
- Ambiguous wording that two engineers could read two ways

Output this as a **"Gaps & Questions for the author"** section. This is the most
valuable part — a tester's leverage is asking the question before the bug ships.

### 3. Draft the test plan
Fill `references/test-plan-template.md` completely. Derive test scenarios from the
acceptance criteria and the gaps you found. Cover positive, negative, boundary,
and cross-role/permission paths. Tag each scenario P0/P1/P2 by risk.

### 4. STOP for human review (mandatory)
End with a **Human Review Gate**:
- Summarize what you assumed and what you could not confirm.
- List the open questions from step 2 that block sign-off.
- Ask the tester to confirm/edit before the plan is considered approved.
- Do **not** proceed to write test cases or automation until a human approves.

## Output shape
```
## Test Plan — <JIRA-KEY>: <title>
1. Scope & Objectives
2. Gaps & Questions for the author   <-- surface missing pieces here
3. Test Scenarios (P0/P1/P2)
4. Test Data & Environment
5. Risks & Assumptions
6. Entry / Exit criteria
--- HUMAN REVIEW GATE ---
Assumptions made / Open questions / "Approve or edit before I continue"
```

## Guardrails
- Never mark the plan "final" — a human owns sign-off.
- Never fabricate acceptance criteria; a missing AC is a finding, not a blank to fill.
- Keep scenarios traceable: each maps to an AC or a gap.

## References
- `references/requirement-checklist.md` — the gap-analysis checklist
- `references/test-plan-template.md` — the plan template to fill
- `scripts/fetch_jira.sh` — pull a ticket over the JIRA REST API
- `copilot/test-plan.prompt.md` — the same skill as a GitHub Copilot prompt file
