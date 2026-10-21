# Feature Specification: Tracked Dependency Lock File

**Feature Branch**: `jmorrison-juniper-dependency-lock-migration`

**Created**: 2026-10-19

**Status**: Draft

**Input**: Issue #3400 asks whether each worktree, each CI run, and each image must
install the same Python package versions.

## Assumptions

- **A-001 (decision)**: The owner is unavailable. The latest read-only assessment on
  issue #3400 recommends option 4. This specification adopts that recommendation as
  the working decision. Option 4 makes `pyproject.toml` the canonical declaration,
  then tracks `uv.lock`. Managed installs use the lock. Pip users receive generated
  requirements exports.
- **A-002**: No package version changes during this migration. The migration moves
  declarations and adds a lock. It does not upgrade a package. Dependabot makes
  later upgrades.
- **A-003**: Option 4 stays valid until a blocker in the Blocker Register below
  shows evidence that it is unsafe. Then work stops and reports the evidence.
- **A-004**: Measured facts come from the assessment at commit `efd0828` and from
  `origin/main` at `531bfe42c`. Each slice measures again before it edits.

## Problem

- `requirements.txt` has 37 range-only entries. A new install takes the newest
  compatible version of each package and of each transitive package.
- `pyproject.toml` omits 16 runtime packages that `requirements.txt` declares.
  Nine shared runtime packages have different floors. Four development packages
  exist only in `requirements-dev.txt`.
- `.gitignore` excludes `uv.lock`, so no commit holds a lock.
- `scripts/bootstrap_worktree.py`, `ci.yml`, `container-build.yml`, `Dockerfile`, and
  `Containerfile` each resolve the declarations again.
- The measured drift is real. Twelve worktrees differed by one to six packages, and
  the main environment differed by 62 packages.

## User Scenarios

### User Story 1 - Same versions in each worktree

As a developer, I need each fresh worktree to install the locked versions.

**Acceptance Scenarios**:

1. **Given** a clean worktree, **When** I run the bootstrap, **Then** it runs a
   locked sync and the installed versions equal the lock.
2. **Given** a manifest change with no lock change, **When** I run the bootstrap,
   **Then** it stops with a message that names the lock refresh command.

### User Story 2 - Same versions in CI and images

As a maintainer, I need each CI job and each root image to use the same lock.

**Acceptance Scenarios**:

1. **Given** a pull request, **When** CI starts, **Then** every Python job installs
   from the lock and a lock check job passes.
2. **Given** a built image, **When** I list its packages, **Then** its runtime
   versions equal the runtime lock export.

### User Story 3 - Pip users keep a working file

As an operator without UV, I need a `requirements.txt` that pip can install.

**Acceptance Scenarios**:

1. **Given** the lock, **When** the export command runs, **Then** it writes
   `requirements.txt` and `requirements-dev.txt` with no diff.
2. **Given** a stale export, **When** the guard runs, **Then** it fails and names
   the file.

### User Story 4 - Dependabot updates the lock

As a maintainer, I need one Dependabot pull request to change a manifest and the
lock together.

**Acceptance Scenarios**:

1. **Given** a new release, **When** Dependabot opens a pull request, **Then** the
   pull request changes `pyproject.toml` and `uv.lock`.
2. **Given** the pull request, **When** the export guard finds a stale export,
   **Then** the failure names the regeneration command.

## Requirements

- **FR-001**: `pyproject.toml` MUST declare every root runtime and development
  package. The declaration MUST keep the higher of the two existing floors and the
  existing upper bound.
- **FR-002**: Slice S1 MUST NOT change the version that any environment resolves.
- **FR-003**: `uv.lock` MUST come from the complete manifest only. No slice commits
  a lock before FR-001 passes its guard.
- **FR-004**: The first lock MUST match a baseline freeze of the current
  environment. Each difference MUST have a written explanation, and no difference
  MAY be an upgrade.
- **FR-005**: `uv lock --check` MUST pass in CI. A manifest and lock mismatch MUST
  fail the pull request.
- **FR-006**: The bootstrap, each CI job, and each root image MUST install with a
  locked sync. Images MUST exclude development packages.
- **FR-007**: `requirements.txt` and `requirements-dev.txt` MUST become generated
  exports with a header that names the command. A guard MUST fail on drift.
- **FR-008**: The Dependabot pip entry MUST change to the `uv` ecosystem in one
  entry. A parallel pip entry MUST NOT remain.
- **FR-009**: Each new guard MUST print the count that it examined and MUST fail
  when it cannot read its input.
- **FR-010**: Each slice MUST be one bounded pull request on current `main`.
- **FR-011**: Windows, macOS, and Linux MUST resolve from one universal lock. The
  `waitress` Windows marker MUST stay.
- **FR-012**: The `misthelper-devtools` Git commit pin MUST stay exact in the lock.

## Success Criteria

- A clean install on each of the three platforms lists zero version differences
  against the lock.
- `pip-audit --locked .` reports no known vulnerability.
- Every root image runtime package set equals the runtime export.
- A Dependabot test pull request changes the manifest and the lock together.

## Blocker Register

Stop and report evidence before editing if any of these appears.

| ID | Blocker | Evidence that proves it |
| - | - | - |
| B-001 | The complete manifest does not resolve on Python 3.13 | `uv lock` fails with no package version change possible |
| B-002 | The devtools Git direct reference cannot enter the lock | `uv lock` rejects the reference under Hatch metadata rules |
| B-003 | A lock install differs from the baseline by an upgrade | The baseline comparison shows a higher version |
| B-004 | Dependabot `uv` cannot read the project | The first scheduled run fails or opens no pull request |
| B-005 | An image build fails offline or behind the corporate proxy | The build log shows a registry failure that no mirror fixes |

## Out of Scope

- Upgrading any package.
- Changing the `ops-portal` npm lock.
- Changing the ops platform lock. Slice S7 covers it after the root slices pass.
