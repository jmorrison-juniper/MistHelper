# Contract: Recovery Register

## Columns

| Column | Rule |
| - | - |
| id | The letter `U`, a hyphen, and three digits, starting at `U-001`. This is the natural key. |
| item | One sentence that names the risk. |
| evidence | The research row, the comment ID, or the command that shows the risk. |
| severity | `warning` for an irreversible loss, `caution` for a recoverable loss, or `note` for no loss. |
| status | One of `open`, `partial`, `accepted`, or `resolved`. |
| owner | The account or role that closes the item. |
| close_condition | The observable state that closes the item. |
| next_action | The next step that moves the item toward closure. |

## Rules

- Each row holds one owner and one close condition.
- A resolved row keeps its evidence. The row does not disappear.
- A row changes status only when its evidence changes.

## Rows (2026-11-26)

| id | item | evidence | severity | status | owner | close_condition | next_action |
| - | - | - | - | - | - | - | - |
| U-001 | Three cited local commits, `7d16297d`, `3cf37c7c`, and `d8900984`, are absent from GitHub and from the primary object store. | Research R-07, R-08, R-09, and L-06. | warning | open | `jmorrison-juniper` | The owner locates each commit in the private backup or another clone, or the owner records that no unique work remains. | Owner review. Do not rebuild the commits. |
| U-002 | 322 local heads have no origin counterpart. The primary disk and the owner backup hold them, and the owner accepted the same-disk risk. | Research L-04. Comment IC_kwDOQltU8c8AAAABeBAB8Q, dated 2026-10-21. | caution | accepted | `jmorrison-juniper` | The owner records a last successful remote backup time, and independent storage exists. | Owner monitors the remote backup. |
| U-003 | Five modified entries are uncommitted in the primary checkout. | Research L-07. | caution | open | The owner of each file, as recorded in UV-03. | Each file has a preserved copy from task T007, and the owner records a decision for each file. | Task T007 creates the copies. |
| U-004 | 325 local heads are not merged into main, and each needs a recorded disposition. | Research L-04. | note | open | Each branch owner, as recorded in UV-03. | The owner records one disposition decision for each unmerged head. | Owner review. This record merges nothing. |
| U-005 | 33 worktree admin entries have an unknown status. | Research L-08 and UV-09. | note | open | `jmorrison-juniper` | The owner confirms each entry as live or stale. No entry is deleted under this issue. | Owner review. |
| U-006 | The owner backup figures cannot be checked from the repository. | Research UV-01. Comment IC_kwDOQltU8c8AAAABc1wR8A. | caution | partial | `jmorrison-juniper` | The owner posts the `git bundle verify` and `git bundle list-heads` results on issue 4277, without bundle content. | Owner posts the results. |
| U-007 | Issue 4707, an export completeness defect, is open. This record does not repair it. | Research L-20. | note | open | `jmorrison-juniper` | Issue 4707 closes, or the owner records that it is outside issue 4277. | Owner review. |
| U-008 | Baseline validation results for the recorded main commit are not recorded. | Tasks T009 to T012. | caution | open | The implementer. | Validation rows V-09, V-10, and V-11 hold results in `design\contracts\validation-report.md`. | The implementer runs tasks T009 to T012. |
| U-009 | PR 4404 has no review entries on GitHub. Issue 4280 requires human review before merge for the repaired class. | Research L-13 and UV-08. | note | open | `jmorrison-juniper` | The owner records a review decision on issue 4280, or the owner accepts the merge as the review. | Owner review. |
