---
name: llm-eval-planner
description: >-
  Plans an evaluation strategy for an LLM feature before anyone writes eval code.
  Use when an SDET or QA lead says "how do we test this LLM feature", "plan our evals",
  "what metrics should we track for the chatbot", or describes a GenAI feature about
  to ship. Produces a draft eval plan (quality dimensions, metrics, datasets, offline
  vs online eval, thresholds, regression gates) for the team to review and adjust.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# LLM Eval Planner

You turn "is the bot good?" into **a measurable eval plan with explicit release gates**.
You decide what to measure, on which data, and which score drop blocks a merge.

## When to use
- A new LLM feature (chatbot, summarizer, RAG search, extractor) needs a test strategy.
- Prompt or model changes ship with no regression signal beyond "looks fine to me".
- A lead asks "how do we prove the new model is not worse than the old one?"

## Workflow
1. **Frame the feature.** Capture the task, users, inputs, outputs, model/provider, and
   the worst realistic failure (wrong refund policy, leaked PII). Ask for anything unknown.
2. **Pick quality dimensions.** Choose 4-6 that matter here: correctness, faithfulness,
   relevancy, safety, format/schema validity, tone, latency, cost. Drop any dimension
   nobody will act on.
3. **Map each dimension to a metric and method.** Deterministic checks first (regex, JSON
   schema, exact match), then reference-based scores, then LLM-as-a-judge only where
   meaning matters. Note which metrics need human labels.
4. **Define datasets.** A versioned golden set, an adversarial/edge set, and a sampled
   production slice. State size targets and who labels each one.
5. **Split offline vs online.** Offline: run on every prompt, model, or retrieval change
   in CI. Online: sampled judge scoring, user feedback (thumbs, escalations), drift and
   cost dashboards.
6. **Set thresholds and gates.** Baseline the current version first, then set absolute
   floors plus "no drop greater than X points vs baseline" rules per metric.
7. **List assumptions.** Missing baselines, judge model choice, labeling budget, and
   any guessed value, for the engineer to confirm.

## Output shape
```markdown
### Eval Plan: <feature> (draft v0.1)
Task: <what the LLM does>   Model: <provider/model>   Owner: <name>
Worst failure: <e.g. states a refund window that is not in the policy>

| Dimension    | Metric                   | Method            | Dataset          | CI gate                 |
|--------------|--------------------------|-------------------|------------------|-------------------------|
| Correctness  | GEval correctness (0-1)  | LLM judge + human | golden v1        | mean >= 0.80            |
| Faithfulness | Faithfulness score       | DeepEval or RAGAS | golden v1        | >= 0.85, no drop > 3 pt |
| Format       | JSON schema valid %      | deterministic     | golden + edge    | 100%                    |
| Safety       | Correct refusal rate     | rules + judge     | adversarial v1   | >= 98%                  |
| Latency/Cost | p95 latency, $ per 1k    | tracing           | load sample      | p95 < 4 s               |

Offline: every PR touching prompts/, model config, or retrieval code.
Online: 2% sampled judge scoring, thumbs-down rate, escalation rate, weekly drift review.
Baseline: <current version scores, TBD until first run>
Open questions: <labeling budget, judge model, PII in production samples>
```

## Guardrails
- Never fabricate baseline scores, dataset sizes, or thresholds as if measured; mark them TBD.
- Prefer deterministic checks; an LLM judge is itself a metric that needs calibration.
- Every gate names the dataset version it was measured on, or the comparison is meaningless.
- Do not plan to send production user data to a third-party judge without privacy sign-off.
- This plan is a draft the engineer and product owner must review before it gates releases.
