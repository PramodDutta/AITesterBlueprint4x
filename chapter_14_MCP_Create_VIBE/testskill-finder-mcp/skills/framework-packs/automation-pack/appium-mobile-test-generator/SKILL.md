---
name: appium-mobile-test-generator
description: >-
  Generates Appium mobile test drafts (WebdriverIO or Java) with accessibility-id
  locators, Android and iOS capabilities, and explicit waits. Use when an SDET says
  "write an Appium test for this screen", "automate this mobile flow", "set up Appium
  capabilities for Android and iOS", or pastes a screen description, page source, or
  manual test case. Produces capabilities and test code a mobile engineer must run on a
  real device or emulator.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: automation
  version: 1.0.0
---

# Appium Mobile Test Generator

You draft **mobile tests that survive app updates**: accessibility-id locators, explicit waits,
and one test flow that runs on both Android and iOS where the app allows it.

## When to use
- A mobile flow (login, checkout, onboarding) needs automated coverage on Android and iOS.
- An existing Appium suite relies on XPath and `sleep` and keeps breaking.
- A team is starting Appium and needs correct capabilities for emulators and simulators.

## Workflow
1. **Collect the inputs.** Ask for platform(s), app path or bundle/package id, device or
   emulator names, OS versions, client (WebdriverIO JS/TS or Java), and the flow steps. Ask
   for the page source (Appium Inspector) instead of guessing element ids.
2. **Pick locators.** Prefer accessibility id (Android `content-desc`, iOS
   `accessibilityIdentifier`): `$('~login-submit')` in WebdriverIO,
   `AppiumBy.accessibilityId("login-submit")` in Java. Fall back to resource-id or iOS
   predicate strings. Never use index-based XPath. List elements that need ids from the devs.
3. **Write the capabilities.** W3C format: `platformName`, plus `appium:automationName`
   (`UiAutomator2` for Android, `XCUITest` for iOS), `appium:deviceName`,
   `appium:platformVersion`, and `appium:app`. App paths and credentials come from env vars.
4. **Write the test with explicit waits.** `waitForDisplayed` / `waitForEnabled` in
   WebdriverIO, `WebDriverWait` with `ExpectedConditions` in Java. No fixed sleeps.
5. **Handle platform differences.** Keyboard, permissions dialogs, back navigation, and
   platform-only screens go in small helpers, not `if` statements scattered in tests.
6. **List assumptions for the engineer.** Missing accessibility ids, assumed device names, app
   build, test account, and anything to confirm in Appium Inspector.

## Output shape
```typescript
// wdio.android.conf.ts (capabilities excerpt; iOS config uses XCUITest)
capabilities: [{
  platformName: 'Android',
  'appium:automationName': 'UiAutomator2',
  'appium:deviceName': 'Pixel_7_API_34',
  'appium:app': process.env.ANDROID_APP_PATH,
}],

// test/specs/login.e2e.ts
describe('Login', () => {
  it('signs in with valid credentials', async () => {
    const email = await $('~login-email');
    await email.waitForDisplayed({ timeout: 15000 });
    await email.setValue(process.env.TEST_USER_EMAIL!);
    await $('~login-password').setValue(process.env.TEST_USER_PASSWORD!);
    await $('~login-submit').click();
    await expect($('~home-greeting')).toBeDisplayed();
  });
});
```

## Guardrails
- This is a **draft the engineer must run on a real device or emulator**; it is not verified until it passes there.
- Never fabricate accessibility ids, package names, or bundle ids; get them from page source or the devs.
- No `driver.pause()` or `Thread.sleep()` as synchronization; use explicit waits.
- Keep credentials and app paths in env vars or the CI secret store, never in code.
- Do not use index-based XPath; ask for accessibility ids instead.
