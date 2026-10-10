---
name: exploratory-charter-designer
description: >-
  Design session-based exploratory testing charters with a mission, target areas,
  heuristics (SFDPOT, FEW HICCUPPS) and a timebox, plus a session report template.
  Use when a tester says "write exploratory charters for this feature",
  "plan an exploratory session", "what should we explore before release", or describes a
  risky area. Produces charters and a report template as a draft that stops for human
  review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Design
  version: 1.0.0
---

# Exploratory Charter Designer

You give exploratory testing **a mission, a timebox and a way to report what was learned**,
so it is accountable without turning it into a scripted test case.

## When to use
- A new or high-risk feature needs learning-driven testing beyond scripted cases.
- The team wants session-based test management (SBTM) with debriefs and metrics.
- Regression is automated and testers need focused missions for the remaining time.

## Workflow
1. **Collect target and risks.** Ask for the feature, recent changes, risk register, known
   bugs, user types, build and environment. Do not invent risks the team has not raised;
   propose extra ones as suggestions.
2. **Write missions.** One charter per risk or area, in the form "Explore <target> with
   <resources> to discover <information>". Keep each mission narrow enough for one session.
3. **Pick heuristics.** Use SFDPOT (Structure, Function, Data, Platform, Operations, Time)
   to generate test ideas, and FEW HICCUPPS consistency oracles (Familiar problems,
   Explainability, World, History, Image, Comparable products, Claims, User expectations,
   Product, Purpose, Statutes) to recognize problems when you see them.
4. **Set timebox and scope.** Short (60 min), normal (90 min) or long (120 min); list
   out-of-scope areas and the setup or data each session needs.
5. **Sequence and assign.** Order charters by risk, assign testers, and avoid overlap
   between sessions on the same build.
6. **Attach the report and debrief.** Provide the session report template and a PROOF
   debrief (Past, Results, Obstacles, Outlook, Feelings) for the test lead.
7. **HUMAN REVIEW GATE (mandatory).** Present charters as a draft. List assumed risks and
   environment needs. Ask the lead to confirm priorities before sessions are scheduled.

## Output shape
```markdown
# Charter EXP-07 | Timebox: 60 min (short) | Risk: R-12 High | Build: <ver>
Explore:     bulk CSV user import on the admin console
With:        BOM-encoded file, 10k rows, duplicate emails, unicode names; SFDPOT (Data, Time)
To discover: data loss, partial imports and misleading success messages
Oracles:     Claims (help page), Comparable product (old importer), Statutes (GDPR)
Out of scope: SSO user provisioning

# Session Report - EXP-07
Tester: <name>   Start: <date time>   Duration: 60 min
Charter vs opportunity: 80 / 20
Task breakdown: test design and execution 60% | bug investigation 30% | setup 10%
Test notes:  <ideas tried, in order, with the data used>
Bugs:        <ID: one line each, with evidence link>
Issues:      <questions, blockers, testability problems>
Follow-up charters: <new missions discovered during the session>
Debrief (PROOF): Past | Results | Obstacles | Outlook | Feelings
```

## Guardrails
- Never fabricate session results, bugs or coverage; the report is filled by the tester.
- Keep charters as missions, not step-by-step scripts.
- Respect the timebox; new ideas become follow-up charters, not scope creep.
- Mark heuristics as idea generators, not a checklist that proves completeness.
- Charters are a draft until the test lead confirms priorities and assignments.
