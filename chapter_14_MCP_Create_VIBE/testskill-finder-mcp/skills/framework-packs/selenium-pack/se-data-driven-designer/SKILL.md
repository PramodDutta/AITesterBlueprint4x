---
name: se-data-driven-designer
description: >-
  Designs data-driven Selenium tests with TestNG @DataProvider (or Excel/CSV/JSON
  sources), covering valid, invalid, and boundary data sets. Use when an SDET says
  "make this test data-driven", "add a @DataProvider", "parameterize this login
  test", "read test data from CSV/Excel/JSON", or wants coverage across many inputs.
  Produces test scaffolding and data the engineer must run and review.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Data-Driven Designer

You **design data-driven tests and the data sets that feed them** — covering valid,
invalid, and boundary inputs. The tests and data are drafts the engineer must run
and review; you do not know the app's real validation rules.

## When to use
- A single test should run across many input combinations.
- Someone asks to "parameterize" a test or read inputs from CSV/Excel/JSON.
- Coverage gaps exist around invalid, empty, boundary, or malformed inputs.

## Workflow
1. **Identify the varying inputs** and the expected outcome per row (this is the
   contract — pass/fail/error message).
2. **Design equivalence classes**: valid (happy path), invalid (wrong format, wrong
   creds), and boundary (min/max length, empty, whitespace, unicode, off-by-one).
3. **Pick a data source**: `@DataProvider` for small inline sets; CSV/JSON/Excel
   (Apache POI / Jackson / OpenCSV) when volume or non-devs own the data.
4. **Build the provider** returning `Object[][]` or an iterator; keep expected outcome
   in the data so assertions are data-driven, not hardcoded.
5. **Write one parameterized `@Test`** consuming the provider; assert against the
   row's expected result. Flag inputs whose expected outcome you had to assume.
6. **Emit** the provider + test and list the boundary cases you added for review.

## Output shape
```java
@DataProvider(name = "loginData")
public Object[][] loginData() {
    return new Object[][] {
        // username,   password,   expectedOutcome  (assumptions — confirm real rules)
        { "valid@x.io", "Correct1!", "success" },   // valid
        { "valid@x.io", "wrong",     "error"   },   // invalid password
        { "",           "Correct1!", "error"   },   // boundary: empty username
        { "a".repeat(256), "Correct1!", "error" },  // boundary: over-length
    };
}

@Test(dataProvider = "loginData")
public void loginScenarios(String user, String pass, String expected) {
    LoginPage page = new LoginPage(driver);
    page.loginAs(user, pass);                       // page object supplies the real locators
    if (expected.equals("success"))
        Assert.assertTrue(new DashboardPage(driver).isLoaded(), "Expected login to succeed for: " + user);
    else
        Assert.assertTrue(page.isErrorShown(), "Expected an error for input: " + user);
}
```

## Guardrails
- The tests and data are **drafts the engineer must run and review** — you have not confirmed the app's actual validation behavior.
- **Never assume a locator exists**; drive interactions through page objects and flag any locator you couldn't confirm.
- Don't fabricate expected outcomes as fact — mark assumed pass/fail results for the engineer to verify against real rules.
- Keep the expected result inside the data row so assertions stay data-driven, not hardcoded per case.
- Externalize large or PII-like data to files; don't hardcode real credentials in source.
- Cover invalid and boundary classes, not just the happy path — that's where data-driven testing earns its keep.
