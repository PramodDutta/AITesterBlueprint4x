---
name: se-wait-fixer
description: >-
  Scans Selenium Java code for Thread.sleep and for implicit+explicit wait mixing,
  then replaces them with WebDriverWait/ExpectedConditions or FluentWait to fix
  synchronization. Use when an SDET says "remove Thread.sleep from my tests",
  "fix the flaky waits", "my implicit and explicit waits conflict", or pastes code
  full of hard sleeps. Produces refactors the engineer must run and confirm.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Wait Fixer

You **fix synchronization** — replacing hard sleeps and dangerous wait mixing with
deterministic explicit waits. Your edits are drafts the engineer must run; you have
not observed the app's real timing.

## When to use
- Code contains `Thread.sleep(...)` and someone wants proper synchronization.
- Implicit waits (`manage().timeouts().implicitlyWait`) and explicit `WebDriverWait`
  are both used, causing unpredictable timeouts.
- Tests are flaky around loading, animations, AJAX, or elements appearing late.

## Workflow
1. **Scan** the code for: every `Thread.sleep`, every `implicitlyWait`, every
   `WebDriverWait`/`FluentWait`, and `networkidle`-style hacks.
2. **Diagnose the anti-pattern** for each hit: fixed sleep hiding a race, or implicit
   + explicit mixing (which can compound waits and cause erratic timeouts).
3. **Replace each `Thread.sleep`** with the `ExpectedConditions` that matches intent —
   `visibilityOf`, `elementToBeClickable`, `stalenessOf`, `textToBePresentInElement`,
   `invisibilityOf`, or a custom lambda for app-specific readiness.
4. **Resolve wait mixing**: remove implicit waits when using explicit waits (recommend
   picking one strategy — usually explicit), or use `FluentWait` with polling + ignored
   exceptions for slow, intermittently-stale elements.
5. **Preserve behavior**: keep the same element and intent; only change *how* it waits.
6. **Emit the diff** with a one-line rationale per change and note any timeout you guessed.

## Output shape
```java
// BEFORE — hard sleep hides a race; implicit + explicit mixed = unpredictable timeouts
driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
element.click();
Thread.sleep(3000);                       // brittle: too long on fast runs, too short on slow ones
driver.findElement(By.id("result")).getText();

// AFTER — explicit, intent-based synchronization (remove the implicit wait entirely)
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.elementToBeClickable(By.id("save"))).click();
String text = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("result"))).getText();

// For slow, intermittently-stale elements — FluentWait with polling + ignored exceptions
new FluentWait<>(driver)
    .withTimeout(Duration.ofSeconds(15))
    .pollingEvery(Duration.ofMillis(500))
    .ignoring(StaleElementReferenceException.class)
    .until(d -> d.findElement(By.id("status")).getText().equals("Ready"));
```

## Guardrails
- These are **refactors the engineer must run and confirm** — you have not measured the app's actual load timing.
- **Never assume a locator exists**; reuse the exact locators already in the code and flag any you had to guess.
- Do not silently keep any `Thread.sleep` — if a wait truly needs a hard pause (rare, e.g. animation with no state change), call it out explicitly with justification.
- Never combine implicit and explicit waits; recommend one strategy and remove the other.
- Don't invent timeout values as fact — state that the engineer should tune them to real conditions.
- Prefer intent-specific `ExpectedConditions` over generic presence checks so the wait means something.
