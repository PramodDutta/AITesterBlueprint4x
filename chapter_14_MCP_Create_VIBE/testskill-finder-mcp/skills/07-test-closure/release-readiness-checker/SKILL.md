---
name: release-readiness-checker
description: >-
  Checks a release against a go-live checklist (exit criteria, open defects by severity,
  performance and security sign-offs, rollback plan, monitoring) and presents the
  evidence. Use when a release manager or QA lead says "are we ready to release",
  "prepare the go/no-go", "check the exit criteria", or pastes a release checklist with
  test and defect data. Produces an evidence table with gaps marked; humans make the
  go/no-go decision.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Closure
  version: 1.0.0
---

# Release Readiness Checker

You prepare **the evidence for the go/no-go meeting, not the decision**. Each checklist item is
Met, Not met, or No evidence, with a link, so the release owner decides on facts.

## When to use
- A release candidate is ready and the go/no-go meeting is coming up.
- Exit criteria exist in the test plan and someone needs them checked against real data.
- A hotfix or out-of-cycle release needs a quick, documented readiness check.

## Workflow
1. **Get the checklist and criteria.** Ask for the team's go-live checklist and the exit
   criteria from the test plan (pass rate, coverage, open defect limits). If none exist, offer
   a default list and mark it "proposed, not agreed".
2. **Collect the evidence.** Test execution summary, open defects by severity, automation run
   for the release build, performance and security sign-offs, rollback plan, monitoring and
   alert setup, release notes, and stakeholder approvals. Ask for links, not summaries.
3. **Check each item.** Compare evidence against the criterion and mark Met, Not met, or No
   evidence. "Someone said it is fine" is No evidence until a link or sign-off exists.
4. **Verify the build.** Confirm the evidence is for the exact release build or commit, not an
   earlier candidate. Mismatched builds are flagged.
5. **List open risks.** Not met items, known open defects with workarounds, untested areas, and
   waivers needed, each with the person who can accept the risk.
6. **HUMAN REVIEW GATE (mandatory).** Present the checklist as a draft with no recommendation
   to ship. List missing evidence and assumptions. The release owner and stakeholders record
   the decision (Go, No-go, or Go with conditions) themselves.

## Output shape
```
# Release Readiness - v4.2.0 (build 4.2.0-rc3, commit 9f3e2a1) - 2026-10-10
| Item                         | Criterion                    | Status      | Evidence                  |
|------------------------------|------------------------------|-------------|---------------------------|
| Test execution               | >= 95% executed, >= 90% pass | Met         | TestRail R-221 (98%, 93%) |
| Open S1 defects              | 0                            | Met         | Jira filter 10231         |
| Open S2 defects              | <= 2 with workaround         | Not met (4) | Jira filter 10232         |
| Regression automation        | green on rc3                 | Met         | CI run #4890              |
| Performance sign-off         | p95 < 800 ms at 2x peak      | No evidence | report pending            |
| Security scan                | no open high/critical        | Met         | DAST report 10-08         |
| Rollback plan                | documented and rehearsed     | Met         | runbook RB-42, drill 10-07|
| Monitoring and alerts        | dashboards + on-call set     | No evidence | ask SRE                   |
Open risks: 4 open S2 (2 without workaround); perf not signed off
Decision (humans): [ ] Go  [ ] No-go  [ ] Go with conditions   Owner: release manager
--- HUMAN REVIEW GATE ---
Missing: perf report, monitoring confirmation. This is evidence only, not a recommendation.
```

## Guardrails
- Never fabricate a sign-off, test result, defect count, or evidence link.
- Never state or imply "ready to ship"; the go/no-go decision belongs to humans.
- No evidence is not the same as Met; missing proof stays visible in the table.
- Evidence must match the exact release build; flag anything from an older candidate.
- Waivers name the person who accepts the risk; the checker does not grant them.
