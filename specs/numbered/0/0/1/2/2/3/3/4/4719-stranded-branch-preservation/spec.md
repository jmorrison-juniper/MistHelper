# Feature Specification: Stranded Branch Preservation

**Feature Branch**: `chore/4719-stranded-branch-preservation`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4719, "chore(git): a branch holds work with no pull request". The issue body lists 51 remote branches. Each branch has commits above `main`. No pull request holds the head of any of them.

## Clarifications

### Session 2026-11-26

- Q: Which branches are in scope? A: The 51 branches in the issue body. The owner assessed these branches in the issue comments. Issue #4911 lists 505 rows. Its 454 extra rows stay out of scope.
- Q: May preservation pull requests open now? A: No. The owner publication hold stays in force until the owner releases it on issue #4719.
- Q: May a branch be deleted after its pull request exists? A: Not in this record. A later record decides deletion after owner review.
- Q: Where is the duplicate-issue defect fixed? A: In `misthelper-devtools`, which owns the reusable workflow. This repository moves its pins after a released fix.
- Q: Does the record pull request close issue #4719? A: Yes. The constitution requires `Closes #4719`. The analysis records the effect on the tracking issue.
- Q: How is the privacy-held branch handled? A: Only metadata is recorded. No source is read until the owner completes a privacy review.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep every stranded branch reachable (Priority: P1)

A maintainer opens one draft preservation pull request for each stranded branch. Each pull request keeps the branch head reachable through the pull request ref under `refs/pull/`.

**Why this priority**: A branch without a pull request has one copy. A cleanup can delete that copy without a warning.

**Independent Test**: For each preserved branch, the pull request head SHA equals the branch head SHA in the inventory.

**Acceptance Scenarios**:

1. **Given** the owner released the publication hold, **When** the maintainer opens a preservation pull request for a clean branch, **Then** the pull request names the branch, the full head SHA, and issue #4719.
2. **Given** a preservation pull request exists, **When** the maintainer compares the branch head with the inventory, **Then** the head SHA is unchanged.

### User Story 2 - See which branches still lack protection (Priority: P1)

A maintainer reads the inventory and the weekly report. The maintainer sees which of the 51 branches still lack a pull request, and the reason for each.

**Why this priority**: The owner must decide each hold with current facts.

**Independent Test**: The inventory has 51 rows. Each row shows the head SHA, the commit count, the changed path count, the overlap state, and the owner head check.

**Acceptance Scenarios**:

1. **Given** the inventory, **When** the maintainer counts the rows, **Then** the count equals 51 and the commit total equals 66.
2. **Given** the weekly report after the preservation batches, **When** the report lists branches, **Then** it names no branch whose current head has a pull request.

### User Story 3 - Hold risky branches until review (Priority: P2)

A maintainer keeps three groups of branches out of the first batch. These groups are the overlap branches, the privacy-held branch, and the two local-only branches.

**Why this priority**: The owner placed holds on these branches. A premature publication can expose private content or create merge conflicts.

**Independent Test**: Batch 1 lists 46 branches. The deferred groups name the other 5 branches with the reason for each.

**Acceptance Scenarios**:

1. **Given** an overlap branch, **When** the open pull request that it overlaps stays open, **Then** the branch stays in the deferred group.
2. **Given** the privacy-held branch, **When** the owner has not completed a privacy review, **Then** no source file of that branch is read or published.

### Edge Cases

- A branch head changes after the inventory. Repeat the head check before each batch. A changed head needs a new inventory row.
- Caution: a closed pull request keeps only the head that it had when it closed. A later commit makes the branch stranded again.
- Warning: deleting a stranded branch before its pull request exists destroys the only copy of its work.
- GitHub returns HTTP 403 or 429. Wait 60 seconds and retry up to three times. Record the check as unverified when every retry fails.
- The two local-only branches do not exist in this clone. Verify them in their own clone before any push.
- The weekly report lists an archive branch. The separate inventory handles it. This record does not preserve it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST list each of the 51 branches with its head SHA, commit count, and changed path count.
- **FR-002**: Before preservation, the record MUST show that no pull request holds any listed head.
- **FR-003**: Each preservation pull request MUST be a draft. Its body MUST name the branch, the full head SHA, and issue #4719.
- **FR-004**: No preservation pull request MUST open before the owner releases the publication hold.
- **FR-005**: The work MUST NOT delete, rename, rebase, or force-push any listed branch.
- **FR-006**: The record MUST hold only branch metadata for `recovery/2977-handoff-20261004` until the owner completes a privacy review.
- **FR-007**: The four branches that overlap open draft pull requests MUST wait for owner reconciliation.
- **FR-008**: The two local-only branches MUST stay local until the owner verifies them in their own clone.
- **FR-009**: The weekly report MUST reuse one open tracking issue. The fix MUST land in `misthelper-devtools`.
- **FR-010**: The pinned tag in both workflow files MUST move to a released tag that contains the FR-009 fix.
- **FR-011**: Duplicate tracking issues MUST close only after the owner approves one canonical issue.
- **FR-012**: The record MUST follow the managed route, the five-child limit, and the guardrail suite.
- **FR-013**: The record pull request MUST use a Conventional Commit title, the closing line `Closes #4719`, and one changelog fragment.
- **FR-014**: Each remote claim in the record MUST cite a path, a ref, a blob SHA, and a line when a line applies.
- **FR-015**: The record MUST leave the 454 extra rows of issue #4911 out of preservation until a separate inventory exists.
- **FR-016**: The plan MUST report each constitution rule with a pass or fail result and a reason.

### Mist Cloud Transport Requirements

Not applicable: this record calls no Mist Cloud REST endpoint. It owns no WebSocket transport.

### Key Entities

- **Stranded Branch**: A remote branch with commits above `main`. No pull request holds its current head. See `design/data-model.md`.
- **Head Holder**: A pull request whose head ref and head SHA match a branch head. See `design/data-model.md`.
- **Owner Hold**: A written owner statement that blocks an action. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After batch 1, 46 of 46 clean branches have a draft preservation pull request with the recorded head SHA.
- **SC-002**: After the deferred batches, 51 of 51 listed branches hold a pull request for their current head.
- **SC-003**: The number of deleted branches in this scope equals zero.
- **SC-004**: After FR-010, the weekly report names no branch whose current head has a pull request.
- **SC-005**: After FR-011, exactly one open tracking issue carries the report title.
- **SC-006**: Every check in `design/quickstart.md` passes, or the failed check names its cause.

## Assumptions

- The issue body table defines the scope of this record. The owner comments describe the same 51 branches.
- The owner holds stay in force until the owner releases them in a written comment.
- The local clone holds every commit of the 51 branches. Each head SHA equals the remote SHA, so the local objects show the remote content.
- The owner comments used `main` at `3964d21d03f9f5717cb8eafb7272ecff21f5362a`. This record does not recheck content equivalence.
- The reusable workflow at pin `79a5e45970e876f1656d69520d9635cea1aa25ef` matches the workflow on the `main` branch of `misthelper-devtools`.

## Non-Goals

- Deleting, renaming, rebasing, or force-pushing any branch.
- Merging or closing any pull request other than the record pull request.
- Editing `.github/workflows/stranded-branch-report.yml` or `.github/workflows/close-linked-issues.yml` in this record.
- Reviewing the 434 archive rows or the 20 other rows of issue #4911.
- Changing a container, a Mist API call, or a product file.
