# Feature Specification: Repository Sync Branch Preservation

**Feature Branch**: `docs/3969-repository-sync-branch-preservation`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #3969, "[Corviknight] Repository sync - 2026-10-06T08:29Z". A bot sync report stopped on an ownership collision. It names branches, worktrees, and pull requests that the owner must verify and preserve.

## Clarifications

### Session 2026-11-26

- Q: Does this record change branches, tags, or pull requests now? A: No. This record defines the checks, the preservation tags, and the deletion gates. The author role is read-only. The owner or an approved writer runs the tasks.
- Q: Which namespace holds the preservation tags? A: `archive/preservation/`. The repository already uses this namespace for earlier preservation tags. Each new tag starts with `archive/preservation/3969-`.
- Q: Are the counts in the sync report current? A: No. Each count changed after 2026-10-06. The table "Report claims against current state" in design/research.md lists each claim and its current result.
- Q: Does a branch name prove that its commits reached main? A: No. Names repeat across pull requests. The name `fix/2746-fm-http-status` matches merged pull request #3077 and closed pull request #3956. Its local tip equals the head of #3956, so the name alone misleads.
- Q: Who holds the write claim? A: One writer at a time. The writer comments the claim on issue #3969 before any write.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve unique commits before deletion (Priority: P1)

The owner needs each local commit that GitHub does not hold to survive cleanup. The writer creates a preservation tag at the tip of each such branch. The writer deletes the local branch only after the tag resolves to that tip.

**Why this priority**: A deleted branch with unique commits can remove the only copy of that work. Preservation prevents the loss.

**Independent Test**: For each class C and class D branch, the preservation tag resolves to the branch tip before deletion. The check changes no other ref.

**Acceptance Scenarios**:

1. **Given** a class D branch with unique commits, **When** the writer pushes its preservation tag, **Then** GitHub shows the tag at the branch tip.
2. **Given** a preservation tag name that already exists, **When** the writer creates the tag, **Then** the writer stops and records the conflict. The writer does not force the tag.

### User Story 2 - Confirm each sync report claim (Priority: P1)

The owner needs a current result for each claim in the sync report. Several report counts and pull request states are stale. The record shows each current result with its evidence.

**Why this priority**: The owner decides cleanup from the report. A stale count causes a wrong decision.

**Independent Test**: Each row of the remote verification table in design/research.md repeats with the same result, or the row records the change.

**Acceptance Scenarios**:

1. **Given** the 14 pull requests that the report names, **When** the owner reads their states, **Then** each pull request shows merged or closed.
2. **Given** the 23 branch names that the report names, **When** the owner checks GitHub, **Then** the record shows the presence or absence of each name.

### User Story 3 - Delete local branches only after gates pass (Priority: P2)

The writer deletes a local branch only after its class gate passes. Class A and class B branches need no tag. Class C and class D branches need a tag first. Class E branches need a recheck with no merge commit and one minus line. Class F branches stay.

**Why this priority**: Gated deletion removes stale local branches without loss. It reduces local clutter after the owner approves the worktree inventory.

**Independent Test**: After the gates, the local branch list shows main and the 7 class F branches only.

**Acceptance Scenarios**:

1. **Given** a class B branch whose tip equals its merged pull request head, **When** the recheck passes, **Then** the writer deletes the local branch.
2. **Given** a class E branch with a plus line, **When** the recheck runs, **Then** the writer keeps the branch and records the plus line.

### User Story 4 - Refresh the container without data loss (Priority: P3)

The owner refreshes the `misthelper` container after the claim is released. The refresh keeps both named volumes.

**Why this priority**: The volumes hold every capture and upgrade run. Warning: a removed volume cannot be recovered.

**Independent Test**: After the refresh, the volume list still shows `misthelper-arangodb-data` and `misthelper-redis-data`.

**Acceptance Scenarios**:

1. **Given** a released claim, **When** the owner runs the refresh commands, **Then** the container runs the rebuilt image and both volumes remain.

### Edge Cases

- A local branch name matches a merged pull request, but its tip differs from that pull request head. The writer tags the tip and keeps the branch until the tag check passes.
- A closed pull request head exists only as a local commit. The writer creates the tag at that commit. The writer fetches nothing to create the tag.
- A worktree uses a local branch. If git refuses the deletion, the writer stops and records the worktree path.
- GitHub returns HTTP 403 or 429 during a check. The writer waits 60 seconds and retries up to three times. The writer records the check as unverified when each retry fails.
- Warning: discarding a modified path removes edits that exist only in the working tree. Owner decision D-5 must approve each discard first.
- Warning: never use the `--tags` push option. The writer names each tag in an explicit refspec.
- Caution: deleting a local branch removes its local name. A preservation tag keeps its commits.
- Warning: removing a named volume during a container refresh destroys captures and upgrade runs. The refresh never removes a named volume.
- The sync report names a session and worktrees that this record cannot observe. The owner verifies them.

### Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The writer MUST verify each sync report claim against GitHub before any write.
- **FR-002**: The writer MUST comment one claim on issue #3969 before any write.
- **FR-003**: The writer MUST create a preservation tag at the tip of each class C and class D branch before deleting that branch.
- **FR-004**: Each preservation tag MUST start with `archive/preservation/3969-`. The writer MUST NOT force or reuse a tag name.
- **FR-005**: The writer MUST create a preservation tag at each of the five closed or unmerged pull request heads that the record names.
- **FR-006**: The writer MUST delete a class A or class B local branch only after its recheck passes.
- **FR-007**: The writer MUST delete a class E local branch only after a recheck shows no merge commit and no plus line.
- **FR-008**: The writer MUST keep each class F local branch.
- **FR-009**: The writer MUST keep each modified path unless the owner approves a discard.
- **FR-010**: The writer MUST NOT delete any local branch before the owner records the worktree inventory.
- **FR-011**: The writer MUST record the preservation proof in one comment on issue #3969.
- **FR-012**: The writer MUST record the terminal state of each of the 14 named pull requests.
- **FR-013**: The owner MUST refresh the container only after the claim is released, and the refresh MUST NOT remove a named volume.
- **FR-014**: The record MUST use the managed Spec Kit route, with five children or fewer in each directory.
- **FR-015**: Each Markdown file in the record MUST score 80 or above in the STE gate.
- **FR-016**: The record MUST list each unverified item with its reason.

### Key Entities

- **Local branch**: A ref under refs/heads in this clone. Its natural key is the branch name. Its tip is one commit.
- **GitHub branch**: A ref under refs/heads on GitHub. Its natural key is the branch name.
- **Pull request**: A GitHub change request. Its natural key is the pull request number. Its head is one commit.
- **Preservation tag**: A lightweight tag under archive/preservation. Its natural key is the tag name. It points to one commit.
- **Claim**: One comment on issue #3969 that names the writer.

### Mist Cloud Transport Requirements

Not applicable. This record makes no Mist Cloud request and names no mistapi method.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each class C and class D branch has a preservation tag at its tip before deletion. Target: zero exceptions.
- **SC-002**: The record shows a terminal state for each of the 14 named pull requests. Target: 14 of 14.
- **SC-003**: The record names one human decision, D-5. Target: one.
- **SC-004**: The writer discards zero modified paths without owner approval. Target: zero.
- **SC-005**: The writer records one claim on issue #3969 before the first write. Target: one claim.

## Assumptions

- The owner, `jmorrison-juniper`, reads the record and approves the writer role.
- The local clone equals GitHub main at commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca. The clone holds five modified paths, listed in design/research.md.
- The author role does not run git worktree or git branch commands. The owner runs the worktree inventory.
- Worktrees outside this clone are unverified.
- Each pull request head on GitHub equals the last commit that the pull request received.

## Out of Scope

- Runtime code changes under `src/`.
- Changes to the 7 open pull requests. None names issue #3969.
- Changes to branch protection, required checks, or repository settings.
- Discarding or committing modified paths.
- Merging or closing any pull request that this record names.
