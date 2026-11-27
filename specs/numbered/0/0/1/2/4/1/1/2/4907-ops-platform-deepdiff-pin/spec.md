# Feature Specification: Ops Platform Deepdiff Pin

**Feature Branch**: `fix/4907-ops-platform-deepdiff-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4907: CI quality gate `ops_platform_pytest` failed on PR #4889. PR #4889 changes the pin of deepdiff from 8.6.2 to 9.2.1 in `mist-ops-platform/requirements.txt`.

## Clarifications

### Session 2026-11-26

- Q: Which check failed, and at which step? → A: The check `pytest (ops platform)` in workflow `Quality Gates` failed at step 4, `Install dependencies`. Run 45064277976 and job 137336827145 hold the log. Steps 5 to 7 were skipped. Source: `.github/workflows/ci.yml` lines 1122 to 1162.
- Q: Which rule failed? → A: The pip resolver stopped with `ResolutionImpossible`. PR #4889 pins `deepdiff==9.2.1` at `mist-ops-platform/requirements.txt` line 56. `mist-ops-platform/pyproject.toml` line 31 declares `deepdiff>=8.6.2,<9.0`. No test ran, so no test name failed.
- Q: Does main fail the same gate? → A: No. Run 45774119357 on main head `f03c6c9` passed the job `pytest (ops platform)`, job 139753527584.
- Q: Which commit does the issue name? → A: The issue names `fd94cfcb`. That commit has two parents, `00d9a16e` (base) and `9d464066` (PR head). The run head is `9d464066`. The issue names the merge commit that GitHub builds for the pull request event. This is an inference, listed as U-7 in research.
- Q: Should this change move deepdiff to 9.x? → A: No. Commit `23379f0e0` (PR #4871, 2026-11-21) added the declared constraint. `mist-ops-platform/src/shared/services/diff.py` line 97 documents 8.x behavior. A 9.x move needs its own reviewed change.
- Q: Why did the existing dependency job pass on PR #4889? → A: `tests/guardrails/test_dependency_export.py` compares the root exports with `uv.lock`. It does not compare the ops platform pins with their declared constraints.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catch a pin that breaks its declared constraint (Priority: P1)

A maintainer changes a pin in `mist-ops-platform/requirements.txt`. The new pin falls outside the range in `mist-ops-platform/pyproject.toml`. The dependency job fails and names the package. The maintainer does not wait for the ops install step.

**Why this priority**: PR #4889 failed only after a long pip install. The dependency job runs earlier and names the package.

**Independent Test**: Run `tests/guardrails/test_dependency_export.py`. The new test case reads the committed ops files. It then proves that a synthetic `deepdiff==9.2.1` pin is reported as a defect.

**Acceptance Scenarios**:

1. **Given** the committed ops pins, **When** the guard runs, **Then** it reports 22 examined pins and 0 defects, and it passes.
2. **Given** a pin of `deepdiff==9.2.1`, **When** the guard compares it with `deepdiff>=8.6.2,<9.0`, **Then** the guard reports `deepdiff` as the only defect.
3. **Given** no pin matches a declared constraint, **When** the guard runs, **Then** it fails and reports no pass.

---

### User Story 2 - Keep the 9.x bump out of main (Priority: P1)

A maintainer keeps PR #4889 out of main. The pull request closes unmerged. The closing comment names the branch and the commit that keep the work.

**Why this priority**: A merge of PR #4889 fails the ops gate and the dependency job. It also breaks a deliberate constraint.

**Independent Test**: After this change merges, `gh pr view 4889` reports state `CLOSED` and no merge date. The closing comment names branch `dependabot/pip/deepdiff-9.2.1` and commit `9d4640661fa40b1e0a7809f46a0007eff7add517`.

**Acceptance Scenarios**:

1. **Given** this change merged, **When** the owner closes PR #4889, **Then** PR #4889 closes without a merge.
2. **Given** the closing comment, **When** a reader opens it, **Then** the comment names the branch, the commit, and the reason.

---

### User Story 3 - Read the counts in the job log (Priority: P2)

A reviewer opens the dependency job log. The log shows how many pins the guard examined.

**Why this priority**: A count proves that the guard read its input. A zero count shows a silent failure.

**Independent Test**: Run the guard with output enabled. The output holds one ASCII summary line.

**Acceptance Scenarios**:

1. **Given** the committed ops pins, **When** the guard prints its summary, **Then** the line reads `ops platform pins: examined 22 pins, 0 defects`.

### Edge Cases

- A pin has no declared constraint. The guard skips it. The examined count does not include it.
- A declared name has extras, such as `uvicorn[standard]`. The guard compares the base package name only.
- A pin is a pre-release, such as `opentelemetry-instrumentation-fastapi==0.66b2`. The guard accepts it when the declared constraint allows that version.
- A required input file is missing or empty. The guard fails with the existing read message.
- Dependabot proposes deepdiff 9.x again. The dependency job fails that pull request.
- The declared constraint changes later. The guard follows the new constraint without a code change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The guard MUST compare every pin in `mist-ops-platform/requirements.txt` with the constraint that `mist-ops-platform/pyproject.toml` declares for the same package.
- **FR-002**: The guard MUST fail and name each package whose pin falls outside its declared constraint.
- **FR-003**: The guard MUST fail when it compares zero pins.
- **FR-004**: The guard MUST print the count of examined pins and the count of defects.
- **FR-005**: The change MUST leave `mist-ops-platform/pyproject.toml`, `mist-ops-platform/requirements.txt`, `.github/dependabot.yml`, and `.github/workflows/ci.yml` unchanged.
- **FR-006**: The change MUST add one changelog fragment named `changelog.d/issue-4907-ops-platform-deepdiff-pin.md`.
- **FR-007**: PR #4889 MUST NOT merge. The owner MUST close it after this change merges, with a preservation proof in the closing comment.

### Key Entities

Not applicable. The change adds no data entity.

## Success Criteria *(mandatory)*

- **SC-001**: The jobs `Dependency lock and exports` and `pytest (ops platform)` pass on the change pull request.
- **SC-002**: The new test case passes on the committed pins. It reports a defect for the synthetic conflict.
- **SC-003**: The change pull request changes only the test file, the changelog fragment, and the record folder.
- **SC-004**: Issue #4907 closes when the change merges. PR #4889 closes without a merge.

## Assumptions

- The CI runner uses Ubuntu and Python 3.15.2. The failed log shows `/opt/hostedtoolcache/Python/3.15.2/x64/bin/pip`.
- The root `requirements-dev.txt` pins `packaging==26.3` at line 228. The job `Dependency lock and exports` installs that file.
- Main keeps the pins that this record reads at head `f03c6c9`.
- The owner accepts that deepdiff stays on the 8.x line until a separate reviewed change.

## Out of Scope

- Moving deepdiff to 9.x, changing the declared constraint, or editing the comment on `mist-ops-platform/pyproject.toml` line 31.
- Changing `.github/dependabot.yml`, including adding an update stream for `/mist-ops-platform`.
- Changing the install command or the timeout of the ops job.
- Correcting the stale test count in the ops job comment at `.github/workflows/ci.yml` line 1135.
- Any change to `DiffService` or to other ops platform code.

## Existing Record

No record exists for issue 4907. The search of `specs\` found no folder whose name starts with `4907-`. Research row 38 holds the remote proof.
