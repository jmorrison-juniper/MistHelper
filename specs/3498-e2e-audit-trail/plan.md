# Implementation Plan: The browser test portal keeps its lock audit trail inside its own run

**Issue**: #3498 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The new class `AuditTrailIsolation` has two jobs. In the child process, it
moves the site lock trail into the artifact directory of the run. In the
parent process, it counts the lines of the checkout trail before the run and
after the run. It fails the run when the count changes.

The function `build_stand_in_app` calls the placement before `create_app`.
A new session fixture holds the guard, and `capture_portal_server` depends
on it. A `pytest_terminal_summary` hook prints the measure. No file under
`src/` changes.

## Technical context

- Python 3.13, pytest, and Playwright. No new dependency.
- No route change, no schema change, and no change to a JSON body.
- No new cloud read and no new store read. The guard reads one local file.
- The placement is one assignment of a module constant that the lock module
  reads at call time.
- The direct tests run with no browser and no network. They use `tmp_path`,
  and `monkeypatch` restores the constant after each test.
- The browser journey drives the capture start page and the history page of
  the browser test server. It runs in Microsoft Edge on this computer. The CI
  job "E2E smoke tests" runs it in Chromium.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The new class holds five methods. Each method takes three parameters or fewer and holds fewer than 25 lines. |
| II. Class-based design | Pass. One class owns the placement and the guard. The fixture and the hook call it, and neither one wraps it. |
| III. Safety first | Pass. The change stops test writes to the production trail. The guard fails closed on an unreadable trail. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, and a hand merge. No deploy, because the portal code does not change. |
| V. Observability | Pass. The guard prints the path and the two counts in each run, and it writes a JSON record. |
| VI. Inline comments | Pass. Each new line carries a comment. |
| VII. Action logging | Pass. The placement and each count log before and after the action. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `tests/support/upgrade_portal_e2e/records/audit.py` | The new class `AuditTrailIsolation`. |
| `tests/e2e/upgrade_portal/conftest.py` | The placement in `build_stand_in_app`. The new session fixture `checkout_audit_trail_guard`. The dependency of `capture_portal_server`. The hook `pytest_terminal_summary`. |
| `tests/unit/upgrade_portal/test_e2e_audit_trail_isolation.py` | New. The direct tests of the placement and the guard decision. |
| `tests/e2e/upgrade_portal/test_audit_log_journey.py` | New. The browser journey of the take, the release, and the Audit log card. |

## Test plan

1. Write the direct tests first. Run them before the class exists, and
   record the red result.
2. Write the class and the guard fixture. Keep the placement out. Run the
   journey and one existing lock test. Record the red result of the guard.
3. Add the placement. Run the direct tests, the journey, and the lock test
   green. Read each screenshot.
4. Run every test under `tests/e2e/upgrade_portal/`. Explain or fix each
   changed result. Run `tests/unit/upgrade_portal`,
   `tests/contract/upgrade_portal`, and `tests/guardrails`.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), and the test
quality gate of the new test files. Also run the STE lint of each new
Markdown file.

## Release note

The change touches test files and specification files only. An operator sees
no change, so the change adds no fragment under `changelog.d/`. The pull
request body states this reason.

## Overlap

The draft pull request #3264 also changes `tests/e2e/upgrade_portal/conftest.py`.
This change takes the file first. Pull request #3264 rebases after this merge.

## Deploy

No deploy. The portal on port 8056 runs no test file.

## Cleanup

The red run writes lines to the trail of this worktree. Delete that file
after the red run, because no production process reads it.