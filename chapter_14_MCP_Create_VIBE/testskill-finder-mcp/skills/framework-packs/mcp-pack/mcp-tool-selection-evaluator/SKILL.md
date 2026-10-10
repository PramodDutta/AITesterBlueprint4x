---
name: mcp-tool-selection-evaluator
description: >-
  Builds a golden question set and scoring harness that checks whether an LLM picks the
  right MCP tool with the right arguments, and reports tool-selection accuracy. Use when
  an engineer says "is the model calling the right tool", "evaluate tool selection for my
  MCP server", "build a golden set for these tools", or shares tools/list output with bad
  transcripts. Produces golden cases, a scorer, and an accuracy report draft the engineer
  runs against the real model.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: mcp
  version: 1.0.0
---

# MCP Tool Selection Evaluator

You measure **whether the model chooses the right tool, with the right arguments, for real user
questions**, and turn every miss into a concrete fix to a tool name, schema, or description.

## When to use
- Tools were added or renamed and you need to know if selection got better or worse.
- Users report the agent calls `search` when it should call `get`, or invents arguments.
- You want a release gate for an MCP server that is consumed by an LLM.

## Workflow
1. **Freeze the tool surface.** Capture `tools/list` (Inspector CLI or `client.list_tools()`) and
   store a hash of names, descriptions, and schemas; evaluate exactly what the model sees.
2. **Write golden cases.** Per tool: 3-5 asks and paraphrases, argument extraction (IDs, enums,
   numbers), confusable pairs (search vs get), multi-step asks (expect the first call), and
   negatives where no tool fits. Fields: `question`, `expected_tool` (or null), `expected_args`.
3. **Get labels reviewed.** Domain owners confirm expected tools; mark ambiguous questions and
   ask instead of forcing a label. Start with 30-50 cases and keep a held-out slice.
4. **Run the harness.** Convert MCP tools to the provider's tool format (name, description,
   input schema), send each question, and record the tool calls without executing them.
5. **Score.** Tool accuracy, argument accuracy, no-call precision on negatives, and a confusion
   matrix of expected vs chosen tool. Repeat each case (e.g. 3 runs) to measure stability.
6. **Diagnose and iterate.** Group misses by cause (overlapping descriptions, vague params, enum
   mismatch); change one thing, re-run the full set, log model id, date, tools hash, and scores.
7. **List assumptions.** Model under test, provider settings, pass threshold (e.g. tool
   accuracy >= 0.90), and labels still awaiting review.

## Output shape
```python
# golden.jsonl, one case per line:
# {"id": "G01", "question": "Find high priority login tests", "expected_tool": "search_test_cases",
#  "expected_args": {"query": "login", "priority": "high"}, "match": {"query": "contains"}}
# {"id": "G02", "question": "Steps of TC-42?", "expected_tool": "get_test_case", "expected_args": {"case_id": "TC-42"}}
# {"id": "N01", "question": "What is a smoke test?", "expected_tool": null, "expected_args": {}}

def _arg_ok(actual, expected, mode: str) -> bool:
    if mode == "contains":
        return isinstance(actual, str) and str(expected).lower() in actual.lower()
    return actual == expected

def score_case(case: dict, calls: list[dict]) -> dict:
    """calls: [{"name": str, "arguments": dict}] produced by the model under test."""
    first = calls[0] if calls else None
    if case["expected_tool"] is None:
        return {"id": case["id"], "tool_ok": first is None, "args_ok": first is None}
    tool_ok = first is not None and first["name"] == case["expected_tool"]
    modes = case.get("match", {})
    args_ok = tool_ok and all(_arg_ok(first["arguments"].get(k), v, modes.get(k, "exact"))
                              for k, v in case["expected_args"].items())
    return {"id": case["id"], "tool_ok": tool_ok, "args_ok": args_ok}

def summarize(results: list[dict]) -> dict:
    n = len(results)
    return {"cases": n, "tool_accuracy": sum(r["tool_ok"] for r in results) / n,
            "arg_accuracy": sum(r["args_ok"] for r in results) / n}
```

## Guardrails
- Never fabricate scores or model outputs; report only real runs, with model id, date, and tools hash.
- Golden labels come from people who know the domain; flag ambiguous questions, do not force them.
- The harness records tool calls without executing writes against real systems.
- LLM output varies: report sample size and repeat runs; one run is not a verdict.
- This is a draft harness and golden set for the engineer to run and verify.
