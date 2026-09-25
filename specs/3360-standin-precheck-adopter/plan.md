# Implementation Plan: The browser test store adopts only a standalone pre-check

**Issue**: #3360 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Make the E2E stand-in adopter obey the two rules of the shipped reader. Seed
one standalone pre-check, so each journey that needs a ready first site keeps
it. Add one browser assertion that the card shows no capture that a run owns.

## Technical context

- **Language**: Python 3.13.
- **Test tools**: pytest and Playwright with the Edge channel.
- **Product code**: none changes.
- **Storage**: none. The stand-in store holds each record in memory.

## Constitution check

- **Safety**: the change touches test code only. No cloud call and no firmware
  write occur.
- **5-Item Rule**: each changed function keeps five blocks or fewer and 25
  lines or fewer.
- **Inline comments and action logging**: each changed line carries an inline
  comment. The stand-in logs before and after its scan.
- **STE**: every new text passes the STE linter at 80 or more.

## Files

| File | Change |
| - | - |
| `tests/support/upgrade_portal_e2e/records/portal.py` | Add the run filter to `_is_precheck`. Add `_start_moment`. Pick the newest match in `newest_precheck`. |
| `tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py` | New. One test for each scenario of user story 1. |
| `tests/e2e/upgrade_portal/conftest.py` | Add the standalone seed `e2e-capture-standalone-0001` to `stand_in_capture_index`. |
| `tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py` | Assert that the first row is ready and names no capture that a run owns. |

## Order of work

1. Write the unit tests. Run them on the old stand-in, and record the red
   result.
2. Add the seed and the browser assertion. Run the journey on the old
   stand-in, and record the red result. Read the screenshot.
3. Change the stand-in. Run the unit tests and the journey green.
4. Run the browser suite of the upgrade portal and every gate.

## Risks

- **A journey that depends on the adoption of a capture that a run owns.** The
  search found one journey: `test_org_missing_precheck_journey.py`. The seed
  keeps its first site ready.
- **A journey that reads the capture list.** The seed sits in the middle of the
  insertion order and of the time order, so the first choice and the last
  choice of each picker stay the same.
