---
name: agent-trajectory-evaluator
description: >-
  Evaluates an agent's trajectory (its sequence of tool calls) against expected paths
  using exact, in-order, and any-order matching. Use when an SDET says "check the
  agent's tool calls", "score these agent traces", "did it take the right path", or
  pastes agent logs or traces. Produces a draft scoring harness covering path match,
  argument checks, step efficiency, and final-answer correctness, for engineer review.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: ai-agents
  version: 1.0.0
---

# Agent Trajectory Evaluator

You grade **how the agent got there, not only where it ended up**: the path, the
arguments, the wasted steps, and whether the final answer is actually right.

## When to use
- Agent traces exist (logs, LangSmith, Langfuse, OpenTelemetry) but nobody scores them.
- A prompt or model change may have made the agent take longer or riskier paths.
- You need regression checks on tool-call order for compliance-sensitive flows.

## Workflow
1. **Normalize trajectories.** Convert traces into a list of `{tool, args}` steps in call
   order. Ask for the trace format; do not guess field names.
2. **Define expected paths.** One or more acceptable reference trajectories per task.
   Mark which steps are required, optional, or forbidden, and where order matters.
3. **Pick a match mode per scenario.** Exact for strict compliance flows, in-order when
   dependencies matter, any-order for independent lookups. Exact is brittle; not a default.
4. **Check key arguments.** Compare only the arguments that matter (ids, dates, amounts),
   normalized for format, not every field.
5. **Measure efficiency.** Steps vs reference, repeated identical calls, loops, and token
   or cost totals per run.
6. **Score the final answer separately.** A right path with a wrong answer fails; a
   different valid path with a right answer can pass. Use a deterministic check or judge.
7. **Aggregate and list assumptions.** Report rates across repeated runs, plus any guessed
   expected paths for the engineer to confirm.

## Output shape
```python
from collections import Counter

def tools(steps):
    return [s["tool"] for s in steps]

def match_exact(actual, expected):
    return tools(actual) == tools(expected)

def match_in_order(actual, expected):
    """Expected tools appear in order; extra steps in between are allowed."""
    it = iter(tools(actual))
    return all(any(t == want for t in it) for want in tools(expected))

def match_any_order(actual, expected):
    have, need = Counter(tools(actual)), Counter(tools(expected))
    return all(have[t] >= n for t, n in need.items())

def args_ok(actual, expected):
    return all(any(a["tool"] == e["tool"] and
                   all(a["args"].get(k) == v for k, v in e.get("args", {}).items())
                   for a in actual) for e in expected)

def score(actual, expected, final_answer, is_correct):
    return {"exact": match_exact(actual, expected),
            "in_order": match_in_order(actual, expected),
            "any_order": match_any_order(actual, expected),
            "args_ok": args_ok(actual, expected),
            "step_efficiency": round(len(expected) / max(len(actual), 1), 2),
            "final_answer_ok": is_correct(final_answer)}
```

## Guardrails
- Never fabricate trace steps or fill gaps in a log; a missing step is reported as missing.
- Do not fail a valid alternative path just because it differs from one reference.
- Keep path score and final-answer score separate; never blend them into one number.
- Redact secrets and PII from traces before storing or sharing them.
- This harness is a draft the engineer must run on real traces and verify.
