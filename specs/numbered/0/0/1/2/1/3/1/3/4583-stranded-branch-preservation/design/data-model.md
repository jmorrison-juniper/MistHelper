# Data Model: Stranded Branch Preservation

**Purpose**: Define the entities, natural keys, and state transitions of the preservation procedure.

**Snapshot**: GitHub state read on 2026-11-26. Command Q-2 in `quickstart.md` reproduces each count.

## BranchSnapshot

- **Natural key**: Branch name. Each name is unique on origin.
- **Fields**: Head SHA (40 hexadecimal characters), ahead count, behind count, changed file count, age in whole days, lane, blocking pull request number.
- **Lane values**: `ready` or the blocking pull request number, such as `#4208`.
- **Exclusion reasons**:
  - `open-head`: An open pull request names the branch.
  - `bot-prefix`: The name starts with `dependabot/`, `gh-readonly-queue/`, or `revert-`.
  - `no-commits`: The ahead count is 0.
  - `young`: The age is below 7 days.
  - `closed-head`: A closed pull request with the same name holds the head.
- **Transitions**: `ready` to `preserving` to `preserved`. `held` to `ready` after the release check. Any state to `stale` when the head SHA differs from the snapshot.
- **Terminal state**: `preserved`, with one closed preservation pull request that names the snapshot head SHA.

## PreservationPullRequest

- **Natural key**: Head branch name plus head SHA.
- **Fields**: Number, title, draft flag, state, `mergedAt`, closing comment.
- **Transitions**: `OPEN` (draft) to `CLOSED` (unmerged). The `MERGED` state never occurs in this procedure.

## HoldRecord

- **Natural key**: Branch name.
- **Fields**: Blocking pull request number, state of that pull request at the check time, release time.
- **Transitions**: `held` to `released` when the blocking state is `CLOSED` or `MERGED`.

## WorkBatch

- **Natural key**: Batch identifier. Ready batches use `W01` to `W09`. Held groups use `H-4813`, `H-4886`, `H-4887`, `H-4888`, and `H-4208`.
- **Fields**: Lane, row count (at most 50 for a ready batch), status, start time, end time.
- **Transitions**: `pending` to `running` to `done`. `running` to `stopped` after a failed step.

## ScopeCheck

- **Natural key**: UTC time of the check plus the main SHA.
- **Fields**: In-scope count, ready count, held count, and the excluded count for each exclusion reason.

## ReportIssue

- **Natural key**: Issue number.
- **Fields**: Title, state, role.
- **Snapshot rows**: #4302, #4583, #4719, #4818, and #4911. All five are `OPEN`. Issue #4583 has the role `subject`. The other four have the role `duplicate`.

## Snapshot Counts

| Count | Value |
| - | - |
| Branches on origin, excluding `main` | 597 |
| Excluded: open pull request names the branch | 7 |
| Excluded: bot prefix | 3 |
| Excluded: no commits above `main` | 11 |
| Excluded: younger than 7 days | 28 |
| Excluded: closed pull request holds the head | 5 |
| Unreadable history | 0 |
| In scope | 543 |
| Ready | 441 |
| Held | 102 |

The exclusions and the in-scope count add up to the branch count. Seven plus 3 plus 11 plus 28 plus 5 plus 543 equals 597.

## Held Branches by Blocking Pull Request

| Blocking pull request | Held branches | State at snapshot | Draft |
| - | - | - | - |
| #4208 | 62 | `OPEN` | Yes |
| #4813 | 12 | `OPEN` | Yes |
| #4886 | 3 | `OPEN` | No |
| #4887 | 4 | `OPEN` | No |
| #4888 | 21 | `OPEN` | No |
| Total | 102 | | |

## Report Comparison

- The 2026-11-23 report in issue #4911 lists 505 rows.
- All 505 report names appear in the 543 in-scope names.
- Thirty-eight in-scope names do not appear in that report. Each has no open pull request with its name. Each holds commits above `main` by the local count. No closed pull request with the same name holds its head.
