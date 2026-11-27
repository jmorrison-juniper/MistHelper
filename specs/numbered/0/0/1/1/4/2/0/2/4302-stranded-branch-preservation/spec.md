# Feature Specification: Stranded Branch Preservation

**Feature Branch**: `docs/4302-stranded-branch-preservation`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4302, "chore(git): a branch holds work with no pull request"

## Clarifications

### Session 2026-11-26

- Q: The orchestrator brief names one branch. Which scope applies? A: Issue #4302 lists 48 rows. Report #4911 lists 505 rows. This record covers all 505 rows. Decision D-1.
- Q: May an unpublished branch open a pull request (PR)? A: Only after owner authorization and a clean content scan. The repository is public. Decisions D-3 and D-16.
- Q: Does the record PR close #4302? A: No. The record PR refers to #4302 with `Refs`. The owner closes #4302 after the final disposition. Decision D-10.
- Q: Which changelog rule applies? A: The constitution requires one fragment for each change. The fragment uses the issue-name form. Decision D-13.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inventory every stranded branch (Priority: P1)

The owner reads one verified inventory. Each row names a branch, its head commit, its commits above `main`, and whether a PR keeps its head.

**Why this priority**: The owner cannot choose a disposition without verified evidence for each row.

**Independent Test**: Run TST-01 and TST-02. Both counts match the remote verification table in `design/research.md`.

**Acceptance Scenarios**:

1. **Given** report #4911 is open, **When** the inventory runs, **Then** it lists 505 rows, and each row has a head commit.
2. **Given** a row whose head commit equals a PR head commit, **When** the inventory runs, **Then** the row shows that it is PR-kept, with the PR number.

### User Story 2 - Publish a batch only after gates (Priority: P1)

The owner authorizes one batch. A scan clears each head in the batch. Each draft PR then keeps the unchanged head.

**Why this priority**: The repository is public. Published content stays readable after its PR closes.

**Independent Test**: Run TST-14, TST-17, and TST-15 for one batch.

**Acceptance Scenarios**:

1. **Given** no owner authorization for a batch, **When** the publication step runs, **Then** no PR opens for that batch.
2. **Given** an owner authorization and a clean scan, **When** a draft PR opens, **Then** its head commit equals the recorded head commit.

### User Story 3 - Keep held work unchanged (Priority: P2)

A row with a human review or an owner reservation stays unpublished. No branch ref changes in this issue.

**Why this priority**: A deleted or rewritten ref can remove the only copy of work.

**Independent Test**: Run TST-16 and TST-18 after each step.

**Acceptance Scenarios**:

1. **Given** a row on hold, **When** the publication step runs, **Then** no PR exists for that row's branch.
2. **Given** any step in this issue, **When** the refs are read, **Then** each head equals its recorded head.

### User Story 4 - Stop the duplicate tracking issues (Priority: P3)

The weekly report opens a new tracking issue each week. A separate issue fixes the title search. The owner then closes the duplicate issues.

**Independent Test**: Run TST-23 before and after the fix.

### Edge Cases

- A branch head moves after its scan: the row returns to the scan step, and the scan repeats for the new head.
- A scan finds a secret: the batch stops. The owner handles the secret under the credential policy.
- A head commit equals a PR head commit: that PR is the proof. No new PR opens for that row.
- Two rows share one head commit: one draft PR serves both rows. The second row cites that PR.
- GitHub returns HTTP 403 or 429: wait 60 seconds, then retry up to three times. Record an unverified result when retries fail.
- A new branch appears after this record: the next scope check adds a row, and the same gates apply.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST list each annotated row with its head commit, its commits above `main`, and its commits behind `main`. Each report row MUST receive a class from TST-02.
- **FR-002**: The record MUST count, for each annotated row, the changed files that are identical, differ, or are absent on `main`, by blob SHA.
- **FR-003**: The record MUST classify each report row as PR-kept or unkept by comparing its head commit with PR head commits.
- **FR-004**: The record MUST state the repository visibility before any publication step.
- **FR-005**: A branch MUST NOT publish until the owner authorizes its batch on #4302 and a scan passes.
- **FR-006**: Each draft PR MUST use an unchanged branch head, and it MUST carry no auto-merge label.
- **FR-007**: A row on hold MUST stay unpublished until its named human or reservation holder releases it.
- **FR-008**: No branch ref MUST change in this issue. Deletion, rewrite, rebase, merge, and force-push are excluded.
- **FR-009**: The scope check MUST run again after each batch, and the record MUST keep the counts.
- **FR-010**: The record MUST use the managed route. Each directory MUST hold five children or fewer.
- **FR-011**: Each Markdown file and the changelog fragment MUST pass the STE gate and the link check.
- **FR-012**: The record PR MUST use a Conventional Commits title, and it MUST refer to #4302 with `Refs`.
- **FR-013**: The remote verification table and the STATUS `remote_checks` array MUST have equal row counts.
- **FR-014**: No deliverable MUST contain a placeholder marker, except `HUMAN-DECISION-REQUIRED`.
- **FR-015**: #4302 MUST stay open until the owner records each disposition.
- **FR-016**: The duplicate tracking-issue defect MUST have its own issue, separate from this record.

### Key Entities *(include if feature involves data)*

- **Branch row**: One branch named in #4302 or in report #4911. Natural key: the branch name.
- **Pull request**: One PR that holds a head commit. Natural key: the PR number.
- **Publication gate**: The owner authorization, the scan result, and the hold state for one branch row.
- **Remote check**: One verified claim. It records a path, a ref, a blob or head SHA, a result, and a line.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the 48 annotated rows has one row in the remote verification table. Each of the 505 report rows has one class from TST-02.
- **SC-002**: No branch ref changes in this issue. Each head equals its recorded head at each batch.
- **SC-003**: Each published batch has one owner authorization comment and one clean scan result per head.
- **SC-004**: Each row on hold has one recorded hold reason and one named releaser.
- **SC-005**: Each record Markdown file scores 80 or above on the STE gate, and the link check reports zero broken links.
- **SC-006**: After the report fix, exactly one open tracking issue carries the report title.
- **SC-007**: #4302 stays open until the owner records each disposition.

## Assumptions

- The owner account can open draft PRs on this repository.
- The repository stays public for the life of this issue. A visibility change requires a new review.
- The report rules follow the shared workflow pinned at `79a5e45970e876f1656d69520d9635cea1aa25ef`.
- The owner comments name the holds. Their counts are stale, so this record uses GitHub data.
- Report #4911 shows the scope at 2026-11-23. TST-02 repeats the count before each batch.

## Out of Scope

- This issue does not delete, rewrite, rebase, merge, or force-push a branch.
- This issue does not change MistHelper code, tests, or workflows.
- This issue does not change the shared report workflow. A separate issue covers that defect.
- This issue does not review the 210 unkept rows in group N. The owner selects them later.
- This issue does not cover Mist API, mistapi, container, or Juniper device behavior.
