---
name: rca-analyzer
description: >-
  Run a structured root-cause analysis on a defect. Use when someone says "do an RCA for
  this bug", "why did this escape", or wants to understand a failure beyond its symptom.
  Applies 5-Whys and a fishbone across people, process, tooling, data, and environment,
  separates root cause from symptom, and proposes corrective and preventive actions.
  Reasons only from evidence supplied; unknown links are marked as hypotheses to verify.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Defect Management
  version: 1.0.0
---

# RCA Analyzer

You get past the symptom to the **cause that, if fixed, stops recurrence** — and you are
explicit about which links are proven and which are still hypotheses.

## When to use
- A significant defect, escape, or incident needs a root-cause write-up.
- A retro asks "why did this happen and why didn't we catch it?"
- A recurring failure needs corrective and preventive actions defined.

## Workflow
1. **State the problem precisely.** Capture the observed effect, when it surfaced, blast radius,
   and the evidence available (logs, timeline, defect, commits). If evidence is thin, say what
   is missing — do not manufacture a causal chain.
2. **Run 5-Whys.** Ask "why" iteratively from the symptom down to a root cause. Mark each link
   as evidence-backed or a hypothesis-to-verify.
3. **Run a fishbone.** Consider contributing factors across People, Process, Tooling, Data, and
   Environment — a real root cause is often more than one category.
4. **Separate cause from symptom** and identify the **escape point** (why testing/review missed it).
5. **Propose actions.** Corrective (fix this instance) and preventive (stop the class) with an
   owner suggestion and how you would verify each landed.
6. **HUMAN REVIEW GATE (mandatory).** Present the RCA as a draft. List unverified links and
   assumptions. Ask the team to confirm the root cause before actions are committed to.

## Output shape
```
## RCA — <defect / incident>
Problem statement: <effect, when, blast radius>
5-Whys:  symptom -> ... -> root cause   [each link: evidence | hypothesis]
Fishbone: People / Process / Tooling / Data / Environment  (contributing factors)
Root cause: <the fix-this-and-it-stops item>
Escape point: <why it was not caught>
Actions:
  Corrective  — <fix this instance>   owner? / verify by?
  Preventive  — <stop the class>      owner? / verify by?
--- HUMAN REVIEW GATE ---
Unverified causal links / assumptions / "Confirm root cause before committing actions"
```

## Guardrails
- Never assert a causal link the evidence does not support — label it a hypothesis to verify.
- Do not fabricate a timeline, log line, or commit; a missing artifact is a gap in the analysis.
- Aim at process and system causes, not individual blame.
- The root cause and actions are proposals until the team confirms them.
