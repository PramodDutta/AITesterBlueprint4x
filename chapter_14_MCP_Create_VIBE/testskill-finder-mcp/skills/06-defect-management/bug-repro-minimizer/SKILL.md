---
name: bug-repro-minimizer
description: >-
  Reduces a long or intermittent bug reproduction to the minimal reliable steps and
  conditions by bisecting steps, data, environment, and timing. Use when a tester says
  "shrink this repro", "find the minimal steps", "this bug only happens sometimes", or
  pastes a 20-step repro the developer cannot follow. Produces a minimal repro with
  required conditions and measured frequency, a draft for human review before the bug is
  updated.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Defect Management
  version: 1.0.0
---

# Bug Repro Minimizer

You cut a messy reproduction down to **the fewest steps that still fail, with the frequency
measured**. A developer should reproduce it on the first try, or know exactly how often it fails.

## When to use
- A bug report has a long session recording or 15+ steps and nobody knows which ones matter.
- An intermittent bug ("happens sometimes") needs its triggering conditions isolated.
- A developer closed a bug as "cannot reproduce" and you need a tighter repro.

## Workflow
1. **Capture the baseline.** Get the full original steps, build, environment, account/role,
   test data, device/browser, and the failure signal (error, wrong value, screenshot). Run it
   N times (for example 10) and record the baseline frequency. Ask for anything missing.
2. **Define the oracle.** One observable check that says "bug reproduced" (a status code, a
   wrong total, a console error). Without a clear oracle, minimization is guesswork.
3. **Bisect the steps.** Remove half of the steps (keeping a valid starting state), rerun
   N times, and keep the cut if the frequency holds. Repeat on smaller chunks until no single
   step can be removed. Record every removed step as "not needed".
4. **Minimize data and environment.** Try a fresh account vs the original, default vs special
   data (long names, unicode, zero, large carts), another browser/device, locale, time zone,
   and feature flags. Keep only the conditions that change the outcome.
5. **Isolate timing.** For intermittent bugs, vary network throttling, CPU throttling, double
   clicks, parallel sessions, and waits between steps. A frequency jump points at a race.
6. **Narrow the build (optional).** If a last-good build is known, bisect builds or commits
   (`git bisect` or deployed versions) and report the first bad one.
7. **HUMAN REVIEW GATE (mandatory).** Present the minimal repro as a draft with before/after
   frequency, removed steps, and conditions not tested. Ask the reporter to confirm before the
   bug is updated.

## Output shape
```
# Minimal Repro - CART-311: order total doubles discount
Build 4.2.0-rc3 | staging | Chrome 129 | user with saved coupon
Oracle: order summary total = subtotal - (2 x discount)
Minimal steps (was 18):
  1. Log in as a user with a saved coupon SAVE10
  2. Add any 1 item to the cart
  3. Click "Apply coupon" twice within 500 ms
Required conditions: saved coupon on account; double click (network fast or slow)
Not needed (removed): search, wishlist, address change, payment method switch (14 steps)
Frequency: baseline 3 / 10 -> minimal 10 / 10
Not tested: Safari, mobile app
First bad build: 4.2.0-rc1 (rc0 clean, 0 / 10)
--- HUMAN REVIEW GATE ---
Confirm the steps on your machine before updating CART-311.
```

## Guardrails
- Never fabricate a run result, frequency, or "first bad build"; report only runs you executed or were given.
- A step is "not needed" only after reruns prove it; one lucky pass is not proof.
- Keep the original repro attached; minimization adds to the record, it does not replace it.
- Do not reproduce on production with real customer data; use a test account and environment.
- The minimal repro is a draft until a human confirms it.
