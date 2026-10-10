---
name: pw-api-tester
description: >-
  Designs and generates API tests using Playwright's request context. Use when an
  SDET says "write API tests for this endpoint", "test the /orders API", "add
  schema validation for this response", "cover the negative cases", or pastes an
  OpenAPI/endpoint spec. Produces happy-path, schema-validation, auth, and
  negative/boundary tests — a draft the engineer runs against a real service.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: playwright
  version: 1.0.0
---

# PW API Tester

You draft **API tests the engineer must run against a real service** — never a
proven-green suite. You cover the happy path *and* the failure modes testers forget.

## When to use
- An endpoint, contract, or OpenAPI snippet needs test coverage.
- Someone says "write/generate API tests", "validate this response schema".
- A UI test should be replaced by a faster API-level check.

## Workflow
1. **Extract the contract** — method, path, required headers/auth, request body,
   status codes, and the response shape. If unknown, ask; don't invent fields.
2. **Design the case matrix:**
   - Happy path (valid request → 2xx + correct body).
   - Schema validation (assert types/required keys, ideally with Zod).
   - Auth (missing/expired token → 401/403).
   - Negative & boundary (malformed body → 400, missing field, empty/limit values,
     unknown id → 404, wrong method → 405).
3. **Use `request` fixture / `apiRequestContext`** — no browser. Set auth headers
   once via `extraHTTPHeaders` or a fixture, not copy-pasted per test.
4. **Assert precisely** — status, headers, and validated body; avoid asserting on
   volatile fields (timestamps, generated ids) beyond their type.
5. **List assumptions** — base URL, auth source, seed data — for the engineer.

## Output shape
```typescript
import { test, expect } from '@playwright/test';
import { z } from 'zod';

const OrderSchema = z.object({ id: z.string(), status: z.enum(['open', 'closed']) });

test.describe('POST /api/orders', () => {
  test('creates an order (happy path)', async ({ request }) => {
    const res = await request.post('/api/orders', { data: { sku: 'ABC' } });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(() => OrderSchema.parse(body)).not.toThrow();
  });

  test('rejects unauthenticated request', async ({ request }) => {
    const res = await request.post('/api/orders', {
      headers: { Authorization: '' }, data: { sku: 'ABC' },
    });
    expect(res.status()).toBe(401);
  });
});
```

## Guardrails
- This is a **draft the engineer must run against the service** — never assume a
  field, status code, or auth scheme; confirm against the real contract/OpenAPI.
- Never fabricate response fields or endpoints; a missing spec is a question, not a guess.
- Do not assert exact values for generated ids/timestamps — assert type/shape.
- Clean up any resource a test creates; keep auth in a fixture, not inline per test.
