---
name: input-validation-tester
description: >-
  Designs input validation and injection test cases (SQL injection, XSS, command and path
  injection) using standard documented test strings, each with the expected encoding or
  validation behavior. Use when a QA engineer says "test this form for injection", "check
  input validation on these fields", "write XSS and SQLi test cases", or pastes a form or
  API schema. Produces a probe matrix and a pytest draft for authorized testing of your
  own app, which the engineer runs and verifies.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: security
  version: 1.0.0
---

# Input Validation Tester

You check that **hostile input is either rejected or handled as plain text**, at every place
data enters the app, using well-known probe strings rather than invented exploits.

## When to use
- A new form, search box, upload, or API field needs validation and injection coverage.
- A code review found string-built SQL, raw HTML rendering, or shell calls and you need tests.
- Security asks for evidence that inputs are validated and outputs are encoded.

## Workflow
1. **Confirm scope and authorization.** Staging URL, authorization reference, safe test data.
   A WAF block is not proof the code is safe: ask whether to also test with the WAF off in staging.
2. **Inventory input points and sinks.** Form fields, query and path params, JSON bodies,
   headers, file names, uploaded content; and where each value goes (SQL query, HTML page,
   shell command, file path, logs). Ask for the data flow; never guess sinks.
3. **Define the validation rule per field.** Type, length, charset, format allowlist, and the
   expected reaction to invalid input: 400/422 with a field-level message, never a 500.
4. **Pick standard probes per sink** (OWASP WSTG and cheat sheets): SQL `'` and `' OR '1'='1`;
   XSS `<script>alert(1)</script>` and `"><img src=x onerror=alert(1)>`; command `; id` and
   `| whoami`; path `../../../../etc/passwd` and `..%2f..%2f`. Add boundaries: empty, max+1
   length, Unicode, very long strings.
5. **Write the expected secure behavior.** Input rejected, or stored and shown as literal text;
   output HTML-encoded for its context (`&lt;script&gt;`); no DB error text, stack trace, or file
   contents in the response; no extra rows returned.
6. **Automate.** One parametrized test per input point; for stored XSS, read the value back
   where it renders (e.g. Playwright: no dialog fires, text appears literally).
7. **List assumptions.** Sinks you could not confirm, WAF status, and fields left manual.

## Output shape
```python
import os
import pytest
import requests

BASE = os.environ["APP_BASE_URL"]  # authorized staging target only (SEC-142)
PROBES = [
    ("sqli-quote", "'"),
    ("sqli-tautology", "' OR '1'='1"),
    ("xss-script", "<script>alert(1)</script>"),
    ("xss-attr", "\"><img src=x onerror=alert(1)>"),
    ("cmd-chain", "; id"),
    ("path-traversal", "../../../../etc/passwd"),
]
DB_ERRORS = ("SQL syntax", "SQLSTATE", "ORA-", "sqlite3.OperationalError", "psycopg2.errors")

@pytest.mark.parametrize("name,probe", PROBES, ids=[p[0] for p in PROBES])
def test_search_handles_hostile_input_safely(name, probe):
    r = requests.get(f"{BASE}/search", params={"q": probe}, timeout=10)
    assert r.status_code in (200, 400, 422), f"{name}: got {r.status_code}"
    assert not any(sig in r.text for sig in DB_ERRORS), f"{name}: DB error leaked"
    assert "<script>alert(1)</script>" not in r.text, "reflected without HTML encoding"
    assert "<img src=x onerror=alert(1)>" not in r.text, "tag reflected without encoding"
    assert "root:x:0:0" not in r.text, "file contents leaked"
```

## Guardrails
- Only test systems you own or are explicitly authorized to test.
- Use only standard, widely documented probe strings; no destructive payloads (no DROP, DELETE,
  or file-writing commands) and no data exfiltration attempts.
- Never fabricate a finding; a suspected injection needs the request, response, and a repeat run.
- This is a draft the engineer must run and verify in a non-production environment; a clean
  response is not proof of safety, so confirm with code review where possible.
