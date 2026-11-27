# Feature Specification: Preserve Repository Versions and Update the Local Main Checkout

**Feature Branch**: `chore/4277-preserve-repository-versions` (planned)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4277, "chore: preserve repository versions and update the local main checkout."

## Clarifications

### Session 2026-11-26

- Q: Does the pull request close issue 4277 when it merges? A: No. The owner requires the issue to stay open. The pull request uses `Refs #4277` (research D-2).
- Q: Is the primary checkout still behind GitHub main? A: No. The primary checkout and `origin/main` both name the commit `f03c6c9b` (research L-01).
- Q: Is the backup stored away from the working disk? A: No. The owner accepted same-disk storage on 2026-10-21. The recovery window is 24 hours (research D-5).
- Q: Does merged PR 4404 close the issue 4280 condition? A: Yes, for the repaired method. GitHub main checks the HTTP status at lines 159 to 162. Three local privacy commits remain absent (research R-07 to R-09, recovery item U-001).
- Q: May this work merge an unmerged feature branch into main? A: No. The owner keeps active work with its owner. This work records dispositions only.
- Q: May this work delete a branch, tag, stash, preserved ref, or worktree? A: No. The issue forbids deletion. The register records each item.
- Q: May this work push a local-only ref or a backup to GitHub? A: No. The repository is public (research D-4).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm the remote and local state (Priority: P1)

An owner reads the record. The record states the GitHub main head, the primary checkout state, and the merge state of PR 4404. Each value has a remote or local source.

**Why this priority**: The owner must trust the evidence before any other step.

**Independent Test**: Run verification tests V-01, V-02, and V-03. Each result equals the value in the record.

**Acceptance Scenarios**:

1. **Given** the record names `f03c6c9b` as GitHub main, **When** V-01 runs, **Then** the GitHub main head equals `f03c6c9b`, or the record names the new head.
2. **Given** the primary checkout and `origin/main`, **When** V-02 runs, **Then** both commit counts are zero.
3. **Given** PR 4404, **When** V-03 runs, **Then** the pull request is merged and its merge commit is an ancestor of GitHub main.

---

### User Story 2 - Read the branch dispositions (Priority: P1)

An owner reads a register of every local head. Each row has one disposition. The row count equals the local head count.

**Why this priority**: The issue requires branch dispositions before any later branch work.

**Independent Test**: Run V-06 and V-08.

**Acceptance Scenarios**:

1. **Given** the local heads, **When** V-06 runs, **Then** the register holds one row for each head, and each row has one disposition.
2. **Given** the counts before the work, **When** V-08 runs, **Then** each count equals the count before the work.

---

### User Story 3 - Validate the clean baseline (Priority: P2)

A maintainer runs the baseline gates in a detached worktree at `f03c6c9b`. The maintainer records each result and removes the worktree.

**Why this priority**: The issue requires validation results on a clean current baseline.

**Independent Test**: Run V-09, V-10, V-11, and V-14.

**Acceptance Scenarios**:

1. **Given** the baseline worktree, **When** V-09 runs, **Then** the compile, lint, format, and type gates exit with code 0.
2. **Given** the baseline worktree, **When** V-10 runs, **Then** each full test shard reports zero failures.
3. **Given** the validation results, **When** V-14 runs, **Then** the baseline worktree folder is absent.

---

### User Story 4 - Track the unresolved recovery work (Priority: P1)

An owner reads each open recovery item. Each item names an owner and a close condition.

**Why this priority**: The issue requires unresolved recovery work to stay visible.

**Independent Test**: Run V-13.

**Acceptance Scenarios**:

1. **Given** the recovery register, **When** V-13 runs, **Then** each row has a severity, an owner, and a close condition.

---

### User Story 5 - Keep the change small (Priority: P2)

A reviewer reads the pull request. The diff holds only record files. The closing reference and the label change follow the decisions.

**Why this priority**: A small diff limits review risk.

**Independent Test**: Run V-12 and V-15.

**Acceptance Scenarios**:

1. **Given** the pull request, **When** V-15 runs, **Then** each changed file lies under the record path.
2. **Given** the record folder, **When** V-12 runs, **Then** the process folder guard test passes.

---

### Edge Cases

- A cited commit is absent from GitHub. The record marks it absent. The record does not infer its content from merged code.
- The primary checkout falls behind GitHub main. Preserve each uncommitted change first. Then run `git merge --ff-only` against `origin/main`.
- Local main and `origin/main` differ. Record both SHAs. Do not reset either ref.
- GitHub returns HTTP 403 or 429. Wait 60 seconds. Retry up to three times. Then record the check as unverified.
- The baseline worktree fails to bootstrap. Record the cause. Do not run tests in the primary checkout.
- A local head has no origin counterpart. Its disposition is `preserved-local-only`. Do not push it.
- A ref count changes during the work. Record the change and stop before any further step.

Warning: a disk failure removes the primary checkout and its same-disk backup together.

Warning: a push of a local-only ref publishes private work in a public repository.

Warning: `git worktree remove --force` deletes the uncommitted files of a worktree. Check the path before you run it.

Caution: `git merge --ff-only` stops when a fast-forward is not possible. Review the stop message before any retry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST state the GitHub main head and the commit that the baseline names.
- **FR-002**: The record MUST state that the primary checkout equals `origin/main` with zero commits ahead and zero behind.
- **FR-003**: The record MUST state the merge status of PR 4404 and the closed state of issue 4280.
- **FR-004**: The record MUST mark each cited commit as present or absent, with its check source.
- **FR-005**: The record MUST report the owner backup evidence as owner-reported. It MUST state the same-disk storage and the 24-hour window.
- **FR-006**: The register MUST give exactly one disposition to each local head.
- **FR-007**: The implementer MUST preserve each uncommitted change in a git-ignored location before any update.
- **FR-008**: The implementer MUST NOT delete a branch, tag, stash, preserved ref, or worktree.
- **FR-009**: The implementer MUST run the static baseline gates in an isolated worktree at the recorded main commit.
- **FR-010**: The implementer MUST run both full test shards on the isolated baseline and record each summary line.
- **FR-011**: The implementer MUST run the safe sweep on the isolated baseline and record its exit code.
- **FR-012**: Each new directory MUST hold five children or fewer. The record MUST use the managed numbered route.
- **FR-013**: The recovery register MUST list each unresolved item with a severity, an owner, and a close condition.
- **FR-014**: The implementer MUST remove the isolated baseline worktree after validation.
- **FR-015**: The pull request MUST change only files under the record path. It MUST use `Refs #4277`.

### Key Entities

- **Local head**: A branch under `refs/heads`. Its natural key is the full ref name.
- **Cited commit**: A commit named by an issue or a pull request. Its natural key is the full 40-character SHA.
- **Recovery item**: An open risk or condition. Its natural key is an identifier from U-001 onward.
- **Validation run**: One check of the record or the baseline. Its natural key is an identifier from V-01 onward.

### Mist Cloud Transport Requirements

Not applicable: this record makes no Mist Cloud REST or WebSocket request. It measures Git and GitHub state only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The primary checkout and `origin/main` show one identical commit, with zero commits ahead and zero behind.
- **SC-002**: The register holds one row for each local head counted at run time. At measurement, the count was 330.
- **SC-003**: Branch, tag, stash, preserved-ref, and worktree counts match before and after the work.
- **SC-004**: Each baseline gate exits with code 0, or the record gives the cause.
- **SC-005**: Each recovery item names one owner and one close condition.
- **SC-006**: The pull request diff lists only files under the record path.

## Assumptions

- The owner comments on issue 4277 state past actions accurately.
- The owner backup is on the same physical disk. A remote backup runs every 24 hours.
- GitHub main is the remote source of truth. Local refs are evidence only.
- The repository is public. Publication of private refs or backups is prohibited.
- The implementer runs PowerShell and Git on the same Windows host as this measurement.

## Out of Scope

- Deletion or archive of any branch, tag, stash, worktree, or preserved ref.
- Merge of any divergent feature branch into main.
- Creation of a new backup, or reading of the owner backup contents.
- Repair of issue 4707, the export completeness defect.
- Mist Cloud operations and any production change.
- Publication of private backups, checkpoint objects, credentials, or customer data.
- Change of any label, except the scope label change in research D-9.
