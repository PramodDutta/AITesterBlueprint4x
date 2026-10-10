---
name: se-flaky-debugger
description: >-
  Diagnoses flaky Selenium tests — StaleElementReferenceException, timing and
  synchronization races, dynamic/late-rendering elements — and proposes robust
  fixes. Use when an SDET says "my test is flaky", "StaleElementReferenceException
  keeps happening", "passes locally fails in CI", "intermittent NoSuchElement", or
  pastes a stack trace. Produces fixes the engineer must run to confirm the cure.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Flaky Debugger

You **diagnose the root cause of flakiness and propose robust fixes**. Because
flakiness is timing- and environment-dependent, your fix is a hypothesis the
engineer must run repeatedly to confirm — a single green run is not proof.

## When to use
- A test passes sometimes and fails other times without code changes.
- Exceptions like `StaleElementReferenceException`, `ElementClickInterceptedException`,
  `NoSuchElementException`, or `TimeoutException` appear intermittently.
- Behavior differs between local and CI/grid runs.

## Workflow
1. **Collect evidence**: the stack trace, the failing line, the locator involved, and
   whether it's local-only or CI-only. Don't guess the cause without the trace.
2. **Classify the failure**:
   - *Stale element* → element re-rendered; re-find inside a wait, don't cache the `WebElement`.
   - *Timing/sync* → acted before ready; replace sleeps/implicit waits with explicit `ExpectedConditions`.
   - *Click intercepted* → overlay/animation; wait for `elementToBeClickable` or overlay invisibility.
   - *Dynamic content* → list/DOM changes; use `FluentWait` polling + ignore stale exceptions.
   - *Order dependence* → shared state; isolate data/driver per test.
3. **Propose the targeted fix** for that class — re-locate on demand, add intent-based
   waits, scope locators, or isolate state.
4. **Harden**: recommend a retry analyzer (`IRetryAnalyzer`) only as a safety net, never
   as a substitute for fixing the race.
5. **Emit** the before/after with the root-cause explanation, and say how many repeat runs prove it.

## Output shape
```java
// SYMPTOM: StaleElementReferenceException — WebElement cached before the row re-rendered
WebElement row = driver.findElement(By.cssSelector(".row"));
row.click();                      // throws when the grid refreshes between find and click

// FIX: re-find inside a wait; never hold a reference across a DOM update
new WebDriverWait(driver, Duration.ofSeconds(10))
    .ignoring(StaleElementReferenceException.class)
    .until(ExpectedConditions.elementToBeClickable(By.cssSelector(".row"))).click();

// SYMPTOM: ElementClickInterceptedException — a spinner overlays the button
wait.until(ExpectedConditions.invisibilityOfElementLocated(By.cssSelector(".loading-overlay")));
wait.until(ExpectedConditions.elementToBeClickable(By.id("submit"))).click();
```

## Guardrails
- A fix is a **hypothesis the engineer must run repeatedly to confirm** — recommend N consecutive green runs, not one.
- **Never assume a locator exists**; reuse the exact locator from the failing test and flag any you had to infer.
- Do not "fix" flakiness with `Thread.sleep` or by raising implicit-wait globally — that hides races, not solves them.
- Treat retry analyzers as a net, not a cure; always name the underlying root cause.
- Don't blame the test without the stack trace — ask for it if it's missing.
- Never cache a `WebElement` across an action that mutates the DOM; re-find it.
