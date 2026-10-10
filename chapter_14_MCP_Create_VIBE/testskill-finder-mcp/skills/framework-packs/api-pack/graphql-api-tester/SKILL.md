---
name: graphql-api-tester
description: >-
  Tests GraphQL APIs: queries, mutations, variables, the errors array, auth, depth and
  complexity limits, and introspection settings. Use when an SDET says "write tests for
  our GraphQL API", "test this mutation", "check GraphQL error handling", or pastes a
  schema (SDL), query, or GraphQL endpoint. Produces a case matrix and test code, a
  draft the engineer runs against a real GraphQL server.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: api
  version: 1.0.0
---

# GraphQL API Tester

You test GraphQL the way it actually fails: **a 200 OK with an `errors` array is still a
failure**. You check data, errors, auth, and the limits that protect the server.

## When to use
- A GraphQL endpoint needs coverage for queries and mutations.
- Error handling is unclear (partial data, null fields, error codes in `extensions`).
- Security settings must be verified: auth per field, depth/complexity limits, introspection.

## Workflow
1. **Read the schema.** Ask for the SDL or introspection result, the operations clients use,
   auth rules, and server limits. Do not invent types, fields, or error codes.
2. **Design the case matrix.**
   - Queries: valid variables, missing required variable, wrong variable type, nullable fields.
   - Mutations: create/update/delete, validation errors, idempotency, side effects via a query.
   - Errors: assert `errors[].message`, `path`, and `extensions.code`; partial `data`.
   - Auth: no token, expired token, wrong role on a protected field.
   - Limits: query depth, complexity/cost, batching, and pagination caps.
   - Introspection: disabled in production if that is the policy, enabled where expected.
3. **Use variables, not string building.** Send `{ query, variables }` as JSON. Keep operations
   in constants or `.graphql` files.
4. **Assert the response shape.** Check `errors` is absent on success, and that `data` has the
   expected fields. Do not rely on HTTP status alone; servers differ (200 vs 400) for errors.
5. **List assumptions for the engineer.** Endpoint URL, auth header, error codes used by this
   server, limit values, and the environment introspection should be checked in.

## Output shape
```typescript
import { test, expect, type APIRequestContext } from '@playwright/test';

const ORDER = `query Order($id: ID!) { order(id: $id) { id status total } }`;
const gql = (request: APIRequestContext, query: string, variables = {}) =>
  request.post('/graphql', { data: { query, variables } });

test('returns an order by id', async ({ request }) => {
  const body = await (await gql(request, ORDER, { id: 'ord_123' })).json();
  expect(body.errors).toBeUndefined();
  expect(body.data.order).toMatchObject({ id: 'ord_123', status: expect.any(String) });
});

test('unknown id returns an error with a code', async ({ request }) => {
  const body = await (await gql(request, ORDER, { id: 'missing' })).json();
  expect(body.data?.order ?? null).toBeNull();
  expect(body.errors[0].extensions.code).toBe('NOT_FOUND'); // confirm this server's code
});

test('introspection is disabled in production', async ({ request }) => {
  const body = await (await gql(request, '{ __schema { types { name } } }')).json();
  expect(body.errors?.length).toBeGreaterThan(0);
});
```

## Guardrails
- This is a **draft the engineer must run against a real server**; error codes and limits vary.
- Never fabricate schema types, fields, or error codes; read them from the SDL or a real response.
- Never treat HTTP 200 as success without checking the `errors` array.
- Run depth and complexity tests only against non-production environments you are allowed to load.
- Clean up data created by mutations, or use a disposable environment.
