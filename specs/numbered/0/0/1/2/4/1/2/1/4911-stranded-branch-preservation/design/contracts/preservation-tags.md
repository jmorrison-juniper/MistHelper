# Contract: Preservation tags and ledger

This contract defines the tag name, the tip source, the held test, the ledger columns, the batch rules, and the output lines. The procedure in `design/quickstart.md` follows this contract.

## Tag name

- The ref name is `refs/tags/preserve/<branch name>`.
- The tag is lightweight. Its target is the tip commit that GitHub reports for the branch.
- The prefix `preserve/` is fixed. A branch name may contain slashes.
- The tag name must pass `git check-ref-format`.
- A tag with the same name is never overwritten. A tag with the same name and the same target is recorded as `verified-present`. A tag with the same name and another target is recorded as `conflict`, and the procedure stops.

## Tip source

- The tip comes from `GET repos/jmorrison-juniper/MistHelper/branches` with pagination. The field is `commit.sha`.
- The tip is read in the same session as the push. The procedure pushes only the tips from that read.

## Held test

- A tip is held when `gh pr list --state all` reports a `headRefOid` that equals the tip.
- A tip that is not held is recorded with `held` set to `no`.
- The held test does not affect the tag. Every named branch receives a tag (decision D-3).

## Ledger columns

The ledger holds one row for each named branch. The columns appear in this order.

| Column | Type | Meaning |
| - | - | - |
| `row` | integer | The position in the report, from 1 to 505. |
| `branch` | text | The branch name, exactly as the report names it. |
| `tip` | commit ID | The tip read in the same session as the push. |
| `held` | `yes` or `no` | Whether a PR head commit equals the tip. |
| `pr_number` | integer or `-` | The number of the PR whose head commit equals the tip. |
| `tag` | text | The ref name `refs/tags/preserve/<branch name>`. |
| `tag_target_on_origin` | commit ID or `-` | The commit that `git ls-remote --tags` reports for the tag. |
| `result` | text | One of `verified-present`, `absent`, `conflict`, `failed`, or `rolled-back`. |

## Batch rules

- The pilot holds the first five rows of the report.
- Each later batch holds at most 50 rows, in report order.
- A batch that fails stops the procedure. The procedure retries the push up to three times, with waits of 30, 60, and 120 seconds.
- A named branch that returns a not-found error is recorded as `absent`. The procedure does not stop for that row alone.
- No batch deletes a branch or a tag.

## Output lines

The procedure prints each count as one line. The lines use this form, with ASCII characters only.

- `rows=<count> unique=<count>`
- `named_on_origin=<count>`
- `held=<count>` and `not_held=<count>`
- `invalid_names=<count>`
- `missing_branches=<count>`
- `pilot_verified=<count> of <count>`
- `tags_verified=<count> of <count>`
- `named_branches_still_present=<count> of <count>`

## Non-goals

- The contract does not define the report format of the upstream tool.
- The contract does not define the deletion of a branch. A later issue defines it.
