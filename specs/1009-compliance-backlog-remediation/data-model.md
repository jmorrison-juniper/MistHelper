# Phase 1: Data Model -- Serial Sub-A Compliance Backlog Remediation

**Feature**: 1009-compliance-backlog-remediation
**Date**: 2026-07-03
**Scope**: This is a refactor initiative. There are no runtime entities, no database tables, and no API objects added by this work. The "data model" here describes the three operational entities the remediation loop reads, produces, and coordinates on.

---

## Entity 1: BacklogRow

**Source**: One row in `data/compliance_backlog.tsv`.
**Cardinality**: 99 at authoring time; refreshed after every 5 merges; drops to 0 at initiative completion.
**Storage**: TSV file, gitignored (lives under `data/`, local-only).
**Unique key**: `path` (the file's repo-relative path with backslashes preserved as authored).

### Fields

| Field    | Type            | Description                                                                       | Source                              |
|----------|-----------------|-----------------------------------------------------------------------------------|-------------------------------------|
| rank     | int             | 1-indexed ordering position after the sort rule below.                            | Computed by the split-parser.       |
| total    | int             | Total analyzer-flagged issues on this file (all severities).                      | `tools.compliance_analyzer` output. |
| critical | int             | Count of `critical` severity issues.                                              | Analyzer.                           |
| high     | int             | Count of `high` severity issues.                                                  | Analyzer.                           |
| medium   | int             | Count of `medium` severity issues.                                                | Analyzer.                           |
| low      | int             | Count of `low` severity issues.                                                   | Analyzer.                           |
| score    | float           | Per-file compliance score (0.0 - 100.0).                                          | Analyzer.                           |
| grade    | str (enum)      | One of `F, D, D+, C-, C, C+, B-, B, B+, A-, A, A+`. Sub-A means grade below `A`.  | Analyzer.                           |
| path     | str (repo-rel.) | Repo-relative path with backslash separator (as emitted by the recursive scan).   | Analyzer.                           |

### Sort rule (FR-002)

1. `total` descending.
2. Tie: `critical` descending.
3. Tie: `high` descending.
4. Tie: `score` ascending.

### State transitions

A `BacklogRow` has three possible transitions:

1. **Picked**: rank == 1 of the current refreshed backlog -> row becomes the target of the next `RemediationPR`.
2. **Skipped**: refresh shows `score >= 94.0` -> row is dropped from the backlog without consuming a PR slot (FR-016).
3. **Retired**: matching `RemediationPR` merges and post-merge scan confirms `score >= 94.0` -> row is dropped from the next-refresh backlog.

### Validation rules

- `rank` MUST be unique per refresh; ties broken by the sort rule above.
- `grade` letter and `score` band MUST agree (e.g., `A` implies `94.0 <= score < 100.0`).
- `path` MUST resolve to an existing file OR MUST be an accepted deletion decision under FR-015.

---

## Entity 2: RemediationPR

**Source**: One GitHub pull request against `main`.
**Cardinality**: Approximately 99 across the initiative, expected lower due to transitive lift.
**Storage**: GitHub (branch + PR + squash-merge commit).
**Unique key**: PR number.

### Fields

| Field        | Type      | Description                                                                                                       |
|--------------|-----------|-------------------------------------------------------------------------------------------------------------------|
| branch       | str       | `refactor/compliance-<rank>-<slug>` where `<rank>` is from the *refreshed* backlog and `<slug>` is filesystem-safe. |
| title        | str       | `refactor: <slug> compliance <old-grade>/<old-score> -> <new-grade>/<new-score>`.                                 |
| body         | str       | Text-only. Exactly `<analysis>...</analysis>` followed by `<summary>...</summary>`. No markdown headers, no code fences. |
| files_touched| list[str] | MUST contain exactly one path -- the `path` of the picked `BacklogRow`.                                          |
| pre_score    | float     | Baseline analyzer score (from `/tmp/before.md`).                                                                  |
| post_score   | float     | Post-refactor analyzer score (from `/tmp/after.md`). MUST be >=94.0.                                              |
| gates        | dict      | Map of gate name -> pass/fail. All 13 gates MUST be `pass` before merge.                                          |
| merge_cmd    | str       | Exactly `gh pr merge <n> --squash --delete-branch --admin`. `--admin` is used only when all gates are `pass`.     |

### State transitions

`draft -> opened -> gates_green -> squash_merged -> deleted_branch`

- `draft`: local branch, unpushed.
- `opened`: PR is open, at least one gate has begun.
- `gates_green`: every one of the 13 gates in the merge matrix is `pass`.
- `squash_merged`: `gh pr merge --squash --admin` succeeded.
- `deleted_branch`: `--delete-branch` cleanup succeeded.

### Validation rules

- `files_touched` MUST have length 1 (FR-003).
- `body` MUST NOT contain markdown headers (`#`, `##`, ...) or fenced code blocks (` ``` `).
- `title` MUST match the exact regex: `^refactor: [\w\-\.]+ compliance [A-F][+\-]?/[\d.]+ -> [A-F][+\-]?/[\d.]+$`.
- Diff MUST NOT introduce `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, or `# pragma: no cover` (FR-010).

---

## Entity 3: ComplianceScan

**Source**: `py -m tools.compliance_analyzer <path> [-r] -o <out> -q`.
**Cardinality**: Two scans per PR (before + after); one full-tree scan per every-5-merges refresh.
**Storage**: Ephemeral for per-file scans (`/tmp/before.md`, `/tmp/after.md`); `data/full_repo_compliance.md` for the recursive scan (gitignored).
**Unique key**: `(target_path, timestamp)`.

### Fields

| Field         | Type        | Description                                                              |
|---------------|-------------|--------------------------------------------------------------------------|
| target_path   | str         | The `<path>` argument to the analyzer.                                   |
| recursive     | bool        | True when invoked with `-r` (whole-tree); false for per-file.            |
| output_path   | str         | The `<out>` markdown file.                                               |
| overall_score | float       | Present only when `recursive=True`; the whole-repo aggregate score.      |
| per_file      | list[dict]  | List of `{path, total, critical, high, medium, low, score, grade}` rows.  |
| timestamp     | ISO 8601    | UTC timestamp when the scan completed.                                    |

### State transitions

None. `ComplianceScan` is an immutable snapshot -- it is either the input to a decision (baseline for a PR, refresh for the next pick) or it is discarded once its downstream artifact (the PR title, or the refreshed TSV) is produced.

### Validation rules

- The scan MUST be produced by a fresh invocation; cached or edited outputs MUST NOT be used.
- When used as a per-file baseline, `recursive` MUST be `False` and `target_path` MUST equal the picked `BacklogRow.path`.
- When used as the refresh input, `recursive` MUST be `True` and `target_path` MUST be `src`.

---

## Cross-entity invariants

- **I1** (FR-001, FR-003): Exactly one `BacklogRow` is `Picked` per open `RemediationPR`, and that PR's `files_touched` MUST equal `[picked.path]`.
- **I2** (FR-004): At most one `RemediationPR` is in state `opened` or `gates_green` at any moment. The next PR is not `opened` until the previous is `squash_merged`.
- **I3** (FR-014, R5): After every fifth `squash_merged` transition, a recursive `ComplianceScan` is produced and the backlog TSV is regenerated before the next pick.
- **I4** (SC-003): Any file transitioning from A+ -> below-A+ across two consecutive refresh scans becomes a `Picked` blocker before any new `BacklogRow` is picked.
- **I5** (SC-009): Every `Picked` transition MUST reference the top unresolved row of the freshly regenerated backlog -- never a stale copy.
