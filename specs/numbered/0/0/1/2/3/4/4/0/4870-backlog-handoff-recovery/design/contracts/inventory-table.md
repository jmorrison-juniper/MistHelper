# Contract: Refreshed Inventory Table

## Location

The inventory is one new GitHub comment on issue 4870. The comment title names the count and the snapshot date. Each refresh adds a new comment. No repository file holds the table (decision D-21). The handoff body links to the newest inventory comment.

## Title line

The first line reads `## Open issue inventory (N open issues, snapshot YYYY-MM-DD)`. The value N equals the open issue count from TST-03. The date is the UTC date of the check.

## Columns

| Column | Content | Rule |
| - | - | - |
| # | The issue number in the form `#NNNN` | Each open issue appears once. The number matches GitHub. |
| Title | The GitHub title | Copy the title exactly. Do not shorten it. |
| Labels | The label names separated by a comma and a space | Match the GitHub label set. Do not add a label. |
| Census category | One value from the vocabulary below | Use the value from the 2026-11-18 census. Use `not classified` for an issue opened after the census. |
| Next action | One instruction of 20 words or fewer | Name the next step and its owner. |
| State on GitHub | OPEN | Read on the snapshot date. Every row in the open table shows OPEN. |

## Census category vocabulary

- `fix-now-candidate`: the fix can start now, with a test first.
- `fix-in-progress`: a branch or a fix already exists.
- `held-reservation`: another file or branch holds the work.
- `held-staging-or-credentials`: the work waits for staging access or credentials.
- `needs-human-decision`: a human must decide before the work starts.
- `owner-decision`: the repository owner must decide the design.
- `stale-or-superseded`: a newer change covers the issue or the issue is out of date.
- `unknown`: the census lacks evidence. A reproducing log is needed first.
- `not classified`: the issue opened after the census. Triage sets a value.

## Closed issues

Closed issues that the handoff names appear in a separate table. That table has the same columns, and its State on GitHub column shows CLOSED. Issue 4867 moves to that table after its closure by PR 4871 (R-09).

## Rules

- Sort the open table by ascending issue number.
- Post a new comment for each refresh. Do not edit an older inventory comment.
- Keep each row's census category unless triage records a new value in a dated note.
- Keep the text ASCII only.
