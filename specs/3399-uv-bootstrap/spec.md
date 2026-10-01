# Feature Specification: Prefer uv for worktree setup

**Feature Branch**: `jmorrison-juniper-unclaimed-issue-repairs`

**Created**: 2026-09-30

**Status**: Ready for planning

**Input**: Use an available uv executable for worktree dependency installation. Keep pip when uv is absent. Preserve index safety and setup compatibility.

**Existing Issue**: [MistHelper #3399](https://github.com/jmorrison-juniper/MistHelper/issues/3399)

**Feature Directory**: `specs/3399-uv-bootstrap/`

**Claim Owner**: Parent session `6d71fd26-57c2-48c0-abc8-607af98f75d0` already owns the issue.

**Current Deliverable**: Write only this specification, its quality checklist, and required feature context.

## User Scenarios & Testing *(mandatory)*

The developer prepares a MistHelper worktree before local development.
The developer needs faster dependency installation without changes to package versions or existing setup safeguards.

An installer is the program that installs packages from a requirement file.
A run is one request to install the worktree's requirement files.

### User Story 1 - Select the available installer (Priority: P1)

The developer uses uv when it is available.
If uv is absent, the developer can still prepare the worktree with pip.
The developer can identify the selected installer and install duration.

**Why this priority**: This behavior removes the fixed pip choice without making uv a required dependency.

**Independent Test**: Use temporary requirement files, simulated executable discovery, simulated installer results, and controlled elapsed times.
Do not start a real installer.

**Acceptance Scenarios**:

1. **Given** uv is available and both requirement files exist.
   **When** the developer starts dependency installation.
   **Then** the script uses the resolved uv executable for both files.
   Each command targets the worktree interpreter.
   The script installs `requirements.txt` before `requirements-dev.txt`.
2. **Given** uv is absent and both requirement files exist.
   **When** the developer starts dependency installation.
   **Then** the script uses the worktree interpreter's pip for both files.
   The report states that uv is absent and pip is the selected installer.
3. **Given** the caller defines different uv link and certificate settings.
   **When** the script starts a uv install.
   **Then** that subprocess receives `UV_LINK_MODE=copy` and `UV_NATIVE_TLS=1`.
   The caller's settings remain unchanged.
4. **Given** controlled elapsed times and successful installer results.
   **When** either installer completes the requirement files.
   **Then** the report identifies the selected installer, each completed file, each file's duration, and the total dependency-install duration.

---

### User Story 2 - Keep index decisions local to one run (Priority: P1)

The developer retains the existing package source when it works.
If the configured index does not answer, setup uses the public index for that run only.

**Why this priority**: A faster installer must not restore long waits against a failed index or change saved settings.

**Independent Test**: Simulate index configuration, connection results, and caller variables for both installers.
Repeat installation with the same setup object to check isolation between runs.

**Acceptance Scenarios**:

1. **Given** a configured index does not answer and inherited index settings conflict with the public fallback.
   **When** the existing probe selects `https://pypi.org/simple`.
   **Then** both requirement-file installs use that public index with either installer.
   Inherited extra indexes cannot restore access to the failed index.
   The script changes neither caller variables nor saved index configuration.
2. **Given** a configured mirror answers and no fallback is necessary.
   **When** either installer installs the requirement files.
   **Then** the mirror remains the primary package source.
   The script preserves the source choices that the existing pip path uses.
3. **Given** the existing pip path uses caller-supplied primary and extra indexes without a fallback.
   **When** the script selects uv.
   **Then** uv uses the same source choices.
   The script does not force the public index.
4. **Given** the first run uses the public fallback.
   **When** a later run finds the configured index reachable.
   **Then** the later run has no stale public override.
   Earlier subprocess environments remain unchanged.
5. **Given** the configured index is already public, configuration is absent, or configuration discovery fails.
   **When** the script checks the index.
   **Then** the existing probe decisions remain unchanged.
   Installer selection does not add another connection probe for each file.

---

### User Story 3 - Stop when an install fails (Priority: P1)

The developer sees a failed setup when the selected installer fails.
The script must not hide that failure through an automatic change to another installer.

**Why this priority**: An incomplete environment must not appear ready for development or tests.

**Independent Test**: Simulate nonzero installer results and an executable launch error.
Observe the setup result and all later action calls.

**Acceptance Scenarios**:

1. **Given** uv is available and its first requirement-file install returns a nonzero code.
   **When** the script handles that result.
   **Then** setup returns exit status `1` and identifies uv, the failed file, and the returned code.
   The script starts no pip install, second requirement-file install, or later setup action.
2. **Given** the first requirement file succeeds and the second fails with either installer.
   **When** the script handles that result.
   **Then** setup returns exit status `1`.
   The script does not print a ready report or start the browser download, health check, or GitHub credential check.
3. **Given** pip is the selected fallback and its install returns a nonzero code.
   **When** the script handles that result.
   **Then** setup returns exit status `1` and reports the failed file and code.
   The script does not change installers.
4. **Given** executable discovery finds uv but the executable cannot start.
   **When** the script attempts installation.
   **Then** setup returns exit status `1` and reports the launch error.
   The script does not treat this error as missing uv or start pip.

---

### User Story 4 - Preserve existing setup compatibility (Priority: P2)

The developer keeps the existing setup command, virtual environment paths, browser trust settings, and GitHub credential checks.
Installer selection changes only dependency installation.

**Why this priority**: The performance change must not break supported worktree setup behavior.

**Independent Test**: Simulate Windows and non-Windows paths, existing browser options, and successful later setup actions.
Replace all external actions with local test substitutes.

**Acceptance Scenarios**:

1. **Given** a Windows worktree path contains spaces.
   **When** either installer receives the target interpreter.
   **Then** it receives the full `.venv/Scripts/python.exe` path as one argument.
   Non-Windows runs retain the `.venv/bin/python` target.
2. **Given** one or both requirement files are absent.
   **When** the script installs dependencies.
   **Then** it skips each absent file and reports only successful files in the original order.
   If both files are absent, the script starts no package install.
3. **Given** the caller defines existing `NODE_OPTIONS`.
   **When** setup prepares the browser download.
   **Then** it preserves those options and adds `--use-system-ca` only when absent.
   It does not add a duplicate.
   The browser command, repair guidance, and nonblocking download failure behavior remain unchanged.
4. **Given** dependency installation succeeds.
   **When** setup continues.
   **Then** the environment health check, browser step, readiness report, and GitHub credential check retain their existing behavior.
   GitHub credentials still use the expected `jmorrison-juniper` account.
5. **Given** existing package pins and the current setup command.
   **When** the developer reviews the change and runs the offline compatibility tests.
   **Then** requirement-file contents and package pins remain unchanged.
   The existing `--recreate` option still creates the same environment layout.

### Edge Cases

- The uv executable or worktree path contains spaces.
- Executable discovery finds uv, but the executable disappears before installation.
- The first file succeeds, but the second file returns a nonzero code.
- Neither requirement file exists.
- Caller variables conflict with required uv settings or a run-only public index override.
- A later run must discard an earlier installer's selection and index override.
- Index configuration discovery fails, names a public host, or contains a URL without a usable host.
- The caller already includes `--use-system-ca` with other browser options.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bootstrap MUST discover uv on the command search path once per dependency-install run.
  It MUST use the resolved executable path for all present requirement files in that run.
- **FR-002**: If uv is available, each installation MUST use `<uv executable> pip install --python <worktree interpreter> -r <requirement file>`.
  Paths MUST remain separate arguments.
  The target MUST be the worktree's virtual environment, not the caller's interpreter or another environment.
- **FR-003**: If discovery finds no uv executable, each installation MUST use `<worktree interpreter> -m pip install -r <requirement file>`.
  This absence MUST be the only automatic reason to select pip instead of uv.
- **FR-004**: The bootstrap MUST install `requirements.txt` before `requirements-dev.txt`.
  It MUST install each present file once, skip absent files, and report only successfully installed files.
- **FR-005**: Each uv installation environment MUST set `UV_LINK_MODE=copy` and `UV_NATIVE_TLS=1`, even when caller values differ.
  These settings support OneDrive file copies and the system certificate store.
  The change MUST NOT disable certificate verification.
- **FR-006**: Each installation MUST receive a separate copy of the caller's environment.
  Required overrides MUST NOT change the caller's environment, saved configuration, another subprocess environment, or later runs.
  Unrelated caller settings MUST remain available.
- **FR-007**: The bootstrap MUST preserve the existing pip-index discovery and probe before dependency installation, including when uv is selected.
  Configuration discovery MUST still use the worktree interpreter's pip.
  The connection probe MUST retain its three-second timeout and existing public-host, unreadable-configuration, and unusable-host behavior.
  Index discovery and fallback selection MUST run once per dependency-install run, not once per file.
  Each run MUST perform at most one connection probe.
- **FR-008**: If no fallback applies, either installer MUST preserve the primary and extra-index choices of the existing pip path.
  A reachable configured mirror MUST remain in use when uv is selected.
  Installer selection MUST NOT silently replace that mirror with an unrelated default.
- **FR-009**: If the probe selects the public fallback, both installers MUST use `https://pypi.org/simple` for that run.
  The override MUST take precedence over inherited primary-index settings for both installers.
  The copied installation environment MUST remove inherited extra-index settings that could defeat the fallback.
  The script MUST NOT write any pip or uv configuration.
- **FR-010**: Each later dependency-install run MUST make a fresh installer choice and index decision.
  The same setup object MUST NOT retain a stale override after an earlier run, including an earlier failed run.
- **FR-011**: The pip fallback MUST retain `PIP_RETRIES=1` and `PIP_TIMEOUT=15`.
  Each uv installation child MUST use `UV_HTTP_RETRIES=1` and `UV_HTTP_TIMEOUT=15`.
  These overrides MUST NOT change the caller or force transport settings into browser children.
  This requirement does not claim that uv reads pip retry settings.
- **FR-012**: A nonzero uv result or uv launch error MUST stop dependency installation.
  The bootstrap MUST NOT retry that install through pip or classify a real uv failure as executable absence.
- **FR-013**: A dependency-install failure with either installer MUST return bootstrap exit status `1`.
  The report MUST identify the installer, failed file, and return code when available.
  No later requirement-file install, health check, browser download, readiness report, or GitHub credential action may start.
- **FR-014**: Before installation, the bootstrap MUST report the selected installer and the reason for missing-uv fallback when applicable.
  Each attempted file install MUST report its elapsed time in seconds to one decimal place, including nonzero results.
  Each successful run MUST report total dependency-install time, including a run with no present files.
  Installer output MUST remain visible.
- **FR-015**: New log messages MUST use ASCII and Simplified Technical English.
  They MUST NOT expose tokens, index credentials, or the contents of the subprocess environment.
- **FR-016**: The bootstrap MUST consume the existing requirement files without changes to package pins or dependency declarations.
  This feature MUST NOT add dependencies, install uv automatically, introduce a lockfile, or add an upgrade operation.
- **FR-017**: The setup command, `--recreate` behavior, and existing virtual environment creation MUST remain compatible.
  Windows MUST retain `.venv/Scripts/python.exe`.
  Other supported platforms MUST retain `.venv/bin/python`.
  Pip MUST remain available in the environment for configuration discovery and fallback installation.
- **FR-018**: Browser setup MUST preserve caller `NODE_OPTIONS`.
  It MUST add `--use-system-ca` only when absent.
  Browser selection, download trust, repair guidance, and nonblocking browser failure handling MUST remain unchanged.
- **FR-019**: After successful dependency installation, the existing health check and GitHub credential behavior MUST remain unchanged.
  The expected GitHub account MUST remain `jmorrison-juniper`.
  Credential-variable warnings and repository credential configuration MUST retain their current behavior.
- **FR-020**: Focused unit tests MUST verify installer selection, both requirement files, isolated environments, index handling, and failure handling without network access.
  Tests MUST replace real installers, connection probes, environment creation, browser downloads, and GitHub operations with local substitutes.
  Tests MUST use existing test dependencies and meet the repository's minimum 80% coverage requirement for changed behavior.

### Key Entities

- **Install run**: One dependency-install request with a selected installer, target environment, file results, elapsed times, and success or failure.
- **Requirement file**: An existing package declaration file whose contents and pins remain unchanged.
- **Index decision**: A run-local decision to retain existing package sources or use the public fallback.
- **Install environment**: A subprocess-only copy of caller settings with the required installer and index overrides.

### Scope Boundaries

- The later implementation covers dependency installation in `scripts/bootstrap_worktree.py` and focused offline unit tests.
- Directly related bootstrap documentation and one unique release fragment for issue #3399 belong to the later implementation.
- This specification task changes no source code, tests, bootstrap documentation, dependency files, or release notes.
- Keep the current app-managed branch. Do not create, switch, or rename branches. Do not create or claim another issue.
- Exclude production network operations, deployment, shared `CHANGELOG.md` edits, unrelated refactoring, and migration of other setup commands to uv.

### Offline Acceptance Coverage

The later implementation must provide the following focused coverage.
These are test requirements, not tests executed during specification.
Every case uses local substitutes and makes zero network calls.
The suite must satisfy the coverage constraint for changed behavior in FR-020.

| Case | Required observation | Requirements |
| --- | --- | --- |
| uv is available | Both files use the resolved executable, explicit interpreter, and separate path arguments. | FR-001, FR-002, FR-004 |
| uv is absent | Both files use the existing pip command and report why pip is selected. | FR-003, FR-004, FR-011, FR-014 |
| One file or both files are absent | Skip absent files and return only successful file names in order. | FR-004 |
| Caller uv settings conflict | Each uv subprocess receives copy mode and native certificate trust. | FR-005 |
| Caller settings contain unrelated values | Preserve those values and leave the caller environment unchanged. | FR-006 |
| An install environment changes after creation | Neither another subprocess environment nor caller settings change. | FR-006 |
| The configured index is unreachable | Both installers use the public fallback despite conflicting inherited index settings. | FR-007, FR-009 |
| A mirror is reachable | Both installers retain the configured mirror without a forced public fallback. | FR-008 |
| Caller primary and extra indexes apply | Both installers preserve the existing pip source choices when no fallback applies. | FR-008 |
| Configuration is absent, public, unreadable, or unusable | Preserve the existing probe outcomes and avoid additional per-file probes. | FR-007 |
| Two runs use the same setup object | Installer discovery and index choice are fresh, including after a failed first run. | FR-010 |
| Either installer returns a nonzero code | Return failure, identify the file and code, and start no later setup action. | FR-012, FR-013 |
| A discovered uv executable cannot start | Return failure without a pip install attempt. | FR-012, FR-013 |
| Controlled elapsed times apply | Report the installer, file durations, failed-file duration, and successful total duration. | FR-014, FR-015 |
| New log messages include user settings | Keep messages in ASCII and do not print secrets or environment contents. | FR-015 |
| Windows or non-Windows paths contain spaces | Preserve the existing target paths as complete arguments. | FR-002, FR-003, FR-017 |
| Existing pins and setup options apply | Leave requirement-file contents unchanged and preserve the current setup command and environment layout. | FR-016, FR-017 |
| Browser options and credential checks apply | Preserve existing trust settings and successful later setup behavior without external calls. | FR-018, FR-019 |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance runs, setup selects the available preferred installer or the defined fallback without user intervention.
- **SC-002**: Every successful two-file acceptance run installs both files exactly once, in order, into the intended worktree environment.
- **SC-003**: Every attempted file install reports its installer and elapsed seconds to one decimal place.
  Every successful dependency-install run reports a total duration.
- **SC-004**: All isolation cases leave caller settings and saved index settings unchanged.
  Every subsequent run uses its own index decision.
- **SC-005**: Every failed dependency install produces a failed setup result.
  Failure cases start zero alternative installers and zero later setup actions.
- **SC-006**: All specified acceptance cases pass without network access.
  Developers can identify the installer, installed files, duration, and failure reason from the report without reading source code.

## Assumptions

- uv is optional and already installed when executable discovery finds it.
  The feature context records the user-required discovery operation.
- A run uses one installer choice for both requirement files.
  A later run checks availability again.
- Existing pip source behavior remains authoritative.
  This change does not redesign pip configuration discovery or connection-probe rules.
- The existing virtual environment includes pip.
  The existing requirement files and test dependencies remain available without changes.
- Offline tests verify commands, settings, outcomes, and timing reports.
  They do not prove a fixed speed improvement under real download or OneDrive conditions.
- Install duration depends on package caches, network conditions, and file storage.
  No unsupported percentage improvement or fixed elapsed-time target is required.
- Ordinary setup retains its existing package, browser, and GitHub interactions.
  This specification task and its acceptance tests perform no real network operations.
