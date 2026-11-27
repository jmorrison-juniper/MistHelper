# Implementation Plan: Ops Platform Deepdiff Pin

**Branch**: `fix/4907-ops-platform-deepdiff-pin` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/1/2/4907-ops-platform-deepdiff-pin/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Keep deepdiff on 8.6.2. Make the dependency guard reject each ops platform pin that breaks its declared constraint. The guard already runs in the job `Dependency lock and exports` on each pull request. The change adds one test method and one changelog fragment. It edits no dependency, no workflow, and no Dependabot setting. PR #4889 closes unmerged after this change merges.

## Technical Context

**Language/Version**: Python 3.15. `mist-ops-platform/pyproject.toml` line 13 requires `>=3.15`.

**Primary Dependencies**: The standard `tomllib` module and `packaging` 26.3 (`requirements-dev.txt` line 228). No new dependency.

**Storage**: Not applicable. The guard reads two committed files and writes no output file.

**Testing**: pytest 9.2.0 (`requirements-dev.txt` line 325). The dependency job runs the guard with `-s` (`.github/workflows/ci.yml` line 650).

**Target Platform**: GitHub Actions runner `ubuntu-latest` (`.github/workflows/ci.yml` line 636).

**Project Type**: A guard inside an existing test module.

**Performance Goals**: The guard reads two files. `mist-ops-platform/pyproject.toml` has 145 lines and `mist-ops-platform/requirements.txt` has 235 lines.

**Constraints**: The guard uses committed files only. It makes no network call and runs no shell command. The Five-Item Rule limits apply to the test module.

**Scale/Scope**: 22 direct dependencies in `mist-ops-platform/pyproject.toml` lines 18 to 39. Each dependency has one pin in `mist-ops-platform/requirements.txt`.

## Constitution Check

*Gate: one rule fails with a recorded cause (Principle IV, U-6). All other rules pass. Re-checked after design.*

| Rule (constitution line) | Result | Reason |
|--------------------------|--------|--------|
| I. Five-Item Rule (line 38) | Pass | No file is added under `tests/guardrails`, which holds 79 grandfathered children. `TestDependencyExport` moves from four methods to five, the limit. The module keeps five top-level names. The changelog fragment is a required process record (line 46). |
| II. Class-Based Architecture (line 91) | Pass | The check is one method of `TestDependencyExport`. It adds no standalone function and no wrapper. |
| III. Safety-First (line 113) | Pass | The guard reads two fixed repository paths and accepts no user input. It prints no secret. |
| IV. Full Deployment Pipeline (lines 143 and 145) | Fail, documented (U-6) | Steps 1 to 9 are planned in the tasks. Steps 10 to 12 need a `container-build.yml` run. Its push paths (lines 6 to 19) match no changed file, so no run starts. Decision D-5 records this result. |
| V. Observability and Logging (line 182) | Pass | Each log message uses ASCII and the module logger with `%s` values. No log line holds a secret. |
| VI. Inline Comments (line 204) | Pass | Each executable line of the new method and each new import carries an inline comment. T-LOCAL-GATES checks this by review. |
| VII. Action Logging (line 235) | Pass | The method logs `info` before each read and each comparison, and `debug` after each one. |
| Technology: Python 3.15 | Pass | `requires-python` is `>=3.15` (`pyproject.toml` line 13). `tomllib` exists in the standard library from Python 3.11. |
| Technology: mistapi | Not applicable | The change makes no REST call and changes no mistapi pin. |
| Technology: UV and requirements.txt | Pass | Neither requirements file changes. The dependency job runs `uv lock --check` (`ci.yml` lines 647 to 648). |
| Technology: file paths | Pass | The method builds each path with `pathlib` from `REPOSITORY_ROOT`. |
| Technology: Podman and containers | Not applicable | The dependency job runs on `ubuntu-latest` with no container. |
| Technology: data directory | Not applicable | The change writes no product output. |
| Documentation: release notes (line 409) | Pass | One fragment is added. `CHANGELOG.md` stays unchanged. |
| Documentation: README | Not applicable | The change alters no user-facing behavior. |
| Compliance review (line 548) | Pass | The PR body answers each checkbox of `.github/PULL_REQUEST_TEMPLATE.md` (lines 1 to 39), and marks each unused checkbox with its reason. |
| Governance (line 529) | Applied | The constitution supersedes practice documents, so it decides the fragment question (D-4). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/1/2/4907-ops-platform-deepdiff-pin/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      pin-guard-output.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
tests/guardrails/test_dependency_export.py              modify: one method, imports, module docstring
changelog.d/issue-4907-ops-platform-deepdiff-pin.md     add: one fragment
```

One contract applies, because the guard prints a summary line and fails with fixed messages. See `design/contracts/pin-guard-output.md`.

## File-by-File Change Map

| Path | Action | Change |
|------|--------|--------|
| `tests/guardrails/test_dependency_export.py` | Modify | Extend the module docstring at line 1. Add imports for `re`, `tomllib`, `Requirement`, `canonicalize_name`, and `Version`. Add the method `test_ops_platform_pins_obey_declared_constraints` to class `TestDependencyExport`, which starts at line 98. |
| `changelog.d/issue-4907-ops-platform-deepdiff-pin.md` | Add | One `###` heading and one `Fixed` bullet that ends with `Issue #4907.` |
| `specs/numbered/0/0/1/2/4/1/1/2/4907-ops-platform-deepdiff-pin/` | Add | This record. T-PR copies it from DRAFT_DIR. |

Unchanged by design (FR-005): `mist-ops-platform/pyproject.toml`, `mist-ops-platform/requirements.txt`, `requirements.txt`, `requirements-dev.txt`, `.github/dependabot.yml`, `.github/workflows/ci.yml`, and `CHANGELOG.md`.

## Design

The new method runs in four steps.

1. It reads the declared constraints from `mist-ops-platform/pyproject.toml`. It parses the list `project.dependencies` with `tomllib`, and it builds one `Requirement` for each entry.
2. It reads the pins from `mist-ops-platform/requirements.txt`. It keeps each line that matches `name==version`, and it keys each pin by its canonical name.
3. It counts each pin that has a declared constraint. It lists each pin that falls outside that constraint.
4. It repeats step 3 on a copy of the requirements text. In the copy, the deepdiff pin becomes `9.2.1`. The method then requires exactly one defect, `deepdiff`.

The method reuses `DependencyExport.read_export` to read both files, so a missing or empty file fails with the existing message. It adds no helper. `DependencyExport` keeps its five methods.

**Method limits**: `TestDependencyExport` moves from four methods to five, which is the limit. The module keeps five top-level names. The new method keeps 25 lines or fewer and five logical blocks or fewer.

## Dependencies

No new package. `packaging` is pinned in the root `requirements-dev.txt` (line 228) and in the root `requirements.txt` (line 146). The job installs `requirements-dev.txt` (`ci.yml` line 646).

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| R-1: Dependabot reopens a deepdiff 9.x pull request. | The dependency job fails that pull request, and the owner closes it. Research U-3 records the open question. |
| R-2: A pin format that the regular expression misses hides a defect. | FR-003 fails the guard when it examines zero pins. The printed count shows the scope. |
| R-3: The negative case goes stale when the main pin changes. | The method asserts that the replacement changed the text before it compares the copy. |
| R-4: Closing PR #4889 hides its failing check. | The closing comment names the reason and the branch. Reopening the pull request restores the check. Caution: keep branch `dependabot/pip/deepdiff-9.2.1` on origin. |
| R-5: The cachebox note at `pyproject.toml` line 31 is stale. | This change keeps the constraint. Research U-1 records the question for a later change. |
| R-6: Constitution steps 10 to 12 do not run. | D-5 records the result at T-MERGE. Research U-6 asks the owner to confirm the result. |

## Rollback Steps

1. Revert the squash commit with a new branch and a new pull request.
2. Remove the changelog fragment in the same revert.
3. Reopen PR #4889 only if the owner chooses the 9.x line. Its branch keeps commit `9d4640661fa40b1e0a7809f46a0007eff7add517`.

Warning: a force-push to `main` removes the commits of other agents. Use a revert commit instead.

## Separate Remediation Action

The directory `tests/guardrails` holds 79 direct children. That count breaks the Five-Item Rule (constitution line 38). This change leaves that grandfathered debt unchanged and adds no child to the directory. Track a separate incremental issue that moves guard tests into compliant packages.
