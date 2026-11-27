# Feature Specification: Black Gate Failure From the Mando Pin

**Feature Branch**: `fix/4892-black-gate-mando-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4892, "CI: quality-gate `black` failed (PR #4888)". The report comes from Quality Gates run 45064243269.

## Clarifications

### Session 2026-11-26

- Q: Does the Black format check fail on its own rule? A: No. The Black format check step never ran. The pip install step failed first in job 137339161296.
- Q: Does main fail the Black gate? A: No. Run 45774119357 on main passes the Black job. All 33 jobs in that run succeed. Evidence: research R-56 and R-57.
- Q: Should this change close pull request #4888? A: No. The repository rule says not to close update pull requests. Source: `.github/copilot-instructions.md` line 533.
- Q: Does this change need a changelog fragment? A: Yes. The constitution requires one fragment for each change. Source: constitution line 409. The constitution governs over the README rule. Source: constitution line 529.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the real cause of the failure (Priority: P1)

A maintainer reads the failed Quality Gates run. The maintainer sees that pip failed in the Black job. The maintainer then knows that the fix is a dependency pin, not a format change.

**Why this priority**: A wrong cause sends the next agent to reformat files that already pass. That costs one CI run and one review cycle.

**Independent Test**: Read `design\research.md`, rows R-52 to R-54. Each failing step and message has a run ID, a job ID, or a log line.

**Acceptance Scenarios**:

1. **Given** run 45064243269, **When** a reader opens the Black job, **Then** the reader sees step 5 failed and step 6 skipped.
2. **Given** the CI log of job 137339161296, **When** a reader searches for `ResolutionImpossible`, **Then** the reader finds line 598 of the log.

---

### User Story 2 - Stop the mando bump from breaking the install (Priority: P1)

The mando pin stays at 0.7.1. Dependabot stops proposing mando releases that radon 6.0.1 rejects. The dependency jobs install `requirements-dev.txt` again.

**Why this priority**: Many jobs install `requirements-dev.txt`. One rejected pin blocked 26 jobs in one run.

**Independent Test**: Run `python -m pytest tests\guardrails\test_dependency_lock_file.py`. Both new tests pass. The first new test fails before the configuration change.

**Acceptance Scenarios**:

1. **Given** the pip entry has no mando ignore rule, **When** the guard runs, **Then** the guard reports the missing rule.
2. **Given** the pip entry has `versions: [">=0.8"]`, **When** the guard runs, **Then** mando 0.8.2 is ignored and mando 0.7.1 is not ignored.

---

### User Story 3 - Leave a clear record for the owner of pull request #4888 (Priority: P2)

The owner of pull request #4888 reads the record. The owner learns why the pull request must not merge. The owner also learns which step closes it.

**Why this priority**: Pull request #4888 stays open after this change. Its red checks look like a Black defect until the record explains them.

**Independent Test**: Read `analysis.md`, section "Unresolved Items". Each item names one owner action.

**Acceptance Scenarios**:

1. **Given** pull request #4888, **When** the owner reads the record, **Then** the owner sees the resolver conflict and the rule against closing the pull request.

### Edge Cases

- What happens when radon releases a version that accepts mando 0.8? The ignore rule and the guard expectation change in one pull request.
- What happens when Dependabot rejects the `versions` value? GitHub shows a configuration error. The owner corrects the value in a new pull request. Unverified: research U-1.
- What happens when a person edits `requirements-dev.txt` to mando 0.8.2? The existing lock guard and export guard fail on that change.
- What happens when Black finds a real format defect after pip succeeds? The local Format gate reports it before the push.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the failing workflow, job, step, and resolver message, with evidence.
- **FR-002**: The change MUST keep the mando pin at 0.7.1 in `uv.lock` and `requirements-dev.txt`.
- **FR-003**: Dependabot pip updates MUST NOT propose a mando version that radon 6.0.1 rejects.
- **FR-004**: The pip entry in `.github\dependabot.yml` MUST ignore mando versions `>=0.8`.
- **FR-005**: A guard test MUST fail when the mando ignore rule is missing or too narrow.
- **FR-006**: The change MUST NOT merge or close pull request #4888.
- **FR-007**: The change MUST add one changelog fragment named `issue-4892-black-gate-mando-pin.md`.
- **FR-008**: The record MUST use the route `specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin`, with five children or fewer per directory.
- **FR-009**: Each applicable local gate MUST pass before the push. The pull request body MUST list each result.

### Key Entities *(include if feature involves data)*

- **Mando pin**: The locked mando version. The value is 0.7.1 in `uv.lock` and `requirements-dev.txt`.
- **Radon range**: The mando range that radon 6.0.1 accepts. PyPI metadata states `<0.8,>=0.6`.
- **Dependabot ignore rule**: The pip entry rule that removes mando releases from update proposals.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: this change calls no Juniper Mist Cloud API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Black (format check) job reports success on the fix pull request.
- **SC-002**: The Dependency lock and exports job reports success on the fix pull request.
- **SC-003**: Both new guard tests pass. The first new test fails before the configuration change.
- **SC-004**: The changelog policy test passes for the new fragment.
- **SC-005**: Each new Markdown file scores 80 or above in `ste-linter`.
- **SC-006**: Pull request #4888 stays open and unmerged after this change merges.

## Assumptions

- Radon 6.0.1 is the latest radon release on PyPI on 2026-11-26. Evidence: research R-47.
- Dependabot accepts a PEP 440 `versions` range for pip. The SchemaStore schema describes this pattern. Runtime behavior is unverified: research U-1.
- The Black format check passes after pip succeeds. Main passes that check. Evidence: research R-56.
- The repository owner closes pull request #4888 after this change merges.

## Out of Scope

- Closing pull request #4888 or any of the 14 sibling gate issues.
- Replacing radon or changing the complexity gate.
- Editing `.github\workflows\ci.yml`, the Black configuration, or any product file.
- Reformatting any file.
- Removing the grandfathered five-children debt in `changelog.d\` and `tests\guardrails\`.
- Changing the changelog README rule. The owner reconciles that rule later.
