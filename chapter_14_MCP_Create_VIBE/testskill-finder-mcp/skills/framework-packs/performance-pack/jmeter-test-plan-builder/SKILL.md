---
name: jmeter-test-plan-builder
description: >-
  Designs an Apache JMeter test plan for a user journey or API flow. Use when a
  performance tester says "build a JMeter test plan", "convert this flow to JMeter",
  "parameterize this with a CSV", "run JMeter from the command line", or pastes endpoints
  with a target load. Produces the plan structure (thread group, CSV data, extractors,
  assertions, timers) plus the non-GUI run and HTML report command, a draft the engineer
  builds and smoke-tests in JMeter.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: performance
  version: 1.0.0
---

# JMeter Test Plan Builder

You design a **plan that models real users and runs headless**, with correlation, test
data, and assertions in place so a green run actually means something.

## When to use
- A journey or API flow needs a JMeter plan for load, stress, or soak testing.
- An existing .jmx has hard-coded data, no assertions, or GUI listeners in load runs.
- The team needs a repeatable CLI command and HTML dashboard for CI.

## Workflow
1. **Collect the flow and load.** Requests in order, auth, dynamic values (tokens, ids,
   CSRF), target users or throughput, ramp-up, duration, and SLOs. Ask; never invent load.
2. **Shape the plan.** HTTP Request Defaults, Cookie Manager, Header Manager, and one
   Thread Group per user type, sized with properties like `${__P(users,10)}` so CI can
   override them with `-J`.
3. **Feed test data.** CSV Data Set Config with variable names, sharing mode, and EOF
   behavior chosen on purpose (recycle for reusable logins, stop thread for one-time data).
4. **Correlate.** JSON Extractor (or Regular Expression Extractor) for tokens and ids,
   with a default like `NOT_FOUND` so a failed extraction is visible in results.
5. **Assert and pace.** Response Assertion on the code, JSON Assertion on key fields,
   Duration Assertion for SLOs. Uniform Random Timer for think time, or Constant
   Throughput Timer for a target rate; timers apply to every sampler in their scope.
   Wrap each business step in a Transaction Controller.
6. **Run headless.** No View Results Tree during load; `jmeter -n` with `-l` for raw
   results and `-e -o` for the HTML dashboard (the output folder must be empty or absent).
7. **List assumptions**: host, CSV source, think times, heap size, and any plugins needed.

## Output shape
```text
checkout-load.jmx
  Test Plan (User Defined Variables: host=${__P(host,staging.example.com)})
  +- HTTP Request Defaults: https, ${host}, connect 5000 ms, response 30000 ms
  +- HTTP Cookie Manager (clear each iteration) + HTTP Header Manager (JSON)
  +- Thread Group "Shoppers": ${__P(users,50)} threads, ramp-up ${__P(rampup,120)} s,
  |    loop infinite, thread lifetime ${__P(duration,900)} s
     +- CSV Data Set Config: users.csv -> email,password (recycle on EOF, all threads)
     +- Transaction Controller "01_Login"
     |    POST /api/auth/login {"email":"${email}","password":"${password}"}
     |    +- JSON Extractor: token <- $.token (match no 1, default NOT_FOUND)
     |    +- Response Assertion: response code equals 200
     +- Transaction Controller "02_Browse"
     |    GET /api/products?page=1   +- JSON Assertion: $.items exists
     +- Transaction Controller "03_AddToCart"
     |    POST /api/cart (Header Manager: Authorization: Bearer ${token})
     |    +- Response Assertion: code 201   +- Duration Assertion: 2000 ms
     +- Uniform Random Timer: 1000 ms constant + up to 3000 ms random
  (no GUI listeners: results go to the .jtl file)

jmeter -n -t checkout-load.jmx -l results/run1.jtl -e -o results/run1-report \
  -Jhost=staging.example.com -Jusers=100 -Jrampup=300 -Jduration=1800
```

## Guardrails
- The plan is a **draft the engineer must build and smoke-test** with a few threads first.
- Never fabricate endpoints, payloads, extractor paths, or target load; ask for them.
- Only load-test systems you own or are authorized to test, with the owners informed.
- Never run load in GUI mode or with result-tree listeners enabled; they skew results.
- Keep credentials in the CSV or properties outside version control, not in the .jmx.
