# Feature Specification: Dependabot mando pin for the dependency_lock job

**Issue**: #4903
**Feature Branch**: `fix/4903-mando-radon-pin`
**Record**: `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin`
**Created**: 2026-11-26
**Status**: Draft
**Input**: CI quality-gate failure report for pull request #4888. Dependabot raised `mando` from 0.7.1 to 0.8.2.

## Clarifications

### Session 2026-11-26

- **Q**: Which check failed? **A**: The check named "Dependency lock and exports" failed. Its job ID is `dependency_lock`. The failing step is "Run pip install -r requirements-dev.txt". The two later steps were skipped.
- **Q**: Which rule failed? **A**: A pip resolution rule failed. `radon 6.0.1` requires `mando` below 0.8. Pull request #4888 pins `mando==0.8.2`.
- **Q**: Does `main` fail the same job? **A**: No. Run 45774119357 passed the job on the `main` head `f03c6c9b`.
- **Q**: Which commit does the issue cite? **A**: The issue cites `5bb4b385`. That commit is the GitHub test merge commit of `main` `00d9a16e` and the pull request head `e86098cd`.
- **Q**: Can a newer radon accept `mando` 0.8? **A**: No. PyPI lists radon 6.0.1 as the latest release. Radon 6.0.1 requires `mando` below 0.8.
- **Q**: Does a legacy record exist? **A**: No. No folder named `4903-*` exists under `specs\` on the local checkout or on `main`.
- **Q**: Does a human decision block the work? **A**: No. The agent decides each open choice. The decisions appear in `design/research.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the failing check and rule (Priority: P1)

A release maintainer reads this record. The maintainer finds the failing check, the failing step, and the failing rule. The maintainer does not need to open the logs first.

**Why this priority**: The issue cannot close until the cause is verified and recorded.

**Independent Test**: Run the first command in `design/quickstart.md`. The output contains `Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`.

**Acceptance Scenarios**:

1. **Given** the issue, **When** the maintainer reads `spec.md`, **Then** the record names the job, the step, and the rule.
2. **Given** run 45064243269, **When** the maintainer runs the quickstart command, **Then** the failed job log shows the resolver error.

### User Story 2 - Stop Dependabot from proposing mando 0.8 (Priority: P1)

Dependabot does not open a pull request that moves `mando` to 0.8 or later. A change that removes the protection fails the policy guard.

**Why this priority**: The same conflict returns on each Dependabot run until the update is skipped.

**Independent Test**: Run `python -m pytest tests/guardrails/test_pr_title_workflow.py`. The guard rejects a removed mando ignore and a weakened update type.

**Acceptance Scenarios**:

1. **Given** the pip update block, **When** Dependabot scans `requirements-dev.txt`, **Then** Dependabot skips the `mando` minor and major updates.
2. **Given** a change that removes the mando ignore, **When** the policy guard runs, **Then** the guard fails with the Dependabot message.

### User Story 3 - Find the pin rule in the gate documentation (Priority: P2)

A maintainer reads `documentation/quality-gates.md`. The maintainer finds the `dependency_lock` job, its checks, and the mando pin rule.

**Why this priority**: The gate table omits the job today, so a maintainer can repeat the same error.

**Independent Test**: Run `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`. The file scores 80 or above.

**Acceptance Scenarios**:

1. **Given** the gate table, **When** a reader looks for `dependency_lock`, **Then** the table holds one row for the job.
2. **Given** the mando pin section, **When** a reader looks for the radon limit, **Then** the section names `radon` 6.0.1 and `mando` below 0.8.

### User Story 4 - Close the failing pull request (Priority: P2)

After the fix merges, a maintainer closes pull request #4888. The closed pull request no longer shows failing checks for the same pin.

**Why this priority**: Fourteen sibling issues cite pull request #4888.

**Independent Test**: Run `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state --jq .state`. The result is `CLOSED`.

### Edge Cases

- What happens when a radon release accepts `mando` 0.8? The ignore and the policy snapshot must change together in a reviewed change.
- What happens when a security advisory names `mando` 0.7.1? A security update can bypass the ignore. The `dependency_lock` job then fails, and a maintainer decides the next step.
- What happens when Dependabot already opened a `mando` 0.8 pull request? Close that pull request. Caution: a recreate command rebuilds it with the broken pin.
- What happens when a sibling issue stays open after pull request #4888 closes? The orchestrator reviews the sibling issue and closes it.
- What happens when a route folder does not exist? Create each folder from the base-5 route. Each folder holds five children or fewer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `dependency_lock` job MUST pass on the fix pull request head.
- **FR-002**: Dependabot MUST NOT propose a minor or major `mando` update in the pip update block.
- **FR-003**: The Dependabot policy guard MUST fail when the mando ignore is removed or weakened.
- **FR-004**: `uv.lock` and `requirements-dev.txt` MUST keep `mando` at version 0.7.1.
- **FR-005**: The change MUST add one release-note fragment named by the issue rule.
- **FR-006**: `documentation/quality-gates.md` MUST name the `dependency_lock` job and the mando pin rule.
- **FR-007**: Pull request #4888 MUST close after the fix merges, with orchestrator authorization.
- **FR-008**: This record MUST name the failing check, the failing step, and the failing rule, with evidence.

### Mist Cloud Transport Requirements

Not applicable: the change uses no Mist Cloud API call and no mistapi method.

### Key Entities

- **Dependabot pip update block**: The mapping in `.github/dependabot.yml` that controls pip updates. It holds the mando ignore entry.
- **Policy snapshot**: The mapping in `tests/guardrails/test_pr_title_workflow.py` that records the complete Dependabot policy.
- **Pinned requirement**: A line in `requirements-dev.txt` that names one package and one version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `dependency_lock` job reports success on the fix pull request head.
- **SC-002**: The policy guard reports zero defects for the new policy. It fails for each of the two weakened policies.
- **SC-003**: `documentation/quality-gates.md` scores 80 or above in `ste-linter`.
- **SC-004**: No Dependabot pull request proposes `mando` 0.8 or later in the first Dependabot run after the merge.

## Assumptions

- Dependabot applies the `update-types` ignore to pip updates. This assumption is unverified. See `design/research.md`, item U-1.
- Radon 6.0.1 remains the latest radon release. The compatible `mando` version remains 0.7.1.
- The CI runner resolves `requirements-dev.txt` with pip, as the job log shows.
- The orchestrator authorizes the merge and the closure of pull request #4888.

## Out of Scope

- Replacing `radon` or changing the complexity gate.
- Changing `requirements.txt`, `uv.lock`, or `pyproject.toml`.
- Repairing the other failed checks of run 45064243269, beyond the shared root cause.
- Changing branch protection, the auto-merge workflow, or the quality-gate issue workflow.
