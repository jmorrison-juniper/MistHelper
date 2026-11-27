# Implementation Plan: Hold mando below 0.8 for the mypy gate

**Branch**: `fix/4893-mando-radon-pin` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record route `specs\numbered\0\0\1\2\4\0\3\3\4893-mando-radon-pin`. The route holds the base-5 digits of 4893, padded to eight digits (research.md, RC-57).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`.

## Summary

Keep `mando` at 0.7.1, the version that `radon` 6.0.1 accepts. Block Dependabot minor and major `mando` updates. Add four guard tests to the existing `tests/guardrails/test_dependency_export.py`. Add one changelog fragment and this record. Change no pinned version.

## Technical Context

- **Language/Version**: Python 3.15 or newer (`pyproject.toml` line 23, research.md RC-16).
- **Primary Dependencies**: pytest, PyYAML 6.0.4 (`requirements.txt` line 209, RC-21), packaging 26.3 (`requirements.txt` line 146, RC-20), radon 6.0.1 (`requirements-dev.txt` line 365, RC-11).
- **Storage**: Not applicable. The change writes no data.
- **Testing**: pytest guard tests in `tests/guardrails/`. CI runs them in the `pytest coverage shards` jobs and in `dependency_lock` (`ci.yml` line 650, RC-05).
- **Target Platform**: GitHub Actions Ubuntu runners (RC-01) and Windows 11 for local work.
- **Project Type**: Repository tooling. The change touches CI configuration and guard tests.
- **Performance Goals**: Not applicable.
- **Constraints**: `tests/guardrails/` holds 79 direct children (RC-34). The change adds no direct child to that folder.
- **Scale/Scope**: Three repository files changed or added, plus this record.

## Constitution Check

Each rule has a result and a reason. Rule names follow `.specify/memory/constitution.md`.

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule (RC-44) | Pass, with debt record | New tests enter an existing child, so no direct child is added. The fragment is one unique record that the constitution allows (RC-45). Debt is recorded in the table below. |
| Principle I, function limits | Pass | Helpers keep five parameters or fewer, five blocks or fewer, and 25 lines or fewer. Task T004 checks each limit. |
| Principle II, class-based architecture | Pass | Helpers live in class `DependencyPinPolicy`. Test methods live in class `TestDependencyPinPolicy`. No wrapper function is added. |
| Principle III, safety-first | Pass | The change adds no keyboard input and no destructive operation. Paths resolve from the repository root with `pathlib`. |
| Principle IV, full deployment pipeline (RC-47) | Pass, with stated condition | Steps 1 to 9 map to tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 depend on `container-build.yml`, which starts only for product file changes (RC-38). This change changes no product file. T-MERGE records the empty run list. |
| Principle V, observability | Pass | New log and test messages use ASCII only. Task T004 checks this. |
| Principle VI, inline comments | Pass | Each new executable line carries an inline comment. Task T006 checks this in review. |
| Principle VII, action logging | Pass | Each file read logs `info` before and `debug` after the read. The existing helper in the same file does this (RC-29). |
| Technology constraints | Pass | Python 3.15 is kept. The `mistapi` pin stays at 0.64.1 (RC-13). `requirements.txt` and `uv.lock` stay unchanged. Paths use `pathlib`. |
| Documentation rule (RC-46) | Pass | The changelog fragment is added. The Dependabot comment records the reason for the ignore entry in one location. |
| Multi-agent Git workflow (RC-41, RC-42) | Pass | The issue is claimed before the branch is made. The branch comes from `main`. One PR closes issue #4893. The Dependabot branch is not changed. |
| Spec Kit escalation | Pass | The change touches three or more files, so this record exists before the code change. |

## Complexity Tracking

| Item | Kind | Reason and action |
| - | - | - |
| `tests/guardrails/` holds 79 direct children (RC-34) | Grandfathered debt | Not added to by this change. Remediation is a separate issue to group guard tests. |
| `changelog.d/` holds 335 direct children (RC-35) | Grandfathered debt | This change adds one unique fragment, which the constitution allows (RC-45). Remediation is a separate issue to group older fragments. |
| New guard tests and helpers | New design | None are new violations. Each stays within the function limits. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/0/3/3/4893-mando-radon-pin/
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

The `contracts/` folder is omitted. No menu, CLI, output, or API contract applies. The Dependabot ignore entry is configuration, and its reason is written in the YAML comment.

### Source Code (repository root)

| Path | Action | Change |
| - | - | - |
| `.github/dependabot.yml` | Modify | Add an `ignore` entry for `mando` with `version-update:semver-minor` and `version-update:semver-major` after line 11 of the pip block (RC-25, RC-26). Add a comment that gives the radon reason. |
| `tests/guardrails/test_dependency_export.py` | Modify | Add helper class `DependencyPinPolicy` and test class `TestDependencyPinPolicy` with four tests. Update the module docstring to name the pin guard (RC-28, RC-29). |
| `changelog.d/issue-4893-mando-radon-pin.md` | Add | Create one `### Fixed` fragment. Rename it to the pull request number form after the PR opens (`.github/copilot-instructions.md` line 451). |
| `specs/numbered/0/0/1/2/4/0/3/3/4893-mando-radon-pin/` | Add | Add this record, copied from the draft folder. |
| `requirements-dev.txt` | No change | Keeps `mando==0.7.1` (line 179, RC-09) and `radon==6.0.1` (line 365, RC-11). |
| `requirements.txt`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml` | No change | The pin set and the CI jobs stay the same. |

### Guard test design

- `DependencyPinPolicy.read_pin` reads the `mando` pin from the requirements text. It fails when the pin is missing.
- `DependencyPinPolicy.radon_requirement` reads the `mando` requirement of the installed `radon` package through `importlib.metadata`.
- `DependencyPinPolicy.holds_minor_updates` reads the pip block of the Dependabot config. It returns true only for an ignore entry that lists minor updates.
- The four tests cover two requirements. The real pin must satisfy the radon requirement (FR-001). A fixture pin of 0.8.2 must fail (FR-001). The real Dependabot config must hold minor updates (FR-002). A fixture config without the entry must fail (FR-002).

### Dependencies

- No package is added, removed, or repinned.
- Test code uses `packaging` and `PyYAML`. Both are pinned in `requirements.txt` (RC-20, RC-21).

## Implementation Outline

1. Confirm the failed check and the pin set (T001, T002, T009).
2. Add the Dependabot ignore entry (T003).
3. Add the guard tests and helpers (T004).
4. Add the changelog fragment (T005).
5. Lint, format, grade, and run the test quality ratchet (T006, T007, T008, T010).
6. Run each applicable local gate (T-LOCAL-GATES).
7. Commit, push, and open the pull request (T-PR).
8. Watch the remote CI (T-REMOTE-CI).
9. Merge, verify the next pip cycle, and close PR #4888 (T-MERGE).

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| R-1 | Dependabot classifies the 0.7.1 to 0.8.x update differently than assumed. The ignore entry then does not block it. | T-MERGE checks the next pip cycle and records the result (research.md, U-1). |
| R-2 | A future radon release accepts `mando` 0.8. The ignore entry then blocks a valid update. | Remove the ignore entry in a new decision record. Do not edit the pin without a new decision. |
| R-3 | Closing PR #4888 removes an open update request. Caution: this removes the open request until a new decision reopens it. | The closing comment names the merged pull request and this record. Each pip update stays enabled except `mando` minor and major releases. |
| R-4 | Another job fails for a different cause after the fix. | T-REMOTE-CI lists each job that still fails. Each cause gets its own issue. |
| R-5 | New test code fails Ruff, Black, or the test quality ratchet. | Tasks T006, T007, and T010 run each gate before the PR opens. |
| R-6 | `importlib.metadata` or `packaging` parses the radon requirement differently than expected. | T004 runs the tests locally. The result is recorded in T-LOCAL-GATES (research.md, U-3). |

## Rollback Steps

1. Revert the squash commit on `main` through a new branch and a new PR. Do not force push.
2. In the same revert, remove the Dependabot ignore entry, the guard tests, and the changelog fragment.
3. Reopen PR #4888 only after a new decision record exists. Caution: reopening PR #4888 restarts the failing `mypy (strict)` gate.
