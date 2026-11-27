# Implementation Plan: Windows Bash Guardrail Skips

**Branch**: `fix/4877-windows-bash-guardrails` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/4/0/0/2/4877-windows-bash-guardrails/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add a platform skip mark to each of the 20 shell cases in two guardrail modules. The mark skips only on a Windows host. It names the cause and issue #4877. Linux and macOS runs do not change. The change also documents the expected Windows result and adds one changelog fragment.

## Technical Context

**Language/Version**: Python 3.15 or newer. See `documentation/development-setup.md` section Requirements (line 9).

**Primary Dependencies**: pytest and PyYAML. The browser module imports both at lines 10 and 11.

**Storage**: Not applicable. The change stores no data.

**Testing**: pytest with `addopts = "-v --tb=short"` in `pyproject.toml` line 523.

**Target Platform**: Windows 11 with PowerShell 7 and `.venv` for local runs (constitution line 363). Ubuntu CI on `ubuntu-latest` (`.github/workflows/ci.yml` line 248).

**Project Type**: Test-only change with one documentation section and one changelog fragment.

**Performance Goals**: Not applicable. The change removes shell runs on a Windows host and adds no runtime work.

**Constraints**: Report text uses ASCII only (constitution Principle V, line 182). Lines stay at 120 characters or fewer (`pyproject.toml` line 559). Documentation passes `ste-linter` at 80 or above.

**Scale/Scope**: Two test modules, one documentation section, and one fragment. The two modules hold 31 cases. Of those, 20 are shell cases and 11 are non-shell cases.

## Constitution Check

Gate result: PASS. Each rule shows its result and reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (line 38) | PASS | The route leaf holds one feature folder. The feature root holds five children. `design/` holds five children. `design/contracts/` and `design/checklists/` hold one file each. |
| II. Class-Based Architecture (line 91) | PASS | The change adds no function. It adds one module constant to each test module. |
| III. Safety-First (line 113) | PASS | The change reads no input, handles no secret, and deletes no data. |
| IV. Full Deployment Pipeline (line 143) | PASS with evidence | Steps 1 to 9 run in T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 (lines 166 to 168) need a `container-build.yml` run. That workflow runs only for the paths in its push filter (check RC-28). This change touches none of them, so no build runs. Decision D-9 records this result. |
| V. Observability and Logging (line 182) | PASS | Each reason uses ASCII characters only. The change adds no log call. |
| VI. Inline Comments (line 204) | PASS | Each new executable line carries an inline comment. Decorator lines are exempt (`AGENTS.md` section Inline comments, line 97). |
| VII. Action Logging (line 235) | PASS with interpretation | The change adds marks, one import, and one constant. The function bodies do not change. Decision D-10 records this scope. |
| Technology: file paths (section line 274) | PASS | The change adds no path string. Each module keeps its `Path(__file__)` usage. |
| Technology: test containers (section line 274) | Not applicable | No container starts for this change. |
| Documentation and release notes (line 409) | PASS | Decision D-7 adds one fragment. Decision D-8 adds one documentation section. |
| Complexity escalation (line 420) | PASS | The change touches four or more files, so a spec is required. |
| Multi-agent Git workflow (line 453) | PASS | Issue #4877 exists. The branch starts from `main`. The commit uses Conventional Commits. The scope label is `tests`. No change goes to `main` directly. |

## Architecture

Each test module keeps its structure. Each module defines one constant that holds the skip mark. The mark decorates each shell case. Helper methods, assertions, and workflow reads do not change.

The browser module gets this constant after `MIRRORS` (line 14). Each line stays within 120 characters, and each executable line carries an inline comment:

```python
REQUIRES_POSIX_SHELL = pytest.mark.skipif(  # Define the skip mark for shell cases on Windows
    sys.platform == "win32",  # Detect the Windows host by its platform value
    reason="Needs bash for the Ubuntu mirror script, which Windows cannot run (issue #4877).",  # Cite cause and issue
)
```

The SNMP module adds `import sys` after line 12 and gets the same constant after `START_SCRIPT` (line 20). Its reason text is shorter:

```python
REQUIRES_POSIX_SHELL = pytest.mark.skipif(  # Define the skip mark for shell cases on Windows
    sys.platform == "win32",  # Detect the Windows host by its platform value
    reason="Needs /bin/bash for the start script, which Windows lacks (issue #4877).",  # Cite cause and issue
)
```

Place `@REQUIRES_POSIX_SHELL` directly above each shell case function. When the function also has `@pytest.mark.parametrize`, place the mark above the parametrize decorator. Decorator lines carry no inline comment, because the repository rules exempt them.

## File Change Map

| Path | Action | Change |
| - | - | - |
| `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` | Modify | Add the constant after `MIRRORS` (line 14). Add `@REQUIRES_POSIX_SHELL` above the functions at lines 71, 92, 111, and 156. For the function at line 140, place the mark above the parametrize decorator at line 128. |
| `tests/guardrails/test_snmp_base_oid_defaults.py` | Modify | Add `import sys` after line 12. Add the constant after `START_SCRIPT` (line 20). Add `@REQUIRES_POSIX_SHELL` above the parametrize decorator at line 71 for `test_shell_overrides` (line 85). |
| `documentation/development-setup.md` | Modify | Add the section in the Documentation text below before the line `## Never install this project into its own environment` (line 339). Rebase onto `main` first, because PR #4880 changed this file. |
| `changelog.d/issue-4877-windows-bash-guardrails.md` | Add | One `###` heading and one `- **Fixed**:` bullet that names issue #4877. |
| `specs/numbered/0/0/1/2/4/0/0/2/4877-windows-bash-guardrails/` | Add | The record copied from the draft folder, in the same pull request. |

## Documentation Text

The implementer adds this section to `documentation/development-setup.md`:

```text
## Run the guardrail tests on Windows

Two guardrail modules start bash. A Windows host cannot run them as written, so their shell cases skip with a named reason.

Run the two modules from the repository root:

    .venv\Scripts\python.exe -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py -rs -q

The expected result is `11 passed, 20 skipped`. The short summary lists each skip reason with its count. Each reason names issue #4877.

Caution: A skip does not prove that a shell case passed. The Ubuntu job `pytest_coverage_shards` in `.github/workflows/ci.yml` runs all 31 cases. That job is the authority for these modules.
```

## Dependencies

- No new package. The change uses pytest and PyYAML, which the browser module already imports.
- The Ubuntu CI job gives the authoritative result for the 20 shell cases (checks RC-22 and RC-23).

## Test Plan

The change adds no test function. The 31 existing cases in the two modules are the planned tests, so `tests_planned` is 31. The checks TC-01 to TC-15 in `analysis.md` cover each requirement.

## Labels

Add the scope label `tests`. Keep the type label `bug` and the label `test`. Add `in-progress` before the branch is created, as `AGENTS.md` requires.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| A Windows skip reads as a pass | A local run can hide a shell case defect | The Ubuntu job runs all 31 cases (checks RC-22 and RC-23). T-REMOTE-CI checks for zero skips. The spec carries a Caution. |
| The mark lands on the wrong function | A shell case still fails on Windows | T-LOCAL-GATES checks the counts 11 and 20. |
| The mark lands at module level | The guard-proof audit rejects the module (check RC-52), and non-shell cases skip | FR-005 and check TC-07 search for a module-level mark. |
| A documentation change fails the STE gate | T-LOCAL-GATES fails | Use short active sentences. Run `ste-linter`. |
| The fragment name fails the changelog guard | The changelog guard fails | The name uses the issue form that check RC-42 accepts. |
| A reviewer reads steps 10 to 12 as skipped | A governance dispute | Decision D-9 and check RC-28 record the evidence. |
| A later shell case lacks the mark | A Windows failure returns | Decision D-6 records a follow-up issue. |

## Rollback

1. Open a revert pull request for the squash commit on `main`. Do not force-push `main`.
2. Remove the constants, the marks, the import, the documentation section, and the fragment in the revert.
3. Run T-REMOTE-CI on the revert branch. The 19 Windows failures return, as issue #4877 records.
