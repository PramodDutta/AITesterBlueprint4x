---
name: k6-load-test-generator
description: >-
  Generates k6 load test scripts from a workload description or API flow. Use when a
  performance tester says "write a k6 script for this API", "load test this endpoint
  with k6", "add thresholds for p95 and error rate", or pastes a user journey with a
  target load. Produces a script with scenarios, stages, thresholds, checks, groups, and
  env vars, a draft the engineer validates with a smoke run before any real load.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: performance
  version: 1.0.0
---

# K6 Load Test Generator

You write k6 scripts where **pass or fail is decided by thresholds, not by eyeballing
graphs**. Load shape, checks, and SLOs live in the script so CI can gate on them.

## When to use
- An API or user journey needs a repeatable load, stress, soak, or spike script.
- A team wants k6 in CI with a failing exit code when SLOs are missed.
- An existing script has no thresholds, hard-coded hosts, or no checks.

## Workflow
1. **Collect the workload.** Journey steps, payloads, auth, target load, duration, SLOs; ask.
2. **Pick the executor.** `ramping-vus` for a closed model with stages;
   `constant-arrival-rate` or `ramping-arrival-rate` when the target is throughput.
3. **Encode SLOs as thresholds.** `p(95)` latency, `http_req_failed` rate, per-group limits.
4. **Add checks and groups.** `check()` for status and key fields plus a `checks` threshold
   (failed checks alone never fail a run); one `group()` per business step.
5. **Parameterize.** Hosts and tokens via `__ENV` and `-e`, data via `SharedArray`.
6. **List assumptions and the run plan**: 1 VU smoke run first; k6 exits non-zero on a
   failed threshold, so CI can gate on `k6 run -e BASE_URL=... -e TOKEN=... load.js`.

## Output shape
```javascript
import http from 'k6/http';
import { check, group, sleep } from 'k6';
const BASE_URL = __ENV.BASE_URL || 'https://staging.example.com';
export const options = {
  scenarios: {
    shoppers: {
      executor: 'ramping-vus',
      stages: [
        { duration: '2m', target: 50 },  // ramp up
        { duration: '10m', target: 50 }, // steady state
        { duration: '2m', target: 0 },   // ramp down
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
    'http_req_duration{group:::checkout}': ['p(95)<800'],
    checks: ['rate>0.99'],
  },
};

export default function () {
  group('browse', () => {
    check(http.get(`${BASE_URL}/api/products`), { 'browse 200': (r) => r.status === 200 });
  });
  group('checkout', () => {
    const res = http.post(`${BASE_URL}/api/cart`, JSON.stringify({ sku: 'ABC-1', qty: 1 }), {
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${__ENV.TOKEN}` },
    });
    check(res, { 'cart is 201': (r) => r.status === 201 });
  });
  sleep(1 + Math.random() * 3); // think time
}
```

## Guardrails
- The script is a **draft the engineer must smoke-test** before applying real load.
- Never fabricate SLOs, target load, endpoints, or payloads; ask for the numbers.
- Only load-test systems you own or are authorized to test; prod needs sign-off.
- A saturated load generator (CPU, network) invalidates results; watch it during the run.
- Never hard-code tokens in the script; pass them with `-e` from CI secrets.
