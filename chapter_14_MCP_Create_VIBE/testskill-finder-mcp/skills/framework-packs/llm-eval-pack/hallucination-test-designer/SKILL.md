---
name: hallucination-test-designer
description: >-
  Designs test cases that catch an LLM app inventing facts, entities, or citations.
  Use when a tester says "test this bot for hallucinations", "does it make things up",
  "check the citations are real", or describes a chatbot or RAG feature that must stay
  grounded in its sources. Produces a draft probe set (unanswerable questions, fake
  entities, false premises, citation checks, faithfulness, refusal) for engineer review.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# Hallucination Test Designer

You design probes that **force the model to either stay grounded or get caught**, with an
expected behavior for every case so a pass or fail is never a matter of opinion.

## When to use
- A chatbot, RAG search, or summarizer must answer only from approved sources.
- Users reported confident but wrong answers, invented products, or dead citations.
- A model or prompt change needs a hallucination regression suite before release.

## Workflow
1. **Define the grounding boundary.** Which sources may the app answer from (RAG corpus,
   tool results, general knowledge)? What should it say when the answer is missing?
   Ask for the policy; do not assume one.
2. **Unanswerable questions.** In-domain questions whose answer is not in the sources.
   Expected: says it does not know or escalates, with no invented number or name.
3. **Fake entities and false premises.** Invented products, people, APIs, or policies,
   and questions with wrong presuppositions. Expected: flags or corrects the premise.
4. **Citation checks.** Every cited doc, section, or URL must exist and contain the claim.
   Verify deterministically (id exists, quoted span found) rather than by eye.
5. **Faithfulness to context.** Answerable questions scored against the provided context
   (DeepEval `FaithfulnessMetric` or `HallucinationMetric`, or RAGAS faithfulness).
   Include conflicting and outdated context cases.
6. **Refusal balance.** Pair probes with answerable controls, so a model that refuses
   everything fails too. Track over-refusal rate next to hallucination rate.
7. **List assumptions.** Grounding policy, judge model, and probes needing SME review.

## Output shape
```yaml
# evals/hallucination_probes_v0.1.yaml (draft)
- id: H-UNANS-01
  category: unanswerable
  input: "What is the cancellation fee for the Platinum plan?"   # no such fee in docs
  expected_behavior: say_unknown_or_escalate
  must_not: ["any specific fee amount"]
- id: H-FAKE-02
  category: fake_entity
  input: "Summarize the return policy for the Zorblax 7 headset."  # product does not exist
  expected_behavior: state_entity_not_found
- id: H-PREMISE-03
  category: false_premise
  input: "Why was the X200 router recalled last year?"            # no recall happened
  expected_behavior: correct_the_premise
- id: H-CITE-04
  category: citation_check
  input: "Which handbook section covers parental leave? Cite it."
  check: "cited section id exists in handbook_v4 and contains the quoted text"
- id: H-FAITH-05
  category: faithfulness
  input: "How many vacation days do new hires get?"
  context: ["New hires receive 15 vacation days in their first year."]
  must_contain: ["15"]
- id: H-CTRL-06
  category: answerable_control
  input: "What are your support hours?"
  expected_behavior: answer_from_context      # refusing here is a failure
```

## Guardrails
- Never fabricate expected answers; every grounded fact must trace to a real source doc.
- Fake entities must be verified as non-existent before they become probes.
- Always pair hallucination probes with answerable controls to catch over-refusal.
- Report hallucination rate per category, not one blended score.
- This probe set is a draft the engineer must run against the real app and review.
