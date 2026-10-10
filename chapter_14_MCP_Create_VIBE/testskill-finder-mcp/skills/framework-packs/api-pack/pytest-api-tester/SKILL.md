---
name: pytest-api-tester
description: >-
  Generates Python API tests with pytest and requests: fixtures for base URL and auth,
  parametrize for negative cases, and schema validation with jsonschema or pydantic.
  Use when an SDET says "write pytest API tests for this endpoint", "add negative cases
  with parametrize", "validate the response schema in Python", or pastes an OpenAPI spec
  or curl request. Produces a conftest and test module, a draft the engineer runs
  against a real service.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: api
  version: 1.0.0
---

# Pytest API Tester

You draft **small, independent pytest API tests** where setup lives in fixtures, negative cases
live in one parametrized table, and every response is checked against a schema.

## When to use
- A Python team needs API coverage for an endpoint or resource.
- Negative and boundary cases are written as copy-pasted tests and need parametrize.
- Responses are only checked for status code and need schema validation.

## Workflow
1. **Extract the contract.** Method, path, params, auth, request body, status codes, and the
   response shape. If the spec is missing, ask; do not invent fields or codes.
2. **Write fixtures in conftest.py.** A session-scoped `requests.Session` with the auth header,
   base URL from an env var, and a factory fixture that creates test data and deletes it after
   `yield`. Always pass a `timeout` on requests.
3. **Cover the happy path.** Assert status, then validate the body with `jsonschema.validate`
   or a pydantic model (`Order.model_validate(r.json())`).
4. **Parametrize negative cases.** One `@pytest.mark.parametrize` table for invalid bodies,
   boundaries, and unknown ids, with `ids=` so reports name each case.
5. **Test auth.** No token -> 401, wrong role -> 403, using a plain request without the
   authenticated session.
6. **List assumptions for the engineer.** Env vars (`API_BASE_URL`, `API_TOKEN`), seed data,
   and packages to install (`pytest`, `requests`, `jsonschema` or `pydantic`).

## Output shape
```python
import os
import pytest
import requests
from jsonschema import validate

BASE_URL = os.environ["API_BASE_URL"]
ORDER_SCHEMA = {
    "type": "object",
    "required": ["id", "status"],
    "properties": {"id": {"type": "string"}, "status": {"enum": ["open", "closed"]}},
}

def test_create_order(api):  # api: session fixture with auth header, from conftest.py
    r = api.post(f"{BASE_URL}/api/orders", json={"sku": "ABC", "qty": 1}, timeout=10)
    assert r.status_code == 201
    validate(instance=r.json(), schema=ORDER_SCHEMA)

@pytest.mark.parametrize("payload, expected", [
    ({}, 400),
    ({"sku": "ABC", "qty": 0}, 400),
    ({"sku": "", "qty": 1}, 400),
], ids=["empty-body", "zero-qty", "blank-sku"])
def test_create_order_rejects_invalid(api, payload, expected):
    r = api.post(f"{BASE_URL}/api/orders", json=payload, timeout=10)
    assert r.status_code == expected

def test_create_order_requires_auth():
    r = requests.post(f"{BASE_URL}/api/orders", json={"sku": "ABC", "qty": 1}, timeout=10)
    assert r.status_code == 401
```

## Guardrails
- This is a **draft the engineer must run against the real service** and check against the spec.
- Never fabricate endpoints, fields, or status codes; a missing spec is a question, not a guess.
- Keep tokens in env vars or the CI secret store; never hardcode them in tests or conftest.
- Do not assert exact generated ids or timestamps; assert type or format.
- Every created resource is cleaned up in fixture teardown.
