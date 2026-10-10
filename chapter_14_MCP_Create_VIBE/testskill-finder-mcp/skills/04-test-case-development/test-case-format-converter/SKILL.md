---
name: test-case-format-converter
description: >-
  Convert test cases between formats (spreadsheet or CSV rows, Jira Xray or Zephyr import
  CSV, Gherkin, Markdown) without losing steps or expected results. Use when a tester says
  "convert these test cases to Xray CSV", "turn this spreadsheet into Gherkin",
  "migrate our cases to Zephyr", or pastes cases in one format and names another. Produces
  the converted output plus a field mapping and loss report, as a draft for review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Case Development
  version: 1.0.0
---

# Test Case Format Converter

You move test cases between tools **with every step and expected result accounted for**.
A conversion that silently drops one expected result is a broken test, not a format change.

## When to use
- A team is migrating cases into Jira (Xray or Zephyr) from spreadsheets or Markdown.
- Manual cases need a Gherkin version for BDD automation, or the reverse.
- Cases must be shared in a different format for an audit, a vendor or another team.

## Workflow
1. **Identify source and target.** Confirm both formats and ask for a sample import file or
   the importer's field configuration. Never guess custom field names or required columns.
2. **Parse into a neutral model.** ID, title, preconditions, priority, labels, requirement
   link, and an ordered list of steps, each with action, data and expected result.
3. **Build the field mapping.** Show source field to target field for every field, and list
   anything with no target (attachments, custom fields) instead of dropping it quietly.
4. **Render the target.** CSV: one row per step with the test ID repeated so the importer
   groups steps; quote fields containing commas, quotes or line breaks and double any
   inner quotes; save as UTF-8. Gherkin: preconditions become Given, actions become When,
   expected results become Then; ID, priority and requirement become tags.
5. **Verify counts.** Compare cases, steps and expected results in vs out, and flag every
   field that changed shape (for example, merged steps or tags that replaced a column).
6. **HUMAN REVIEW GATE (mandatory).** Present the output as a draft with the mapping and loss
   report. Recommend importing one or two cases into a sandbox project first, and ask the
   tester to confirm before the full set is imported.

## Output shape
```text
SOURCE (Markdown)
TC-021 Login with valid credentials | Priority: High | Covers: REQ-12
Pre: user asha@example.com exists
1. Open the login page          -> Login form is shown
2. Enter email and password     -> Sign in button is enabled
3. Select Sign in               -> Dashboard shows "Welcome, Asha"

TARGET 1: Xray CSV (columns mapped in the Xray Test Case Importer)
TCID,Summary,Priority,Requirement,Precondition,Action,Data,Expected Result
TC-021,Login with valid credentials,High,REQ-12,User exists,Open the login page,,Login form is shown
TC-021,,,,,Enter email and password,asha@example.com,Sign in button is enabled
TC-021,,,,,Select Sign in,,"Dashboard shows ""Welcome, Asha"""

TARGET 2: Gherkin
@TC-021 @priority-high @REQ-12
Scenario: Login with valid credentials
  Given user "asha@example.com" exists
  When she opens the login page
  Then the login form is shown
  When she enters her email and password
  Then the Sign in button is enabled
  When she selects Sign in
  Then the dashboard shows "Welcome, Asha"

CONVERSION REPORT
Cases 1 -> 1 | Steps 3 -> 3 | Expected results 3 -> 3 | Unmapped fields: none
Note: Gherkin keeps 3 When/Then pairs to preserve every expected result; refactor later.
```

## Guardrails
- Never drop, merge or invent a step, data value or expected result; report every change.
- Never fabricate importer column names or custom fields; confirm against the target tool.
- Keep IDs and requirement links intact so traceability survives the move.
- Escape CSV correctly and keep UTF-8; a broken quote shifts every column after it.
- The converted set is a draft until a sandbox import is checked by a human.
