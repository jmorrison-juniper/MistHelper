# Data Model: Stranded branch preservation

This model describes the records that the procedure reads and writes. The procedure writes no database. The durable records are git refs on origin and the ledger rows in the tracking issue.

## NamedBranch

One row of the report in issue 4911. The report date is 2026-11-23.

- **Natural key**: `name`, the branch name. Each name appears once in the report.
- **Fields**: `name` (text), `tip` (commit ID), `commits_ahead` (integer from the report), `age_days` (integer from the report), `held` (yes or no), `preservation_tag` (text `preserve/<name>`).
- **States**:
  - `reported`: the row exists in the report and the name exists on origin.
  - `preserved`: the tag `preserve/<name>` exists on origin and points to the tip.
  - `absent`: the branch no longer exists when its batch runs. No tag is created.
  - `conflict`: a tag with the same name exists and points to another commit. The procedure stops.
  - `deletion_eligible`: the tag exists and a later issue approves deletion. This state is outside the change.
- **Transitions**: `reported` to `preserved` after a verified push. `reported` to `absent` when the branch is missing. `reported` to `conflict` when a tag points to another commit.

## Tip

The commit at the end of a named branch.

- **Natural key**: the 40-character commit ID.
- **Fields**: `commit_id`, `commits_ahead_of_main` (integer from a local `git rev-list origin/main..TIP`).
- **Relations**: one tip can serve several named branches. Each named branch has one tip at a time.

## PullRequestHead

A pull request record, read from `gh pr list --state all`.

- **Natural key**: `pr_number`.
- **Fields**: `pr_number` (integer), `state` (OPEN, CLOSED, or MERGED), `head_name` (`headRefName`), `head_commit` (`headRefOid`), `closed_at` (timestamp), `merged_at` (timestamp or empty).
- **Relations**: a tip is held when a PullRequestHead has the same `head_commit`.

## PreservationTag

A lightweight tag on origin.

- **Natural key**: the ref name `refs/tags/preserve/<branch name>`.
- **Fields**: `ref_name` (text), `target_commit` (the tip), `remote_commit` (the commit read by `git ls-remote`), `status` (`absent`, `pushed`, `verified`, `conflict`, or `rolled-back`).
- **Transitions**: `absent` to `pushed` after a push that exits with 0. `pushed` to `verified` when `remote_commit` equals `target_commit`. `pushed` to `rolled-back` when the rollback command deletes the tag. `absent` to `conflict` when a tag with the same name exists with another commit.

## Batch

A group of tag refspecs pushed in one command.

- **Natural key**: `batch_index`. Index 1 is the pilot with 5 rows. Indexes 2 to 11 hold 50 rows each.
- **Fields**: `batch_index` (integer), `row_count` (integer, at most 50), `push_exit_code` (integer), `verified_count` (integer).
- **Transitions**: `pending` to `pushed` when the push exits with 0. `pending` to `failed` when the push exits with another code. `failed` to `pushed` after a retry, at most three retries. `failed` to `stopped` after the third retry.

## LedgerRow

One result line for each named branch. The ledger is the tracking issue comment.

- **Natural key**: `branch`.
- **Fields**:
  - `row`: integer from 1 to 505.
  - `branch`: text, the branch name.
  - `tip`: commit ID.
  - `held`: yes or no.
  - `pr_number`: integer, or `-` when no PR holds the tip.
  - `tag`: text, the ref `preserve/<name>`.
  - `tag_target_on_origin`: commit ID, or `-` when no tag exists.
  - `result`: `verified-present`, `absent`, `conflict`, `failed`, or `rolled-back`.

## TrackingIssue

An issue that carries the report.

- **Natural key**: the issue number.
- **States**: `open-tracker` for issue 4911. `closed-duplicate` for issues 4302, 4583, 4719, and 4818 after the link comment.
- **Invariant**: one issue with the report title stays open after the duplicate handling.

## ReportSnapshot

The report table as of its date.

- **Natural key**: the report date and the issue number. The date is 2026-11-23 and the issue number is 4911.
- **Fields**: `row_count` (505), `commits_total` (1,616), `age_min_days` (7), `age_max_days` (65), `rows_30_days_or_more` (274).

## Relationships

- NamedBranch to Tip: many to one.
- Tip to PullRequestHead: a tip is held when the commit IDs are equal. The relation has no stored key.
- NamedBranch to PreservationTag: one to one.
- Batch to PreservationTag: one to many.
- LedgerRow to NamedBranch: one to one.
- ReportSnapshot to NamedBranch: one to many.

## Not applicable

The change adds no database table, no API schema, and no code entity.
