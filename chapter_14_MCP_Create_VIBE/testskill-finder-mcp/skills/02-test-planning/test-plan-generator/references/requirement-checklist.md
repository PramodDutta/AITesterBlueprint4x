# Requirement Gap-Analysis Checklist

Score every row: ✅ present · ⚠️ ambiguous · ❌ missing. Every ⚠️/❌ becomes a
question for the ticket author.

## Functional
- [ ] Clear user story / goal ("As a … I want … so that …")
- [ ] Acceptance criteria are testable (observable pass/fail)
- [ ] Happy path fully described
- [ ] Negative / error paths described (bad input, failure responses)
- [ ] Boundary & empty states (0, 1, max, empty list, null)
- [ ] State transitions / workflow steps enumerated

## Data & environment
- [ ] Required test data specified or derivable
- [ ] Environment / config / feature flags named
- [ ] External dependencies & integrations listed
- [ ] Preconditions / setup stated

## Non-functional (often missing)
- [ ] Performance / load expectations
- [ ] Security / authorization (which roles can/can't)
- [ ] Accessibility (a11y) expectations
- [ ] Internationalization / localization
- [ ] Audit / logging / observability

## Cross-cutting
- [ ] Impact on existing features (regression surface)
- [ ] Backward compatibility / migration
- [ ] Mobile / responsive / browser matrix
- [ ] Rollback / feature-flag behavior

## Clarity
- [ ] No ambiguous wording ("should", "etc.", "handle gracefully")
- [ ] Terms defined consistently
- [ ] Mockups / designs linked and match the text
