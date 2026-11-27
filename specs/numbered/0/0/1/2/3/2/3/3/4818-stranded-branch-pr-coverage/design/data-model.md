# Data Model: Stranded branch pull request coverage

This model holds the entities of the rollout. Each entity has a natural key. The state transitions show how an entity moves during the rollout. The system of record is GitHub. No local database holds these entities.

## StrandedBranch

- **Natural key**: The branch name, such as `fix/3158-wip-controls` (RC-059).
- **Attributes**: Head commit (40 hexadecimal characters), commits above `main`, commits behind `main`, status from the compare call, last commit date, age in days, and class.
- **Class values**: `stranded`, `quiet`, `not-ahead`, `protected-open`, `protected-closed`, `ignored-prefix`, or `unreadable` (research.md R2).
- **Rule**: A branch is `stranded` when it holds commits above `main`. It has no open pull request head and no bot prefix. It is at least seven days old. No closed pull request holds its head (RC-040 to RC-044).
- **Count at the snapshot**: 537 `stranded` branches, 54 of them named in the issue body (RC-049, RC-055).

## PreservationPullRequest

- **Natural key**: The pull request number. The head branch name is a second key. Each head branch has at most one preservation pull request.
- **Attributes**: Title, body, base `main`, head branch, head commit, draft state, labels, and state (`OPEN`, `CLOSED`, or `MERGED`).
- **Constraints**: Draft on creation. Labels `chore` and `ci` only. Body contains `Refs #4818` and no closing keyword. Head commit equals the branch head at creation (contracts\preservation-pull-request.md).
- **Relationship**: One `StrandedBranch` has one `PreservationPullRequest` after its rollout batch completes.

## Pilot

- **Natural key**: The ordinal `pilot`.
- **Attributes**: Five pull request numbers, five head commits, the gate issue count before and after the pilot, and the stop-rule result.
- **Relationship**: The pilot holds five `PreservationPullRequest` rows. The pilot precedes the owner approval.

## Batch

- **Natural key**: The ordinal `batch-NN`, where `NN` counts from `01`.
- **Attributes**: Up to ten `StrandedBranch` names in oldest-head order, the pull request numbers created, and the check run state at the end of the batch.
- **Constraint**: A batch starts after the previous batch completes its check runs (FR-007).

## TrackerIssue

- **Natural key**: The issue number. Issue 4818 is the canonical tracker.
- **Attributes**: Title, state (`OPEN` or `CLOSED`), and labels.
- **Duplicates**: Issues 4302, 4583, 4719, and 4911 carry the same title (RC-052). Each duplicate closes after issue 4818 names the closure (FR-012).

## LedgerComment

- **Natural key**: The comment identifier that GitHub assigns.
- **Attributes**: The batch or pilot ordinal, the pull request numbers, the head commits, and the count of new gate issues.
- **Constraint**: A ledger comment is new. The rollout never edits a previous ledger comment (FR-010).

## QualityGateIssue

- **Natural key**: The issue number.
- **Attributes**: Title with the gate name and the pull request number, labels, and state.
- **Count at the snapshot**: 18 open issues (RC-051).

## State Transitions

### StrandedBranch

```text
quiet (age under 7 days) -> stranded (age 7 days or more, no protection)
stranded -> protected-open (preservation pull request opens)
protected-open -> protected-closed (owner closes the pull request with a preservation comment)
protected-open -> merged-pull-request (owner merges the pull request. This issue does not merge it)
stranded -> not-ahead (the branch head equals or falls behind main)
```

- The rollout moves a branch from `stranded` to `protected-open` only.
- No transition removes a branch (FR-004).

### PreservationPullRequest

```text
(none) -> draft OPEN (created by the rollout)
draft OPEN -> closed CLOSED (owner closes with a preservation comment, not in this issue)
draft OPEN -> merged MERGED (not in this issue. FR-005 forbids it)
```

### TrackerIssue

```text
OPEN -> CLOSED (owner closes after the report exits with status 0 and authorization)
```

### Batch

```text
pending -> running (pull requests created)
running -> complete (check runs finished, ledger comment posted)
running -> stopped (stop rule fired or retries failed)
```

## Relationships

- `StrandedBranch` 1 to 0..1 `PreservationPullRequest`. A branch with one open or closed pull request leaves the stranded class.
- `Batch` 1 to 0..10 `StrandedBranch`.
- `Pilot` 1 to 5 `PreservationPullRequest`.
- `TrackerIssue` 1 to many `LedgerComment`.
- `PreservationPullRequest` 1 to many `QualityGateIssue`, because a pull request can open several gate issues.
