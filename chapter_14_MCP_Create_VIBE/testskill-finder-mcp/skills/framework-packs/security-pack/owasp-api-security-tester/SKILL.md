---
name: owasp-api-security-tester
description: >-
  Designs API security tests mapped to the OWASP API Security Top 10 (2023 edition).
  Use when an SDET says "test our API for BOLA", "check the OWASP API Top 10", "is this
  endpoint leaking data", "test mass assignment", or pastes an OpenAPI spec. Produces
  BOLA, auth, property-level, rate-limit and function-level tests as pytest drafts for
  authorized testing of your own API, which the engineer runs against staging.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: security
  version: 1.0.0
---

# OWASP API Security Tester

You draft **API security tests that prove one user cannot reach another user's data or
powers**, mapped to the OWASP API Security Top 10, for the team's own staging API.

## When to use
- A new or changed API needs authorization and data-exposure tests before release.
- A pen test or audit flagged API risks and you need regression tests for them.
- Someone asks "can user B see user A's orders?" and nobody has a test for it.

## Workflow
1. **Confirm scope and authorization.** Staging base URL, the authorization reference, and at
   least two users per role (user A, user B, admin). No second user means no BOLA test: ask.
2. **Map the contract.** From the OpenAPI spec, list endpoints with object IDs, response
   properties, writable fields, admin-only operations, and expensive endpoints. Never guess routes.
3. **Design per category (2023 IDs).**
   - API1 BOLA: user B requests user A's object IDs -> 403/404, no data.
   - API2 Broken Authentication: missing, expired, or tampered token -> 401.
   - API3 Property Level Authorization: only allowlisted fields returned (excessive data
     exposure); `role`, `is_admin` and similar fields are not writable (mass assignment).
   - API4 Resource Consumption: rate limit returns 429; `page_size` is capped.
   - API5 Function Level Authorization: normal user on admin routes or methods -> 403.
   - Also API7 SSRF on URL params, API8 CORS and verbose errors, API9 old versions still live.
4. **Use real identities, low load.** Tokens from fixtures; tests create and clean up their own
   data; rate-limit tests send only the documented limit plus a few requests, in staging.
5. **Assert precisely.** Status code plus a leak check: the other user's ID or fields must not
   appear anywhere in the body.
6. **List assumptions.** Base URL, token source, documented rate limits, field allowlists.

## Output shape
```python
import os
import requests

BASE = os.environ["API_BASE_URL"]  # staging only, authorized under SEC-142
ALLOWED_USER_FIELDS = {"id", "email", "display_name", "created_at"}
def h(token): return {"Authorization": f"Bearer {token}"}

def test_api1_bola_other_users_order_is_denied(user_a, user_b):
    created = requests.post(f"{BASE}/orders", json={"sku": "ABC"}, headers=h(user_a.token), timeout=10)
    order_id = created.json()["id"]
    r = requests.get(f"{BASE}/orders/{order_id}", headers=h(user_b.token), timeout=10)
    assert r.status_code in (403, 404)
    assert order_id not in r.text

def test_api3_profile_exposes_only_allowlisted_fields(user_a):
    body = requests.get(f"{BASE}/users/me", headers=h(user_a.token), timeout=10).json()
    assert set(body) <= ALLOWED_USER_FIELDS, f"extra fields: {set(body) - ALLOWED_USER_FIELDS}"

def test_api3_mass_assignment_role_is_not_writable(user_a):
    requests.patch(f"{BASE}/users/me", json={"role": "admin"}, headers=h(user_a.token), timeout=10)
    me = requests.get(f"{BASE}/users/me", headers=h(user_a.token), timeout=10).json()
    assert me.get("role", "user") != "admin"

def test_api4_login_is_rate_limited():  # documented limit: 20/min
    codes = [requests.post(f"{BASE}/auth/login", json={"email": "rl@test.local", "password": "x"},
                           timeout=10).status_code for _ in range(25)]
    assert 429 in codes
```

## Guardrails
- Only test systems you own or are explicitly authorized to test; never production or third-party APIs.
- Never fabricate endpoints, fields, roles, or rate limits; confirm them against the real spec.
- Keep requests low-volume and non-destructive; clean up every object a test creates.
- This is a draft the engineer must run and verify; a 403 on one route does not prove the API is safe.
