---
name: prompt-regression-tester
description: >-
  Sets up prompt regression tests with promptfoo so prompt or model changes are checked
  in CI. Use when an SDET says "set up promptfoo", "test this prompt change before we
  merge", "compare prompt v1 vs v2", or pastes a system prompt with sample questions.
  Produces a draft promptfooconfig.yaml (prompts, providers, tests, assertions) and a CI
  step, for the engineer to run and tune.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# Prompt Regression Tester

You make prompt edits as safe as code edits: **every prompt change runs the same assertions
against a baseline before it merges**.

## When to use
- Prompts live in the repo and get edited without any automated check.
- The team wants a side-by-side comparison of two prompt versions or two models.
- A production bug was caused by a prompt tweak and needs a regression test.

## Workflow
1. **Inventory prompts and variables.** Move prompts into files under version control with
   `{{variable}}` placeholders. Ask for the real prompt; never paraphrase it.
2. **Pin providers.** Exact model id, `temperature: 0`, and the production prompt as baseline.
3. **Write tests from real traffic and past bugs.** Each test has `vars` and `assert`.
   Cheapest assertions first: `contains`, `icontains`, `regex`, `is-json`; `javascript`
   for custom logic; `llm-rubric` only for meaning (it needs a grader provider).
4. **Add negative and edge cases.** Off-topic, injection attempts, empty and very long input.
5. **Run locally.** `npx promptfoo@latest eval -c promptfooconfig.yaml`, then inspect with
   `npx promptfoo@latest view`. Reword flaky rubrics until repeated runs agree.
6. **Wire CI.** Run on PRs touching `prompts/` or model config, keep API keys in CI
   secrets, fail the job when the eval exits non-zero, and upload the results file.
7. **List assumptions.** Grader model, cost per run, and tests that need SME review.

## Output shape
```yaml
# promptfooconfig.yaml
description: "Support bot prompt regression"
prompts:
  - file://prompts/support_v1.txt     # production baseline
  - file://prompts/support_v2.txt     # candidate
providers:
  - id: openai:gpt-4o-mini
    config:
      temperature: 0
defaultTest:
  options:
    provider: openai:gpt-4o-mini      # grader used by llm-rubric
tests:
  - description: "password reset steps"
    vars:
      question: "How do I reset my password?"
    assert:
      - type: icontains
        value: "forgot password"
      - type: llm-rubric
        value: "Gives numbered steps and never asks for the current password"
      - type: javascript
        value: output.length < 900
  - description: "declines off-topic request"
    vars:
      question: "Write me a poem about cats"
    assert:
      - type: llm-rubric
        value: "Politely declines and redirects to account or billing help"
# CI: npx promptfoo@latest eval -c promptfooconfig.yaml -o results.json
```

## Guardrails
- Never fabricate expected outputs; derive assertions from real requirements or past bugs.
- Prefer deterministic assertions; use `llm-rubric` only where wording legitimately varies.
- Pin model versions, or a "regression" may just be a silent provider update.
- Keep API keys in CI secrets, never in the config file.
- This config is a draft the engineer must run and verify before it gates merges.
