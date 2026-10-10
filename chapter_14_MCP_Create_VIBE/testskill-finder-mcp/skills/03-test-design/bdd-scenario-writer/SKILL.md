---
name: bdd-scenario-writer
description: >-
  Write Gherkin feature files (Feature, Background, Scenario Outline with Examples, tags)
  from acceptance criteria, using declarative business-language steps. Use when a tester
  or SDET says "write BDD scenarios for this story", "convert these ACs to Gherkin",
  "create a feature file", or pastes acceptance criteria. Produces a tagged .feature draft
  traced to each AC, and stops for human review before it is automated.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Design
  version: 1.0.0
---

# BDD Scenario Writer

You write **feature files a product owner can read and an SDET can automate** without
rewriting. Steps describe behavior in business language, never clicks and selectors.

## When to use
- Approved acceptance criteria need to become executable specifications.
- An existing feature file is full of imperative "click the button" steps and needs a rewrite.
- A Three Amigos session produced examples that should be captured as Gherkin.

## Workflow
1. **Collect ACs and vocabulary.** Ask for the acceptance criteria, domain terms, personas
   and any existing step library. If an AC is missing an outcome, ask; do not invent one.
2. **Map ACs to scenarios.** At least one scenario per AC, tagged with its AC ID. Add a
   negative scenario where the AC implies a rejection path.
3. **Extract a Background only when it is true for every scenario.** Keep it to a few
   Given lines; anything scenario-specific stays in the scenario.
4. **Use Scenario Outline when only data varies.** Put variations in Examples with column
   names that explain meaning. Different outcomes deserve separate outlines.
5. **Write declarative steps.** One When per scenario, Then states an observable business
   outcome, consistent persona and tense, no UI selectors, waits or URLs.
6. **Tag for execution.** Use @smoke/@regression, @AC-n for traceability, and @wip for
   scenarios blocked on open questions. Reuse existing step wording where it fits.
7. **HUMAN REVIEW GATE (mandatory).** Present the feature file as a draft. List assumed
   values, @wip scenarios and new step phrases. Ask the PO and SDET to confirm before
   step definitions are written.

## Output shape
```gherkin
@checkout @coupon
Feature: Apply a coupon at checkout
  As a returning shopper
  I want to apply a coupon code
  So that I pay the discounted price

  Background:
    Given Asha is signed in with a cart totalling 100.00 USD

  @smoke @AC-1
  Scenario: Valid coupon reduces the order total
    When Asha applies the coupon "SAVE10"
    Then her order total is 90.00 USD

  @regression @AC-2
  Scenario Outline: Invalid coupon is rejected and the total is unchanged
    When Asha applies the coupon "<code>"
    Then she is told "<message>"
    And her order total is still 100.00 USD

    Examples:
      | code     | message                    |
      | EXPIRED5 | This coupon has expired    |
      | BOGUS99  | This coupon is not valid   |
```

## Guardrails
- Never fabricate business rules, messages or amounts; unknown values get @wip and a question.
- Keep steps declarative: no selectors, clicks, sleeps or URLs in Gherkin.
- One behavior per scenario; split scenarios that need two When steps.
- Every scenario carries an AC tag so coverage stays traceable.
- The feature file is a draft until the PO and SDET confirm it.
