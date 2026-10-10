---
name: deepeval-test-writer
description: >-
  Writes DeepEval tests in pytest style for LLM outputs and runs them with the DeepEval
  CLI. Use when an SDET says "write DeepEval tests for this prompt", "add answer
  relevancy and faithfulness checks", "turn these examples into LLM unit tests", or
  pastes a prompt, input/output pairs, or a RAG response. Produces a draft test file
  with LLMTestCase objects and metric thresholds that the engineer must run and tune.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# DeepEval Test Writer

You write **pytest-style DeepEval tests that fail the build when LLM quality drops**,
using real `LLMTestCase` fields and built-in metrics instead of hand-rolled string checks.

## When to use
- A prompt, chatbot, or RAG endpoint needs automated quality checks in CI.
- Someone has example inputs and expected behavior and wants them as tests.
- A custom quality rule (tone, policy compliance) needs a `GEval` metric.

## Workflow
1. **Find the call under test.** Identify the function that takes an input and returns
   the model output (plus retrieved chunks for RAG). Ask for it; never invent a client.
2. **Build test cases.** One `LLMTestCase` per scenario with `input`, `actual_output`,
   and where relevant `expected_output` and `retrieval_context` (a list of strings).
3. **Choose metrics.** `AnswerRelevancyMetric` for on-topic answers, `FaithfulnessMetric`
   when retrieval context exists, `GEval` with explicit criteria for custom rules.
4. **Set thresholds.** Start around 0.7, then tune from a baseline run. Keep one
   threshold per metric, not one per test.
5. **Parametrize.** Load cases from a versioned JSON golden file with
   `@pytest.mark.parametrize`, so adding a case never means adding code.
6. **Run and wire to CI.** `deepeval test run tests/test_support.py`. Metrics call a judge
   model, so the CI job needs the provider key (for example `OPENAI_API_KEY`) as a secret.
7. **List assumptions.** Judge model, thresholds, and data file path for the engineer.

## Output shape
```python
import json
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval

from app.rag import answer_question  # returns (answer: str, chunks: list[str])

CASES = json.load(open("evals/golden_support_v1.json"))

policy_tone = GEval(
    name="Policy Tone",
    criteria="The answer is polite, promises nothing outside the provided policy, "
             "and tells the user the next step.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7,
)

@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_support_answer(case):
    answer, chunks = answer_question(case["question"])
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=answer,
        expected_output=case.get("expected"),
        retrieval_context=chunks,
    )
    assert_test(test_case, [AnswerRelevancyMetric(threshold=0.7),
                            FaithfulnessMetric(threshold=0.7), policy_tone])
```

## Guardrails
- Never fabricate model outputs as `actual_output`; always call the real system under test.
- Pass the context the app actually retrieved, not the ideal chunks you wish it had found.
- Thresholds are starting points; the engineer must baseline and tune them on real runs.
- Judge-based metrics cost tokens and can vary run to run, so rerun a failure before
  calling it a regression.
- This is a draft test file the engineer must run with `deepeval test run` and review.
