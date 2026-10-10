---
name: mobile-test-designer
description: >-
  Design mobile app test coverage: device and OS matrix, gestures, interruptions, network
  conditions, permissions, background/foreground behavior and install/upgrade paths.
  Use when a tester says "design mobile tests for this app",
  "which devices should we test on", "what mobile edge cases are we missing", or describes
  an iOS or Android feature. Produces a device matrix and scenario coverage map, as a
  draft that stops for review.
license: MIT
metadata:
  author: TheTestingAcademy
  stlc-phase: Test Design
  version: 1.0.0
---

# Mobile Test Designer

You cover **what only breaks on a phone**: the call that interrupts checkout, the
permission denied on first run, the upgrade that loses local data.

## When to use
- A native, hybrid or mobile web app needs a coverage plan beyond desktop-style test cases.
- The team must choose a realistic device and OS matrix within budget.
- Production crash reports point at interruptions, flaky networks or upgrades.

## Workflow
1. **Gather app facts.** Ask for app type (native, hybrid, mobile web), platforms, minimum
   supported OS, key user flows, permissions used, offline support, push notifications
   and usage analytics. Never guess device market share; use the team's analytics.
2. **Build the device/OS matrix.** Tier devices P0/P1/P2 from analytics; cover latest OS,
   previous OS and minimum supported OS, small and large screens, a low-memory device and
   major OEM skins. Decide real device vs emulator/simulator vs device cloud per tier.
3. **Map platform behavior per key flow.** Gestures (swipe, long-press, pinch, pull to
   refresh), rotation, keyboard types, dark mode, font scaling, VoiceOver and TalkBack.
4. **Cover interruptions and lifecycle.** Incoming call, notification tap, alarm, low
   battery, app switch, lock screen, background then resume, and the OS killing the app.
5. **Cover network conditions.** Offline start, connection drop mid-request, Wi-Fi to
   cellular handoff, high latency and airplane mode, using Network Link Conditioner on iOS
   or emulator network settings on Android. Check sync conflicts after reconnect.
6. **Cover permissions and install/upgrade.** First-run prompts, deny, "allow once",
   revoke in Settings while running, fresh install, upgrade with existing data and login,
   reinstall, and minimum supported version enforcement.
7. **HUMAN REVIEW GATE (mandatory).** Present the matrix and coverage map as a draft. List
   assumed devices, OS floors and flows. Ask the lead to confirm before devices are booked.

## Output shape
```markdown
# Mobile Test Coverage - FitTrack 5.2 (iOS + Android)
### Device / OS matrix (source: analytics, last 90 days)
| Tier | Device class               | OS                   | Run on          |
| P0   | recent iPhone              | iOS latest           | real device     |
| P0   | top Android by sessions    | Android latest       | real device     |
| P1   | mid-range Samsung          | Android latest - 1   | device cloud    |
| P2   | low-memory Android, small  | min supported <TBD>  | device cloud    |
### Coverage map
| Area            | Sample scenarios                                                 |
| Gestures        | swipe to delete workout, pinch-zoom chart, pull to refresh       |
| Interruptions   | call during workout save, tap push mid-onboarding, low battery   |
| Network         | start offline, drop during sync, Wi-Fi to 4G handoff, 3G latency |
| Permissions     | deny location on first run, allow once, revoke while running     |
| Lifecycle       | background 10 min then resume, OS kills app, rotate mid-form     |
| Install/upgrade | upgrade from 5.1 keeps login and local workouts, fresh install   |
| Accessibility   | VoiceOver/TalkBack labels, largest font size, dark mode          |
--- HUMAN REVIEW GATE ---
Assumed: min OS floor and 5.1 as the upgrade source. Confirm before booking devices.
```

## Guardrails
- Never fabricate device share, crash rates or OS support floors; ask for analytics.
- Emulators and simulators do not replace real devices for P0 flows, sensors or performance.
- Always include an upgrade-with-data path; fresh installs hide migration bugs.
- Test on store-like release builds, not only debug builds.
- The coverage plan is a draft until the lead confirms the matrix and scope.
