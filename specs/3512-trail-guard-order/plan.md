# Implementation Plan: The browser trail guard reads the checkout trail from the root guard

**Issue**: #3512
**Branch**: `fix/3512-trail-guard-order`
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)

## Summary

The browser guard of #3498 must read the checkout trail from the root guard of #3503.
Remove the default path of `AuditTrailIsolation`, so each caller names the source of the path.
Add the builder `AuditTrailIsolation.for_session`, which reads the path from the root guard.
The fixture `checkout_audit_trail_guard` names the root guard as a parameter and calls the builder.
The child process names the path of the lock module explicitly.

## Technical Context

- **Language**: Python 3.13
- **Test tools**: pytest, pytest-playwright, and Microsoft Edge through `--browser-channel msedge`
- **Scope**: Test code only. No portal code changes, so the change needs no deploy and no release note.
- **Performance goal**: The direct tests finish in less than 5 seconds. The browser runs keep the time of #3507.

## Constitution Check

| Rule | Result |
| - | - |
| Class-based design, no wrappers | Pass. The builder is a class method of `AuditTrailIsolation`. |
| No legacy compatibility shims | Pass. The change removes the default. No caller keeps the old form. |
| Five-Item Rule | Pass. The builder takes 2 parameters and holds fewer than 25 lines. |
| Inline comments and action logging | Pass. Each new line carries a comment. The builder logs before and after. |
| Safe > Fast | Pass. A missing root guard fails the build, and never falls back to a read of the lock module. |
| STE | Pass. Each Markdown file must score 80 or more with 0 errors. |

## Project Structure

```text
tests/
  conftest.py                                CHANGED: the docstring of the root guard names issue #3512
tests/support/upgrade_portal_e2e/records/
  audit.py                                   CHANGED: required checkout_trail, the builder for_session
tests/e2e/upgrade_portal/
  conftest.py                                CHANGED: the fixture names the root guard, the child names its path
tests/unit/upgrade_portal/
  test_e2e_audit_trail_isolation.py          CHANGED: three direct tests of issue #3512
```

## Design

### The class `AuditTrailIsolation`

| Member | Change |
| - | - |
| `__init__(artifact_directory, checkout_trail)` | `checkout_trail` becomes required. The docstring names the source of the path for each caller. |
| `for_session(artifact_directory, root_guard)` | New class method. It raises `RuntimeError` when `root_guard` is None. Otherwise it builds the isolation with `root_guard.checkout_trail`. |
| `NO_ROOT_GUARD` | New class constant. The message of the `RuntimeError` names the root fixture and the lock module. |

The other members keep their code, so the guard line, the record file, and the decision rule do not change (FR-007).

### The fixture `checkout_audit_trail_guard`

The fixture adds the parameter `checkout_site_lock_trail_guard`.
The first line of the body calls `AuditTrailIsolation.for_session(ARTIFACT_DIRECTORY, checkout_site_lock_trail_guard)`.
The docstring states why the fixture reads the root guard.

### The child process

`build_stand_in_app` imports the lock module late, and it calls `AuditTrailIsolation(ARTIFACT_DIRECTORY, lock.audit_trail_path())`.
A comment states that the child runs no pytest fixture, so no move applies before `place`.

## Test Strategy

| Step | Command | Expected result |
| - | - | - |
| Red, direct | `pytest tests/unit/upgrade_portal/test_e2e_audit_trail_isolation.py` | The three new tests fail. The ten old tests pass. |
| Red, browser | `pytest tests/e2e/upgrade_portal/test_run_controls/test_existing.py` in Edge | The guard line of #3498 names a path in the temporary folder. |
| Green, direct | The same direct command | Each test passes. |
| Green, browser | `test_existing.py` alone, the pair `test_capture.py` and `test_existing.py`, and `test_audit_log_journey.py` | SC-001, SC-002, and SC-005. |
| Green, full | The whole folder `tests/e2e/upgrade_portal` in Edge | SC-003. |
| Gates | py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter | Each gate passes. |

## Risks

| Risk | Mitigation |
| - | - |
| Another caller builds the isolation with one argument. | A search of the repository finds three callers. The change updates each caller. A missing argument raises `TypeError` at once. |
| The root guard and the browser guard now count one file. | Both guards read the file only. Two reads of one file do not change the file. |
| A run with the lock module absent reaches the builder. | The browser conftest imports the lock module when pytest loads it. The builder still raises a clear error. |
