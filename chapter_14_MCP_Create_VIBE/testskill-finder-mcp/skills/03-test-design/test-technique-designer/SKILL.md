---
name: test-technique-designer
description: >-
  Apply black-box test design techniques (equivalence partitioning, boundary value
  analysis, decision tables, state transition, pairwise) to a field or business rule and
  show the derived cases. Use when a tester says "apply BVA to this field",
  "build a decision table for this rule", "how many cases do I need for this form", or
  pastes a validation rule. Produces technique tables plus derived cases, as a reviewable
  draft.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Design
  version: 1.0.0
---

# Test Technique Designer

You derive **the smallest set of cases that still catches the classic bugs**, and you show
the technique so a reviewer can see why each case exists.

## When to use
- A field has ranges, formats or lengths and someone is writing cases by gut feel.
- A business rule combines several conditions and the outcomes are easy to miss.
- A workflow has states (locked, active, expired) or too many configuration combinations.

## Workflow
1. **Pin down the rule.** Get the exact spec: type, min, max, inclusive or exclusive,
   required or optional, allowed characters, error text. If any of it is missing, ask.
2. **Pick the technique to fit.** Ranges and formats: equivalence partitioning (EP) and
   boundary value analysis (BVA). Combined conditions: decision table. Lifecycle or
   status rules: state transition. Many independent parameters: pairwise.
3. **Build the technique table.** EP: valid and invalid partitions with a representative
   each. BVA: 2-value or 3-value boundaries at every edge. Decision table: all condition
   combinations, then collapse rules with "-" (don't care) only when outcomes match.
   State transition: states, events, valid and invalid transitions. Pairwise: parameter
   list for a tool such as PICT, plus any constraints between values.
4. **Derive the cases.** One row per case with technique, input, expected result and
   requirement trace. Merge duplicates that two techniques produced.
5. **Show the count and the gaps.** Say how many cases each technique produced and which
   risks these techniques do not cover (performance, security, concurrency).
6. **HUMAN REVIEW GATE (mandatory).** Present tables and cases as a draft. List assumed
   boundaries and unconfirmed error texts. Ask the tester to confirm before the cases
   are written up in full.

## Output shape
```markdown
# Age field (integer, valid 18-65 inclusive) - REQ-55
### Equivalence partitions
| ID  | Partition       | Valid | Representative |
| EP1 | 18 to 65        | yes   | 40             |
| EP2 | below 18        | no    | 10             |
| EP3 | above 65        | no    | 80             |
| EP4 | non-integer     | no    | "4o", 30.5     |
| EP5 | empty           | no    | ""             |
### Boundary values (3-value)
17 reject | 18 accept | 19 accept | 64 accept | 65 accept | 66 reject
### Decision table: shipping fee (REQ-61)
Rule: free with promo FREESHIP, or for members with cart >= 50.00; otherwise 4.99
| Condition        | R1 | R2 | R3   | R4   | R5   |
| Promo FREESHIP   | Y  | N  | N    | N    | N    |
| Member           | -  | Y  | Y    | N    | N    |
| Cart >= 50.00    | -  | Y  | N    | Y    | N    |
| Fee              | 0  | 0  | 4.99 | 4.99 | 4.99 |
### Derived cases (sample)
| TC   | Technique | Input              | Expected                  | Trace  |
| TC-1 | BVA       | age = 17           | rejected, <TBD message>   | REQ-55 |
| TC-2 | BVA       | age = 18           | accepted                  | REQ-55 |
| TC-3 | DT R3     | member, cart 49.99 | fee 4.99                  | REQ-61 |
Totals: EP 5 + BVA 6 + DT 5 = 16; BVA 17 and 66 already cover EP2/EP3 -> 14 unique
--- HUMAN REVIEW GATE ---
```

## Guardrails
- Never fabricate a boundary, format rule or error message; an unknown is `<TBD>` + a question.
- Collapse decision table rules only when outcomes are truly identical.
- Pairwise reduces combinations, not risk: keep known high-risk combinations explicitly.
- State that these techniques cover input logic only, not non-functional risks.
- The case set is a draft until a tester confirms the rules behind it.
