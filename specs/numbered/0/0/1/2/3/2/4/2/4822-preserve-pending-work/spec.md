# Feature Specification: Preserve Pending Work Before Branch Cleanup

**Feature Branch**: `chore/4822-preserve-pending-work`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4822: preserve unfinished local work in nine merged branches before cleanup. Create private recovery archives and local recovery commits. Compare both Dynamic JVD Labs copies. Remove only verified obsolete worktrees and branches.

## Clarifications

### Session 2026-11-26

- Q: Can the snapshot tags and recovery branches move to origin now? A: No. A secret review and owner approval must come first. See FR-009 and D-2.
- Q: Can an archive path appear in Git or in an issue comment? A: No. Only identifiers, hashes, and counts appear. See FR-011 and D-3.
- Q: Can a worktree folder be removed while it holds ignored output? A: No. Archive the ignored output first. See FR-004 and D-5.
- Q: Which command deletes a merged local branch? A: `git branch -d`. Force deletion is not allowed. See FR-008 and D-4.
- Q: Does the Labs comparison need the private folders? A: Yes. Git snapshots give file-level evidence. The private folders need a SHA-256 comparison. See FR-005 and D-7.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify that each pending change has a recovery copy (Priority: P1)

An owner lists each snapshot tag and classifies its files against main. The owner also checks each archive. Each pending change then has a verified copy before any removal.

**Why this priority**: Warning: Deleting the only copy of a pending change destroys that work. Verification must come first.

**Independent Test**: Run the inventory and classification steps in `design/quickstart.md`. Each count matches the table in `design/research.md`.

**Acceptance Scenarios**:

1. **Given** nine snapshot tags, **When** the owner lists them, **Then** nine rows show the commit, the parent, and the file count.
2. **Given** a file in a snapshot, **When** the owner compares it with main, **Then** the result is identical, different, or absent.
3. **Given** a private archive, **When** the owner computes its SHA-256 hash, **Then** the hash matches its manifest entry.

### User Story 2 - Remove only verified obsolete worktrees and branches (Priority: P1)

An owner removes a worktree folder or a local branch only after its copy is verified. Ignored output is archived first. Unmerged commits and locked admin directories stay in place.

**Why this priority**: Warning: Removal cannot be undone from Git records alone.

**Independent Test**: After the cleanup, run TST-011 to TST-015 and TST-022 to TST-023 in `tasks.md`. The main commit is unchanged. Each removed branch is merged or has a verified copy.

**Acceptance Scenarios**:

1. **Given** a merged branch with a registered worktree, **When** its ignored output is archived, **Then** the owner may remove the worktree folder.
2. **Given** a recovery branch with commits that main lacks, **When** the cleanup runs, **Then** the branch remains unchanged.
3. **Given** a locked admin directory, **When** its app sessions close, **Then** the owner runs `git worktree prune -v`. If the lock remains, the directory is a blocker.

### User Story 3 - Report each remaining blocker on the issue (Priority: P2)

An owner posts one public report. The report names each blocker, its cause, and its next action. The report holds no private path or operational data.

**Why this priority**: The issue requires a blocker report. Other agents need that report before they continue the work.

**Independent Test**: Run TST-016 and TST-017 against the report text.

**Acceptance Scenarios**:

1. **Given** a blocker, **When** the report is posted, **Then** the blocker has a cause and a next action.
2. **Given** the report text, **When** the private path scan runs, **Then** the scan finds no private path.

### Edge Cases

- A snapshot has no tracked change. The `release` and `sync` snapshots hold zero files, so their pending content exists only in the private recovery store.
- A registration is prunable. Its worktree folder is missing, but its admin directory remains.
- Windows blocks deletion of an admin directory, as the owner reports. This record does not identify the holding process.
- A branch is merged into main but has no pull request. Its commits remain in main history.
- A snapshot file differs from main by three lines. The issue 2977 `spec.md` shows this difference.
- A closed issue has a changelog fragment only in a snapshot. Issue #4624 shows this pattern.
- A snapshot restores `.specify/feature.json`. Restoring it changes the Spec Kit feature state.
- A bundle restores fewer references than the owner reports. The count check fails.
- An archive hash differs from its manifest. The archive is not a valid copy.
- The two Labs folders differ in one file. The Labs comparison fails for that file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The process MUST list each snapshot tag and recovery branch with its commit identifier.
- **FR-002**: The process MUST classify each file in each snapshot as identical to main, different from main, or absent from main.
- **FR-003**: The process MUST verify each private archive with its SHA-256 hash and entry count before removal.
- **FR-004**: The process MUST archive the ignored output of each worktree before its folder is removed.
- **FR-005**: The process MUST compare both Dynamic JVD Labs copies file by file and record the identical count.
- **FR-006**: The process MUST verify the Git bundle and restore its references into an independent bare repository.
- **FR-007**: The process MUST remove a local branch only when main contains its commits or a verified recovery copy exists.
- **FR-008**: The process MUST delete a merged local branch with `git branch -d`. The process MUST NOT use `git branch -D`.
- **FR-009**: The process MUST NOT push a snapshot tag or recovery branch before a secret review and owner approval.
- **FR-010**: The process MUST leave the main checkout, unrelated branches, and files of other sessions unchanged.
- **FR-011**: The process MUST keep private paths and operational data out of tracked files and issue comments.
- **FR-012**: The process MUST report each remaining blocker, with its cause, on issue #4822.
- **FR-013**: The process MUST run the focused offline tests from exported trees and record the counts.
- **FR-014**: The record change MUST add files under the record folder only. It MUST NOT change a product file.
- **FR-015**: The record MUST pass the STE gate with a score of 80 or above, and the route guard tests.
- **FR-016**: The process MUST close each app session that uses a worktree before it removes that worktree or its admin directory.
- **FR-017**: The process MUST NOT widen file permissions or force-delete a locked admin directory.

### Key Entities

- **Snapshot**: The commit named by a snapshot tag under `refs/tags/recovery/4822/`. It records one pending state of one worktree.
- **Recovery branch**: One of four local branches. Each holds one recovery commit above the base commit.
- **Archive**: A private ZIP file that holds one worktree. Its SHA-256 hash identifies it.
- **Bundle**: One private Git bundle that holds the snapshots and the recovery branches.
- **Registration**: A worktree entry in the output of `git worktree list`. Each registration names one admin directory.
- **Admin directory**: A folder under `.git\worktrees\`. Git stores the metadata of one linked worktree there.
- **Blocker**: A cleanup item that prevents completion. Each blocker has a cause and a next action.
- **Remote check**: One read from GitHub or one file read in the repository. Each check has a result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nine of nine snapshot tags appear in the inventory with a commit, a parent, and a file count.
- **SC-002**: Twenty-nine of twenty-nine shared Labs files match between the two Labs snapshots.
- **SC-003**: Nine of nine private archives match their SHA-256 manifest entries.
- **SC-004**: Zero branches or tags are deleted without a merge proof or a verified recovery copy.
- **SC-005**: Zero private paths appear in tracked files or in the issue report.
- **SC-006**: The remote check count is equal in `STATUS.json`, `design/research.md`, and the summary.
- **SC-007**: Each remaining blocker appears in the issue report with its cause.

## Assumptions

- The owner keeps the private recovery store complete and readable.
- The owner-reported archive counts remain unverified until TST-006 and TST-007 pass.
- The two Windows admin directories unlock after their app sessions close.
- The main branch receives new commits during this issue. Each check records the commit it read.
- This issue changes no product behavior.

## Out of Scope

- Completing the work of issues #2746, #2977, #4504, #4590, #4624, or #4631.
- Rebasing a recovery branch onto current main.
- Deleting unrelated local branches or their worktrees.
- Changing `requirements.txt` or `uv.lock`, or fixing the bootstrap failure that the owner reported.
- Restoring `.specify/feature.json` from any snapshot.
