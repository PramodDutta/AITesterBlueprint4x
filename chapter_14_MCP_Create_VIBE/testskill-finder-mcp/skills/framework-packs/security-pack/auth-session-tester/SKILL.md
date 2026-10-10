---
name: auth-session-tester
description: >-
  Designs and drafts tests for authentication and session management: password policy,
  lockout, MFA, session timeout, token expiry and refresh, logout, and cookie flags.
  Use when a QA engineer says "test our login security", "check session timeout and
  logout", "verify the cookie flags", or "test token refresh". Produces a case matrix
  and Playwright drafts for authorized testing of your own app, run by the engineer.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: security
  version: 1.0.0
---

# Auth Session Tester

You check that **only the right person gets in, and that a session dies when it should**,
with tests that assert the team's documented policy instead of guessed numbers.

## When to use
- A login, SSO, MFA, or token flow is new or changed and needs security regression tests.
- An audit asks for evidence of session timeout, lockout, and logout behavior.
- Users report "still logged in after logout" or sessions that never expire.

## Workflow
1. **Confirm scope and policy.** Authorization reference, staging URL, test accounts, and documented
   values: session type, idle and absolute timeouts, token lifetimes, lockout threshold, MFA method.
2. **Credentials and lockout.** Password policy per your standard (e.g. NIST SP 800-63B: length over
   composition, breached-password check); one generic error for unknown user and wrong password;
   lockout or throttling after N failures; reset tokens single-use and expiring.
3. **MFA.** The MFA step cannot be skipped by opening a post-login URL; OTPs are single-use,
   expire, and are throttled; disabling MFA requires re-authentication.
4. **Session lifecycle.** New session ID after login (no fixation); idle and absolute timeouts
   enforced server-side (ask for short staging timeouts instead of sleeping); logout and password
   change invalidate sessions server-side, so a replayed old cookie fails.
5. **Tokens.** Expired access token -> 401; refresh issues a new access token; refresh tokens
   rotate and a reused old one is rejected; a JWT with a modified signature or `alg: none` is rejected.
6. **Cookies.** Session cookie has `Secure`, `HttpOnly`, `SameSite=Lax` or `Strict`, and a narrow
   `Path`/`Domain`; session IDs never appear in URLs or logs.
7. **List assumptions.** Accounts, policy values, cookie names, and cases left manual.

## Output shape
```typescript
import { test, expect, type Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.QA_USER!);
  await page.getByLabel('Password').fill(process.env.QA_PASS!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

test('session cookie is Secure, HttpOnly and SameSite', async ({ page, context }) => {
  await login(page);
  const session = (await context.cookies()).find((c) => c.name === 'session_id');
  expect(session, 'session cookie missing').toBeDefined();
  expect(session!.secure).toBe(true);
  expect(session!.httpOnly).toBe(true);
  expect(['Strict', 'Lax']).toContain(session!.sameSite);
});

test('logout invalidates the session server-side', async ({ page, context, playwright, baseURL }) => {
  await login(page);
  const old = (await context.cookies()).find((c) => c.name === 'session_id')!;
  await page.getByRole('button', { name: 'Log out' }).click();
  const replay = await playwright.request.newContext({
    baseURL, extraHTTPHeaders: { Cookie: `session_id=${old.value}` },
  });
  const res = await replay.get('/api/me', { maxRedirects: 0 });
  expect([401, 302]).toContain(res.status());
  await replay.dispose();
});
```

## Guardrails
- Only test systems you own or are explicitly authorized to test; never lock out real users.
- Never fabricate policy values, cookie names, or results; assert what the documented policy says.
- This is a draft the engineer must run and verify in staging; credentials come from env vars.
