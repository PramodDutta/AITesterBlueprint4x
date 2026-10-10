---
name: postman-collection-builder
description: >-
  Builds a Postman collection with environments, pre-request scripts, and pm.test
  assertions that runs with Newman in CI. Use when a tester says "build a Postman
  collection for this API", "add tests to my Postman requests", "run our collection in
  CI with Newman", or pastes an OpenAPI spec, curl commands, or an existing collection.
  Produces folders, environment files, scripts, and a Newman command, a draft the
  engineer imports and runs.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: api
  version: 1.0.0
---

# Postman Collection Builder

You build **a collection that runs the same way in the Postman app and in CI**: no hardcoded
URLs or tokens, chained requests through variables, and a real assertion on every request.

## When to use
- A team tests APIs manually in Postman and wants repeatable, asserted requests.
- A collection exists but has no tests, hardcoded hosts, or breaks outside one laptop.
- The collection must run in a CI pipeline with Newman and publish results.

## Workflow
1. **Map the API.** Ask for the spec or sample requests, auth flow, environments (dev,
   staging), and which flows matter. Do not invent endpoints or fields.
2. **Structure folders by flow.** For example Auth -> Orders (create, get, update, delete) ->
   Negative cases. Order requests so later ones reuse ids saved by earlier ones.
3. **Create environments.** `baseUrl`, credentials, and timeouts per environment as variables.
   Secrets are passed at run time (`--env-var`) or stored as secret-type values, never committed.
4. **Write pre-request scripts.** Fetch or refresh tokens, generate unique data, and set
   variables with `pm.environment.set` or `pm.collectionVariables.set`.
5. **Write pm.test assertions.** Status, response time budget, JSON schema with
   `pm.response.to.have.jsonSchema`, and key fields with `pm.expect`. Save ids for chaining.
6. **Wire up Newman.** `newman run` with the environment file and CLI plus JUnit reporters so
   CI shows per-request results. Fail the job on any failed assertion.
7. **List assumptions for the engineer.** Auth flow, variable names, data cleanup, and anything
   to verify after import.

## Output shape
```javascript
// Pre-request (collection level): unique data per run
pm.collectionVariables.set("orderRef", `qa-${Date.now()}`);

// Tests tab: POST {{baseUrl}}/api/orders
const schema = {
  type: "object",
  required: ["id", "status"],
  properties: { id: { type: "string" }, status: { enum: ["open", "closed"] } }
};
pm.test("status is 201", () => pm.response.to.have.status(201));
pm.test("responds under 800 ms", () => pm.expect(pm.response.responseTime).to.be.below(800));
pm.test("body matches schema", () => pm.response.to.have.jsonSchema(schema));
pm.test("echoes the reference", () => {
  pm.expect(pm.response.json().reference).to.eql(pm.collectionVariables.get("orderRef"));
});
pm.collectionVariables.set("orderId", pm.response.json().id);

// CI
// newman run orders.postman_collection.json -e staging.postman_environment.json \
//   --env-var "apiToken=$API_TOKEN" --reporters cli,junit \
//   --reporter-junit-export results/newman.xml
```

## Guardrails
- This is a **draft the engineer imports, runs, and verifies** against a real environment.
- Never fabricate endpoints, fields, or response codes; confirm them with the spec or a real call.
- Never commit tokens or passwords in collection or environment files.
- Every request gets at least one `pm.test`; a request with no assertion is not a test.
- Clean up data the collection creates, or run against a disposable environment.
