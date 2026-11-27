# Feature Specification: Hold mando below 0.8 for the mypy gate

**Feature Branch**: `fix/4893-mando-radon-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4893, `CI: quality-gate mypy failed (PR #4888)`. The failed check is `mypy (strict)` in workflow `Quality Gates`, run 45064243269.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mypy gate installs its dependencies (Priority: P1)

The `mypy (strict)` job installs `requirements-dev.txt`, then runs mypy. On PR #4888, the install step fails with a resolution conflict. Mypy never runs.

**Why this priority**: Every pull request that installs the development requirements fails the same way. Merges stay blocked until the install succeeds.

**Independent Test**: On the fix pull request, the `mypy (strict)` job reaches `Run mypy` and exits with code 0.

**Acceptance Scenarios**:

1. **Given** `requirements-dev.txt` pins `mando==0.7.1` and `radon==6.0.1`, **When** the job runs the install step, **Then** the install step completes.
2. **Given** the install step completes, **When** the job runs `mypy $MYPY_PATHS --config-file pyproject.toml`, **Then** mypy reports no errors, and the gate result is `Success`.

---

### User Story 2 - Dependabot holds the blocked update (Priority: P2)

Dependabot does not propose a minor or major `mando` update. The `radon` release in use accepts only `mando` below 0.8.

**Why this priority**: Without this control, Dependabot reopens the same conflict on its next pip cycle.

**Independent Test**: The two new guard tests pass. `.github/dependabot.yml` holds an ignore entry for `mando`.

**Acceptance Scenarios**:

1. **Given** the pip block of `.github/dependabot.yml`, **When** a guard test reads it, **Then** the test finds an ignore entry for `mando` with `version-update:semver-minor`.
2. **Given** a fixture that pins `mando==0.8.2`, **When** the guard test checks it against the radon requirement, **Then** the guard reports a conflict.

---

### User Story 3 - Reviewer sees PR #4888 closed with proof (Priority: P3)

After the fix merges, PR #4888 closes. Its closing comment names the merged pull request and this record.

**Why this priority**: A closed update request must show the reason for the close.

**Independent Test**: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,comments` returns state `CLOSED` and one comment that names the merged pull request.

---

### Edge Cases

- Radon releases a version that accepts `mando` 0.8. The ignore entry then blocks a valid update, and a new decision is required.
- Dependabot proposes a `mando` patch release. The ignore entry allows patch releases, because it lists minor and major types only.
- A developer edits the `mando` pin by hand. The pin guard fails, and pip fails in CI.
- The job `E2E smoke tests` fails at step `Verify E2E shards`. Its cause is not read in this record. It needs its own issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The development requirements MUST resolve. `requirements-dev.txt` MUST keep `mando` at a version that `radon` 6.0.1 accepts.
- **FR-002**: Dependabot MUST NOT propose a `mando` minor or major update. `.github/dependabot.yml` MUST hold an ignore entry for `mando`.
- **FR-003**: The `mypy (strict)` job MUST run mypy after the install step. The job MUST exit with code 0 on the fix pull request.
- **FR-004**: The change MUST add one unique changelog fragment under `changelog.d/`.
- **FR-005**: Each changed file MUST pass each local gate that applies to it.
- **FR-006**: PR #4888 MUST close only after the fix merges. Its closing comment MUST name the merged pull request.

### Key Entities

Not applicable: this change adds no data entity.

### Mist Cloud Transport Requirements

Not applicable: this change calls no Mist Cloud API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `mypy (strict)` job on the fix pull request reaches `Run mypy` and exits with code 0.
- **SC-002**: The fix pull request run shows no `ResolutionImpossible` line in any job log. The failed run showed that line in 26 of 28 failed jobs.
- **SC-003**: The first Dependabot pip cycle after the merge opens no `mando` 0.8.x pull request.
- **SC-004**: PR #4888 shows state `CLOSED`, and its closing comment names the merged pull request.

## Assumptions

- **A-1**: `radon` 6.0.1 is the newest radon release. The PyPI project page shows that version as current (research.md, RC-69).
- **A-2**: `mando` is a development dependency only. `requirements.txt` holds no `mando` pin (research.md, RC-22).
- **A-3**: Dependabot applies an `update-types` ignore to pip updates the same way it applies one to npm updates (research.md, section 8, U-2).
- **A-4**: The record route follows the base-5 rule in `spec-route.ps1` (research.md, RC-57). Issue 4893 is `124033` in base 5. Padded to eight digits, the route is `0\0\1\2\4\0\3\3`.

## Out of Scope

- Replacing `radon`, changing `mypy`, or changing the mypy settings in `pyproject.toml`.
- Changing `requirements-dev.txt`, `requirements.txt`, `pyproject.toml`, or `uv.lock`.
- Triage of the other quality-gate issues from the same run, #4891 to #4905. Each keeps its own record.
- Restructuring `tests/guardrails/` or `changelog.d/`. Their folder debt stays on record.
- Repository settings, branch protection, and required status checks.

## Clarifications

- **Q**: Which revision failed? **A**: PR head revision `e86098cdc2b189d217805b3b4060ef609cbc37af`. The issue cites merge revision `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`, which CI checked out (research.md, RC-65, RC-66).
- **Q**: Does `main` fail? **A**: No. The three newest `ci.yml` runs on `main` conclude `success`.
- **Q**: Which check is the exact failing check? **A**: `mypy (strict)`, job `mypy` (`ci.yml` lines 201-237). The issue label `mypy` names the job ID.
- **Q**: Does a legacy record exist? **A**: No. Neither the local `specs` tree nor the `main` tree holds a `4893-*` folder.
- **Q**: Does a human decision block the work? **A**: No. No decision falls in the brief's human categories.
