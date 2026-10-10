---
name: se-cross-browser-runner
description: >-
  Sets up cross-browser Selenium execution across Chrome, Firefox, and Edge via
  TestNG parameters or a factory, plus a browser matrix. Use when an SDET says "run
  my tests on Chrome and Firefox", "add cross-browser support", "parameterize the
  browser in testng.xml", "set up a browser matrix", or wants multi-browser CI runs.
  Produces config and code the engineer must run per browser to confirm.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Cross-Browser Runner

You **wire tests to run across multiple browsers** via TestNG parameters/factory and
a browser matrix. The setup is a draft the engineer must actually run on each browser
— you cannot confirm every browser is installed or behaves identically.

## When to use
- The same suite must execute on Chrome, Firefox, and/or Edge.
- Someone wants the browser selectable from `testng.xml` or a system property.
- A CI browser matrix (browser × maybe version/OS) needs defining.

## Workflow
1. **Parameterize the browser**: a `@Parameters("browser")` value from `testng.xml`,
   or a `@Factory` that instantiates the test class once per browser.
2. **Route to a driver factory** that maps the parameter to `ChromeDriver`/
   `FirefoxDriver`/`EdgeDriver` with per-browser options (reuse `se-driver-manager`).
3. **Define suite blocks** in `testng.xml` — one `<test>` per browser, or a single
   test parameterized and run under `parallel="tests"` for concurrency.
4. **Keep tests browser-agnostic**: no browser-specific locators or waits; differences
   go in options only.
5. **Add a matrix note** for CI (e.g. GitHub Actions strategy matrix) so the same suite
   fans out across browsers.
6. **Emit** `testng.xml` + factory glue and list browsers you could not verify installed.

## Output shape
```xml
<!-- testng.xml — one <test> per browser, run in parallel -->
<suite name="cross-browser" parallel="tests" thread-count="3">
  <test name="chrome">  <parameter name="browser" value="chrome"/>  <classes><class name="com.qa.tests.LoginTest"/></classes></test>
  <test name="firefox"> <parameter name="browser" value="firefox"/> <classes><class name="com.qa.tests.LoginTest"/></classes></test>
  <test name="edge">    <parameter name="browser" value="edge"/>    <classes><class name="com.qa.tests.LoginTest"/></classes></test>
</suite>
```
```java
public class BaseTest {
    protected WebDriver driver;

    @Parameters("browser")
    @BeforeMethod
    public void setUp(@Optional("chrome") String browser) {
        driver = DriverFactory.create(browser);   // maps param -> Chrome/Firefox/Edge (+ options)
    }

    @AfterMethod
    public void tearDown() { if (driver != null) driver.quit(); }
}
```

## Guardrails
- This is a **draft the engineer must run on each browser** — passing on Chrome does not prove Firefox/Edge pass.
- **Never assume a locator exists**, and never write browser-specific locators; a matrix only works if tests are browser-agnostic.
- Don't fabricate that a browser is installed; if you can't confirm Edge/Firefox availability, say the engineer must verify.
- Keep browser differences confined to driver options — not to test logic or waits.
- Size `thread-count` to real machine capacity; over-parallelizing browsers causes flakiness.
- Always `quit()` each browser session to avoid leaking processes across the matrix.
