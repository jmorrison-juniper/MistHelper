# Contract: Branch Disposition Register

## File

- Path: `test-artifacts\4277\branch-register.tsv`. Git ignores this path through the `/test-artifacts/` rule (research R-41).
- Format: tab-separated text, UTF-8 without a byte-order mark, LF line endings, and one header row.

## Columns

| Order | Column | Rule |
| - | - | - |
| 1 | ref_name | The full ref name, `refs/heads/` followed by the branch name. This is the natural key. |
| 2 | tip_sha | The commit SHA of the local head. It has 40 lower-case hexadecimal characters. |
| 3 | origin_tip_sha | The commit SHA of the remote-tracking ref with the same branch name, or the word `absent`. |
| 4 | origin_state | One of `same-tip`, `different-tip`, or `absent`. |
| 5 | merged_into_main | `yes` when `tip_sha` is reachable from `main`, otherwise `no`. |
| 6 | disposition | One of `integrated-remote-copy`, `integrated-local-only`, `integrated-diverged`, `preserved-remote-copy`, `preserved-local-only`, or `preserved-diverged`. |
| 7 | owner_note | The owner entry from the recovery register, or the word `not-recorded`. |

## Rows

- The file holds one row for each entry under `refs/heads`.
- Rows sort by `ref_name` in ordinal order.
- The row count equals the count from `git for-each-ref refs/heads` in the same run.
- No row records a deletion, a rename, or a push.

## Checks

- The header row appears once. Each data row holds seven columns.
- Each `disposition` value follows the rule in `design\data-model.md`, section LocalHead.
- Each `origin_state` value follows from `origin_tip_sha`.
- The count of each disposition value equals the measured count in `design\research.md`, section 3, row L-04, when the repository has not changed. Otherwise the record names the new counts.

## Measured counts (2026-11-26)

- Total: 330.
- `integrated-remote-copy`: 1. `integrated-local-only`: 4. `preserved-remote-copy`: 7. `preserved-local-only`: 318.
- `integrated-diverged`: 0. `preserved-diverged`: 0.
