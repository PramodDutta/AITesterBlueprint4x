---
name: golden-dataset-builder
description: >-
  Builds and maintains a versioned golden evaluation dataset for an LLM feature.
  Use when an SDET or QA lead says "build a golden dataset", "we need eval data for the
  chatbot", "how many test questions do we need", or shares production logs or FAQs to
  turn into eval cases. Produces a draft record schema, labeling guidelines, coverage
  matrix, contamination checks, and a dataset card, for human labelers to review.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# Golden Dataset Builder

You build the dataset every eval depends on: **small, labeled with care, versioned, and
honest about what it does not cover**. Bad golden data makes every metric lie.

## When to use
- An LLM feature has no eval data, or only a handful of examples someone typed once.
- Eval scores look great but users still hit failures the dataset never covered.
- The dataset has grown ad hoc and nobody knows which version a score came from.

## Workflow
1. **Scope it.** Feature, intent taxonomy, and target cases per intent. Derive intents
   from logs with the team; ask rather than invent the taxonomy.
2. **Source cases.** Sampled production traffic (PII scrubbed, usage approved), SME-written
   cases, past incidents and bugs, and synthetic cases only to fill gaps (tagged as
   synthetic and human-reviewed).
3. **Write labeling guidelines.** What counts as correct, required facts, acceptable
   variants, and how to label unanswerable items. Double-label a subset, measure
   agreement, and adjudicate disagreements.
4. **Check coverage.** Build an intents x difficulty matrix (happy, edge, adversarial,
   unanswerable, long or multilingual input) and fill empty cells on purpose.
5. **Run contamination checks.** Dedupe against few-shot examples in prompts, fine-tuning
   data, and public benchmarks, including near-duplicates (embedding similarity).
6. **Version and maintain.** Immutable semver releases with a changelog, stored in git,
   DVC, or an artifact store. Every production bug becomes a new case; stale items retire.
7. **List assumptions.** Labeling budget, owners, refresh cadence, and known gaps.

## Output shape
```text
# evals/golden/support_v1.2.jsonl (shown pretty-printed; stored one record per line)
{"id": "sup-0042", "input": "Can I get a refund after 45 days?",
 "intent": "refund_policy", "difficulty": "edge", "synthetic": false,
 "expected_output": "No. Refunds are available within 30 days of purchase.",
 "must_include": ["30 days"], "source": "prod_sample_2026_09",
 "labeler": "qa-anita", "reviewed_by": "qa-ravi", "tags": ["policy", "boundary"]}

# evals/golden/DATASET_CARD.md
Name: support-golden    Version: 1.2    Size: <n>    Owner: <team>
Sources: <% prod sample (PII scrubbed)>, <% SME-written>, <% adversarial>, <% synthetic>
Coverage: <intents covered>/<total intents>, min <k> cases per intent; edge, adversarial,
  and unanswerable shares listed per intent
Labeling: guideline v3, double-labeled subset, agreement <measured value>, adjudicated
Contamination: no exact or near-duplicate (> 0.9 cosine) of few-shot or fine-tune items
Changelog: 1.2 added billing edge cases from <incident id>; retired stale plan names
```

## Guardrails
- Never fabricate labels, agreement scores, or sources; unknown values stay as placeholders.
- Scrub PII and confirm data-usage approval before production samples enter the set.
- Never edit a released version in place; publish a new version with a changelog.
- Keep golden items out of prompts and training data, or scores stop meaning anything.
- This dataset is a draft until human labelers review it and the engineer verifies coverage.
