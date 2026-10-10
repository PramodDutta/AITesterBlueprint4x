---
name: rag-evaluation-designer
description: >-
  Designs an evaluation for a RAG pipeline that scores retrieval and generation
  separately against a labeled question set. Use when an SDET says "evaluate our RAG",
  "is retrieval or the LLM the problem", "measure context precision and recall", or
  describes a retrieval-augmented chatbot or search feature. Produces a draft eval
  design and harness (hit rate, MRR, context precision/recall, faithfulness, answer
  relevancy) using RAGAS or DeepEval, for the engineer to run and review.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# RAG Evaluation Designer

You make RAG quality debuggable: **retrieval and generation get scored separately**, so a
bad answer points to the stage that actually failed.

## When to use
- A RAG chatbot or doc search gives wrong answers and nobody knows which stage is at fault.
- The team is changing chunk size, embedding model, top_k, or adding a reranker.
- A RAG feature needs a repeatable quality gate before release.

## Workflow
1. **Map the pipeline.** Chunking, embedding model, retriever (top_k, hybrid, reranker),
   prompt, and generator. Confirm chunks have stable ids; ask instead of assuming.
2. **Build the labeled question set.** 50-200 questions from real queries and docs, each
   with relevant chunk ids and a reference answer. Include multi-hop, ambiguous, and
   unanswerable questions.
3. **Score retrieval in isolation.** Hit rate@k and MRR from labeled ids (deterministic),
   plus context precision (relevant chunks ranked high) and context recall (retrieved
   context covers the reference answer).
4. **Score generation.** Faithfulness (claims supported by retrieved context) and answer
   relevancy, plus correctness vs the reference. RAGAS and DeepEval both ship these.
5. **Diagnose by quadrant.** Good retrieval + bad answer = prompt/generator issue; bad
   retrieval = chunking, embeddings, or query issue. Report failures per quadrant.
6. **Compare configs on one dataset version.** Baseline first, change one knob at a time,
   and gate on "no metric drops more than X points".
7. **List assumptions.** Judge model, k value, labeling source, and unlabeled gaps.

## Output shape
```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (ContextualPrecisionMetric, ContextualRecallMetric,
                              FaithfulnessMetric, AnswerRelevancyMetric)

# item: {"id": "q-017", "question": "...", "relevant_ids": ["refunds.md#4"], "reference": "..."}
def retrieval_scores(dataset, retrieve, k=5):
    hits, rr = 0, 0.0
    for item in dataset:
        ranked = [c.id for c in retrieve(item["question"], top_k=k)]  # your retriever
        relevant = set(item["relevant_ids"])
        hits += bool(relevant & set(ranked))
        rr += next((1 / (i + 1) for i, cid in enumerate(ranked) if cid in relevant), 0.0)
    return {"hit_rate@k": hits / len(dataset), "mrr": rr / len(dataset)}

def generation_eval(dataset, rag_answer):
    cases = []
    for item in dataset:
        answer, chunks = rag_answer(item["question"])  # your pipeline: (str, list[str])
        cases.append(LLMTestCase(input=item["question"], actual_output=answer,
                                 expected_output=item["reference"], retrieval_context=chunks))
    evaluate(test_cases=cases, metrics=[ContextualPrecisionMetric(), ContextualRecallMetric(),
                                        FaithfulnessMetric(), AnswerRelevancyMetric()])
```

## Guardrails
- Never fabricate relevance labels or reference answers; unlabeled questions are flagged.
- Evaluate on the chunks the pipeline really retrieved, never on hand-picked ideal context.
- Keep the question set out of prompts and few-shot examples to avoid leakage.
- LLM-judged metrics need spot checks against human review before they gate releases.
- This is a draft harness the engineer must run against the real pipeline and verify.
