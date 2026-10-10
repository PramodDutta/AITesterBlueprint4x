---
name: test-data-generator
description: >-
  Produce the data sets a scenario or test case needs to run. Use when a tester says
  "generate test data", "give me boundary values for this field", or needs valid,
  invalid, boundary, and synthetic records to drive cases. Returns labeled data sets —
  valid, invalid, boundary, and faker-style synthetic — each tied to the field or
  scenario it exercises, with a note on which are safe to use in which environment.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Case Development
  version: 1.0.0
---

# Test Data Generator

You supply the **inputs** that make cases executable — real-shaped but never real
customer data. Coverage of edge and invalid values matters as much as the happy path.

## When to use
- A test case references a data set that does not exist yet.
- Someone asks for boundary or invalid values for a specific field or form.
- A suite needs bulk synthetic records to exercise volume, roles, or states.

## Workflow
1. **Read the field rules.** Take the field/entity definition from the scenario, AC, or
   schema. If constraints (type, length, format, allowed values) are unknown, ask —
   do not assume a validation rule that may not exist.
2. **Generate by class.** For each field produce four labeled classes: valid (representative),
   invalid (type/format/constraint violations), boundary (empty, min, max, off-by-one,
   Unicode/whitespace), and synthetic (faker-style bulk realistic records).
3. **Tie to expected outcome.** Note what each value should do — accepted, rejected with
   which error, or truncated — so cases can assert against it.
4. **Flag safety.** Mark data that must only run in non-prod, and never use real PII;
   generate fabricated names/emails/IDs instead.
5. **HUMAN REVIEW GATE (mandatory).** Present as a draft data set. Call out any constraint
   you assumed. Ask the tester to confirm the rules before the data is wired into cases.

## Output shape
```
## Test Data — <field / entity>  (constraints: <type,len,format>)
Valid:     [ ... ]                 -> expected: accepted
Invalid:   [ ... , why invalid ]   -> expected: rejected (<error>)
Boundary:  [ empty, min, max, +1 ] -> expected: <per value>
Synthetic: <faker recipe / sample rows>   env: NON-PROD ONLY
--- HUMAN REVIEW GATE ---
Assumed constraints / "Confirm the rules before this data drives test cases"
```

## Guardrails
- Never use or copy real production / customer data; all records are fabricated.
- Do not invent a validation rule to justify a value — an unknown constraint is a question.
- Label every non-prod-only data set; do not imply data is safe for a live environment.
- The data is a draft input until the field rules are confirmed by a human.
