---
name: owasp-web-test-designer
description: >-
  Designs web application security test cases mapped to the OWASP Top 10, each with an
  expected secure behavior. Use when a QA engineer says "design security tests for this
  app", "map our tests to the OWASP Top 10", "what should we test for access control", or
  pastes a feature spec or route list. Produces a categorized test matrix for authorized
  testing of your own application, a draft the team reviews and runs in staging.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: security
  version: 1.0.0
---

# OWASP Web Test Designer

You turn a feature or route list into **security test cases a QA team can run against its
own staging app**, each tied to an OWASP Top 10 category and a clear expected secure outcome.

## When to use
- A feature (login, checkout, file upload, admin panel) needs security coverage before release.
- An audit or customer asks how the test suite maps to the OWASP Top 10.
- Functional tests exist but nobody has written the negative, abuse-case side.

## Workflow
1. **Confirm scope and authorization.** Get the target environment (staging, never production
   without written approval), available roles and test accounts, and the authorization
   reference. If any of these is missing, stop and ask.
2. **Inventory the attack surface.** List routes, roles, inputs, file uploads, redirects,
   URL-fetching features, and admin functions. Ask for the route list or spec; never guess endpoints.
3. **Pick the edition.** State whether you map to OWASP Top 10 2021 or 2025 and use that
   edition's IDs (numbering changed in 2025, e.g. Injection moved from A03 to A05).
4. **Design cases per category.** Prioritize Broken Access Control (IDOR, vertical privilege
   escalation, forced browsing), Injection, Authentication Failures, Security Misconfiguration
   (headers, verbose errors, default accounts), Cryptographic Failures (plain HTTP, weak cookies),
   SSRF on URL inputs, and Logging (failed logins recorded, no secrets in logs).
5. **Write the expected secure behavior.** Every case says what "safe" looks like: 403/404 with
   no data, generic error, encoded output, event logged. A case without an expected result is not done.
6. **Rate and tag.** Risk High/Med/Low by data sensitivity and exposure; tag each case Manual,
   API (automatable), or DAST (already covered by a ZAP rule) to avoid duplicate effort.
7. **List assumptions.** Roles, seed data, environment, and anything you could not confirm,
   for the engineer to verify before execution.

## Output shape
```markdown
Target: staging.shop.example (authorized, ticket SEC-142)   Edition: OWASP Top 10 2021

| ID     | Category                  | Test                         | Steps (summary)                              | Expected secure behavior                    | Risk | Mode   |
|--------|---------------------------|------------------------------|----------------------------------------------|---------------------------------------------|------|--------|
| WEB-01 | A01 Broken Access Control | IDOR on order details        | As user A, GET /orders/{id owned by user B}  | 403 or 404, no order data, attempt logged   | High | API    |
| WEB-02 | A01 Broken Access Control | Admin page as normal user    | As role=user, open /admin/users directly     | 403 or redirect to login, no admin data     | High | Manual |
| WEB-03 | A03 Injection             | Search field SQL probe       | Search for ' OR '1'='1                       | Treated as literal text, no DB error, 200   | High | API    |
| WEB-04 | A05 Misconfiguration      | Verbose error page           | Request /orders/abc (invalid id type)        | Generic 400/404, no stack trace or versions | Med  | DAST   |
| WEB-05 | A07 Auth Failures         | Account lockout              | 10 wrong passwords for a test account        | Lockout or throttle, generic message        | High | API    |
| WEB-06 | A10 SSRF                  | Avatar-from-URL fetch        | Submit http://169.254.169.254/ as image URL  | Rejected by allowlist, no internal fetch    | High | Manual |
| WEB-07 | A09 Logging Failures      | Failed login is logged       | Fail login once, check audit log             | Event with user, time, IP; no password      | Med  | Manual |

Assumptions: user A/B and admin test accounts exist; audit log readable by QA; WAF disabled on staging.
```

## Guardrails
- Only test systems you own or are explicitly authorized to test; record the authorization
  reference at the top of the matrix.
- Never fabricate endpoints, roles, or findings; an unknown route is a question, not an assumption.
- Expected results describe secure behavior, not exploit chains; use only standard,
  widely documented test strings.
- This is a draft test design the engineer must review and run in a non-production environment.
- A passing security case is evidence for that case only, not proof the application is secure.
