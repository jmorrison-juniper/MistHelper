# Contract: Branch Disposition Table

This contract defines the table that each proof comment on #4302 carries. Each batch adds one comment. Earlier comments stay unchanged.

## Comment Header

The first line names the batch, the report snapshot, and the record path. The second line gives the date of the scope check.

```text
Batch: B1. Report snapshot: #4911 (2026-11-23). Record: specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation.
Scope check: 505 rows, 248 PR-kept, 257 unkept, on 2026-11-26.
```

## Table Columns

| Column | Allowed values | Meaning |
| - | - | - |
| Branch | An exact branch name | The branch that the row describes |
| Group | H1, H2, H3, B1, B2, B3, N, or ABSENT | The batch or hold of the row |
| Head | 40 hexadecimal characters | The head commit read from GitHub |
| Ahead | Integer | Commits above `main`, from the compare API |
| Behind | Integer | Commits on `main` that the branch lacks |
| Identical | Integer | Changed files whose blob equals the `main` blob |
| Differs | Integer | Changed files whose blob differs from the `main` blob |
| Absent | Integer | Changed files that `main` does not have |
| Scan | pending, clean, or finding | The content scan of the head |
| Gate | blocked, authorized, cleared, or held | The publication state of the row |
| PR | A PR number, or none | The draft PR of the row, or the PR that keeps the head |
| Evidence | RC ID | The remote check in `design/research.md` |

## Rules

- Each row shows one branch. A PR-kept row shows the PR number in the PR column.
- A row with a finding in the Scan column shows `held` in the Gate column.
- The table holds one row for each branch in the batch. It holds no row for an unrelated branch.
- A correction appears in a new comment. The earlier comment stays as it was.

## Example Row

```text
| recovery/2708-handoff-20261004 | B2 | f195788a090d6ace8f2f320dc1f96a413876e2c4 | 1 | 490 | 1 | 0 | 0 | clean | cleared | none | RC-81 |
```

The example row shows the format only. It is not a status claim.
