# Data Model: Stranded Branch Preservation

## Entities

### BranchRow

- **Natural key**: The branch name, without the `refs/heads/` prefix.
- **Fields**: `name`, `head_sha` (40 hexadecimal characters), `ahead` (integer), `behind` (integer), `report_age_days` (integer), `group` (one of H1, H2, H3, B1, B2, B3, N, or ABSENT), `pr_kept_by` (the PR number, or none), `identical_files`, `differs_files`, and `absent_files`.
- **Rule**: A row is PR-kept when `head_sha` equals the head commit of a PR. A row is unkept otherwise.
- **States**: listed, then verified, then classified, then gated, then authorized, then scanned, then published, then preserved. A row can also reach the states held or absent-proven.
- **Transition rule**: A changed `head_sha` returns the row to the classified state. The scan repeats for the new head.

### PullRequest

- **Natural key**: The PR number.
- **Fields**: `head_ref`, `head_sha`, `state` (OPEN, CLOSED, or MERGED), `is_draft`, and `labels`.
- **States**: draft, then closed without merge, or merged by squash. A closed PR keeps its head. A merged PR keeps its head too.
- **Transition rule**: No step force-pushes a head. A PR whose head moves leaves the PR-kept group.

### PublicationGate

- **Natural key**: The branch name. The relation to BranchRow is one to one.
- **Fields**: `owner_authorization_comment` (the comment ID on #4302), `scan_result` (clean or finding), `scan_head_sha`, `hold_reason`, and `releaser`.
- **States**: blocked, then authorized, then scanned, then cleared. A held row stays in the held state until its releaser acts.
- **Transition rule**: A PR opens only from the cleared state, and only when `scan_head_sha` equals `head_sha`.

### Batch

- **Natural key**: The batch ID, one of H1, H2, H3, B1, B2, B3, or N.
- **Fields**: `members` (the branch names), `gate_status`, and `proof_comment` (the comment ID on #4302).
- **Membership**: The members of each batch are listed in `tasks.md`.

### ReportSnapshot

- **Natural key**: The issue number of the tracking issue.
- **Fields**: `title`, `created_at`, `state`, and `row_count`.
- **Relation**: One snapshot holds many BranchRow entries, matched by name.

### RemoteCheck

- **Natural key**: The check ID, from `RC-01` to `RC-93`.
- **Fields**: `claim`, `path`, `ref`, `blob_sha`, `result` (present, absent, partial, or stale), and `line`.
- **Rule**: The count of RemoteCheck rows equals the count of rows in `research.md`, and the count of `remote_checks` in STATUS.

## Relationships

- BranchRow has one PublicationGate.
- BranchRow belongs to one Batch.
- BranchRow may match one or more PullRequest entries, by head SHA (PR-kept) or by name (report matching).
- ReportSnapshot holds many BranchRow entries.
- RemoteCheck supports one or more BranchRow entries, or the scope.

## Counts at Verification Time

These values come from GitHub at 2026-11-26. TST-02 repeats them before each batch.

| Quantity | Value |
| - | - |
| Annotated rows in #4302 | 48 |
| Annotated rows present | 47 |
| Annotated rows absent (`fix/3417-snmp-base-oid`, kept by PR #4318) | 1 |
| Rows in report #4911 | 505 |
| PR-kept rows | 248 |
| Unkept rows | 257 |
| Distinct head commits among unkept rows | 251 |
| Unkept annotated rows | 47 |
| Unkept new rows (group N) | 210 |
| Group H1 | 3 |
| Group H2 | 6 |
| Group H3 | 3 |
| Group B1 | 11 |
| Group B2 | 23 |
| Group B3 | 1 |

Group N splits into 188 archive rows and 22 other rows. The 22 other rows are named in `analysis.md`.

## Keys and Identifiers

- Branch rows use the branch name as the key. The branch name appears once in a batch.
- PR rows use the PR number as the key.
- Batch rows use the batch ID as the key.
- Remote checks use the RC ID as the key.
- Decisions use the D ID as the key, from D-1 to D-17.
