# Feature Specification: Pin the verified auto-merge commit

**Feature Branch**: `fix/4906-auto-merge-verified-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "CI quality-gate failure report for issue 4906. The pytest gate failed on Dependabot pull request 4886."

## Clarifications

### Session 2026-11-26

- Q: Accept the Dependabot update, or keep the old pin? A: Accept it. The reusable workflow blob SHA matches at both commits (D-1).
- Q: Change the Dependabot branch, or open a new branch? A: Open a new branch from main (D-3).
- Q: Add a guard test? A: No. The failed run proves that the existing guard fails on a pin mismatch (D-4).
- Q: Add a changelog fragment? A: No. The change is internal only (D-5).
- Q: Does any decision need human approval? A: No. No decision falls in a licensing, data, credential, or product category (D-1 to D-9).

## User Scenarios & Testing *(mandatory)*

### Failure summary

Run 45064239338 of the Quality Gates workflow failed on the head of pull request 4886. The job `pytest coverage shard (root-and-contracts)` failed on one test. The job `pytest (coverage gate)` then failed, because one shard failed.

The failing test is `TestAutoMergeJob::test_merge_recovery_uses_the_verified_shared_commit` in the guard file, `tests/guardrails/test_auto_merge_issue_close.py`. The pin is the `uses` value at line 61 of `.github/workflows/auto-merge.yml`. The verified commit is the constant at line 46 of the guard file. The Dependabot update changes the pin only. The guard file requires both values to match.

### User Story 1 - Pass the pytest gate with the reviewed commit (Priority: P1)

A maintainer needs the pytest gate to pass with the pin set to the reviewed commit. The pin and the verified commit must name the same full commit SHA.

**Why this priority**: The failing gate blocks the Dependabot update and every later pull request that runs the same gate.

**Independent Test**: Run `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`. All 17 tests pass.

**Acceptance Scenarios**:

1. **Given** the pin and the verified commit both name `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`, **When** the guard file runs, **Then** all 17 tests pass.
2. **Given** the pin and the verified commit name different commits, **When** the guard file runs, **Then** the merge-recovery test fails.

### User Story 2 - Keep the reviewed evidence with the pin (Priority: P2)

A reviewer needs proof that the reusable workflow did not change between the old commit and the new commit. The proof is the blob SHA of the reusable workflow file. A blob SHA is the git hash of one file content.

**Why this priority**: The guard file checks equality only. It cannot show that new upstream code is safe. A reviewer must check the blob SHA.

**Independent Test**: Read the blob SHA of `.github/workflows/reusable-auto-merge.yml` at both commits in `jmorrison-juniper/misthelper-devtools`. Both values equal `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8`.

**Acceptance Scenarios**:

1. **Given** the two commits, **When** the reviewer compares the blob SHA values, **Then** the values match.
2. **Given** the verified commit line in the guard file, **When** the reviewer reads its comment, **Then** the comment names the matching blob SHA.

### User Story 3 - Close the superseded Dependabot update (Priority: P3)

A maintainer needs pull request 4886 closed after the replacement pull request merges. The closing comment names the replacement and the files examined on main.

**Why this priority**: Two open updates for one pin cause conflicting pull requests and a second failing gate.

**Independent Test**: Read pull request 4886 after the merge. Its state is closed, and its closing comment names the merged replacement.

**Acceptance Scenarios**:

1. **Given** the replacement pull request merged, **When** the orchestrator authorizes the close, **Then** pull request 4886 closes with a preservation comment.

### Edge Cases

- What happens when main moves before the merge? Rebase the branch and rerun the guard file. The pin and the verified commit stay equal.
- What happens when Dependabot opens a newer update? Change the pin and the verified commit in one commit. Move them only after the blob SHA matches.
- What happens when the blob SHA changes at a newer upstream commit? Do not move the verified commit. Review the upstream change first.
- What happens when pull request 4886 closes first? The replacement pull request still stands alone, because it has no dependency on pull request 4886.
- What happens when another file names the old commit? Before this record exists, a search of the working tree finds the old commit only at the pin and at the verified commit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The auto-merge job MUST call `reusable-auto-merge.yml` at the commit that the verified commit names.
- **FR-002**: The verified commit MUST name `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- **FR-003**: The pin and the verified commit MUST each use a full 40-character commit SHA.
- **FR-004**: The guard MUST keep failing when the pin and the verified commit differ. The guard MUST NOT read its expected value from the workflow file.
- **FR-005**: Each changed file MUST pass each local gate that applies to its file type.
- **FR-006**: The change MUST add no changelog fragment. The pull request body MUST state that the change is internal only.
- **FR-007**: The spec record MUST sit under `specs/numbered/0/0/1/2/4/1/1/1/` and keep five children or fewer at each level.

### Key Entities *(include if feature involves data)*

Not applicable: the change edits one pin and one constant. It creates no data entity.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: the change makes no Mist Cloud request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The replacement pull request shows passing checks for `pytest (coverage gate)` and `pytest coverage shard (root-and-contracts)`.
- **SC-002**: After the merge, main names `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` at line 61 of the workflow and at line 46 of the guard file.
- **SC-003**: Pull request 4886 closes after the replacement merges. Its closing comment names the replacement.
- **SC-004**: The reusable workflow blob SHA at the new commit stays `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8`.

## Assumptions

- The reusable workflow blob SHA matches at both commits. Rows R-14 to R-16 in `design/research.md` record this check.
- The orchestrator authorizes the merge. No agent merges without that authorization.
- The implementation session runs the local gates. The spec author runs no test.
- The base of the replacement pull request is the current main tip. At spec time, that tip is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Out of Scope

- Changes to the `misthelper-devtools` repository.
- Changes to other shared workflow pins, such as the pin for `reusable-close-linked-issues.yml`.
- Changes to the guard design or to the names of required checks.
- Direct changes to the Dependabot branch of pull request 4886.
- A new guard test or a new changelog fragment.
