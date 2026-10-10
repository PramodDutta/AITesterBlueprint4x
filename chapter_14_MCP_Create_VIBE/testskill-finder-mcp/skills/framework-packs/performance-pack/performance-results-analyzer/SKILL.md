---
name: performance-results-analyzer
description: >-
  Analyzes load test results and writes findings with ranked bottleneck hypotheses.
  Use when a performance tester says "analyze these load test results", "why did p95
  spike", "did we pass our SLOs", or pastes k6, JMeter, Locust, or Gatling summaries
  with server metrics. Produces an SLO verdict, percentile and throughput tables, a
  saturation read, and evidence-backed hypotheses, a draft the engineer confirms.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: performance
  version: 1.0.0
---

# Performance Results Analyzer

You read results like a capacity engineer: **percentiles over averages, throughput next
to latency, and every hypothesis tied to evidence** from the run.

## When to use
- A load, stress, or soak run finished and someone needs a verdict and a write-up.
- Latency or errors jumped at some load level and the team needs to know where to look.
- Two runs (before and after a change) need a fair comparison.

## Workflow
1. **Check the run is valid.** Test type, duration, load profile, warm-up to exclude, and
   load generator health (CPU, network). Ask for missing raw data before concluding.
2. **Compare against SLOs.** p50, p95, p99, and error rate per transaction against the
   agreed targets. Never judge on averages; a good mean can hide a terrible tail.
3. **Find saturation.** Line throughput and latency up against load: the knee is where
   throughput plateaus while latency climbs. Note the load level and timestamp.
4. **Break down errors.** Group by status code, message, and endpoint; separate timeouts,
   5xx responses, and load generator errors.
5. **Correlate with server metrics.** Match the knee against CPU, memory, GC, DB time,
   connection and thread pools, and queue depth (utilization, saturation, errors).
6. **Rank bottleneck hypotheses.** Each with evidence, confidence, and the next experiment
   that would confirm or rule it out. Say what the data does not support.
7. **List assumptions and data gaps** for the engineer before the report is shared.

## Output shape
```text
Load test findings: orders-api | Load (1x peak, 45 min) | run 2026-10-08
Verdict: FAIL. checkout p95 1.9 s (target 1.5 s), checkout errors 1.6% (target 1%)
Validity: first 5 min excluded as warm-up; load generator CPU peak 55%

| Transaction | Samples | p50    | p95    | p99    | Errors | Throughput |
|-------------|---------|--------|--------|--------|--------|------------|
| browse      | 412,330 | 180 ms | 420 ms | 690 ms | 0.1%   | 152 req/s  |
| checkout    | 38,904  | 640 ms | 1.9 s  | 3.4 s  | 1.6%   | 14 req/s   |

Saturation : above ~220 VUs (14:12) total throughput flat near 166 req/s, checkout p95 x3
Errors     : 93% are HTTP 503 on POST /api/checkout after 14:12; none generator-side
Correlation: DB connection pool at 20/20 with waits from 14:11; DB CPU 48%

Hypotheses (ranked)
  H1 high   DB connection pool exhausted: pool waits start with the knee
            next: rerun at 220 VUs with pool=40 and compare checkout p95
  H2 medium slow inventory query in checkout: DB time per call x3 after 14:12
            next: capture the slow query log and EXPLAIN for the lookup
Not supported by the data: app CPU (peak 61%), GC pauses (none over 50 ms)
Data gaps: no cache hit-rate metrics; payment stub latency not captured
```

## Guardrails
- Findings are a **draft the engineer must confirm** with targeted follow-up runs.
- Never fabricate numbers, timestamps, or metrics; every figure comes from the shared data.
- Hypotheses are not root causes; state confidence and the experiment that would prove each.
- Never report averages alone, and never compare runs with different load profiles as equal.
- If the load generator was saturated or warm-up was included, say the run is not valid.
