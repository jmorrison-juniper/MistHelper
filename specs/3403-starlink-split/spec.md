# Feature Specification: Move the Starlink dashboard to its own repository

**Issue**: #3403
**Feature Branch**: `chore/3403-starlink-split`
**Status**: Draft
**Requested by**: the repository owner on 2026-09-25

## Problem

`starlink_dashboard.py` is a PyQt6 desktop dashboard for a Starlink terminal.
It is not a part of MistHelper. No menu operation, no container, and no
document starts it. The file and its test still cost maintenance, because five
quality gate settings, two tools, and two ignore files name them.

## User Story 1 (P1): A Starlink user runs the dashboard from its own repository

**Acceptance scenarios**:

1. **Given** a new clone of `jmorrison-juniper/starlink-dashboard` with its
   submodule, **When** the user follows the README, **Then** the protocol
   modules generate, the dashboard module imports, and the tests pass.

2. **Given** the new repository, **When** a user reads `git log` for
   `starlink_dashboard.py`, **Then** the log shows the commits from MistHelper.

## User Story 2 (P2): A MistHelper maintainer sees no live Starlink code

**Acceptance scenarios**:

1. **Given** the MistHelper tree after the change, **When** the maintainer runs
   `git grep -i starlink`, **Then** the search finds only the historical text
   that "Out of scope" names.

2. **Given** the changed gate settings, **When** CI runs, **Then** every
   required check passes and no gate names a missing file.

## Functional requirements

- **FR-001**: The new repository keeps the commit history of the dashboard and
  its test.

- **FR-002**: The new repository pins the SpaceX `enterprise-api` repository as
  a submodule. It holds no copy of the upstream files, because the upstream
  repository has no license.

- **FR-003**: MistHelper deletes `starlink_dashboard.py` and
  `tests/unit/test_starlink_dashboard_startup_and_gps.py`.

- **FR-004**: No gate setting, tool default, or ignore rule in MistHelper names
  the dashboard or the `starlink-api-reference` folder.

- **FR-005**: The performance catalog of #2448 names no deleted file. Its three
  summaries state the counts of its tables.

- **FR-006**: The release note names the new repository.

## Out of scope

- The CodeQL verdict register keeps the rows for alerts #193 and #194. The
  register job compares the register with the dismissed alerts. GitHub keeps a
  dismissed alert in the dismissed state after a commit deletes its file.

- `CHANGELOG.md` and most `specs/` folders keep their Starlink text, because
  that text records past work. The one exception is the performance catalog of
  #2448, because a guard test compares its rows with the tracked files.

- Historical comments in `ci.yml`, `pyproject.toml`, and
  `tests/test_issue_433_src_g_no_regress.py` keep the file name.

- A WAN probe test uses "starlink" as a WAN profile name. That use is not the
  dashboard.

## Success criteria

- **SC-001**: The CI of the new repository passes on its first push.

- **SC-002**: Every required check passes on the MistHelper pull request.

- **SC-003**: The test quality ratchet reports `gate: 0 new findings vs
  baseline`.
