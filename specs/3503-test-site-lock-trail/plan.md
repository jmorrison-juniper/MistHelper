# Implementation Plan: Each test keeps its site lock actions out of the checkout trail

**Branch**: `fix/3503-test-site-lock-trail` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)
**Input**: The feature specification in `specs/3503-test-site-lock-trail/spec.md`

## Summary

The tests of the upgrade portal write lock actions to the checkout trail, `data/upgrade_takeover_audit.jsonl`.
The operator reads that trail as the record of real lock actions.
This change moves the trail of each test to its own temporary folder.
A session guard counts the checkout trail before the first test and after the last test.
If the two counts differ, the run fails, and the error names the path and the two counts.
If the lock module cannot import, the guard skips and prints the reason.
research.md holds the decisions R1 through R11.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: pytest, and the lock module `src/upgrade_portal/runtime/lock.py`.
**Storage**: The trail is one JSON Lines file. The change adds no store.
**Testing**: pytest. The browser tests use Playwright with Edge.
**Target Platform**: Windows 11 on this computer, and Ubuntu on the CI runners.
**Project Type**: A test support change. The change touches no file under `src/`.
**Performance Goals**: Less than 1 millisecond of setup for each test, and less than 2 seconds for each session (SC-005).
**Constraints**: The browser guard of #3498 stays unchanged (FR-010).
**Scale/Scope**: Three new or changed files, plus this record.

## Constitution Check

| Principle | Result | Note |
| - | - | - |
| Class-based design, no wrappers | Pass | The guard is the class `CheckoutTrailGuard`. The two fixtures call it. |
| The 5-item rule | Pass | Each function holds 25 lines or fewer and 5 parameters or fewer. |
| An inline comment on each line | Pass | Each new executable line gets a comment. |
| A log before and after each action | Pass | The fixtures log the move, the counts, and the decision. |
| No secrets in logs | Pass | The measure holds a path and two counts only. |
| Prove new guard behavior | Pass | Direct tests and one red run (research.md R7) |
| STE for all text | Pass | Each Markdown file scores 80 or more with 0 errors. |

## Project Structure

### Documentation (this feature)

```text
specs/3503-test-site-lock-trail/
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
| `tests/support/site_lock_trail.py` | New. The class `CheckoutTrailGuard` counts a trail, writes the measure, and makes the decision. |
| `tests/conftest.py` | Add the autouse move `isolate_site_lock_trail`, the session guard `checkout_site_lock_trail_guard`, and a hook `pytest_terminal_summary`. Update the module text. |
| `tests/unit/upgrade_portal/test_checkout_trail_guard.py` | New. The direct tests of the move, the count, the measure, and the decision. |

The change touches no file under `src/`, so the menu map needs no new pages.

## Test Plan

1. **Red first.** Write the direct tests before the class and the fixtures, and record the failures.
2. **The baseline.** Record the count of lines that the portal suites write to the worktree trail before the change.
3. **Green.** Run the direct tests, then the portal unit, contract, and integration suites and `tests/test_upgrade_portal_audit.py`.
   The worktree trail must stay absent after the run (SC-001).
4. **The red proof.** Add one temporary test that writes to the checkout trail.
   The run must fail and name the path and the two counts.
   Delete the temporary test, then run again to show a pass.
5. **The wide run.** Run `tests/unit`, `tests/contract`, and `tests/guardrails` in full (SC-003).
6. **The browser run.** Run the audit log journey and a broad set of journeys in Edge.
   The two guard lines must show, and each line must report no change.
7. **The cost.** Read the setup time of the two fixtures with `--durations` (SC-005).

## Gates

- `python -m py_compile` on each changed Python file.
- `python -m ruff check .` and `python -m black --check .`.
- `python -m mypy` on the paths of the CI job.
- The test quality gate on the changed test files.
- The STE linter on each new Markdown file and on the pull request text.

## Release Note

The change touches the tests only, and no user sees it.
The pull request body states that reason, so the change adds no fragment under `changelog.d/`.

## Overlap

No open pull request changes `tests/conftest.py` or `tests/support/`.
Draft #3264 changes the browser test files only.

## Deploy

None. The change touches no file that the container runs.