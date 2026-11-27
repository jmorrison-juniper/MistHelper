# Feature Specification: Stranded branch pull request coverage

**Record folder**: `4818-stranded-branch-pr-coverage`
**Record branch**: `docs/4818-stranded-branch-pr-coverage`
**Created**: 2026-11-26
**Status**: Draft
**Input**: Issue 4818, `chore(git): a branch holds work with no pull request`.

## Clarifications

### Session 2026-11-26

- Q: Does issue 4818 name one branch? A: No. The issue body lists 54 branches. The replica of the report names 537 stranded branches on 2026-11-26. The scope is the live report at each batch start (D-1, RC-049, RC-055).
- Q: What protects a branch from the report? A: An open pull request protects it. A closed or merged pull request protects it when the closed head holds every branch commit (RC-043, RC-044).
- Q: Can the report close issue 4818? A: Not as written. The title query finds no open tracker (RC-053). The owner closes issue 4818 (D-7).
- Q: Does the record pull request close issue 4818? A: No. The record pull request uses `Refs #4818` (D-8).
- Q: Does this issue delete any branch? A: No (D-11).
- Q: Does this issue change a workflow? A: No (D-9).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep each stranded branch reachable (Priority: P1)

A maintainer opens one draft pull request for each branch that the report names. The draft keeps the branch head after a later cleanup.

**Why this priority**: The replica names 537 branches, and each branch has one copy. A cleanup can remove the only copy of the work.

**Independent Test**: Open one draft pull request for one pilot branch. Its head commit equals the branch head before the pull request opens. The replica no longer names the branch.

**Acceptance Scenarios**:

1. **Given** a stranded branch with head H, **When** the maintainer opens a draft pull request, **Then** the pull request head equals H.
2. **Given** an open draft pull request for a branch, **When** the replica runs, **Then** the replica does not name that branch as stranded.

### User Story 2 - Pilot the rollout before the full volume (Priority: P1)

An operator opens five draft pull requests first. The operator measures the gate issues before any batch starts.

**Why this priority**: Each draft starts a full Quality Gates run on a shared public repository (RC-018, RC-050).

**Independent Test**: The tracker issue holds one pilot comment. The comment lists five pull request numbers, five head commits, and the count of new gate issues.

**Acceptance Scenarios**:

1. **Given** five pilot pull requests, **When** their check runs complete, **Then** the tracker issue holds one pilot comment with each number and head.
2. **Given** a branch ref that moved after its pull request opened, **When** the stop rule runs, **Then** the rollout stops before the first batch.

### User Story 3 - Approve the volume before the batches start (Priority: P1)

The owner approves the full rollout after the pilot. No batch starts before the approval.

**Why this priority**: The full rollout creates 537 pull requests and their CI runs.

**Independent Test**: The tracker issue holds an owner approval comment before the first batch comment.

**Acceptance Scenarios**:

1. **Given** a completed pilot, **When** the owner has not approved the volume, **Then** no batch pull request opens.

### User Story 4 - Keep one tracker until the report is clean (Priority: P2)

The owner keeps issue 4818 open until the replica names no stranded branch. The owner then closes issue 4818 and the four duplicate trackers.

**Why this priority**: Five open trackers with one title hide the current state of the report.

**Independent Test**: After closure, no open issue carries the report title.

**Acceptance Scenarios**:

1. **Given** the replica names no stranded branch, **When** the owner closes the trackers, **Then** each closing comment names issue 4818.

### User Story 5 - Record the follow-up defects in their own repositories (Priority: P3)

The record names each defect in the report tooling. Each defect gets an issue in the repository that owns it. This repository changes no workflow.

**Why this priority**: The tracker defect and the pin drift affect every future report. Their owners sit outside this record.

**Independent Test**: The record names two follow-up items. Each item cites its evidence row.

**Acceptance Scenarios**:

1. **Given** the record, **When** a reader checks the follow-up list, **Then** each item names its repository and its evidence row.

### Edge Cases

- A branch head moves after its pull request opens. The stop rule halts the rollout. The owner reviews the new head.
- The report names a branch younger than seven days. The replica counts it as quiet. The branch joins a batch after it ages.
- A branch equals `main` or lies behind `main`. The report does not name it. No pull request opens for it.
- An open pull request already names a branch. Skip that branch.
- A closed pull request already holds the head. The report does not name the branch. Skip that branch.
- Two branches share one head commit. Each branch still needs its own pull request (RC-109, RC-110).
- GitHub returns a secondary rate-limit response. Wait 60 seconds. Retry up to three times. Then stop and record the failure.
- A pilot check run fails. The draft still keeps the head. Record the failure. Do not merge the draft.
- A retry creates a duplicate pull request. Close the duplicate with a comment that names the kept pull request.
- A compare call returns HTTP 404 for a name. Stop and inspect the name. The report lists such a name as unknown.
- The owner names a local-only branch. Do not push that branch (FR-015).

Warning: Deleting a branch without a pull request removes its only copy. The rollout deletes no branch (FR-004).

Caution: A duplicate tracker stays open until the owner closes it. The report does not close it.

### Functional Requirements

- **FR-001**: The rollout MUST use the live report output as its scope at the start of each batch.
- **FR-002**: The rollout MUST create one draft pull request for each named branch, with the existing branch head.
- **FR-003**: Each pull request that this issue creates MUST use `Refs #4818` and no closing keyword.
- **FR-004**: The rollout MUST NOT delete, rewrite, or force push any branch, tag, or commit.
- **FR-005**: The rollout MUST NOT merge, approve, or add the auto-merge label to any preservation pull request.
- **FR-006**: The rollout MUST start with a pilot of five pull requests. The rollout MUST stop when the stop rule applies.
- **FR-007**: Each batch MUST finish its check runs before the next batch starts.
- **FR-008**: The rollout MUST stay under the documented content-creation limits. The rollout MUST wait and retry after a secondary rate-limit response.
- **FR-009**: Each pull request title MUST use a Conventional Commits form that the title check accepts.
- **FR-010**: The rollout MUST post one new ledger comment for each pilot and batch on the tracker issue.
- **FR-011**: The tracker issue MUST stay open until the replica names no stranded branch.
- **FR-012**: The owner MUST close each duplicate tracker after authorization. Each closing comment MUST name issue 4818.
- **FR-013**: The record change MUST pass the Markdown gate, the process folder guard, the route guard, and the changelog guard.
- **FR-014**: After the rollout, the report MUST print the clean message and exit with status 0.
- **FR-015**: The rollout MUST NOT push a local-only branch to the remote.
- **FR-016**: This issue MUST NOT change a workflow, a guard test, a dependency pin, or a reusable workflow.
- **FR-017**: Each defect in the report tooling MUST have its own issue in the repository that owns the tooling.
- **FR-018**: The record change MUST add one changelog fragment.
- **FR-019**: The rollout MUST process branches in order of the oldest head commit first.
- **FR-020**: The rollout MUST NOT start the first batch until the owner approves the volume.

### Mist Cloud Transport Requirements

Not applicable. The record makes no Mist Cloud request and uses no mistapi function.

### Key Entities

- **Stranded branch**: A remote branch that the report names. Natural key: the branch name.
- **Preservation pull request**: A draft pull request whose head is one stranded branch head. Natural key: the pull request number.
- **Pilot**: The first five preservation pull requests and their measurement comment.
- **Batch**: A group of up to ten stranded branches that the rollout processes together.
- **Tracker issue**: Issue 4818, or one duplicate issue with the report title.
- **Ledger comment**: One new comment on issue 4818 for each pilot or batch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the rollout, the report prints the clean message and exits with status 0.
- **SC-002**: Every branch in the pre-rollout scope has one preservation pull request with the same head commit.
- **SC-003**: The remote branch count after the rollout equals or exceeds the count before the rollout. No branch is deleted.
- **SC-004**: No preservation pull request body contains a closing keyword for issue 4818.
- **SC-005**: The pilot comment states the count of new gate issues before batch one starts.
- **SC-006**: The ledger comments name a total pull request count that equals the scope count.

## Out of Scope

- Branch deletion, force push, branch rewrite, and tag creation.
- Merge, approval, or closure of any preservation pull request.
- Review of branch content and reconciliation with `main`. The owner campaign owns that work.
- Changes to workflows, guard tests, dependency pins, and reusable workflows.
- Local-only branches, including the two private-corpus branches that the owner excluded.
- Changes to the owner bundles and the archive branches.

## Assumptions

- The installed report version 0.6.4 implements the rule in `documentation/contributing.md` (RC-023, RC-045).
- The repository stays public, so standard runners cost no minutes (RC-006, RC-050).
- The implementing account can open pull requests in `jmorrison-juniper/MistHelper`.
- The live report output is the scope of truth. The snapshots in research.md are context only.
- The owner closes the tracker issue and the duplicate trackers after the report is clean.
