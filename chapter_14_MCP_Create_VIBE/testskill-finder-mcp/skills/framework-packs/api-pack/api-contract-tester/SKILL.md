---
name: api-contract-tester
description: >-
  Designs consumer-driven contract tests (Pact) and OpenAPI schema conformance checks
  between services. Use when an SDET says "add contract tests between these services",
  "set up Pact for our consumer", "check the API matches the OpenAPI spec", or describes
  a provider and its consumers. Produces consumer pacts, provider verification setup,
  and conformance checks, a draft the engineers on both sides run and confirm.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: api
  version: 1.0.0
---

# API Contract Tester

You catch breaking API changes **before deploy, without a shared end-to-end environment**:
consumers state what they use, providers prove they still honor it.

## When to use
- Microservices break each other on deploy and E2E tests find it too late.
- A provider team wants to know which fields consumers actually depend on before changing them.
- An OpenAPI spec exists but nobody checks that the running service matches it.

## Workflow
1. **Map the interactions.** Ask for the consumer, provider, the endpoints the consumer calls,
   the fields it reads, and provider states needed (for example "order 123 exists"). Only
   include what the consumer uses, not the full provider response.
2. **Write consumer tests.** With Pact, define each interaction (`given`, `uponReceiving`,
   `withRequest`, `willRespondWith`) and run the real consumer client against the Pact mock
   server. Use matchers (`like`, `eachLike`, `regex`) instead of exact values.
3. **Publish and verify.** Publish pacts to a Pact Broker (or PactFlow) tagged with the
   consumer version. On the provider, run `Verifier` with `stateHandlers` that set up each
   provider state, and publish verification results.
4. **Gate deploys.** Use `can-i-deploy` against the target environment before each deploy so
   a broken contract blocks the release, not production.
5. **Add OpenAPI conformance.** Validate real provider responses against the OpenAPI schema
   (a schema-based tool such as Schemathesis, or response validation in API tests). Report
   undocumented fields, wrong types, and status codes missing from the spec.
6. **List assumptions for the engineers.** Broker URL, versioning scheme, provider states,
   and who owns fixing a failed verification.

## Output shape
```javascript
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const { like, eachLike } = MatchersV3;
const { getOrder } = require('../src/ordersClient');

const provider = new PactV3({ consumer: 'checkout-web', provider: 'orders-api' });

describe('orders-api contract', () => {
  it('returns an existing order', () => {
    provider
      .given('order ord_123 exists')
      .uponReceiving('a request for order ord_123')
      .withRequest({ method: 'GET', path: '/orders/ord_123', headers: { Accept: 'application/json' } })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: like({ id: 'ord_123', status: 'open', items: eachLike({ sku: 'ABC', qty: 1 }) }),
      });

    return provider.executeTest(async (mockServer) => {
      const order = await getOrder(mockServer.url, 'ord_123');
      expect(order.id).toBe('ord_123');
    });
  });
});
// Deploy gate: pact-broker can-i-deploy --pacticipant checkout-web --version $GIT_SHA --to-environment production
```

## Guardrails
- This is a **draft both consumer and provider engineers must run and confirm**.
- Never fabricate fields, provider states, or endpoints; contracts describe real usage only.
- Contracts cover what the consumer uses, not every provider field; avoid over-specifying.
- Contract tests do not replace functional tests; they check shape and agreement, not business logic.
- A failed verification is a conversation between teams, not a reason to loosen matchers silently.
