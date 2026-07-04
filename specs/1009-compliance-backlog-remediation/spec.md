# Feature Specification: Serial Sub-A Compliance Backlog Remediation

**Feature Branch**: `1009-compliance-backlog-remediation`
**Created**: 2026-07-03
**Status**: Draft
**Input**: User description: "Serial, most-issues-first remediation of the 99 sub-A files listed in `data/compliance_backlog.tsv`, one file per PR, following the established compliance-easy-wins conventions, until the repository reaches an overall A grade (>=94.0)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retire the highest-issue file in the backlog (Priority: P1)

As the compliance owner, I want the single file with the largest issue count in the ranked backlog to be brought to A grade (target A+) in its own PR before any lower-ranked file is touched, so that each merge delivers the largest measurable drop in the repository's outstanding-issue total.

**Why this priority**: The remediation model is a serial, highest-yield-first loop. Every merged PR reduces the ranked issue total by the largest amount available at that moment; without this guarantee the batch collapses back into ad-hoc cleanup.

**Independent Test**: Verify that after the top-ranked file's PR is squash-merged, (a) the file's re-scanned score is >= 94.0, (b) no other backlog file was modified in that PR, and (c) the file no longer appears in the sub-A list produced by re-running `py -m tools.compliance_analyzer <path> -r -o <out> -q` at the repo root.

**Acceptance Scenarios**:

1. **Given** the ranked backlog in `data/compliance_backlog.tsv` and a clean working tree on `main`, **When** the owner opens the next remediation PR, **Then** the PR touches exactly the file at rank 1 (or the next unresolved rank), on branch `refactor/compliance-<rank>-<slug>`, with title `refactor: <file> compliance <old-grade>/<old-score> -> <new-grade>/<new-score>`.
2. **Given** a merged remediation PR for a backlog file, **When** the compliance analyzer is re-run against that file, **Then** its grade is >= A (score >= 94.0) and it is absent from a regenerated sub-A list.
3. **Given** a remediation PR is under review, **When** any CI gate fails (Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, or the E2E smoke), **Then** the PR is not merged until the gate is green; `--admin` merge is used only after all gates report success.

---

### User Story 2 - Resolve the F-tier untracked file before treating it as rank 1 (Priority: P1)

As the compliance owner, I need the untracked file `src\mist_ideas_analyzer\__init__.py` (129 KB, F/54.0, 45 issues) triaged for provenance before any refactor work begins, because it is not yet part of the tracked codebase and could be experimental, generated, or unintended.

**Why this priority**: Refactoring a file whose keep/commit/delete status is undecided would either lock in unintended code or throw the work away. Provenance resolution is a prerequisite that gates the entire ordered pipeline at rank 1.

**Independent Test**: Confirm that before the rank-1 refactor PR is opened, a decision (keep-and-commit, delete, or relocate) exists in writing (issue, PR description, or spec note) and the file's git status matches that decision.

**Acceptance Scenarios**:

1. **Given** the file exists only as an untracked path, **When** provenance triage is complete, **Then** the outcome is one of: (a) committed as-is on `main` in a preparatory PR and only then refactored under rank 1, (b) deleted (with justification recorded), or (c) relocated/renamed with the rank-1 slot re-derived from the refreshed backlog.
2. **Given** the file is chosen to be kept, **When** it enters the remediation loop, **Then** it follows the same one-file-per-PR, `refactor/compliance-01-mist_ideas_analyzer` branch convention as every other file, with the initial-baseline score of F/54.0 captured in the PR title.
3. **Given** the file is chosen to be deleted, **When** the deletion PR merges, **Then** rank 1 is reassigned to the next file by the ordering rule after a backlog refresh.

---

### User Story 3 - Refresh the ranked backlog between PRs (Priority: P2)

As the compliance owner, after every merged remediation PR I want the ranked backlog regenerated from a fresh recursive scan so that transitive gains (a shared utility being cleaned lifts every caller's score) reorder the queue before the next file is picked.

**Why this priority**: Rank drift is the single most likely source of wasted work. A file that was rank 12 may drop to rank 40 after an upstream cleanup; picking by stale rank spends effort where the yield is no longer highest.

**Independent Test**: After a merged PR, re-run the recursive analyzer, regenerate `data/compliance_backlog.tsv`, and confirm the next PR targets the top unresolved row in the refreshed file (not the stale one).

**Acceptance Scenarios**:

1. **Given** a remediation PR has just merged, **When** the next file is chosen, **Then** the choice is made from a backlog regenerated after that merge, not from a cached copy.
2. **Given** a refreshed backlog, **When** two rows tie on `total`, **Then** the tie is broken by (a) `critical` desc, (b) `high` desc, (c) `score` asc.
3. **Given** the refresh reveals a file has already crossed >= A/94.0 through transitive effects, **When** the next pick is computed, **Then** that file is skipped and does not consume a PR slot.

---

### User Story 4 - Reach and maintain a whole-repository A grade (Priority: P2)

As the compliance owner, once every file in the backlog is at >= A/94.0, I want the overall repository score reported by the recursive analyzer to be >= A/94.0, and I want a mechanism to catch any regression on files that were already A+ before this initiative started.

**Why this priority**: The per-file target is necessary but not sufficient; the repository-level metric is what stakeholders read. Regressions on already-A+ files would silently undo prior wins.

**Independent Test**: Run `py -m tools.compliance_analyzer src -r -o out.md -q` after the final backlog file merges and confirm the summary reports >= A/94.0 and no file previously at A+ has dropped below A+.

**Acceptance Scenarios**:

1. **Given** the last backlog file's PR has merged, **When** a full recursive scan is run against the repository, **Then** the overall grade is >= A/94.0 and the sub-A file list is empty.
2. **Given** any merged remediation PR, **When** the recursive scan runs against previously A+ files, **Then** none has dropped below A+.
3. **Given** a regression is detected on a previously A+ file, **When** the next PR is opened, **Then** that regression is treated as a blocker and repaired before any new backlog rank is picked.

---

### Edge Cases

- **F-tier untracked file at rank 1** — see User Story 2; do not refactor until provenance is decided.
- **Rank drift during a long-running PR** — if a PR sits open long enough that a refreshed scan moves its file out of the top slot, the PR is still completed and merged (the work is not wasted); the drift is absorbed on the next pick.
- **File deleted or renamed by an unrelated PR** — the remediation loop skips the missing path, regenerates the backlog, and picks from the refreshed list.
- **A file cannot reach A+ without a behavior change** — the target is relaxed to A (>= 94.0); the deviation from A+ is recorded in the PR body's `<analysis>` block. Behavior changes are out of scope (see below).
- **A remediation PR uncovers a genuine bug** — the bug fix is split into its own PR; the compliance PR must remain behavior-preserving.
- **CI gate is flaky, not failing on merit** — the merge is held; flake diagnosis and remediation happen outside this workflow. `--admin` never bypasses a red gate.
- **Suppressions requested by reviewer** — any new `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, or `# pragma: no cover` is rejected; the underlying issue must be resolved instead.
- **Inline comment coverage below 80%** — the PR is not merged until same-line `# WHY:` anchor comments raise coverage to >= 80%.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The remediation queue MUST be the exact set of files listed in `data/compliance_backlog.tsv` (99 files at authoring time; count refreshed on each rescan).
- **FR-002**: Ordering MUST be strictly by the `total` column descending; ties MUST be broken by (a) `critical` desc, (b) `high` desc, (c) `score` asc.
- **FR-003**: Exactly one backlog file MUST be modified per PR. No PR is permitted to touch two backlog files simultaneously.
- **FR-004**: Work MUST proceed serially: a PR MUST be squash-merged before the next PR is opened.
- **FR-005**: Each PR's branch name MUST follow `refactor/compliance-<rank>-<slug>`, where `<rank>` is the file's current rank in the refreshed backlog and `<slug>` is a filesystem-safe short form of the file's stem.
- **FR-006**: Each PR's title MUST follow `refactor: <file> compliance <old-grade>/<old-score> -> <new-grade>/<new-score>`, with the old values taken from the pre-refactor scan and the new values from the post-refactor scan.
- **FR-007**: Each PR body MUST be text-only, consisting of an `<analysis>...</analysis>` block followed by a `<summary>...</summary>` block, with no markdown headers and no code fences.
- **FR-008**: Merges MUST use `gh pr merge <n> --squash --delete-branch --admin` and MUST NOT occur while any CI gate is red.
- **FR-009**: Every listed CI gate MUST pass green before merge: Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, and the E2E smoke.
- **FR-010**: No new `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, or `# pragma: no cover` suppressions MAY be introduced by a remediation PR.
- **FR-011**: Each file MUST reach the target grade of A+ (100.0) where feasible; the minimum acceptable grade is A (>= 94.0).
- **FR-012**: Same-line `# WHY:` anchor comments MUST be used to reach an inline comment coverage of >= 80% on every remediated file.
- **FR-013**: The 120-character line limit MUST hold; Black and Ruff MUST both pass on the modified file.
- **FR-014**: After each merge, the backlog TSV MUST be regenerated via `py -m tools.compliance_analyzer <root> -r -o <out> -q` and re-ranked before the next file is picked.
- **FR-015**: The rank-1 file `src\mist_ideas_analyzer\__init__.py` MUST have its keep/commit/delete provenance decided (and the working tree brought into agreement with that decision) BEFORE any remediation PR is opened for it.
- **FR-016**: Any file whose refreshed grade has already crossed >= A/94.0 through transitive effects MUST be skipped on the next pick and not consume a PR slot.
- **FR-017**: A file previously at A+ that drops below A+ during this initiative MUST be repaired in its own remediation PR before the next backlog rank is picked.
- **FR-018**: The initiative MUST terminate only when (a) every file in the refreshed backlog is >= A/94.0 and (b) the overall recursive score reported by the analyzer is >= A/94.0.
- **FR-019**: Where the analyzer or a CI gate flags an issue that could be resolved only by changing behavior, the change MUST be deferred to a separate non-remediation PR and the compliance PR MUST leave the behavior intact (see Out of Scope).
- **FR-020**: The ordering, ranking, and success criteria MUST be reproducible from `data/compliance_backlog.tsv` alone; no ad-hoc reshuffling of the queue is permitted.

### Key Entities

- **Backlog Row** — one line in `data/compliance_backlog.tsv`; fields: `rank`, `total`, `critical`, `high`, `medium`, `low`, `score`, `grade`, `path`. Unique key: `path`.
- **Remediation PR** — one GitHub pull request targeting `main`; scope: one Backlog Row's `path`; artifacts: branch, title, text-only body, squash merge commit.
- **Compliance Scan** — output of `py -m tools.compliance_analyzer <path> -r -o <out> -q`; produces per-file scores/grades and an overall repository score/grade.
- **Rank-1 F-Tier File** — `src\mist_ideas_analyzer\__init__.py`; currently untracked, 129 KB, F/54.0, 45 issues; provenance gate for the whole initiative.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every file listed in `data/compliance_backlog.tsv` reaches score >= 94.0 (grade A or better) on a recursive rescan.
- **SC-002**: The overall repository score reported by `py -m tools.compliance_analyzer src -r -o <out> -q` is >= 94.0 (grade A or better).
- **SC-003**: No file that was at A+ (100.0) at the start of this initiative is below A+ at the end of it.
- **SC-004**: 100% of remediation PRs merged during this initiative touch exactly one backlog file.
- **SC-005**: 100% of remediation PRs merged during this initiative pass every listed CI gate (Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, E2E smoke) prior to merge.
- **SC-006**: 0 new suppressions of the form `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, or `# pragma: no cover` are introduced by remediation PRs.
- **SC-007**: Inline comment coverage on every remediated file is >= 80% at merge time.
- **SC-008**: The rank-1 F-tier file's provenance decision (keep-and-commit, delete, or relocate) is recorded before any refactor PR is opened for it.
- **SC-009**: The picked file on every iteration matches the top unresolved row of the freshly regenerated backlog (i.e., zero picks are made from a stale backlog).

## Out of Scope

- Any behavior change, API surface change, output format change, or observable-side-effect change that is not strictly required to lift a compliance issue.
- Dead-code removal that is not itself the compliance issue being resolved (removing dead code that the analyzer does not flag is deferred to a separate initiative).
- Adding, removing, or reordering public modules, classes, or functions outside what a single compliance issue requires.
- Test rewrites that change assertions; tests may only be edited to accommodate mechanical refactors (renames, formatting) with equivalent semantics.
- Dependency upgrades, pip-audit fixes that require version bumps, or CI configuration changes unless a specific compliance issue demands them.
- Rewriting the `data/compliance_backlog.tsv` schema or the analyzer's output; both are treated as fixed inputs to this initiative.
- Any parallelization of remediation PRs; work is strictly serial.

## Assumptions

- The recursive analyzer (`py -m tools.compliance_analyzer`) is authoritative for grading and remains stable in output format for the duration of this initiative.
- `data/compliance_backlog.tsv` at authoring time correctly reflects the 99 sub-A files; the pipeline refreshes it after every merge.
- The existing CI gates (Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, E2E smoke) are the complete list of merge blockers; any additional gate added later is folded in automatically without needing a spec update.
- `gh` CLI and repository admin privileges are available so `gh pr merge <n> --squash --delete-branch --admin` can complete once gates are green.
- The compliance-easy-wins convention set (branch name, title format, text-only PR body, `# WHY:` anchor comments, 80% inline comment coverage, 120-char lines, no new suppressions) is unchanged and remains the correctness bar for every PR in this initiative.
- Transitive gains from cleaning up a shared module can lift multiple callers' scores; the refresh-after-merge step is the mechanism that captures this.
- The rank-1 F-tier file's provenance decision is made outside the compliance analyzer's control loop by a human reviewer.

## Risks

- **Transitive rank drift** — cleaning a shared module can move many downstream files off the sub-A list, which is good but requires strict adherence to the refresh-then-pick rule to avoid wasted PRs on stale ranks.
- **F-tier file provenance ambiguity** — the untracked `src\mist_ideas_analyzer\__init__.py` may need product/owner review; if that decision is delayed, the whole ordered pipeline stalls at rank 1.
- **mypy strict / Ruff regressions from restructuring** — moving code to reduce complexity or comment density can introduce type or lint regressions elsewhere; the CI gates catch these but each incident adds turnaround time.
- **PR review fatigue** — 99 sequential PRs is a large review load; reviewer bandwidth or consistency may degrade, risking silent acceptance of subpar remediations. Mitigation belongs to the plan phase, not this spec.
- **Analyzer instability** — a change in the compliance analyzer's scoring during the initiative would invalidate ranks in-flight; treated as out-of-band and handled by re-baselining if it occurs.
- **Behavior-preservation slips** — a refactor may inadvertently change behavior; mitigation is scope discipline (one file, no behavior changes) plus the E2E smoke gate.
- **Suppression pressure** — reviewers may propose adding `# noqa` or `# type: ignore` to close a stubborn issue; this is explicitly forbidden by FR-010 and SC-006.
