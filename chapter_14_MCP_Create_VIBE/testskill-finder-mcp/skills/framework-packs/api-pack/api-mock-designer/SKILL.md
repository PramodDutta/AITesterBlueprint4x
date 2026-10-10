---
name: api-mock-designer
description: >-
  Designs API mocks and stubs (WireMock or similar) for dependencies, covering success,
  error, latency, and stateful scenarios. Use when an SDET says "mock the payment
  service", "stub this third-party API", "simulate timeouts and 500s from a dependency",
  or pastes a dependency's API spec or sample responses. Produces WireMock stub mappings
  and a scenario list, a draft the engineer loads and verifies against the real
  contract.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: api
  version: 1.0.0
---

# API Mock Designer

You design mocks that **test how your service behaves when a dependency misbehaves**, not just
when it returns the happy path. Every stub traces back to the real dependency's contract.

## When to use
- A dependency (payments, shipping, a third-party API) is slow, costly, or unavailable in test.
- You need to test timeouts, retries, 5xx handling, and rate limits that are hard to trigger for real.
- A multi-step flow (create, then poll status) needs a dependency that changes state.

## Workflow
1. **Get the dependency contract.** Ask for its OpenAPI spec, sample requests and responses,
   auth, and the calls your service makes. Do not invent fields or status codes.
2. **List the scenarios.** Success, 400/404/409, 500/503, 429 with `Retry-After`, responses
   near and over your timeout, connection faults, and malformed bodies.
3. **Write request matching.** Match on method, URL path or pattern, and only the headers or
   body fields that select the scenario. Use `priority` so specific stubs win over catch-alls.
4. **Add latency and faults.** `fixedDelayMilliseconds` for slow responses, `fault` (for
   example `CONNECTION_RESET_BY_PEER`) for broken connections.
5. **Model state.** Use WireMock scenarios (`scenarioName`, `requiredScenarioState`,
   `newScenarioState`) for flows like pending -> captured. Reset scenarios between tests.
6. **Keep mocks honest.** Plan a drift check (contract tests, or recorded responses
   refreshed on a schedule) so stubs keep matching the real contract.
7. **List assumptions for the engineer.** Base URL wiring, timeouts in your service, and which
   scenarios still need confirmation against the real dependency.

## Output shape
```json
{
  "mappings": [
    {
      "priority": 1,
      "request": { "method": "POST", "urlPath": "/v1/payments",
                   "bodyPatterns": [{ "matchesJsonPath": "$[?(@.amount == 9999)]" }] },
      "response": { "status": 200, "fixedDelayMilliseconds": 5000,
                    "jsonBody": { "id": "pay_slow", "status": "pending" } }
    },
    {
      "priority": 1,
      "request": { "method": "POST", "urlPath": "/v1/payments",
                   "bodyPatterns": [{ "matchesJsonPath": "$[?(@.amount == 5003)]" }] },
      "response": { "status": 503, "headers": { "Retry-After": "2" } }
    },
    {
      "scenarioName": "payment-lifecycle", "requiredScenarioState": "Started",
      "newScenarioState": "captured",
      "request": { "method": "GET", "urlPath": "/v1/payments/pay_123" },
      "response": { "status": 200, "jsonBody": { "id": "pay_123", "status": "pending" } }
    },
    {
      "scenarioName": "payment-lifecycle", "requiredScenarioState": "captured",
      "request": { "method": "GET", "urlPath": "/v1/payments/pay_123" },
      "response": { "status": 200, "jsonBody": { "id": "pay_123", "status": "captured" } }
    }
  ]
}
```

## Guardrails
- This is a **draft the engineer loads and verifies** against the dependency's real contract.
- Never fabricate dependency fields, error formats, or status codes; use the spec or real samples.
- Mocks prove your service's handling, not the dependency's behavior; keep contract checks too.
- Reset stateful scenarios between tests so results do not depend on order.
- Never put real credentials or customer data in stub files.
