---
name: llm-judge-rubric-designer
description: >-
  Designs LLM-as-a-judge rubrics with G-Eval style criteria, explicit evaluation steps,
  and anchored scoring scales. Use when an SDET says "write a judge prompt for this",
  "design a rubric for grading answers", "can we trust the LLM judge", or pastes sample
  outputs that need consistent grading. Produces a draft rubric, a calibration plan
  against human labels, and bias checks, for the engineer to run and tune.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: llm-eval
  version: 1.0.0
---

# LLM Judge Rubric Designer

You design judges that **agree with careful humans before they are allowed to gate a
release**. A judge without calibration is just another unverified model output.

## When to use
- A quality dimension (helpfulness, tone, correctness) cannot be checked with regex or
  exact match and needs an LLM judge.
- An existing judge prompt gives scores nobody trusts or that drift between runs.
- The team wants pairwise A/B comparison of two prompts or models.

## Workflow
1. **Define what is judged.** One dimension per judge, single-output scoring or pairwise.
   Collect 5-10 real good and bad outputs first; ask for them instead of inventing them.
2. **Write criteria and evaluation steps.** G-Eval style: a one-sentence criterion plus
   3-6 concrete steps the judge follows. Replace "is it good" with observable checks.
3. **Choose the scale.** Binary pass/fail or a 1-5 scale with an anchor description for
   every point. Prefer binary or 3-point when humans cannot agree on finer grades.
4. **Calibrate against human labels.** 50-100 items labeled by two or more people. Measure
   human-human agreement first, then judge-human agreement (weighted Cohen's kappa or %
   agreement). Revise steps where they disagree and re-measure.
5. **Check for bias.** Position bias: swap A/B order and require the same verdict. Verbosity
   bias: pad a correct answer and confirm the score does not rise. Self-preference: avoid
   judging with the generator's own model family. Leniency: inspect the score histogram.
6. **Lock and version.** Pin judge model, temperature 0, and rubric version; re-calibrate
   whenever any of them changes.
7. **List assumptions.** Judge model, label source, agreement target, and open gaps.

## Output shape
```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams
from sklearn.metrics import cohen_kappa_score

helpfulness_judge = GEval(
    name="Support Helpfulness v1.2",
    evaluation_steps=[
        "Check whether the actual output directly answers the question in the input.",
        "Penalize any claim that contradicts or goes beyond the expected output.",
        "Check that a concrete next step is given (link, setting, or contact path).",
        "Do not reward length: a short complete answer scores as high as a long one.",
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT,
                       LLMTestCaseParams.EXPECTED_OUTPUT],
    threshold=0.7,
)

# Calibration: the same items graded by humans and by the judge, bucketed to 1-5
human = load_scores("labels/calibration_v1.csv", column="human")   # your loader
judge = load_scores("labels/calibration_v1.csv", column="judge")
kappa = cohen_kappa_score(human, judge, weights="quadratic")
print(f"weighted kappa = {kappa:.2f} (agree a target, e.g. >= 0.6, before gating CI)")
```

## Guardrails
- Never fabricate human labels or agreement numbers; calibration needs real annotators.
- One rubric, one dimension; a combined "overall quality" score hides what failed.
- Report bias-check results alongside the rubric, including the ones that failed.
- Treat the judge as a test instrument: version it and recalibrate when it changes.
- This rubric is a draft the engineer must calibrate and verify before it gates releases.
