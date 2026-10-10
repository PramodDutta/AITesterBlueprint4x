---
name: se-report-integrator
description: >-
  Integrates reporting (Allure or ExtentReports) into a Selenium + TestNG suite
  with listeners, screenshot-on-failure, and step logging. Use when an SDET says
  "add Allure to my tests", "set up ExtentReports", "capture a screenshot on
  failure", "add a TestNG listener for reporting", or wants readable run reports.
  Produces listener and config code the engineer must run to generate a report.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Report Integrator

You **wire reporting into a TestNG + Selenium suite** — Allure or ExtentReports, with
failure screenshots and step logs. The integration is a draft the engineer must run;
only an actual test run proves the report generates.

## When to use
- A suite produces only console/TestNG default output and needs a readable report.
- Someone wants a screenshot attached automatically when a test fails.
- Step-level logging is needed for triage across a run.

## Workflow
1. **Pick the reporter**: Allure (CI-friendly, `allure serve` HTML, annotations) or
   ExtentReports (self-contained HTML, rich in-code logging). Match what CI expects.
2. **Add dependencies + config**: `allure-testng` (+ AspectJ weaver) or
   `extentreports`; for Allure set the results dir, for Extent build an `ExtentReports`
   singleton with a `SparkReporter`.
3. **Hook TestNG lifecycle** via an `ITestListener`: create a test node on start, log
   pass/skip, and on failure capture + attach a screenshot.
4. **Capture screenshots** with `((TakesScreenshot) driver).getScreenshotAs(...)` inside
   `onTestFailure`; attach as Allure attachment or Extent `addScreenCaptureFromPath`.
5. **Log steps** — Allure `@Step`/`Allure.step(...)` or Extent `test.log(...)` from page
   actions — so the report reads as a narrative.
6. **Register the listener** in `testng.xml` and emit config, noting versions to confirm.

## Output shape
```java
public class ScreenshotListener implements ITestListener {
    @Override
    public void onTestFailure(ITestResult result) {
        WebDriver driver = DriverFactory.getDriver();   // driver from the running test's factory
        byte[] png = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);
        // Allure:
        Allure.addAttachment(result.getName() + "-failure", "image/png", new ByteArrayInputStream(png), "png");
        // ExtentReports alternative:
        // ExtentTestManager.getTest().fail("Failed", MediaEntityBuilder.createScreenCaptureFromPath(path).build());
    }

    @Override public void onTestSuccess(ITestResult r) { Allure.step("PASS: " + r.getName()); }
}
```
```xml
<!-- testng.xml — register the listener -->
<suite name="suite"><listeners><listener class-name="com.qa.listeners.ScreenshotListener"/></listeners> ... </suite>
```

## Guardrails
- This integration is a **draft the engineer must run** — the report only exists after an actual test execution (e.g. `allure serve target/allure-results`).
- **Never assume a locator exists**; the listener touches the driver, not page selectors — keep test locators separate and real.
- Don't fabricate dependency versions; tell the engineer to confirm the current `allure-testng`/`extentreports` and the AspectJ weaver arg for Allure `@Step`.
- Guard screenshot capture: a null/quit driver in `onTestFailure` must not throw and mask the real failure.
- Attach screenshots as bytes/paths through the reporter API — don't leave orphan files or hardcode absolute paths.
- Keep secrets out of logs/screenshots; don't log credentials into the report.
