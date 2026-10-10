---
name: locust-load-test-generator
description: >-
  Generates Locust load tests in Python from a user journey or API flow. Use when a
  performance tester says "write a Locust test", "load test this API with Python", "run
  Locust headless in CI", or pastes endpoints with a target user count. Produces a
  locustfile with HttpUser classes, weighted tasks, wait_time, and response checks, plus
  the headless run command, a draft the engineer smoke-tests before a real run.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: performance
  version: 1.0.0
---

# Locust Load Test Generator

You write **locustfiles that model how real users mix their actions**: weighted tasks,
realistic think time, and named requests so the stats table stays readable.

## When to use
- A Python team wants load tests as plain code in the repo.
- A journey needs a weighted traffic mix (browse a lot, buy a little).
- Locust must run headless in CI and fail the job when errors or latency are too high.

## Workflow
1. **Collect the traffic mix.** Endpoints, payloads, auth, action ratios, think time,
   users, spawn rate, and duration. Ask; never invent ratios or SLOs.
2. **Model users.** One `HttpUser` per persona with `wait_time = between(a, b)`; log in
   in `on_start` with credentials from env vars; a class-level `weight` mixes personas.
3. **Weight the tasks.** `@task(n)` mirrors production ratios; `name=` groups dynamic URLs
   so `/products/42` and `/products/43` share one stats row.
4. **Check responses.** `catch_response=True` and `resp.failure()` for a 200 with a bad body.
5. **Gate in CI.** No built-in thresholds: an `events.quitting` listener sets
   `environment.process_exit_code = 1` on a high `fail_ratio`. `LoadTestShape` for stages.
6. **List assumptions and the run plan**: smoke with `-u 1 -t 1m`, then the full headless
   run; use `--master` and `--worker` when one machine cannot generate the load.

## Output shape
```python
# locustfile.py
import os
from locust import HttpUser, task, between, events

class Shopper(HttpUser):
    wait_time = between(1, 4)  # think time in seconds
    def on_start(self):
        resp = self.client.post("/api/auth/login", json={
            "email": os.environ["LOAD_USER"], "password": os.environ["LOAD_PASSWORD"]})
        self.client.headers.update({"Authorization": f"Bearer {resp.json()['token']}"})

    @task(6)
    def browse(self):
        self.client.get("/api/products?page=1", name="/api/products")

    @task(3)
    def view_product(self):
        with self.client.get("/api/products/42", name="/api/products/[id]",
                             catch_response=True) as resp:
            if resp.status_code != 200 or "price" not in resp.text:
                resp.failure(f"bad product response: {resp.status_code}")

    @task(1)
    def add_to_cart(self):
        self.client.post("/api/cart", json={"sku": "ABC-1", "qty": 1})

@events.quitting.add_listener
def _(environment, **kwargs):
    if environment.stats.total.fail_ratio > 0.01:
        environment.process_exit_code = 1

# locust -f locustfile.py --headless -u 100 -r 10 -t 15m \
#   --host https://staging.example.com --csv results/run1 --html results/run1.html
```

## Guardrails
- The locustfile is a **draft the engineer must smoke-test** before a full-load run.
- Never fabricate endpoints, payload fields, task ratios, or SLOs; ask for real numbers.
- Only load-test systems you own or are authorized to test; prod needs sign-off.
- Watch worker CPU; a saturated load generator reports its own slowness as server latency.
