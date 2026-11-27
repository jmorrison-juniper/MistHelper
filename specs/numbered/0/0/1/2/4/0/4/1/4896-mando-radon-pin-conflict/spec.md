# Feature Specification: Mando pin conflict in the pip-audit gate

**Feature Branch**: `fix/4896-mando-radon-pin-conflict`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4896, "CI: quality-gate `pip_audit` failed (PR #4888)". Pull request #4888 changes the mando pin from 0.7.1 to 0.8.2. The radon 6.0.1 pin requires mando below 0.8. The pip install step therefore fails before the CVE scan runs.

## Terms

- **Gate**: A quality gate of this repository, such as `pip_audit`.
- **Job**: A GitHub Actions job in `.github/workflows/ci.yml`. The job `pip_audit` runs the gate.
- **Check**: A status name on a pull request, such as `pip-audit (CVE scan)`.
- **Hold**: Keep mando at 0.7.1 while radon 6.0.1 is pinned.
- **Range**: The version range that radon 6.0.1 declares for mando, `<0.8,>=0.6`.
- **Replacement pull request**: The new pull request that carries this record's change.

## Clarifications

### Session 2026-11-26

- Q: Which check failed, and which step failed? A: The check `pip-audit (CVE scan)` failed at step 5, `Run pip install -r requirements-dev.txt`. The step `Run pip-audit` was skipped. Run 45064243269, job 137338084755 (R-03, R-05).
- Q: Which rule failed? A: The pip dependency resolver. It cannot satisfy `mando==0.8.2` with `radon==6.0.1`, because radon 6.0.1 requires `mando (<0.8,>=0.6)` (R-04, R-51).
- Q: Is the failure a CVE finding? A: No. The CVE scan never ran, because the install step failed first (R-05).
- Q: Does main fail in the same way? A: No. Main pins `mando==0.7.1` at line 179, and the latest main run passes this job (R-13, R-43).
- Q: How does the record fix the conflict? A: Hold mando at 0.7.1 while radon 6.0.1 is pinned. Add a Dependabot ignore rule for mando minor and major updates. Close pull request #4888 after the replacement merges.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the pip-audit check able to install (Priority: P1)

A maintainer opens a pull request that changes a pin in `requirements-dev.txt`. The job installs `requirements-dev.txt`, and then it runs the CVE scan. The check reports the scan result, not a resolver error.

**Why this priority**: The resolver error stops 26 jobs on pull request #4888. Those 26 jobs stop before their gate command (R-06). A Dependabot update cannot merge while the install fails.

**Independent Test**: Run `python -m pytest tests/guardrails/test_dependency_lock_file.py`. The range test passes on main, because main pins mando 0.7.1.

**Acceptance Scenarios**:

1. **Given** `requirements-dev.txt` pins `mando==0.7.1` and `radon==6.0.1`, **When** the range test runs, **Then** the test reports no defect.
2. **Given** the replacement pull request is open, **When** the job `pip_audit` runs, **Then** the install step exits with code 0 and the step `Run pip-audit` runs.

### User Story 2 - Stop Dependabot from reopening the conflict (Priority: P2)

Dependabot does not propose a mando update to 0.8 or later while radon 6.0.1 is pinned. A maintainer reads the reason in `.github/dependabot.yml` and in `documentation/quality-gates.md`.

**Why this priority**: The same resolver failure stopped pull request #4673 (issue #4688). A rule in the update configuration stops the next conflict before CI runs.

**Independent Test**: Run the guard test that reads `.github/dependabot.yml`. The test passes when the rule exists. The test fails on a fixture without the rule.

**Acceptance Scenarios**:

1. **Given** the pip entry of `.github/dependabot.yml` holds the ignore rule, **When** the guard test runs, **Then** the test reports no defect.
2. **Given** a configuration without the ignore rule, **When** the guard test runs on that fixture, **Then** the test reports one defect that names mando.

### User Story 3 - Catch a mando pin outside the radon range in a local test (Priority: P2)

A developer changes a pin in `requirements-dev.txt`. The guard test compares the mando pin with the range that radon 6.0.1 declares. The test fails in the local test run, before the CI install step starts.

**Why this priority**: The install step fails late, and only in CI. A local test gives the developer the reason at the first run.

**Independent Test**: Run the range test with a fixture that pins mando 0.8.2. The test reports one defect that names mando 0.8.2 and the range.

**Acceptance Scenarios**:

1. **Given** radon 6.0.1 and mando 0.8.2, **When** the range check runs, **Then** it reports one defect that names both versions.
2. **Given** a radon version that has no declared range in the guard, **When** the range check runs, **Then** the test fails and names that radon version.

### Edge Cases

- A radon release accepts mando 0.8 or later. The range check fails for the new radon version until a maintainer adds its range. The hold then ends in a separate change.
- A mando security advisory affects version 0.7.1. Pip-audit does not scan mando, because `requirements.txt` does not list it. The owner reviews the hold when an advisory appears.
- Pull request #4888 stays open after the replacement merges. Task T-MERGE closes it with a preservation proof.
- The replacement pull request fails another check. This record does not fix that check. Each new failure needs its own issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The job `pip_audit` MUST install `requirements-dev.txt` without a resolver conflict on each pull request.
- **FR-002**: `requirements-dev.txt` MUST pin mando inside the range that the pinned radon declares.
- **FR-003**: The pip entry of `.github/dependabot.yml` MUST ignore mando minor and major updates.
- **FR-004**: The guard test MUST report one defect when the mando pin leaves the radon range.
- **FR-005**: The guard test MUST fail when the pinned radon version has no declared range.
- **FR-006**: The guard test MUST report one defect when the Dependabot ignore rule for mando is absent.
- **FR-007**: The change MUST keep the job ID `pip_audit` and the check name `pip-audit (CVE scan)`.
- **FR-008**: The change MUST NOT add a suppression, an ignore flag, or a change to the pip-audit command.
- **FR-009**: `documentation/quality-gates.md` MUST state the mando hold, the source of the radon range, and the review trigger.
- **FR-010**: The change MUST add one release-note fragment named `changelog.d/issue-4896-mando-radon-pin-conflict.md`.
- **FR-011**: The replacement pull request MUST merge before pull request #4888 closes. The closing comment MUST carry a preservation proof.
- **FR-012**: The change MUST add no direct child under `tests/guardrails/` or `.github/`, because both parents hold more than five children.

### Mist Cloud Transport Requirements

Not applicable: this change calls no Mist Cloud endpoint and no mistapi function.

### Key Entities

Not applicable: this change adds no data entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The check `pip-audit (CVE scan)` reports success on the replacement pull request.
- **SC-002**: All five new test functions pass. Each negative test reports the defect that it expects.
- **SC-003**: `.github/dependabot.yml` holds exactly one ignore rule for mando.
- **SC-004**: The latest Quality Gates run on main stays green after the merge.
- **SC-005**: The remote check count is 69 in `STATUS.json`, in `design/research.md`, and in `summary.md`.

## Assumptions

- The replacement pull request starts from `main`, and it uses the branch `fix/4896-mando-radon-pin-conflict`.
- The repository owner authorizes the merge. The agent does not merge without that authorization.
- PyPI lists radon 6.0.1 as the current release on 2026-11-26 (R-47).
- Dependabot applies an `update-types` ignore rule to the pip ecosystem. The fetched reference does not confirm this for pip (R-50, U-1).

## Non-Goals

- This change does not replace radon or its complexity gate.
- This change does not change the pip-audit command, its flags, or the CVE policy.
- This change does not fix the other quality-gate issues, #4891 to #4905. Each issue keeps its own scope.
- This change does not add a general resolver check for all pins. The owner files a follow-up issue for that check.
- This change does not change a container image, a menu, or a Mist API call.
- Deployment under constitution Principle IV, step 12, stays with the owner. See decision D-8.
