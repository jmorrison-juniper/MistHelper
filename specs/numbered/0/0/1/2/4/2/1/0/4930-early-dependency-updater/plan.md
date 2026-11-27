# Implementation Plan: Early dependency check without half-removed packages

**Branch**: `fix/4930-early-dependency-updater` | **Date**: 2026-11-26 | **Spec**: [spec.md](../spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/4/2/1/0/4930-early-dependency-updater/spec.md`. The route is the base-5 form of issue 4930, as `design/research.md` R-08 shows.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The early check imports each requirement to probe it. On Windows, the imported extension modules stay locked. The same process then uninstalls and reinstalls outdated packages, and the uninstall stops in the middle. This change reads package state from metadata, skips loaded packages, refuses a drift above five packages, and restores RECORD files after a failed upgrade. The name and the startup caller of the entry point do not change.

## Technical Context

**Language/Version**: Python 3.15 or newer (`pyproject.toml`, R-32).

**Primary Dependencies**: Standard library `importlib.metadata`, `sys`, `shutil`, and `tempfile`. Existing `packaging`, uv, and pip. No new package.

**Storage**: None. The snapshot is a temporary copy. The check removes it after a successful upgrade.

**Testing**: pytest with fakes, plus one integration test that uses a real temporary folder. Local gates come from the Local gates table in `.github/copilot-instructions.md` (R-45).

**Target Platform**: Windows 11 (primary), macOS, and Linux.

**Project Type**: Single command-line project with packages under `src/`.

**Performance Goals**: No new network request. The snapshot copies only the RECORD files of the packages that the check upgrades.

**Constraints**: No import of a requirement module during the probe. ASCII-only log text. At most five parameters for each function. An inline comment on each changed line.

**Scale/Scope**: The pins in `requirements.txt`, checked on each start.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution version is 1.9.0 (R-09). Each rule has a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass with recorded debt | The change adds two classes and no directory child. `dependency_check.py` and `package_installer.py` already exceed five top-level names. See Complexity Tracking. |
| II. Class-Based Architecture | Pass | The new behavior lives in `DistributionInventory` and `DistributionSnapshot`. The change adds no wrapper function. |
| III. Safety-First | Pass | The change reads no secret. Log text omits tokens. The change calls no Mist endpoint, so no typed confirmation applies. |
| IV. Full Deployment Pipeline | Pass (planned) | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 12. Steps 10 to 12 run after the merge, in T-MERGE. |
| V. Observability and Logging | Pass (planned) | `design/contracts/startup-messages.md` gives ASCII text. Each log call uses a `%s` template. |
| VI. Inline Comments | Pass (planned) | Each changed line, and each adjacent uncommented line in a touched block, gets an inline comment. |
| VII. Action Logging | Pass (planned) | Each in-process change, skip, and refusal has an info record before it and a debug record after it. |
| Technology: Python | Pass | `pyproject.toml` requires 3.15 or newer (R-32). |
| Technology: mistapi | Not applicable | The change calls no Mist REST endpoint and changes no SDK pin. |
| Technology: UV and requirements.txt | Pass | `requirements.txt`, `pyproject.toml`, and `uv.lock` stay unchanged (FR-009). |
| Technology: Podman and test containers | Not applicable | No test container starts. Both container files keep `DISABLE_AUTO_INSTALL=true` (R-42, R-43). |
| Technology: File paths | Pass | The new code joins paths with `os.path.join` or `pathlib`. |
| Technology: Output backends and data directory | Not applicable | The change exports no data. The snapshot is temporary, so no product output enters `data/`. |
| Technology: Database keys and operational store | Not applicable | The change writes no database record. |
| Development: Testing and syntax | Pass (planned) | T-LOCAL-GATES runs `python -m py_compile MistHelper.py` before the commit. |
| Development: Fix over suppress | Pass | The change adds no `# noqa`, `# type: ignore`, or `#nosec` annotation. |
| Development: Documentation | Pass (planned) | README.md and the operator guide change (FR-010). |
| Development: Release notes | Pass (planned) | One changelog fragment (FR-009). |
| SpecKit escalation | Pass | This record exists because the change touches more than three files and two classes. |
| Multi-agent git | Pass (planned) | Issue #4930 is open. The branch is `fix/4930-early-dependency-updater`. The issue has the labels `bug` and `MistHelper.py`, and the change adds `in-progress` (R-01). No open pull request touches the target files (R-02). |
| Governance | Pass | No amendment is needed. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/1/0/4930-early-dependency-updater/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      startup-messages.md
    checklists/
      requirements.md
```

The route parent `specs/numbered/0/0/1/2/4/2/1` holds one child before this record (R-05). The route parent `specs/numbered/0/0/1/2` holds five children (R-04). This record adds no child at either level, because `4` and `2` already exist.

### Source Code (repository root)

| Path | Action | Purpose | Requirements |
| - | - | - | - |
| `src/foundation/runtime/bootstrap/dependency_check.py` | Modify | Replace the import probe with metadata reads. Remove the import map field. Add the loaded-package skip, the drift threshold, the snapshot wrap, and the log records. | FR-001 to FR-008 |
| `src/foundation/runtime/bootstrap/package_installer.py` | Modify | Add `DistributionInventory` for the incomplete-RECORD check and the loaded check. Add `DistributionSnapshot` for capture, restore, and discard. | FR-001 to FR-004 |
| `MistHelper.py` | Modify, one call site | In `early_dependency_check()`, pass an `inventory` argument that holds a `DistributionInventory` instance, and remove the `package_import_map` argument. Lines 1051 to 1062. | FR-011 |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py` | Modify | Replace `TestIsImportable` and the import map tests. Add the loaded, drift, broken, and log tests. | FR-001 to FR-007 |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_package_installer_wave9.py` | Modify | Add the snapshot and inventory unit tests, and the integration test. | FR-002 to FR-004 |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Modify | Add the lock reference agreement test, TC-13. | FR-009 |
| `tests/bootstrap/test_dependency_check_venv_guard.py` | Modify | Patch the new presence method instead of `_is_importable`. | FR-008 |
| `tests/unit/config/standalone/foundation/runtime/startup/test_dependency_check.py` | Modify | Remove the `package_import_map` argument. | FR-008 |
| `README.md` | Modify | Add a short startup dependency check section before `## Documentation` (R-41). | FR-010 |
| `documentation/operator-guide.md` | Modify | Add the repair steps and the `DISABLE_AUTO_INSTALL` workaround. | FR-010 |
| `changelog.d/issue-4930-early-dependency-updater.md` | Add | One `### Fixed` heading and one bullet that names issue 4930. After the pull request opens, rename it to the pull request form that `changelog.d/README.md` names (R-46). | FR-009 |

Unchanged files: `requirements.txt`, `pyproject.toml`, `uv.lock`, `Containerfile`, `Dockerfile`, `container/scripts/misthelper-session.sh`, `documentation/development-setup.md`, and `src/foundation/support/refactors/package_import_map.py`.

### Implementation Outline

1. Read the requirements with the existing parser. The parser does not change.
2. For each requirement, read the installed version from metadata. A missing version means missing. An incomplete RECORD means broken. A version that fails the pin means off pin.
3. Count the drift. If the count is above five, log the refusal with the repair command, and return.
4. For each missing package that is not loaded and not broken, install it with uv, then with pip. Log before and after each attempt.
5. For each off-pin or latest-only package that is not loaded and not broken, take a snapshot. Upgrade the package. Restore the snapshot on failure, or discard it on success. Log before and after each attempt.
6. For each loaded or broken package, log the skip with the repair command.

The PyPI lookup and the version rules stay unchanged. The uv command and the pip fallback stay unchanged.

## Complexity Tracking

Existing debt. The change adds no new debt beyond the two classes.

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `dependency_check.py` holds 27 constants and two classes, and the orchestrator holds 22 methods (R-19, blob 514d1fb2). The change removes `_is_importable` and adds at most three methods, so the count reaches at most 25. | The change touches `run()` and the classification path in the same class. | Splitting the class here widens the diff and the review scope. A separate issue owns the split. |
| `package_installer.py` holds 16 constants and one class (R-21, blob aff48cba). | The change adds the two new classes that the snapshot and inventory need. | A new module in `src/foundation/runtime/bootstrap/` would add a sixth child to a folder that already holds five (R-06). |
| `changelog.d/` holds 335 children (R-07). | The release-note rule requires one unique fragment for each change. | The change adds one unique record only. |

Remediation action: open a separate issue after this change merges. That issue splits `DependencyCheckOrchestrator` and reduces the constant count. This change does not include that work.

## Dependencies

No new package. `importlib.metadata.packages_distributions()` exists in Python 3.10 and later. The Python documentation section "Mapping import to distribution packages" describes it (see `design/research.md`, Sources).

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
| - | - | - | - |
| `packages_distributions()` misses a package in some editable installs. | Medium | A loaded package could change. | A package with no top-level name counts as loaded, so the check does not change it. |
| The snapshot copies a large package, such as numpy. | Medium | Disk use and time. | The snapshot copies only the RECORD files of the packages that the check upgrades. The check removes the snapshot after success. |
| A restore fails because another process holds a file. | Low | The package stays partly changed. | The check logs the snapshot path and the repair command, and it keeps the snapshot. |
| A threshold of five hides real drift. | Low | Some packages stay off their pin. | Each refusal logs the repair command. The operator runs it. |
| A fresh environment with more than five missing packages now stops. | Medium | The first start asks for the repair command. | The bootstrap already runs `uv sync --locked --extra dev` (R-35). The message names that command. |
| `MistHelper.py` is a hot file. | Low | A merge conflict. | No open pull request touches it (R-02). The change edits one call site. |
| The Windows lock behavior is not in CI. | High | A Windows regression passes CI. | The manual check in `design/quickstart.md` gives the evidence for SC-004. CI runs on `ubuntu-latest` (R-44). |
| The interpreter gate from feature 1020 changes. | Low | A system-Python install runs. | FR-008 keeps the gate. The venv guard tests run in T-LOCAL-GATES. |
| Two processes start at the same time. | Low | Two processes change one environment. | The spec excludes this case (Assumptions). |

Rollback steps:

1. Revert the squash commit on `main` with a new pull request.
2. Set `DISABLE_AUTO_INSTALL=true` for each operator environment, as the issue workaround states.
3. Run `uv sync --locked --extra dev` after each process that uses the environment closes.
4. Delete the folders named `misthelper-pkg-snapshot-*` in the system temporary folder after each restore is verified.
