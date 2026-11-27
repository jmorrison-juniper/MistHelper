# Implementation Plan: Ops platform dateutil pin (issue #4908)

**Branch**: `fix/4908-ops-platform-dateutil-pin` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric record route `specs\numbered\0\0\1\2\4\1\1\3\4908-ops-platform-dateutil-pin`, from the base-5 rule in `.specify\scripts\powershell\spec-route.ps1` (RC-38).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place supporting files under `design\`.

## Summary

Keep the ops pin at python-dateutil 2.9.0.post0. That version is the only one the celery pin accepts. Add a Dependabot rule that ignores python-dateutil major updates. Add nine guard cases to the existing parity guard. Document the pin. Add one changelog fragment. The change alters no runtime code.

## Technical Context

- **Language/Version**: Python 3.15 for the guard module. The CI default is 3.15 (RC-04).
- **Primary Dependencies**: pytest, PyYAML 6.0.4 (RC-28), and packaging. The guard module already imports packaging (RC-29). No dependency is added.
- **Storage**: Not applicable. The change stores no data.
- **Testing**: pytest. The local command is `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`.
- **Target Platform**: GitHub Actions `ubuntu-latest` for the CI check (RC-01). Windows 11 for local runs.
- **Project Type**: CI configuration and one guard module.
- **Performance Goals**: Not applicable. The guard reads two small files.
- **Constraints**: No new direct child under `tests/guardrails/` (RC-31). The requirements files keep every pin except the ops pin, which stays unchanged.
- **Scale/Scope**: Three modified files, one new changelog fragment, and this record.

## Constitution Check

*Checked against `.specify/memory/constitution.md` version 1.9.0 (RC-39, RC-40).*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The change adds no direct child under `tests/guardrails/`, which already holds 79 tracked children (RC-31). The guard edits an existing module. The changelog fragment is the unique record that a process folder allows. The record uses the numbered route. |
| II. Class-Based Architecture | Pass | The guard logic sits in one class, `OpsPlatformPins`, with static methods. No wrapper function delegates to a method. |
| III. Safety | Pass | The change handles no keyboard input and no destructive operation. It stores no secret. |
| IV. Full Deployment Pipeline | Pass with exception | Steps 1 to 9 run through T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 do not run, because `container-build.yml` runs only for a product file change (RC-34). Decision D-7 records the exception. |
| V. Observability and Logging | Pass | The guard writes ASCII log text only. The guard prints the number of files and cases that it examined. |
| VI. Inline Comments | Pass | Each added Python line has an inline comment. Each added YAML line has a comment on its own line above it. |
| VII. Action Logging | Pass | The guard logs an `info` line before each file read and a `debug` line after it, as the existing module does. |
| Technology: Python 3.15 | Pass | The guard targets Python 3.15 only. |
| Technology: pip compatibility | Pass | `requirements.txt` keeps pip compatibility. The change leaves each requirements file unchanged (RC-16, RC-26, RC-27). |
| Technology: file paths | Pass | The guard builds paths with `pathlib.Path` (RC-29, line 20). |
| Release notes | Pass | One fragment, `changelog.d/issue-4908-ops-platform-dateutil-pin.md`, is added (RC-40, RC-42). |
| Specifications | Pass | Three or more files change, so a specification is required. This record is that specification (Sources S-1). |
| Multi-agent workflow | Pass | The branch name is `fix/4908-ops-platform-dateutil-pin`, which follows the fix type, issue number, and slug rule. The labels are `bug` and `ci` (existing), and `in-progress` (added). |

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\4\1\1\3\4908-ops-platform-dateutil-pin\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      ci-dependency-contract.md
    checklists\
      requirements.md
      ci-gate.md
```

### Source Code (repository root)

| Path | Action | Change |
| - | - | - |
| `.github/dependabot.yml` | Modify | Add an `ignore` block under the pip entry, after line 11 (RC-23). The rule names `python-dateutil` and the type `version-update:semver-major`. |
| `tests/guardrails/test_dependency_declaration_parity.py` | Modify | Add `import yaml`, two path constants, one pin constant, class `OpsPlatformPins`, and four test functions with nine cases. Extend the module docstring to name the ops pin and the Dependabot rule. |
| `documentation/quality-gates.md` | Modify | Add the section `Ops platform dependency pins` before the heading `## Exclusion drift report`. That heading follows the gate issue rule (RC-37). |
| `changelog.d/issue-4908-ops-platform-dateutil-pin.md` | Add | One `###` heading and one `**Fixed**` bullet that names issue #4908. |
| `mist-ops-platform/requirements.txt` | No change | Line 157 keeps `python-dateutil==2.9.0.post0` (RC-16). |
| `requirements.txt`, `requirements-dev.txt` | No change | Lines 201 and 341 keep `python-dateutil==4.0.0` (RC-26, RC-27). |
| `specs\numbered\0\0\1\2\4\1\1\3\4908-ops-platform-dateutil-pin\` | Add | The record folder, copied from this draft folder during T-PR. |

## Architecture

The flow for this failure starts at the pull request. The pull request triggers the Quality Gates workflow (`.github/workflows/ci.yml`). The job `ops_platform_pytest` runs in `mist-ops-platform`. Its step `Install dependencies` runs pip against `requirements.txt`. Pip fails when the ops pin and the celery pin differ.

The fix places three controls on that flow:

1. The ops pin keeps the value that the celery pin accepts.
2. The Dependabot rule blocks the major update that would change the ops pin.
3. The guard fails in the root test run when either control changes.

The guard reads two files and runs no pip command. It does not depend on the ops install step.

## Dependencies

- No package is added or changed.
- The guard reads `.github/dependabot.yml` with PyYAML. The root environment provides PyYAML through the pin in `requirements-dev.txt` (RC-28).
- The ops pin keeps its current version. The celery pin does not change.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
| - | - | - | - |
| The Dependabot rule does not cover the ops requirements file (U-1). | Medium | Dependabot opens another 4.x pull request. | T-MERGE checks the next pip run (SC-004). The guard keeps the rule in place. |
| PR #4890 stays red after the fix merges. | High | The PR stays in the review queue. | D-4 assigns the closing action to a maintainer. The fix PR closes issue #4908 on merge. |
| A celery release relaxes its pin later. | Low | The pin test fails by design. | The maintainer removes the Dependabot rule and updates the pin constant in one pull request. |
| The Dependabot rule covers root major updates. | High | Root 5.x updates pause. | The root stays at 4.0.0 (RC-26). Root 4.x updates still flow. Caution: revisit the rule when root needs a 5.x update. |
| A python-dateutil 2.x minor release appears later. | Low | The semver-major rule does not cover it. | No such release exists (RC-54). The maintainer adds a minor rule when a release appears. |
| The guard passes with a wrong file path. | Low | A drift goes unseen. | The guard reads each file by path and fails when the file is missing or empty. |

## Revert Steps

1. Open a new pull request that reverts the squash commit of the fix pull request. Do not push to `main` directly.
2. Read `.github/dependabot.yml` on `main` after the revert. Confirm that the `ignore` block for python-dateutil is absent.
3. Read `mist-ops-platform/requirements.txt` on `main` after the revert. Confirm that line 157 keeps `python-dateutil==2.9.0.post0`.

Caution: a revert removes the Dependabot rule. Dependabot can then propose the 4.x pin again, and the ops install fails on that pull request.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `tests/guardrails/` already holds 79 tracked children (RC-31). | The guard belongs with the other dependency guards. | A new guard file adds a direct child to a noncompliant parent, which Principle I forbids. |
| `changelog.d/` is a process folder with many children. | Principle IV requires one fragment for each change. | None. Principle I allows one unique record under a process folder. |
| Route parents under `specs\numbered\` hold child counts that stay at five or fewer after this record (local listing, U-5). | The numbered route is mandatory for new records (RC-38). | None. The route is fixed. |
