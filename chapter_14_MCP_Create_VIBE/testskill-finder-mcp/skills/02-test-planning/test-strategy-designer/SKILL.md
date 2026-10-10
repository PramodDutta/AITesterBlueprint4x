---
name: test-strategy-designer
description: >-
  Write a product or release level test strategy covering test levels, test types,
  environments, tooling, automation approach, risk, entry/exit criteria and roles.
  Use when a QA lead says "write a test strategy for this product",
  "define our testing approach for the release",
  "what should our automation pyramid look like", or describes a product and team.
  Produces a strategy document draft that stops for human review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Planning
  version: 1.0.0
---

# Test Strategy Designer

You define **how this product gets tested, release after release**, not what to test in
one ticket. Per-story plans come later and inherit the rules you set here.

## When to use
- A new product, team or major release needs an agreed testing approach.
- Testing happens ad hoc and nobody can say which test types run where, or who owns them.
- Leadership asks for entry/exit criteria, automation targets or a quality gate definition.

## Workflow
1. **Gather context.** Ask for the product shape (web, mobile, API, integrations), release
   cadence, team size and skills, current tools, compliance needs (PCI, HIPAA, GDPR) and
   recent production incidents. Do not assume a compliance regime or a tool stack.
2. **Set scope and test levels.** State in-scope and out-of-scope areas, then define unit,
   API/contract, integration, E2E and UAT levels with an owner for each.
3. **Choose test types.** For functional, API, performance, security and accessibility
   (plus compatibility, localization or migration when relevant) give the approach, tool,
   environment, owner and trigger (per PR, nightly, per release).
4. **Define the automation approach.** Target pyramid ratio, what qualifies for automation
   (stable, high value, repeated), what stays manual or exploratory, and the CI gates.
5. **Cover environments, data and risk.** Environment chain, data approach (masked or
   synthetic), and the risk method that decides test depth.
6. **Write entry/exit criteria, defect process and roles.** Measurable criteria, severity
   definitions, triage cadence, fix SLAs and a RACI for sign-off.
7. **HUMAN REVIEW GATE (mandatory).** Present the strategy as a draft. List assumptions,
   every `<TBD>` threshold and open questions. Ask the QA lead and stakeholders to approve
   before teams plan against it.

## Output shape
```markdown
# Test Strategy - ShopFast Web + API, Release 2026.4
1. Scope: checkout, catalog, account | Out: legacy admin (frozen)
2. Levels: unit (dev) | API/contract (SDET) | integration | E2E UI (QA) | UAT (PO)
3. Test types
   | Type          | Approach                         | Tool        | Trigger     | Owner  |
   | Functional    | risk-based, ACs to cases         | Xray        | per story   | QA     |
   | API           | contract + negative per endpoint | Playwright  | per PR      | SDET   |
   | Performance   | load at 2x peak, p95 < <TBD> ms  | k6          | per release | Perf   |
   | Security      | OWASP Top 10 DAST on staging     | ZAP         | nightly     | AppSec |
   | Accessibility | WCAG 2.2 AA: axe scan + keyboard | axe-core    | per release | QA     |
4. Automation: pyramid target 70 unit / 20 API / 10 UI; PR gate = smoke + API suite
5. Environments: dev -> QA (synthetic data) -> staging (masked prod copy) -> prod
6. Risk: likelihood x impact per feature; High = full depth + exploratory charters
7. Entry: build deployed, smoke green, ACs approved
   Exit: 0 open S1/S2, 100% P0 executed, P1 pass rate >= <TBD>%
8. Defects: Jira, severity S1-S4, daily triage, S1 fix SLA <TBD> hours
9. Roles: QA lead owns strategy, SDETs own automation, PO signs UAT
10. Risks, assumptions, open questions
--- HUMAN REVIEW GATE ---
```

## Guardrails
- Never fabricate thresholds, SLAs or compliance requirements; leave `<TBD>` and ask.
- Keep it release-level: no per-ticket test cases (that belongs in a test plan).
- Name only tools the team has or has agreed to adopt; flag any new tool as a proposal.
- Every exit criterion must be measurable from data the team already collects.
- The strategy is a draft until the QA lead and stakeholders approve it.
