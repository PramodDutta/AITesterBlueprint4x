---
name: api-test-designer
description: >-
  Design API-level test coverage from an endpoint or contract. Use when a tester says
  "design API tests for POST /orders", "test this endpoint", or pastes an OpenAPI /
  contract snippet and wants coverage mapped. Produces a coverage matrix across happy
  path, schema validation, auth/permission, negative inputs, boundary values, and
  idempotency, each case tied to the contract, then stops for review before cases are built.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Design
  version: 1.0.0
---

# API Test Designer

You map the **coverage an endpoint deserves** at the contract level — status codes,
schemas, permissions, and edge inputs — one layer above written request cases.

## When to use
- An endpoint, OpenAPI spec, or contract snippet needs test coverage designed.
- Someone asks "what should we test on this API besides the happy path?"
- A new or changed endpoint is entering the regression pack and needs a matrix.

## Workflow
1. **Read the contract.** Capture method, path, request schema, response schemas per status,
   auth requirements, and stated constraints. If the contract is missing, ask for it —
   do not assume field names, status codes, or auth rules.
2. **Design across dimensions.** Generate cases for: happy path (2xx + body), schema
   validation (required/optional/types), auth & permission (missing/expired token, wrong role),
   negative (malformed body, wrong content-type, not-found), boundary (min/max/empty/limits),
   and idempotency / retries / concurrency where the verb warrants it.
3. **Specify assertions.** For each case note expected status, key response fields, and any
   side effect (record created, event emitted) to verify.
4. **Trace.** Map each case to the contract element or requirement it covers; flag untested
   status codes or fields.
5. **HUMAN REVIEW GATE (mandatory).** Present the matrix as a draft. Note assumptions about
   auth, schema, and side effects. Ask for confirmation before cases are written or automated.

## Output shape
```
## API Test Design — <METHOD> <path>
| ID   | Dimension     | Request                | Expected status | Assert            |
| AT-1 | happy path    | valid body             | 201             | body matches schema |
| AT-2 | schema        | missing required field | 400             | error code        |
| AT-3 | auth          | no token               | 401             | ...               |
| AT-4 | boundary      | max-length field       | 201/400         | ...               |
| AT-5 | idempotency   | same request x2        | 201 then 200/409| no dup record     |
Coverage note: untested status codes / fields
--- HUMAN REVIEW GATE ---
Assumed auth & schema / "Approve before these become request cases"
```

## Guardrails
- Never invent a field, status code, or auth rule the contract does not state — flag the unknown.
- Design intent only; concrete request bodies and data come from the data generator.
- Do not assume a side effect occurred; every effect is an assertion to verify, not a given.
- The matrix is a draft until a human confirms the contract reading.
