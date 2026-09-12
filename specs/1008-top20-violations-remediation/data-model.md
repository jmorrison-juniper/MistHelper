# Phase 1 Data Model: Top-20 Compliance Violations Remediation

**Feature**: Top-20 Compliance Violations Remediation
**Note**: This initiative is a refactor campaign, not a runtime system. The "data
model" describes the workflow entities materialized as GitHub artifacts and repo
artifacts. There is no database schema, no persistent state.

## Entities

### TargetFile

One of the twenty source files being remediated.

| Field | Type | Notes |
|-------|------|-------|
| `rank` | int (1-20) | Rank in the worst-first order. Immutable; taken from `compliance_report.md` on 2026-07-02. |
| `path` | str (repo-relative) | Canonical repo-relative path, forward slashes. |
| `baseline_grade` | str (`F`/`D-`/`D`/`C` in this campaign) | Grade at baseline. |
| `baseline_score` | float | Score 0.0-100.0 at baseline. |
| `baseline_violations` | dict[Severity, int] | `{critical, high, medium, low}` counts. |
| `baseline_total` | int | Sum of all severities. |
| `post_grade` | str | Grade after remediation; MUST be `A+`. |
| `post_score` | float | Score after remediation; MUST be >=95.0. |
| `pr_number` | int \| None | The PR that landed the remediation (null until open). |
| `merge_sha` | str \| None | Squash-merge commit SHA on `main` (null until merged). |
| `extracted_helpers` | list[str] | Names of new modules or classes created during decomposition (may be empty). |

**Validation rules**:
- `post_score >= 95.0` (FR-001).
- `post_grade == "A+"` (FR-001).
- `path` MUST match exactly one of the twenty paths listed in `spec.md`.
- `rank` MUST be unique across all target files.
- `pr_number` MUST become non-null before `merge_sha` becomes non-null.

**State transitions**:
```
NEW  ->  BRANCHED  ->  PR_OPEN  ->  CI_GREEN  ->  MERGED
                 ^--- (may return to BRANCHED if CI fails / review blocks)
```
- `NEW`: baseline captured; no branch yet.
- `BRANCHED`: `refactor/compliance-<rank>-<slug>` created from `main`.
- `PR_OPEN`: PR opened; body contains pre-analyzer output.
- `CI_GREEN`: all 234+ required CI checks pass; post-analyzer output added to PR body.
- `MERGED`: squash-merged to `main`; `merge_sha` recorded.

### RemediationPR

One pull request whose scope is exactly one `TargetFile`'s compliance remediation.

| Field | Type | Notes |
|-------|------|-------|
| `number` | int | GitHub PR number. |
| `target_file_rank` | int (1-20) | Foreign key to `TargetFile.rank`. Exactly one. |
| `branch` | str | `refactor/compliance-<rank>-<slug>` per plan branch-naming rule. |
| `title` | str | `refactor: <file-slug> compliance <old-grade>/<old-score> -> A+/<new-score>` |
| `body_pre_analyzer` | str | Output of `python -m tools.compliance_analyzer <path>` before refactor. |
| `body_post_analyzer` | str | Output of `python -m tools.compliance_analyzer <path>` after refactor. |
| `body_structural_summary` | str | Prose description: which helpers extracted, which module boundaries moved. |
| `required_checks_status` | dict[str, str] | All 234+ required-check names -> `pass`/`fail`/`pending`. |
| `merge_method` | str | Always `squash`. |
| `merged_at` | ISO 8601 datetime \| None | Set on merge. |

**Validation rules**:
- `target_file_rank` MUST reference the currently-active target file in the worst-first
  queue (i.e., the previous rank must already be `MERGED` before this PR opens).
- `body_pre_analyzer` and `body_post_analyzer` MUST both be present (FR-009).
- Every entry in `required_checks_status` MUST equal `pass` before merge (FR-010,
  SC-005).
- Diff MUST NOT contain any of the forbidden suppression markers (FR-004, SC-003):
  `# noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint: disable`, `# ruff: noqa`,
  `# mypy: ignore`, `# flake8: noqa`, `# nosec`.
- Diff MUST NOT touch `tools/compliance_analyzer/scoring.py`,
  `tools/compliance_analyzer/models.py`, `tools/compliance_analyzer/analyzers.py`,
  `tools/check_compliance.py`, or any related config file (FR-005, SC-004).

### Violation

A single guideline violation as emitted by `tools/compliance_analyzer` (source of truth:
`tools/compliance_analyzer/models.py::Violation`).

| Field | Type | Notes |
|-------|------|-------|
| `rule_id` | str | Stable identifier, e.g., `STRUCT-PARAMS`, `ARCH-DELEGATE`, `LOG-LAZY`. |
| `category` | str | Human-readable grouping, e.g., `Architecture`, `Complexity`, `Comments`. |
| `severity` | enum (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) | Drives scoring weight. |
| `line` | int (1-based) | Line number where the issue begins. |
| `symbol` | str | Enclosing function/class name. |
| `message` | str | What is wrong and why. |
| `remediation` | str | Concrete suggested fix (seeds task description in Phase 2). |

**Scoring reference** (from `tools/compliance_analyzer/scoring.py` and `models.py`):
- `CRITICAL` = 10 points penalty per violation
- `HIGH` = 6 points per violation
- `MEDIUM` = 3 points per violation
- `LOW` = 1 point per violation
- `CATEGORY_PENALTY_CAP` = 20 (no single category can cost more than 20 points)
- Grade thresholds (worst-to-best): F, D-, D, D+, C-, C, C+, B-, B, B+, A-, A, A+
- `A+` requires score >= 97.0
- To land at >=95.0 (bar for this initiative), remaining post-refactor penalty must be
  <=5.0 across all categories combined.

### AnalyzerRun

One invocation of `python -m tools.compliance_analyzer <path>` on a target file. Not
persisted; captured only in PR body text.

| Field | Type | Notes |
|-------|------|-------|
| `path` | str | Which file was analyzed. |
| `timestamp_utc` | ISO 8601 | Wall-clock at run time. |
| `analyzer_commit` | str | Git SHA of `tools/compliance_analyzer/` at run time. |
| `score` | float | Result score 0.0-100.0. |
| `grade` | str | Result letter grade. |
| `violations` | list[Violation] | Every violation found. |

### RequiredCICheck

One of the 234+ status checks the `main` branch protection requires green before merge.

| Field | Type | Notes |
|-------|------|-------|
| `name` | str | The check's display name in GitHub. |
| `status` | str | `pass`/`fail`/`pending`/`skipped` on a given PR. |
| `run_url` | str | Link to the CI run. |

**Validation rule**: `status == "pass"` for every required check before `RemediationPR`
transitions to `MERGED` (FR-010, SC-005). `skipped` is not a merge-allowing state on any
required check.

## Relationships

```text
TargetFile 1 -------- 1 RemediationPR
                          |
                          | 1
                          v
                        many
                     AnalyzerRun     (>=2 per PR: one pre, one post)
                          |
                          | 1
                          v
                        many
                       Violation     (0 in the post-refactor run for A+ score)

RemediationPR 1 -------- 1..* RequiredCICheck
```

## Invariants

1. Exactly 20 `TargetFile` records exist. No file added or removed during the
   initiative (FR-002).
2. Exactly 20 `RemediationPR` records exist at completion, one per `TargetFile`
   (FR-002).
3. Sequential merge: for any two `RemediationPR`s A and B where
   `A.target_file_rank < B.target_file_rank`, `A.merged_at < B.merged_at` (FR-003).
4. Zero forbidden suppressions across all 20 merged diffs (SC-003).
5. Zero changes to `tools/compliance_analyzer/scoring.py` and related configs across
   the initiative (SC-004).
6. Every `TargetFile.post_score >= 95.0` and `post_grade == "A+"` after its PR merges
   (SC-001).
