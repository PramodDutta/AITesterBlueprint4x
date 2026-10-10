---
name: restassured-api-tester
description: >-
  Generates REST Assured API tests in Java (given/when/then) with status, JSON schema,
  and auth checks. Use when an SDET says "write REST Assured tests for this endpoint",
  "add JSON schema validation in Java", "cover auth and negative cases with
  RestAssured", or pastes an OpenAPI spec or curl request. Produces JUnit 5 test classes
  with a shared request spec, a draft the engineer runs against a real service.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: api
  version: 1.0.0
---

# REST Assured API Tester

You draft **readable given/when/then API tests that fail for one clear reason**, with the
schema, auth, and negative cases that hand-written suites usually skip.

## When to use
- A Java team needs API coverage for an endpoint or a whole resource.
- Responses must be validated against a JSON schema, not just a status code.
- Auth (missing, expired, wrong-role tokens) and negative paths have no tests yet.

## Workflow
1. **Extract the contract.** Method, path, path/query params, headers, auth scheme, request
   body, status codes, and the response shape. If the spec is missing, ask; do not invent fields.
2. **Build a shared request spec.** `RequestSpecBuilder` with base URI from config or env, content
   type, and auth header, so tests do not repeat setup. Token comes from a helper or env var.
3. **Design the case matrix.** Happy path (2xx + body), schema validation, auth (no token -> 401,
   wrong role -> 403), negative and boundary (invalid body -> 400, unknown id -> 404,
   wrong method -> 405, limits and empty values).
4. **Validate schema.** Store JSON schemas under `src/test/resources/schemas/` and assert with
   `matchesJsonSchemaInClasspath` from the `json-schema-validator` module.
5. **Assert precisely.** Status, content type, key fields with Hamcrest matchers; for generated
   ids and timestamps assert type or pattern, not exact value. Clean up created resources.
6. **List assumptions for the engineer.** Base URL, token source, seed data, and dependencies
   (`rest-assured`, `json-schema-validator`, JUnit 5) to add to the build file.

## Output shape
```java
import static io.restassured.RestAssured.given;
import static io.restassured.module.jsv.JsonSchemaValidator.matchesJsonSchemaInClasspath;
import static org.hamcrest.Matchers.equalTo;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;
import org.junit.jupiter.api.Test;

class OrdersApiTest {
  static final RequestSpecification spec = new RequestSpecBuilder()
      .setBaseUri(System.getenv("API_BASE_URL"))
      .setContentType(ContentType.JSON)
      .addHeader("Authorization", "Bearer " + System.getenv("API_TOKEN"))
      .build();

  @Test
  void getOrderMatchesSchema() {
    given().spec(spec).pathParam("id", "ord_123")
    .when().get("/api/orders/{id}")
    .then().statusCode(200)
      .body("id", equalTo("ord_123"))
      .body(matchesJsonSchemaInClasspath("schemas/order.json"));
  }

  @Test
  void rejectsMissingToken() {
    given().baseUri(System.getenv("API_BASE_URL"))
    .when().get("/api/orders/ord_123").then().statusCode(401);
  }
}
```

## Guardrails
- This is a **draft the engineer must run against the real service** and confirm with the spec.
- Never fabricate endpoints, fields, status codes, or auth schemes; a missing spec is a question.
- Keep tokens and base URLs in env vars or config, never hardcoded in the test.
- Do not assert exact values for generated ids or timestamps; assert type or format.
- Tests must be independent: each creates its own data and cleans it up.
