# Implementation Plan: Put a space after the signal word of each alert

**Issue**: #3277 | **Spec**: [spec.md](spec.md)

## Design

1. Add one trailing space to each of the four `content` values in section 12
   of `src/upgrade_portal/app/assets/static/css/portal.css`.
2. Extend the comment above `.flash-item::before`. The comment states why the
   space exists and why the flex items keep their look.

The change is in the stylesheet, not in the script. Every alert gets its
signal word from the stylesheet, so one rule set covers each current alert and
each later alert. A script repair would cover one call site only.

## Tests

- Unit test `tests/unit/upgrade_portal/test_flash_prefix_space.py`. It reads
  the rule of each level and compares the `content` value with the signal word
  and one space.
- Browser test `tests/e2e/upgrade_portal/test_alert_prefix_space.py`. It walks
  the sign-in journey of the issue with a refused browser token. It also writes
  one message for each level through `window.upgradePortal.showFlash`. Each
  test reads the ARIA snapshot of the alert, which holds the generated signal
  word, and saves a screenshot.

## Guard proof

- On the old stylesheet, the unit test fails 4 of 4. The sign-in journey fails
  with the snapshot `- alert: Warning:The portal could not sign you in.`
- The four flash tests pass on the old stylesheet too. A flash item is a flex
  box, so the ARIA text already holds a break. These tests are parity guards.

## Risks

- A test that compares the exact `content` value breaks. The current tests
  use `in` on the computed value, so they pass. The run of
  `tests/e2e/upgrade_portal/test_signin.py` and
  `tests/e2e/test_hidden_flash_guard.py` proves it.
