# Implementation Plan: Each browser test frees each site lock that it took, and the run fails when a lock stays

**Branch**: `fix/3508-browser-lock-leaks` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)
**Input**: The feature specification in `specs/3508-browser-lock-leaks/spec.md`

## Summary

Two browser tests leave a site lock after the test ends.
This change repairs the two tests and adds two guards.

1. The lock fixture of the run controls fails when a release fails.
2. A session check replays the site lock trail of the browser run after the portal stops.
   The run fails when a hold has no release.

research.md holds the decisions R1 through R11.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: pytest, Playwright with Edge, the lock module `src/interfaces/portals/upgrade_portal/runtime/lock.py`, and the audit reader `src/interfaces/portals/upgrade_portal/compare/lock_audit.py`.
**Storage**: The trail is one JSON Lines file in the artifact folder of each browser run. The change adds no store.
**Testing**: pytest. The direct tests use stand-in pages and temporary trail files.
**Target Platform**: Windows 11 on this computer, and Ubuntu on the CI runners.
**Project Type**: A test support change. The change touches no file under `src/`.
**Performance Goals**: The trail check adds less than 1 second to a full browser run (SC-005).
**Constraints**: The checkout trail guard of #3498 stays unchanged.
**Scale/Scope**: Nine new or changed test files, plus this record.

## Constitution Check

| Principle | Result | Note |
| - | - | - |
| Class-based design, no wrappers | Pass | The classes `HeldSiteLocks` and `TrailHoldCheck` hold each decision. The fixtures call them. |
| The 5-item rule | Pass | Each function holds 25 lines or fewer and 5 parameters or fewer. Each new module holds 5 top-level names or fewer. |
| An inline comment on each line | Pass | Each new executable line gets a comment. |
| A log before and after each action | Pass | Each take, release, read, and decision logs before and after. |
| No secrets in logs | Pass | No log line holds a lock token. The run trail holds stand-in addresses of the `.invalid` domain only. |
| Prove new guard behavior | Pass | Direct tests with no network, and one red run of the two tests (research.md R11). |
| STE for all text | Pass | Each Markdown file scores 80 or more with 0 errors. |

## Design

### The class `HeldSiteLocks`

The fixture `site_lock` yields one object of this class for each test.

| Method | Decision |
| - | - |
| `take(site_id, lock_page)` | Send the take from the page. Fail on each status other than 200, and fail on a 200 that names no token. Record the page, the site, and the token. |
| `release(site_id)` | Release the newest hold of the site now, and forget the hold. Fail when the fixture holds no lock of the site. |
| `release_all()` | Release each remaining hold, newest first. Collect each fault, and fail after the last release with one message that names each fault. |

A release passes only when it answers 200 with a JSON object that holds `released` true.
Each failure names the lock path, the status, and the body.
A release that cannot run names the site and the cause.

### The class `TrailHoldCheck`

| Trail content | Decision |
| - | - |
| No file | Pass. The measure names 0 records. |
| A blank line | Skip the line. |
| A line that is not a JSON object | Fail, and name the line number. |
| A line with no site | Fail, and name the line number. |
| A line with an unknown action | Fail, and name the line number and the action. |
| A line with no action | Read the line as a takeover, as the audit log of the portal does. |
| A take that follows an open hold of the same site | Count one leaked hold. The shipped function `mark_expiries` finds it. |
| An open hold at the end of the trail | Count one leaked hold. |
| Each hold closes with a release | Pass. |

The check reads the known actions from the lock module, and it reads `OPENING_ACTIONS` and `LEGACY_ACTION` from the audit reader.

## Project Structure

### Documentation (this feature)

```text
specs/3508-browser-lock-leaks/
|-- spec.md
|-- research.md
|-- plan.md
|-- tasks.md
`-- checklists/
    `-- requirements.md
```

### Source Code (repository root)

| File | Change |
| - | - |
| `tests/support/upgrade_portal_e2e/lock_holds.py` | New. The class `HeldSiteLocks`. |
| `tests/e2e/upgrade_portal/test_run_controls/conftest.py` | The fixture `site_lock` yields `HeldSiteLocks`, and its teardown calls `release_all`. The old helpers move into the class. |
| `tests/e2e/upgrade_portal/test_run_controls/test_bulk.py` | The three calls change from `site_lock(...)` to `site_lock.take(...)`. |
| `tests/e2e/upgrade_portal/test_run_controls/test_isolation.py` | The call changes to `site_lock.take`. The test calls `site_lock.release` before it clears the cookies. |
| `tests/e2e/upgrade_portal/test_later_site_checks.py` | `PlanSteps.take_the_site` fails on a site that is not free. The new step `PlanSteps.release_the_site` presses the release control. The capture start test calls it. |
| `tests/support/upgrade_portal_e2e/records/audit.py` | New class `TrailHoldCheck`. |
| `tests/e2e/upgrade_portal/conftest.py` | New session fixture `run_trail_hold_guard`. The fixture `capture_portal_server` requests it. The terminal summary prints the measure of both guards. |
| `tests/unit/upgrade_portal/test_e2e_lock_holds.py` | New. The direct tests of `HeldSiteLocks`. |
| `tests/unit/upgrade_portal/test_e2e_trail_hold_check.py` | New. The direct tests of `TrailHoldCheck`. |

The change touches no file under `src/`, so the menu map needs no new pages.

## Test Plan

1. **Red first.** Write the direct tests before the two classes, and record the collection error.
2. **Green.** Run the direct tests.
3. **The red proof.** Wire the strict fixture and the trail check, and keep the two old tests.
   Run `test_run_controls/test_isolation.py` and `test_later_site_checks.py` in Edge.
   The isolation test must report a teardown error that names the lock path and the refusal (SC-002).
   The trail check must fail and name the two sites (SC-001).
4. **Green.** Repair the two tests, and run the same pair again.
   The run must pass, and the summary must name 0 leaked holds.
5. **The wide run.** Run the folder `test_run_controls` and the later site checks together.
6. **The full run.** Run all of `tests/e2e/upgrade_portal` in Edge (SC-003).
7. **The cost.** Time the trail check on the trail of the full run (SC-005).

## Gates

- `python -m py_compile` on each changed Python file.
- `python -m ruff check .` and `python -m black --check .`.
- `python -m mypy` on the paths of the CI job.
- The full test quality gate, and `tests/guardrails`.
- The STE linter on each new Markdown file and on the pull request text.

## Release Note

The change touches the tests only, and no user sees it.
The pull request body states that reason, so the change adds no fragment under `changelog.d/`.

## Overlap

One open pull request changes a file of this set.
Draft #3264 changes `tests/e2e/upgrade_portal/conftest.py`.
That draft waits for a later rebase, and the rebase must keep the new fixture.

## Deploy

None. The change touches no file that the container runs.
