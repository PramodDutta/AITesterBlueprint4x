---
name: se-page-object-builder
description: >-
  Builds a Page Object Model class in Java (PageFactory @FindBy or explicit
  locators) with action methods and a WebDriverWait for a given page. Use when
  an SDET says "create a page object for the login page", "build a POM class",
  "refactor these locators into a page object", or pastes a page's fields and
  wants a reusable POM. Produces a draft class the engineer must review and run.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Page Object Builder

You draft a **Page Object the engineer still has to wire up and run** — a reusable
class that encapsulates one page's locators and actions. Locators are proposals
until confirmed against the real DOM.

## When to use
- A page's fields/buttons/flows are described and someone wants a POM class.
- Someone says "make a page object" / "encapsulate these locators" / "give me the POM for X page".
- Inline `driver.findElement` calls in a test need refactoring into a page class.

## Workflow
1. **Identify the page's responsibilities**: the elements it owns and the user
   actions it exposes (e.g. `login()`, `search()`, `getErrorText()`).
2. **Choose a style** — PageFactory `@FindBy` for simple pages, or explicit
   `By` locators for dynamic/lazy elements (explicit is more robust against staleness).
3. **Assign stable locators** — `By.id` > `By.cssSelector` > relative locators;
   avoid absolute XPath. Flag any locator you cannot confirm with a `// TODO` comment.
4. **Add a `WebDriverWait`** field; action methods wait for element readiness before
   acting. Never use `Thread.sleep`.
5. **Return types**: navigation actions return the next page object; queries return
   data (String/boolean). Keep methods small and intention-revealing.
6. **Emit the class** with a constructor taking `WebDriver`, then list unconfirmed locators.

## Output shape
```java
public class LoginPage {
    private final WebDriver driver;
    private final WebDriverWait wait;

    private final By username = By.id("username");
    private final By password = By.id("password");                 // TODO: confirm locator
    private final By submit   = By.cssSelector("button[type='submit']");

    public LoginPage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public DashboardPage loginAs(String user, String pass) {
        wait.until(ExpectedConditions.visibilityOfElementLocated(username)).sendKeys(user);
        driver.findElement(password).sendKeys(pass);
        driver.findElement(submit).click();
        return new DashboardPage(driver);
    }

    public boolean isErrorShown() {
        return !driver.findElements(By.cssSelector("[data-test='error']")).isEmpty();
    }
}
```

## Guardrails
- This is a **draft the engineer must review and run** — the class is unverified until exercised against the app.
- **Never assume a locator exists**; every unverified locator is a `// TODO: confirm locator` and appears in your notes.
- Keep pages focused — one class per page/component; don't cram unrelated flows in.
- No assertions inside the page object; assertions belong in tests.
- Never use `Thread.sleep`; synchronize with `WebDriverWait`/`ExpectedConditions`.
- Prefer explicit `By` locators when elements are dynamic — PageFactory proxies can go stale.
- Do not fabricate fields the page doesn't have; a missing element is a question.
