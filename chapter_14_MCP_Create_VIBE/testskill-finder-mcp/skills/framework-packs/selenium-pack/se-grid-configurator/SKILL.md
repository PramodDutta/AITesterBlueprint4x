---
name: se-grid-configurator
description: >-
  Configures Selenium Grid 4 (hub-and-node or standalone, including Docker) and
  wires RemoteWebDriver for parallel and distributed runs. Use when an SDET says
  "set up Selenium Grid", "run my tests on a remote grid", "dockerize Selenium Grid
  4", "point my tests at RemoteWebDriver", or wants parallel execution across nodes.
  Produces config and code the engineer must run and validate in their environment.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: selenium
  version: 1.0.0
---

# Selenium Grid Configurator

You **stand up Selenium Grid 4 and connect tests via RemoteWebDriver**. All config
is a draft the engineer must run in their own environment — you cannot see their
network, ports, or host resources.

## When to use
- Someone wants distributed/parallel execution across browsers or machines.
- A local test suite must be pointed at a remote grid endpoint.
- Someone asks to "dockerize the grid" or "add nodes for Chrome and Firefox".

## Workflow
1. **Pick a topology**: standalone (single JVM, quickest), hub-and-node (classic
   distributed), or fully distributed (router/distributor/sessions) for scale.
2. **Choose the runtime**: local JARs (`selenium-server-<v>.jar`) or Docker via
   `docker-compose` with `selenium/hub` + `selenium/node-chrome`/`node-firefox`.
3. **Set grid endpoint & capacity**: hub URL (default `http://localhost:4444`),
   `SE_NODE_MAX_SESSIONS`, and `--max-sessions` for parallelism.
4. **Wire RemoteWebDriver** in the test with `browserName`/`browserVersion` options,
   pointing at the hub `/wd/hub` (or root in Grid 4) URL — parameterize the URL by env var.
5. **Enable parallelism** in TestNG (`parallel="methods"` + `thread-count`) so multiple
   sessions hit the grid at once.
6. **Emit** compose file + Java, then note ports/versions the engineer must confirm.

## Output shape
```yaml
# docker-compose.yml — Selenium Grid 4 (hub + chrome/firefox nodes)
services:
  selenium-hub:
    image: selenium/hub:4.25.0
    ports: ["4442:4442", "4443:4443", "4444:4444"]
  chrome:
    image: selenium/node-chrome:4.25.0
    depends_on: [selenium-hub]
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_MAX_SESSIONS=4
```
```java
// RemoteWebDriver pointed at the grid (parameterize the URL by env var)
String gridUrl = System.getProperty("gridUrl", "http://localhost:4444");
ChromeOptions options = new ChromeOptions();
WebDriver driver = new RemoteWebDriver(new URL(gridUrl), options);
// TestNG: <suite parallel="methods" thread-count="4"> to drive concurrent grid sessions
```

## Guardrails
- This config is a **draft the engineer must run and validate** — ports, image tags, and host capacity are environment-specific.
- **Never assume a locator exists** in any example test; keep tests locator-agnostic and let the engineer supply real selectors.
- Pin image/JAR versions to the Selenium version in use — don't fabricate a version or use `:latest` in examples without saying so.
- Size `thread-count` and `SE_NODE_MAX_SESSIONS` to real node CPU/RAM; over-subscription causes flakiness, not speed.
- Don't hardcode the hub URL in tests — parameterize by env var/system property for CI portability.
- Always `driver.quit()` remote sessions so grid slots are released.
