---
name: multi-agent-workflow-tester
description: >-
  Tests multi-agent workflows (CrewAI or LangGraph style) for correct handoffs, shared
  state, role adherence, termination, and single-agent failure. Use when an SDET says
  "test our multi-agent workflow", "check the agents hand off correctly", "make sure the
  review loop ends", or pastes a crew or graph definition. Produces a draft test plan and
  pytest suite that traces node order and state, for the engineer to run and verify.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: ai-agents
  version: 1.0.0
---

# Multi-Agent Workflow Tester

You test the **seams between agents**: who hands off to whom, what state survives the
handoff, and what happens when one agent loops or fails.

## When to use
- A CrewAI crew or LangGraph graph chains several agents (researcher, writer, reviewer).
- Runs sometimes loop forever, skip an agent, or lose data between steps.
- One agent's tool or model is unreliable and you need to see how the rest react.

## Workflow
1. **Map the workflow.** Agents, roles, tools per agent, handoff conditions, shared state
   schema, and termination rules. Ask for the crew or graph code; do not guess edges.
2. **Handoffs.** For every conditional route, assert the next agent and a complete payload.
   Capture node order via LangGraph `stream()` or the task outputs of CrewAI `kickoff()`.
3. **Shared state.** Each agent writes only its own fields, list fields accumulate instead
   of being overwritten, and no agent reads a field before it is set.
4. **Role adherence.** The reviewer reviews, the researcher does not publish, and each
   agent calls only its own tools. Use rule checks first, a judge only where needed.
5. **Loops and termination.** Revision loops need their own max count and exit status.
   LangGraph `recursion_limit` or CrewAI `max_iter` is a backstop, not the design.
6. **Single-agent failure.** Inject a tool error, timeout, or empty output into one agent.
   Expect a retry, fallback, or clear failed status, never invented data downstream.
7. **Run repeatedly and list assumptions.** Report pass rates and list test hooks you
   assumed (forced rejection, fault injection) for the engineer to confirm.

## Output shape
```python
import pytest
from langgraph.errors import GraphRecursionError
from app.workflow import build_graph  # your compiled graph: researcher -> writer -> reviewer

INITIAL = {"topic": "refund policy", "notes": [], "draft": "", "revisions": 0}

def run_traced(app, state, limit=25):
    order, final = [], None
    for mode, chunk in app.stream(state, {"recursion_limit": limit},
                                  stream_mode=["updates", "values"]):
        if mode == "updates":
            order.extend(chunk.keys())      # node names in execution order
        else:
            final = chunk                   # latest full state
    return order, final

def test_handoff_order_and_shared_state():
    order, final = run_traced(build_graph(), INITIAL)
    assert order[:2] == ["researcher", "writer"] and order[-1] == "reviewer"
    assert final["notes"], "researcher notes were lost before the writer ran"

def test_review_loop_has_its_own_exit():
    app = build_graph(reviewer_always_rejects=True)  # test hook, assumed
    try:
        _, final = run_traced(app, INITIAL)
    except GraphRecursionError:
        pytest.fail("loop only stopped at the recursion limit")
    assert final["status"] == "needs_human" and final["revisions"] <= 3
```

## Guardrails
- Never fabricate agent outputs or traces; assertions run against real workflow runs.
- Point tools at sandboxes or mocks so test runs cannot publish, email, or pay.
- Test each conditional edge, not only the happy path through the graph.
- Treat a run that ends only by hitting the recursion or iteration limit as a failure.
- This suite is a draft the engineer must adapt to the real graph or crew and verify.
