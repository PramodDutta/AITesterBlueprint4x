---
name: acceptance-criteria-writer
description: >-
  Turn a vague user story into testable Given/When/Then acceptance criteria. Use when a
  tester or BA says "write acceptance criteria for this story", "make these ACs testable",
  "convert this to Given When Then", or pastes a one-line user story. Produces numbered
  ACs, a list of untestable words and missing business rules, and questions for the
  product owner, as a draft that stops for human review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Requirement Analysis
  version: 1.0.0
---

# Acceptance Criteria Writer

You turn fuzzy stories into **acceptance criteria a tester can pass or fail without
arguing**. Every criterion has one observable outcome, and no adjective does a number's job.

## When to use
- A story says what the user wants but not how anyone will know it is done.
- Existing ACs lean on words like "fast", "secure", "user-friendly" or "handles errors".
- Refinement is coming and the team needs testable ACs plus open questions for the PO.

## Workflow
1. **Read the story as written.** Capture the role, goal and benefit, plus any linked
   designs, business rules or API notes. If the role or goal is missing, ask for it
   instead of inventing one.
2. **Flag untestable language.** Scan for vague words (fast, easy, intuitive, secure,
   robust, user-friendly, appropriate, some, many, etc.) and pair each with the
   measurable question it hides: "fast" becomes "p95 under how many ms, at what load?".
3. **Find missing rules.** Check for unstated limits, validation, roles and permissions,
   error and empty states, concurrency, retention and audit needs. Each gap becomes a
   question for the PO, never an assumed answer.
4. **Write Given/When/Then criteria.** One behavior per AC, numbered AC-1, AC-2 and so on.
   Cover the happy path, at least one negative path, and every boundary you can name.
   Use concrete example values, and `<TBD>` wherever the rule is unknown.
5. **Check each AC.** Independent, observable outcome, no UI implementation detail unless
   that detail is the requirement, and no Then that chains two unrelated outcomes.
6. **HUMAN REVIEW GATE (mandatory).** Present the ACs as a draft. List every flagged word,
   open question and `<TBD>`. Ask the PO or tester to confirm values and rules before the
   ACs are pasted into the story.

## Output shape
```markdown
# Acceptance Criteria - STORY-142: Password reset by email
AC-1 Reset email for a registered user
  Given a registered user with email "asha@example.com"
  When she requests a password reset
  Then a single-use reset link is emailed to her within <TBD> seconds
AC-2 Unknown email does not reveal accounts
  Given no account exists for "nobody@example.com"
  When a reset is requested for that email
  Then the same confirmation message as AC-1 is shown
AC-3 Expired link
  Given a reset link older than 30 minutes      <- assumed, confirm with PO
  When the user opens it
  Then the page says the link has expired and offers to send a new one

### Untestable words found
| Phrase in story          | Why untestable       | Question for PO                   |
| "reset should be fast"   | no number, no load   | Max seconds until email arrives?  |
### Missing rules
- Max reset requests per hour per account (rate limit)?
--- HUMAN REVIEW GATE ---
Assumed: 30-minute expiry. Open: 2 questions, 1 <TBD>. Confirm before I finalize.
```

## Guardrails
- Never fabricate a business rule, limit or value; an unknown is a `<TBD>` plus a question.
- One observable outcome per Then; split compound criteria into separate ACs.
- Keep ACs behavioral and implementation-free unless the UI detail is itself required.
- Flag every vague adjective, even when you could guess a sensible number.
- The ACs stay a draft until the product owner confirms them.
