# Feature Specification: Tracked Dependency Lock File

**Feature Branch**: `docs/3400-dependency-lock-file` (this record). Each implementation slice uses its own branch.

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #3400 asks whether to pin the Python dependencies with a tracked lock file. It also asks whether each worktree, each CI run, and each image install the same package versions.

## Terms

- **Lock**: the file `uv.lock` at the repository root. It records each resolved package, its version, its source, and its artifact hashes.
- **Declaration**: a dependency entry in `pyproject.toml`. The root declarations are the source of truth.
- **Export**: a requirements file that `uv export` writes from the lock. `requirements.txt` is the runtime export. `requirements-dev.txt` is the export for the `dev` extra, which adds development packages.
- **Install path**: a command or file that installs Python packages. The install paths are the worktree bootstrap, each CI job, each image build, each ops container build, and the Dependabot updates.
- **Guard**: a pytest case in `tests/guardrails/` or `tests/unit/` that fails when a repository fact drifts.
- **Gate**: a CI job that reports pass or fail for a pull request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same versions in each worktree (Priority: P1)

A developer creates a worktree and runs the bootstrap. The bootstrap syncs the environment from the lock. Each run installs the same package versions.

**Why this priority**: Drift between worktrees made test results hard to trust. The issue body measured this drift on 2026-09-25.

**Independent Test**: Run the bootstrap guard cases in `test_uv_locked_sync.py`. They confirm one locked sync per run and a pinned uv install.

**Acceptance Scenarios**:

1. **Given** a clean worktree, **When** the bootstrap runs, **Then** it runs `uv sync --locked --extra dev`.
2. **Given** uv is missing, **When** the bootstrap installs uv, **Then** it installs the pinned version `uv==0.13.9` outside the project environment.

---

### User Story 2 - Same versions in each CI run (Priority: P1)

A pull request starts CI. Each Python job installs from the lock. A gate fails when the lock or an export is stale.

**Why this priority**: A new release of a transitive package can fail CI on an unchanged commit. The issue body records this risk.

**Independent Test**: Run `uv lock --check` and the export guard. Both pass on `main`.

**Acceptance Scenarios**:

1. **Given** a pull request, **When** the `dependency_lock` job runs, **Then** it runs `uv lock --check` and the export guard.
2. **Given** a CI job that installs packages, **When** it starts, **Then** it runs a locked `uv sync` with uv 0.13.9.
3. **Given** the `pip_audit` job, **When** it runs, **Then** it audits `requirements.txt`, which is the runtime export.

---

### User Story 3 - Same runtime set in each image (Priority: P1)

A maintainer builds the root image. The image installs the runtime set from the lock. The container workflow compares the image package list with the runtime export.

**Why this priority**: The image runs in production NOC environments. Its package set must match the tested lock.

**Independent Test**: Run the image contract cases. After approval, run a dispatch build and read the freeze comparison.

**Acceptance Scenarios**:

1. **Given** the image build context, **When** the build starts, **Then** the context includes `uv.lock`.
2. **Given** the image build, **When** it installs packages, **Then** it runs a locked `uv sync` and does not run `pip install -r requirements.txt`.
3. **Given** a built image, **When** the freeze step runs, **Then** its runtime package versions equal the runtime export.

---

### User Story 4 - Pip users keep a working export (Priority: P2)

An operator without uv installs `requirements.txt` with pip. The file pins each runtime package. The export guard fails when the file differs from the lock.

**Why this priority**: Pip remains the install path for users who do not use uv.

**Independent Test**: Run the export guard. It compares each export with the lock output.

**Acceptance Scenarios**:

1. **Given** the lock, **When** the export command runs, **Then** its output equals the committed export.
2. **Given** a stale export, **When** the export guard runs, **Then** it fails and names the regeneration command.

---

### User Story 5 - Dependabot changes the declaration and the lock together (Priority: P2)

Dependabot opens an update pull request. The pull request changes `pyproject.toml` and `uv.lock`. A maintainer regenerates the exports when the export guard fails.

**Why this priority**: The current pip entry edits the exports directly. PR #4888 shows the conflict.

**Independent Test**: Read `.github/dependabot.yml` in the guard. It holds a `uv` entry for each lock.

**Acceptance Scenarios**:

1. **Given** Dependabot updates a dependency, **When** the pull request opens, **Then** the entry uses the `uv` ecosystem.
2. **Given** a pull request edits an export without the lock, **When** the export guard runs, **Then** the guard fails.

---

### User Story 6 - The ops platform uses its own lock (Priority: P3)

A maintainer builds an ops container. The build installs from `mist-ops-platform/uv.lock`. The ops export replaces the Windows-compiled `requirements.txt`.

**Why this priority**: The ops containers install unlocked ranges today.

**Independent Test**: Run `uv lock --check` in `mist-ops-platform/`. Run the ops export guard.

**Acceptance Scenarios**:

1. **Given** the ops lock, **When** `uv lock --check` runs in `mist-ops-platform/`, **Then** it passes.
2. **Given** an ops container build, **When** it installs packages, **Then** it uses the ops lock.

---

### Edge Cases

- A declaration changes and the lock does not change. `uv lock --check` fails in CI.
- An export changes a version and the lock does not change. The export guard fails.
- A developer runs a uv version outside `>=0.13.9,<0.14`. uv reports a version error.
- The image context excludes `uv.lock`. The `COPY` step fails. Today the root `.dockerignore` excludes it (RC-09).
- A Windows-only package keeps its marker in each export. The waitress marker stays in `requirements.txt`.
- A base image tag changes its content. The lock does not pin the base image. This case is out of scope (decision D-8).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The root `pyproject.toml` MUST declare every runtime and development package that an install path uses.
- **FR-002**: The lock MUST be tracked on `main` and MUST pass `uv lock --check`.
- **FR-003**: The `.gitignore` file MUST NOT ignore `uv.lock`, and a guard MUST fail when it does.
- **FR-004**: Each export MUST equal the output of `uv export` from the lock, and the export guard MUST fail on drift.
- **FR-005**: The worktree bootstrap MUST sync the environment from the lock with `uv sync --locked --extra dev`.
- **FR-006**: The CI job `dependency_lock` MUST run `uv lock --check` and the export guard, and the aggregator MUST require it.
- **FR-007**: Each CI job that installs Python packages MUST run a locked `uv sync` with the pinned uv version.
- **FR-008**: The CI job `pip_audit` MUST audit `requirements.txt`, the runtime export.
- **FR-009**: The container build MUST run its unit tests from the lock with `uv sync --locked`.
- **FR-010**: Each image MUST install the runtime set with a locked `uv sync` in a virtual environment.
- **FR-011**: Each image build MUST NOT run `pip install -r requirements.txt`, and its build context MUST admit `uv.lock`.
- **FR-012**: The container workflow MUST compare each built image package list with the runtime export.
- **FR-013**: Dependabot MUST use the `uv` ecosystem for `/` and `/mist-ops-platform`, and the export guard MUST name the regeneration command.
- **FR-014**: `mist-ops-platform/uv.lock` MUST be tracked, MUST pass `uv lock --check`, and its containers MUST install from it.
- **FR-015**: uv 0.13.9 MUST be pinned in `pyproject.toml`, the bootstrap, and the container build, with a `required-version` range.
- **FR-016**: The documentation MUST describe the locked install paths and the export regeneration command.
- **FR-017**: Each declaration and each document MUST state Python 3.15 and the mistapi floor from `pyproject.toml`.

### Mist Cloud Transport Requirements

Not applicable. This record names no Mist REST endpoint, no WebSocket path, and no SDK call. The only SDK fact is the locked version `mistapi 0.64.1` (RC-03).

### Key Entities

- **Declaration**: a dependency entry in `pyproject.toml`. Its natural key is the normalized package name and its table.
- **Lock package**: a `[[package]]` table in `uv.lock`. Its natural key is the name, the version, and the source.
- **Export line**: one requirement in an export. Its natural key is the normalized name and the marker.
- **uv pin**: the exact uv version that CI, the bootstrap, and the image use. Its natural key is the tool name and the version.
- **Install path**: one command or file that installs packages. Its natural key is its file path and step name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `uv lock --check` passes on `main` after each slice.
- **SC-002**: The export guard reports zero defects after each slice.
- **SC-003**: After slices 2 and 3, `ci.yml`, `Dockerfile`, and `Containerfile` contain no `pip install -r requirements` command.
- **SC-004**: After slice 5, no Dependabot pull request edits `requirements.txt` or `requirements-dev.txt` directly.
- **SC-005**: After slice 3, each image package list has zero differences from the runtime export.
- **SC-006**: After slice 4, `mist-ops-platform/uv.lock` passes `uv lock --check` in its folder.

## Assumptions

- The Python floor stays at 3.15, as `pyproject.toml` line 23 states (RC-10).
- The lock records one registry for each registry package, `https://pypi.org/simple` (RC-03 shows that source for mistapi).
- GitHub-hosted `ubuntu-latest` runners run every CI job (RC-24).
- Slices follow the order in plan.md. Each slice starts from `main`.

## Out of Scope

- Upgrading any package version. Each slice keeps every resolved version.
- The `ops-portal` npm lock, `ops-portal/package-lock.json`.
- Base image digest pinning and apt package pinning (follow-up F-3).
- Hash-checked exports (follow-up F-4).
- Restructuring `mist-ops-platform/` into a compliant folder layout (follow-up F-2).
- Changing the default SSH password that the Dockerfile sets.

## Clarifications

### Session 2026-11-26

- Q: Is the pinning decision still open? A: No. The owner gave go-ahead on 2026-11-06. `main` holds slices S0 to S4 and part of S5 (R1 and R4).
- Q: Does CI keep `pip-audit -r requirements.txt`? A: Yes. Decision D-2.
- Q: Does this record close issue #3400? A: No. Decision D-10 uses `Refs #3400`. The final slice uses `Closes #3400`.
- Q: May the ops lock add a direct child to `mist-ops-platform/`? A: Yes. Plan.md records the Principle I exception in Complexity Tracking. Decision D-5.
- Q: Who approves publication of the remaining slices? A: The user approves each slice. The 2026-11-17 hold applies, and it requires a serial-slot assignment before push, PR creation, or merge.
