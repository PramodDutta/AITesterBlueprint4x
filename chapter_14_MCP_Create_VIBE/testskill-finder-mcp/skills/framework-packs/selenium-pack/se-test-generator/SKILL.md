---
name: se-test-generator
description: >-
  Generates a runnable Selenium 4 + TestNG test in Java from a plain-language
  scenario, using explicit waits and stable locators. Use when an SDET says
  "write a Selenium test for login", "generate a TestNG test for the checkout
  flow", "automate this scenario in Selenium", or pastes Gherkin/steps and wants
  Java WebDriver code. Produces a draft test the engineer must review and run.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Test Generator

You draft a **Selenium + TestNG test the engineer still has to run and verify** —
not a guaranteed-passing artifact. Locators you emit are proposals until confirmed
against the real DOM.

## When to use
- A scenario, user story, or Gherkin steps are given and someone wants a Java Selenium test.
- Someone says "automate this flow" / "generate a TestNG test" / "turn these steps into WebDriver code".
- An existing manual test case needs a first-pass automation draft.

## Workflow
1. **Parse the scenario** into: preconditions, ordered actions, and observable
   assertions. If the target URL, credentials, or expected result are missing,
   ask — do not invent them.
2. **Map each step to an interaction**: navigation, input, click, or assertion.
   Note which UI element each touches and flag any element whose locator you cannot confirm.
3. **Choose stable locators** — prefer `By.id`, then `By.cssSelector`, then Selenium 4
   relative locators (`with(...).below(...)`). Avoid absolute XPath. Mark unconfirmed
   locators with a `// TODO: confirm locator` comment.
4. **Add explicit synchronization** — a `WebDriverWait` with `ExpectedConditions`
   before every interaction that depends on element state. Never emit `Thread.sleep`.
5. **Write assertions** using TestNG `Assert`, tied to the scenario's expected result.
6. **Emit the test** with `@BeforeMethod`/`@AfterMethod` lifecycle and Selenium Manager
   driver setup, then list the assumptions and unconfirmed locators for the engineer.

## Output shape
```java
public class LoginTest {
    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {
        driver = new ChromeDriver();            // Selenium Manager resolves the driver
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    @Test
    public void validUserCanLogIn() {
        driver.get("https://app.example.com/login");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("username"))).sendKeys("qa_user");
        driver.findElement(By.id("password")).sendKeys("secret");     // TODO: confirm locator
        driver.findElement(By.cssSelector("button[type='submit']")).click();
        WebElement banner = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-test='welcome']")));
        Assert.assertTrue(banner.isDisplayed(), "Welcome banner should appear after login");
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) driver.quit();
    }
}
```

## Guardrails
- This is a **draft the engineer must run and review** — never claim the test passes; you have not executed it.
- **Never assume a locator exists.** Every locator you did not verify against the real DOM gets a `// TODO: confirm locator` and appears in your assumptions list.
- Do not fabricate URLs, credentials, or expected results — a missing input is a question, not a blank to fill.
- Never emit `Thread.sleep`; synchronize with `WebDriverWait`/`ExpectedConditions`.
- Prefer `By.id`/`By.cssSelector`/relative locators over brittle absolute XPath.
- Always `driver.quit()` in teardown so sessions don't leak.
