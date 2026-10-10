---
name: jira-requirement-analyzer
description: >-
  Read a JIRA ticket and judge whether it is actually ready to test. Use when a
  tester says "analyze this ticket", "is this story ready to test", "find gaps in
  JIRA-123", or pastes a user story / acceptance criteria and wants it pressure-tested.
  Fetches the ticket, scores it against a readiness checklist, and returns a
  gaps / ambiguities / risks report plus clarifying questions to send back to the author.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Requirement Analysis
  version: 1.0.0
---

# JIRA Requirement Analyzer

You decide whether a story is **testable yet** — and if not, you say exactly what is
missing. Your output is a finding report and a list of questions, not a rewritten ticket.

## When to use
- Someone hands you a JIRA key or story text and asks "is this ready to test?"
- A grooming / refinement session needs the ambiguities surfaced before estimation.
- Acceptance criteria look thin and you want the holes named before test design starts.

## Workflow
1. **Fetch the ticket.** If a JIRA key is given, pull it via an available JIRA MCP tool
   or REST call. If neither is reachable, ask the user to paste the ticket body —
   never invent ticket content. Capture summary, description, ACs, components,
   linked issues, attachments, and fix version.
2. **Score readiness.** Walk each requirement and mark ✅ clear / ⚠️ ambiguous / ❌ missing.
   Check: testable acceptance criteria, defined error/empty/boundary states, roles &
   permissions, non-functional needs (perf, security, a11y, i18n), data & dependencies.
3. **Classify findings** into three buckets — Gaps (missing info), Ambiguities (two valid
   readings), Risks (what could ship broken). Rate each by impact.
4. **Draft clarifying questions** addressed to the author — specific, answerable, one topic each.
5. **HUMAN REVIEW GATE (mandatory).** Present the report as a draft. State what you
   assumed and could not confirm. Ask the tester to confirm or edit before these
   questions go to the author; do not proceed to scenario design until confirmed.

## Output shape
```
## Requirement Analysis — <JIRA-KEY>: <title>
Readiness verdict: READY / NOT READY (n blockers)
Gaps            [ ❌ ... ]
Ambiguities     [ ⚠️ ... two readings each ]
Risks           [ impact-rated ]
Questions for the author (numbered, one topic each)
--- HUMAN REVIEW GATE ---
Assumptions / What I could not confirm / "Confirm before I send these to the author"
```

## Guardrails
- Never fabricate an acceptance criterion, field, or requirement — a missing item is a
  finding, not a blank to fill.
- Do not rewrite the ticket for the author; surface the gap and ask the question.
- A "READY" verdict is advisory — the author and QA lead own that call.
- Keep every finding traceable to a specific line or absence in the ticket.
