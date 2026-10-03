# Implementation Plan: Capture Click Journey Qualification

**Branch**: `jmorrison-juniper-qualify-issue-3380-capture-journey` |
**Date**: 2026-10-03 | **Spec**: [spec.md](./spec.md)

**Input**: Issue #3380 and the native browser run at accepted commit
`18127a874259732e9e6770de027e9485388b7592`.

## Summary

The unchanged journey creates a run and reaches its options page. It then skips
because it searches for the removed `upgrade-version-select-all` control.

The options page has separate controls for APs, switches, and gateways. Require
one device and one offered version for each control. Reuse the selection and
save helper from `tests/e2e/upgrade_portal/test_upgrade.py`.

Remove the obsolete row from the 1823 UI identifier contract. After the
confirmation path, return through the Sites link and the row for that site.
The unchanged fixture then cancels the run before it clicks the site's release
control.

The native capture module passed 12 tests with no skips. The live-run and
site-hold checks found no leaks. The site-selection module passed 10 tests.
The focused failure tests also passed.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing pytest, Playwright, and local portal fixture.

**Storage**: Existing isolated E2E fixture state. No schema or persistent data change.

**Testing**: Focused unit guard tests and native Playwright tests.

**Target Platform**: Local macOS worktree with the native test fixture.

**Project Type**: Test and contract documentation change.

**Performance Goals**: No new performance target.

**Constraints**: Do not edit `conftest.py`, support modules, production code, or
other tests. Keep browser recordings disabled. Do not connect to Mist Cloud.
Do not start firmware.

**Scale/Scope**: One click journey, one contract row, focused negative tests,
one release-note fragment, and three SpecKit artifacts.

## Constitution Check

- The change reuses the existing browser test and helper patterns.
- The test checks each control, device, and offered version.
- Run refusals and empty type controls fail before plan save.
- Run-ledger cleanup remains before site-lock release.
- No shared fixture or production code changes.

## Project Structure

```text
tests/e2e/upgrade_portal/test_capture.py
tests/unit/upgrade_portal/test_capture_click_journey.py
specs/1823-upgrade-capture-portal/contracts/ui-testids.md
changelog.d/issue-3380-capture-click-journey.md
specs/3380-capture-click-journey/
```

**Structure Decision**: Keep the test logic in the existing capture journey.
Add failure tests under the unit-test tree. Correct only the stale interface
row.

## Verification Plan

1. Run the target browser test with video, trace, and screenshots disabled.
2. Run the new failure tests.
3. Run all tests in `test_capture.py` and `test_site_selection.py`.
4. Run `test_upgrade.py` only if you must verify the shared selection helper.
5. Run Ruff, Black, and `py_compile` on the changed test modules.
6. Verify unchanged fixtures and zero leaked local runs or site holds.
