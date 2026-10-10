---
name: se-framework-scaffolder
description: >-
  Scaffolds a Maven Selenium framework — TestNG suite, base test, Page Object
  package, config loader, logging, and reporting hooks. Use when an SDET says
  "scaffold a Selenium framework", "set up a new Maven Selenium project", "give me
  a POM/TestNG project structure", or is starting automation from zero. Produces a
  starter layout and files the engineer must build, run, and adapt.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Framework Scaffolder

You **lay out a Maven + Selenium + TestNG framework skeleton**. Everything you emit
is a starter the engineer must build (`mvn test`), run, and adapt — it is not a
finished framework.

## When to use
- A new project needs a repeatable structure instead of ad-hoc test files.
- Someone asks for "the standard Selenium framework layout" or "a base test + POM setup".
- An existing suite needs restructuring into layers (config, pages, tests, utils).

## Workflow
1. **Define the module layout**: `pom.xml`, `src/test/java` with packages `base`,
   `pages`, `tests`, `utils`, `config`, and `src/test/resources` for `testng.xml`,
   `config.properties`, `log4j2.xml`.
2. **Pin dependencies** in `pom.xml`: `selenium-java`, `testng`, a logger (Log4j2/SLF4J),
   and a reporter hook (Allure/ExtentReports) — state versions must be confirmed current.
3. **Write `BaseTest`**: driver lifecycle via a `DriverFactory` (ThreadLocal), config
   load in `@BeforeMethod`, `quit` in `@AfterMethod`.
4. **Add config loading**: a `ConfigReader` over `config.properties` (baseUrl, browser,
   timeouts) with system-property overrides for CI.
5. **Add logging + reporting hooks**: a TestNG `ITestListener` for start/pass/fail and
   screenshot-on-failure.
6. **Emit the tree + key files**, then list what the engineer must fill in (real URLs, pages).

## Output shape
```
selenium-framework/
├── pom.xml                         # selenium-java, testng, log4j2, allure/extent
├── testng.xml                      # suite: parallel + thread-count
└── src/test/
    ├── java/com/qa/
    │   ├── base/BaseTest.java      # driver up/down + config
    │   ├── config/ConfigReader.java
    │   ├── pages/                  # Page Objects
    │   ├── tests/                  # @Test classes extending BaseTest
    │   └── listeners/TestListener.java  # ITestListener: log + screenshot on fail
    └── resources/
        ├── config.properties       # baseUrl, browser, timeout
        └── log4j2.xml
```
```java
public abstract class BaseTest {
    protected WebDriver driver;

    @BeforeMethod
    public void setUp() {
        driver = DriverFactory.getDriver();
        driver.get(ConfigReader.get("baseUrl"));   // TODO: set real baseUrl in config.properties
    }

    @AfterMethod
    public void tearDown() { DriverFactory.quitDriver(); }
}
```

## Guardrails
- This is a **starter the engineer must build, run, and adapt** — `mvn test` on the raw skeleton proves structure, not passing tests.
- **Never assume a locator exists**; scaffolded page classes ship with `// TODO` locators, not fabricated selectors.
- Do not invent dependency versions as current — tell the engineer to confirm the latest compatible `selenium-java`/`testng`.
- Keep layers separated: no locators in tests, no assertions in pages, no config strings hardcoded.
- Wire driver management through a ThreadLocal factory so the suite is parallel-ready.
- Don't fabricate a baseUrl or credentials — leave them as config the engineer supplies.
