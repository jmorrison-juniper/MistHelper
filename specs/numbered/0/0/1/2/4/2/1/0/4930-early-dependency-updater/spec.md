# Feature Specification: Early dependency check without half-removed packages

**Feature Branch**: `fix/4930-early-dependency-updater`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4930, "Runtime: the early dependency updater leaves half-removed packages on Windows"

The issue title calls the feature the early dependency updater. This record calls it the early check.

## Clarifications

### Session 2026-11-26

No live user answered these questions. The author records each answer as a decision in `design/research.md`.

- Q: Must the early check import a requirement module to read its state? A: No. It reads package metadata and RECORD files. (D-1)
- Q: May the early check change a loaded package? A: No. It skips the package and logs the repair command. (D-2)
- Q: How many drifted packages may one run change? A: Five. A run with more than five drifted packages changes nothing. (D-3)
- Q: How does a failed upgrade recover? A: The check restores RECORD files from a snapshot taken before the upgrade. (D-4)
- Q: Which list defines the lock? A: The pins in `requirements.txt`. A test compares them with `uv.lock`. (D-5)

## Terms

- **Early check**: The dependency check that starts with MistHelper. It runs through `early_dependency_check` in `MistHelper.py`.
- **Package**: An installed Python package that `requirements.txt` lists.
- **Drift**: A package that is missing, broken, or off its pin.
- **Broken package**: A package with an incomplete RECORD. The RECORD file is missing, or a file that it lists is missing.
- **Loaded package**: A package with a top-level module in `sys.modules`.
- **In-process change**: An install or upgrade that the early check runs in the current process.
- **Repair command**: `uv sync --locked --extra dev`. The operator runs it after closing each process that uses the environment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep a loaded package intact (Priority: P1)

An operator starts MistHelper on Windows. A package that the process loads has a version that does not match its pin. The early check leaves that package unchanged and logs the repair command.

**Why this priority**: A locked file stops the uninstall step. The result is a half-removed package, and every later start fails.

**Independent Test**: Run the unit tests for a loaded package with a version mismatch. The installer receives no call for that package.

**Acceptance Scenarios**:

1. **Given** a package with a version mismatch and a loaded module, **When** the early check runs, **Then** it makes no call for that package.
2. **Given** any requirement, **When** the early check reads its state, **Then** it does not import the requirement module.

---

### User Story 2 - Stop before a large drift (Priority: P1)

An operator starts MistHelper with an environment that differs from the lock reference by six packages. The early check changes nothing and logs the repair command.

**Why this priority**: The failed run in the issue had 20 drifted packages. A large change in one process repeats the locked-file risk for each package.

**Independent Test**: Run the unit tests with six drifted packages and with five drifted packages.

**Acceptance Scenarios**:

1. **Given** six drifted packages, **When** the early check runs, **Then** it makes no change and logs one error with the repair command.
2. **Given** five drifted packages, **When** the early check runs, **Then** it makes the in-process changes that it can make.

---

### User Story 3 - Restore a failed upgrade (Priority: P2)

An upgrade removes files and then fails. The early check copies the removed files back from its snapshot.

**Why this priority**: A restored package keeps MistHelper startable after a failed in-process change.

**Independent Test**: Use a fake installer that removes a RECORD file and returns a failure code. The removed file exists again after the run.

**Acceptance Scenarios**:

1. **Given** an upgrade that removes a RECORD file and fails, **When** the early check handles the failure, **Then** the file exists again.
2. **Given** a snapshot that cannot be written, **When** the early check plans the upgrade, **Then** it skips that upgrade and logs an error.

---

### User Story 4 - Keep the disabled and container paths unchanged (Priority: P2)

An operator sets `DISABLE_AUTO_INSTALL=true`. The container image also sets this flag. The early check returns before it reads any package state.

**Why this priority**: Every container start uses this flag. A change in this path changes every container start.

**Independent Test**: Run the disabled-path unit test. The metadata reader receives no call.

**Acceptance Scenarios**:

1. **Given** `DISABLE_AUTO_INSTALL=true`, **When** the early check starts, **Then** it logs the disabled message and returns before any metadata read.
2. **Given** the container build files, **When** this change merges, **Then** `Containerfile` and `Dockerfile` remain unchanged.

### Edge Cases

- A package with no RECORD file is broken. It counts as drift even when its version matches the pin.
- A RECORD file that lists a missing file marks the package as broken.
- A loaded package counts toward the drift threshold, because only the repair command can fix it.
- A package with no top-level import name counts as loaded. The check does not change that package.
- A snapshot write fails because the disk is full. The check skips that upgrade and logs an error.
- A restore fails because another process holds a file. The check logs the snapshot path and keeps the snapshot.
- uv is missing. The pip path runs only after a snapshot exists for that package.
- The PyPI lookup fails. The latest version is unknown, and the check makes no latest-only upgrade.
- The requirements file is missing. The check keeps the existing empty-list behavior.
- Caution: a refused run changes nothing. The operator can run the repair command at a planned time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The early check MUST NOT install, upgrade, or reinstall a loaded package in the current process.
- **FR-002**: The early check MUST read presence and version from package metadata. It MUST NOT import a requirement module.
- **FR-003**: The early check MUST treat a package with an incomplete RECORD as broken, and MUST NOT change it in-process.
- **FR-004**: Before each upgrade, the early check MUST copy the package RECORD files, and MUST restore them after a failed upgrade.
- **FR-005**: The early check MUST change nothing when more than five packages are missing, broken, or off their pin.
- **FR-006**: The early check MUST log the repair command when it refuses or skips any package.
- **FR-007**: Each in-process change MUST log at info level before it and at debug level after it.
- **FR-008**: The early check MUST keep the `DISABLE_AUTO_INSTALL` short-circuit and the interpreter gate unchanged.
- **FR-009**: The change MUST keep `requirements.txt`, `pyproject.toml`, and `uv.lock` unchanged, and MUST add one changelog fragment.
- **FR-010**: The change MUST update `README.md` and `documentation/operator-guide.md` with the repair command, the threshold, and the workaround.
- **FR-011**: The change MUST keep the name and the signature of `MistHelper.early_dependency_check` and its startup caller.

### Key Entities

- **Package**: An installed Python package that `requirements.txt` lists. Its key attributes are the normalized name, the installed version, the pinned version, the RECORD state, and the loaded state.
- **Drift set**: The packages that are missing, broken, or off their pin. Its size controls the threshold in FR-005.
- **Snapshot**: Copies of the RECORD files of one package. The check makes one snapshot before each upgrade.
- **Lock reference**: The pins in `requirements.txt`. The header of that file states that `uv export --locked` writes it.
- **Repair command**: `uv sync --locked --extra dev`. The operator runs it after closing each process that uses the environment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the unit suite, zero installer calls target a loaded package in every loaded-package test case.
- **SC-002**: With six drifted packages, the unit suite records zero installer calls and one error line that names the repair command.
- **SC-003**: In the failed-upgrade tests, 100 percent of the captured RECORD files exist again after the run.
- **SC-004**: On a Windows 11 virtual environment, a start with five or fewer drifted packages leaves no package without a RECORD file. `design/quickstart.md` records the check.
- **SC-005**: Each applicable local gate passes, and each required check on the pull request passes.

## Assumptions

- The affected platform is Windows 11 with a virtual environment. The constitution names this platform for local development.
- The CI jobs run on `ubuntu-latest`. CI cannot show the Windows lock behavior, so the tests use fakes and `design/quickstart.md` records the manual check.
- The pins in `requirements.txt` equal the versions in `uv.lock`. Test TC-13 checks this assumption.
- The snapshot uses the system temporary folder. It is an internal copy, and it is not a product output under `data/`.
- Warning: an in-process change can remove files that a running MistHelper process needs. The next start can then fail.
- Two MistHelper processes do not start at the same time in the same environment.
- A fresh environment with more than five missing packages stops with the repair command. The bootstrap already runs the locked sync.

## Non-Goals

- Remove the in-process change. The change keeps repairs of up to five packages.
- Repair an existing broken environment without the operator. The operator runs the repair command.
- Change the PyPI latest-version lookup or its `requests` import.
- Edit `documentation/development-setup.md`. Issue #4879 owns that file.
- Split `DependencyCheckOrchestrator`. This existing five-item debt needs a separate issue.
- Remove `PackageImportMapManager` or its `MAPPING` export.
- Change the mistapi pins, or the mistapi wording in `.github/copilot-instructions.md`. `analysis.md` records the stale wording.
- Call any Mist API endpoint.
