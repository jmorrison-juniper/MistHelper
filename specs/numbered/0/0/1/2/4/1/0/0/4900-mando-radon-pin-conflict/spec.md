# Feature Specification: Mando Pin Conflict Behind the pydocstyle Gate Failure

**Feature Branch**: `fix/4900-mando-radon-pin-conflict`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 4900, "CI: quality-gate `pydocstyle` failed (PR #4888)"

## Clarifications

### Session 2026-11-26

- Q: Which job failed? A: The job `pydocstyle (docstring style)` in the Quality Gates workflow, run 45064243269. Its step `Run pip install -r requirements-dev.txt` failed.
- Q: Did a pydocstyle rule fail? A: No. The step `Check docstring conventions` was skipped, so no pydocstyle rule ran.
- Q: What caused the install failure? A: pip cannot combine `mando==0.8.2` with `radon==6.0.1`. Radon 6.0.1 requires `mando<0.8`.
- Q: Does main pass the same job? A: Yes. Run 45774119357 passed the pydocstyle job on commit f03c6c9.
- Q: Does a newer radon release accept mando 0.8? A: No. The PyPI project page lists radon 6.0.1 as the latest release.
- Q: Which commit does the issue name? A: Commit 5bb4b385 is a GitHub test-merge commit. Commit e86098cd is the pull request head that the run tested.
- Q: Does a decision need a human? A: No. The decisions concern dependency policy and process only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore the Quality Gates on pull requests (Priority: P1)

A maintainer opens a pull request that does not change the mando pin. The Quality Gates workflow then installs requirements-dev.txt and runs every job to its end.

**Why this priority**: Twenty-eight jobs in three workflows fail at the same install step. Every pull request in this state stays blocked.

**Independent Test**: Run the Quality Gates workflow on the fix pull request. Read the pydocstyle job and the dependency lock job.

**Acceptance Scenarios**:

1. **Given** the fix pull request, **When** the Quality Gates workflow runs, **Then** each pip install step reports success.
2. **Given** the fix pull request, **When** the pydocstyle job runs, **Then** the step `Check docstring conventions` runs and reports success.
3. **Given** the fix pull request, **When** the dependency lock job runs, **Then** the export guard reports 2 files and 0 defects.

---

### User Story 2 - Stop Dependabot from reopening the blocked update (Priority: P2)

A maintainer expects Dependabot to skip mando minor and major updates while radon pins mando below 0.8.

**Why this priority**: Dependabot can reopen the same update on each weekly run after a close. Each such pull request fails the same way.

**Independent Test**: Read the pip entry in `.github/dependabot.yml`. Run the policy guard test.

**Acceptance Scenarios**:

1. **Given** the change on main, **When** Dependabot runs its weekly pip check, **Then** Dependabot opens no mando minor or major pull request.
2. **Given** the change on main, **When** the policy guard test runs, **Then** the test passes and the snapshot holds the same two update types.

---

### User Story 3 - Close the blocked pull request and keep its commit (Priority: P2)

A maintainer closes pull request 4888 after the fix merges. Commit e86098cd stays reachable by its SHA.

**Why this priority**: Pull request 4888 stays open and failing until someone closes it.

**Independent Test**: Read the state of pull request 4888 and the commit e86098cd.

**Acceptance Scenarios**:

1. **Given** the fix merged to main, **When** the maintainer closes pull request 4888, **Then** the state reads CLOSED and its branch is deleted.
2. **Given** the closed pull request, **When** a reader fetches commit e86098cd by its SHA, **Then** the commit still resolves.

---

### Edge Cases

- Dependabot proposes mando 0.7.2. The policy allows the update. The update must also change uv.lock, or the export guard reports requirements-dev.txt as stale.
- A later radon release accepts mando 0.8. The maintainer removes the ignore block in the same pull request as the radon update.
- Pull request 4888 gets a new commit before the close. The close still applies, because the minor update stays declined.
- After the fix, another job fails for a different cause. The maintainer reads that job log and opens a new issue for that cause.
- A reader compares commit 5bb4b385 with the branch head. The record names both commits and their roles.
- After the fix, pip reports a different resolver conflict. The maintainer treats it as a new defect and opens a new issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fix MUST let the pydocstyle job reach its step `Check docstring conventions` on the fix pull request.
- **FR-002**: The requirements-dev.txt pin for mando MUST equal the uv.lock version, 0.7.1.
- **FR-003**: The Dependabot pip policy MUST ignore mando minor and major updates.
- **FR-004**: The Dependabot pip policy MUST keep mando patch updates allowed.
- **FR-005**: The change MUST NOT remove, skip, or relax any quality gate.
- **FR-006**: The change MUST NOT edit ci.yml, pyproject.toml, requirements.txt, requirements-dev.txt, or uv.lock.
- **FR-007**: The change MUST add one changelog fragment named issue-4900-mando-radon-pin-conflict.md.
- **FR-008**: The record MUST name the failing job, the failing step, the error text, and the fact that no pydocstyle rule ran.
- **FR-009**: The change MUST close pull request 4888 without merge after the fix merges, and it MUST keep commit e86098cd reachable by its SHA.
- **FR-010**: The branch, commit, pull request title, and labels MUST follow AGENTS.md and the constitution.
- **FR-011**: The record MUST use the managed route `specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict`.

### Key Entities *(include if feature involves data)*

- **Mando pin**: The line `mando==0.7.1` in requirements-dev.txt. It must equal the locked version in uv.lock.
- **Dependabot pip policy entry**: The pip block in `.github/dependabot.yml`. It holds the commit prefix `chore` and the new mando ignore block.
- **Failing run**: GitHub Actions run 45064243269. It tested pull request 4888 at head commit e86098cd.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: this change sends no request to the Mist Cloud and changes no transport.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 28 directly failing jobs and both downstream jobs conclude success on the fix pull request.
- **SC-002**: The pydocstyle job shows `Check docstring conventions` with conclusion success, not skipped.
- **SC-003**: The export guard output reports `examined 2 files` and `0 defects`.
- **SC-004**: The policy guard test passes, and the mando update types are exactly minor and major.
- **SC-005**: Pull request 4888 reads CLOSED, and its branch no longer exists.
- **SC-006**: Seven days after the merge, Dependabot opens no mando minor or major pull request.
- **SC-007**: Both changelog guard tests pass for the new fragment.

## Assumptions

- Dependabot honors the ignore block for a transitive pip pin. The team confirms this after the first weekly run.
- Dependabot updates uv.lock with requirements-dev.txt for pip updates. Sibling pull requests #4802 to #4806 changed uv.lock.
- The Windows workflows install the same requirements-dev.txt. Their workflow lines confirm this.
- The team accepts mando 0.7.1 until radon changes. Radon 6.0.1 remains the latest release.
- The remote evidence in design/research.md reflects the repository state on 2026-11-26.

## Out of Scope

- Replacing radon or raising its version. No compatible release exists, so a separate issue owns this work.
- Auditing development-only packages with pip-audit. The gate audits requirements.txt only.
- Consolidating the 335 fragments in changelog.d. The release process owns this work.
- Changing rule four in changelog.d/README.md. A separate issue owns the conflict with the constitution.
- Changing the Mist API, mistapi, the container build, or Podman settings.
- Closing any open pull request other than pull request 4888.

## Human Decisions

No decision needs a human. No licensing, data, credential, or product priority question exists.
