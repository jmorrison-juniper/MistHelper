# Implementation Plan: Restart healthy reset test repair

**Branch**: `fix/4531-restart-healthy-reset-delay` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record route `specs/numbered/0/0/1/2/1/1/1/1/`. The route digits are the base-5 digits of 4531, padded to eight places. The rule is in `.specify/scripts/powershell/spec-route.ps1` lines 7 and 17 to 29 on main.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This record has no contracts folder because no interface changes.

## Summary

PR 4555 repaired the restart test on main. This plan completes issue 4531. It keeps the merged repair. It adds compliance logs and comments to one test file. It adds the record, the review path, and the CI evidence.

## Technical Context

**Language/Version**: Python 3.15.2. The project requires Python 3.15 or newer (`pyproject.toml` line 23). CI uses Python 3.15 (`.github/workflows/ci.yml` line 77).

**Primary Dependencies**: pytest 9.2.0 and pytest-timeout 2.4.0 (`requirements-dev.txt` lines 325 and 335). This change adds no dependency.

**Storage**: None. Each test writes only under its `tmp_path` fixture.

**Testing**: pytest. The changed file is `tests/unit/container/output_defaults/test_session.py`.

**Target Platform**: Windows 11 for the local run. Ubuntu for CI. macOS for the issue author.

**Project Type**: Test-only change in a command-line tool repository.

**Performance Goals**: No production goal. Each restart case has a 30-second timeout (`test_session.py` line 233).

**Constraints**: The session script and the shared helper must not change. The DEBUG trap in the controlled clock must keep its matched command text.

**Scale/Scope**: One test file, one record folder, and eight restart cases.

## Constitution Check

Gate result: Pass with one justified violation and recorded scope notes.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Fail, justified | `TestSessionRestarts` holds six members after PR 4555 (remote lines 237, 263, 323, 351, 372, and 382). Complexity Tracking records it with remediation R-1. The module holds five classes. The record root holds five children. |
| II. Class-Based Architecture | Pass | All new behavior stays in test classes. The change adds no wrapper function. |
| III. Safety-First | Pass | The change adds no keyboard read and no destructive operation. Tests use synthetic values and owned paths. |
| IV. Full Deployment Pipeline | Pass with scope note (D-6) | Steps 1 to 9 apply. Steps 10 to 12 do not apply because `.github/workflows/container-build.yml` lists product paths only (remote lines 6 to 19). The image content does not change. |
| V. Observability and Logging | Pass | New log lines use ASCII text and `%s` formatting. No log line prints a token value. |
| VI. Inline Comments | Fail before T005, pass after T005 | Two gaps exist in the bash fixture lines of `CLOCK_SOURCE` (remote lines 238 to 259). After T005, each bash line carries a comment. Three exceptions remain (see analysis.md, item N-3). |
| VII. Action Logging | Fail before T005, pass after T005 | `test_restart_controls_ignore_startup_stall` (remote lines 351 to 370) and `test_clock_exhaustion_refuses_unmeasured_launch` (remote lines 372 to 380) log no action. T005 adds the logs. |
| Technology constraints | Pass | Python 3.15 is used. The change calls no Mist API. Tests use `pathlib` paths. Tests use synthetic credential values only. |
| Development workflow | Pass | Issue 4531 exists. The branch uses the `fix/` prefix. The labels are `bug`, `tests`, and `in-progress`. |
| Security | Pass | The change adds no suppression comment. The existing disclosure checks remain. |
| Multi-agent Git workflow | Pass | One branch starts from main. One pull request holds one issue. T005 runs the overlap check before the first edit. |
| Changelog | Pass | No fragment is added because the change is internal (D-7). |
| Spec Kit escalation | Pass | The root cause is unclear. This record satisfies the escalation rule. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/1/1/1/1/4531-restart-healthy-reset-delay/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
tests/unit/container/output_defaults/
  test_session.py    (modified by T005 only)
  session.py         (unchanged, shared helper)
  contract.py        (unchanged)
  test_contract.py   (unchanged)
  __init__.py        (unchanged)
container/scripts/
  misthelper-session.sh  (unchanged, session script)
```

## Architecture

The restart class runs the real session script in Bash. The shared helper writes a synthetic recorder and a session environment file. `TestSessionRestarts.configure_clock` appends the controlled clock to that file. The controlled clock sets `SECONDS` at two script lines. Line 133 is `RUN_START_SECONDS=$SECONDS`. Line 141 is `RUN_SECONDS=$(( SECONDS - RUN_START_SECONDS ))`. The restart cases then compare the return code, the launch count, and the restart delays with the expected tuple.

## File Change Map

| Action | Path | Purpose |
| - | - | - |
| Modify | `tests/unit/container/output_defaults/test_session.py` | Add logs to two functions and comments to the bash fixture (T005). |
| Add | `specs/numbered/0/0/1/2/1/1/1/1/4531-restart-healthy-reset-delay/` | This record (T-PR). |
| Unchanged | `container/scripts/misthelper-session.sh` | Session script. FR-007 forbids a change. |
| Unchanged | `tests/unit/container/output_defaults/session.py` | Shared helper. FR-007 forbids a change. |
| Unchanged | `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` | No dependency change. |
| Unchanged | `changelog.d/` | No fragment (D-7). |
| Unchanged | `documentation/` | No behavior change, so no document changes. |

## Dependencies

No new dependency. The local gates use tools from `requirements-dev.txt`: pytest, ruff, black, mypy, radon, bandit, symbol-diff, test-quality-analyzer, ste-linter, and pytest-chunks.

## Principle IV Mapping

| Step | Applies | Where |
| - | - | - |
| 1. Local gates | Yes | T-LOCAL-GATES |
| 2. Build the manifest | Yes | T-PR, with the explicit file list |
| 3. Stage the feature | Yes | T-PR, with explicit paths |
| 4. Commit | Yes | T-PR, with Conventional Commits |
| 5. Rebase | Yes | T-PR, before push |
| 6. Push the feature branch | Yes | T-PR |
| 7. Open the pull request | Yes | T-PR |
| 8. Pass CI | Yes | T-REMOTE-CI |
| 9. Squash merge | Yes | T-MERGE, after human approval |
| 10. Wait for the main build | No | `container-build.yml` ignores tests and specs (remote lines 6 to 19). T-MERGE records that no run started. |
| 11. Verify the revision label | No | No image is built. |
| 12. Deploy and check health | No | No product file changes. The running image stays the same. |

## Risks and Mitigations

- Caution: The controlled clock depends on the text of two script lines (133 and 141). A script edit can change that text. The exact tuple and launch-count assertions (remote lines 344 to 346) fail on a mismatch.
- Caution: A comment inside a Python string enters the bash source. T005 adds bash comments only inside the fixture lines. The opening line of `CLOCK_SOURCE` keeps no comment.
- Caution: Logging can add noise to test output. The changes use info and debug levels only. No test asserts a log line.
- Warning: Do not run `git clean`, `git reset --hard`, or `git checkout` on a path in a checkout that another agent uses. Such commands delete uncommitted work.
- Caution: Another open pull request may edit the same test file. T005 runs the overlap check before the first edit.
- Caution: The root cause stays unverified for the original run. D-3 records this. CI results after the merge provide the continuing evidence.

## Revert Steps

1. If CI fails on the pull request head, add a fix commit. Do not force-push a branch that a reviewer has read.
2. If a merged commit breaks main, open a new pull request that reverts the squash commit. Reverting T005 restores the merged test file.
3. Revert the record commit in the same way to remove the record folder.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `TestSessionRestarts` holds six members. The limit is five. | The four restart test functions and the two fixture members form one restart feature. | Moving the fixture to the shared helper changes a file that FR-007 forbids. A new module in `output_defaults` makes that folder hold six children. Splitting the class still needs the same fixture. |

Remediation action R-1: Move `CLOCK_SOURCE` and `configure_clock` into a helper class in the shared helper. Do this in the next change that edits the shared helper for another reason. File this as a separate issue.

## Contracts

No contracts folder. This change adds no CLI, menu, output, or API shape. The record omits `design/contracts/`.
