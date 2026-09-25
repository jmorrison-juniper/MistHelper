# Implementation Plan: The single-site upgrade journey measures every step

**Issue**: #3377 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Make the stand-in options view answer the shipped shape. Give the single-site
upgrade journey its own stand-in site. Turn each skip of a broken step into a
failure that names the cause.

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
  comment. The new stand-in helper logs before and after its build.
- **STE**: every new text passes the STE linter at 80 or more.

## Files

| File | Change |
| - | - |
| `tests/e2e/upgrade_portal/conftest.py` | Add `JOURNEY_SITE_ID` and `JOURNEY_SITE_NAME`. List the site in `stand_in_cloud_read`. Add `stand_in_view_of`, and call it from both stand-in options views. |
| `tests/e2e/upgrade_portal/test_upgrade.py` | Add the type control test. Use the journey site. Turn each skip of a broken step into a failure. Free the site lock at the end of each confirm test. Save two screenshots. |

## Order of work

1. Add the type control test, and turn the skips into failures. Run the file
   on the old stand-in, and record the red result.
2. Change `conftest.py`, and point the journey at its own site.
3. Add the release step to `confirm_page`, as research Decision 5 records.
4. Run the file green with 0 skips. Read the screenshots.
5. Run the browser suite of the upgrade portal, the portal suites, and every
   gate.

## Risks

- **A test that counts the site rows.** The search in the research file found
  none.
- **A test that reads the multi-site options view.** The new field is extra,
  and the multi-site route ignores it.
- **A stale journey run in a later module.** `test_upgrade.py` is the last
  module of its folder, and the run lives on its own site.
- **A site lock that one test leaves for the next test.** Each confirm test
  frees the lock at the end. A release that fails reports a teardown error that
  names the answer.
