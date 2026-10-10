---
name: se-driver-manager
description: >-
  Sets up browser driver management with Selenium Manager (built-in) or
  WebDriverManager, browser options, and a thread-safe driver factory. Use when
  an SDET says "set up my WebDriver", "I keep getting driver version mismatch",
  "make a thread-safe driver factory", "configure ChromeOptions headless", or
  wants clean driver lifecycle for parallel runs. Produces code the engineer runs.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Driver Manager

You **set up driver resolution, browser options, and a thread-safe lifecycle**.
The factory code is a draft the engineer must run; driver/browser availability
depends on their machine.

## When to use
- A project hits driver/browser version mismatches or manual `chromedriver` paths.
- Someone wants headless, incognito, or custom `ChromeOptions`/`FirefoxOptions`.
- Parallel TestNG runs need per-thread isolated drivers (`ThreadLocal`).

## Workflow
1. **Choose resolution**: Selenium Manager (built-in to Selenium 4.6+, zero config —
   just `new ChromeDriver()`) or WebDriverManager (`WebDriverManager.chromedriver().setup()`)
   when you need pinning/proxy/mirror control. Recommend Selenium Manager by default.
2. **Build browser options** per browser: headless mode (`--headless=new`), window size,
   download prefs, disabling notifications — keep them in one place.
3. **Create a thread-safe factory** using `ThreadLocal<WebDriver>` so parallel tests each
   get an isolated session; expose `getDriver()` and `quitDriver()`.
4. **Select browser by config** (system property/env var) so the same factory serves
   Chrome/Firefox/Edge.
5. **Guarantee cleanup**: `quitDriver()` calls `quit()` and `remove()` from the ThreadLocal
   to avoid leaks across threads.
6. **Emit** the factory + options, noting which browsers you could not verify installed.

## Output shape
```java
public final class DriverFactory {
    private static final ThreadLocal<WebDriver> TL = new ThreadLocal<>();

    public static WebDriver getDriver() {
        if (TL.get() == null) TL.set(create(System.getProperty("browser", "chrome")));
        return TL.get();
    }

    private static WebDriver create(String browser) {
        switch (browser.toLowerCase()) {
            case "firefox":
                return new FirefoxDriver(new FirefoxOptions());
            case "edge":
                return new EdgeDriver(new EdgeOptions());
            default:                                   // Selenium Manager auto-resolves the driver
                ChromeOptions opts = new ChromeOptions();
                if (Boolean.getBoolean("headless")) opts.addArguments("--headless=new", "--window-size=1920,1080");
                return new ChromeDriver(opts);
        }
    }

    public static void quitDriver() {
        if (TL.get() != null) { TL.get().quit(); TL.remove(); }   // remove() prevents thread leaks
    }
}
```

## Guardrails
- This factory is a **draft the engineer must run** — driver resolution can fail on machines without the target browser installed.
- **Never assume a locator exists** in example usage; the factory returns a driver only, tests supply real selectors.
- Prefer Selenium Manager over hardcoded driver paths or `System.setProperty("webdriver.chrome.driver", ...)`.
- Always `remove()` the ThreadLocal in cleanup — a lingering entry leaks a session into the next test on that thread.
- Don't share one static `WebDriver` across parallel threads; that is the classic cause of cross-talk flakiness.
- Do not fabricate installed browser versions; if you can't confirm one, say the engineer must verify it.
