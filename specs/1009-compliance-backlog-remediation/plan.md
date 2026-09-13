# Implementation Plan: Serial Sub-A Compliance Backlog Remediation

**Branch**: `1009-compliance-backlog-remediation` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/1009-compliance-backlog-remediation/spec.md`

## Summary

Bring every file in `data/compliance_backlog.tsv` (99 sub-A files at authoring time) up to grade A (>=94.0) or better, one file per PR, in strict `total`-descending order, using the already-validated per-file refactor pattern established across the five prior refactors on this branch's ancestry (d0428cc, c69c4bd, 86cf887, 7bc97ba, 912fa74). The initiative terminates when both the last backlog file merges at >=A and the overall recursive score reported by `py -m tools.compliance_analyzer src -r` is also >=A/94.0.

**Technical approach**: This is a serial refactor initiative, not a new feature build. There is no new runtime code, no new API surface, and no new dependency. The work product is a sequence of ~99 (or fewer, after transitive rank drift) squash-merged remediation PRs whose only cross-cutting artifact is the refreshed `data/compliance_backlog.tsv` used to pick the next file. Each PR follows an identical shape: baseline scan, helper-extraction + `# WHY:` inline comments, verification scan, local gate sweep (ruff / black / mypy strict / targeted pytest), then push and merge only after the full CI gate matrix (Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, E2E smoke) is green. After every 5 merged PRs the backlog TSV is regenerated so the next pick reflects transitive gains.

The rank-1 slot is currently blocked by an untracked file (`src\mist_ideas_analyzer\__init__.py`, 129 KB, F/54.0, 45 issues). Its keep/commit/delete provenance MUST be decided before any refactor PR is opened for it (FR-015 / SC-008).

## Technical Context

**Language/Version**: Python 3.13+ (repo-wide constraint from constitution).
**Primary Dependencies**: None new. Existing tool matrix: `tools.compliance_analyzer` (repo-local scorer, authoritative for grading), `ruff`, `black`, `mypy --strict`, `pylint`, `pytest`, `bandit`, `vulture`, `pydocstyle`, `interrogate`, `pip-audit`, `radon`, CodeQL (in CI), E2E smoke (in CI).
**Storage**: N/A for runtime. Backlog artifact is `data/compliance_backlog.tsv` (TSV, 100 lines incl. header). `data/` is gitignored, so the TSV is a local-only pick queue -- reproducibility is guaranteed by the analyzer + split-parser, not by committing the file.
**Testing**: Existing pytest suite. Per file, a targeted `pytest tests/<matching-tests>` runs locally before push; full suite runs in CI. No new tests are added by remediation unless a file has zero coverage on a refactored helper and the analyzer flags it as a compliance issue.
**Target Platform**: Windows 11 dev host (primary), Linux container (deploy). Bash shell for tool invocation. `py` launcher used consistently.
**Project Type**: Single-project Python CLI (MistHelper). Structure already in place; no new packages or modules are created by this initiative.
**Performance Goals**: N/A. Refactors MUST be behavior-preserving; no runtime performance target moves. The only "throughput" metric that matters is PR-per-day cadence, which is not a spec-level goal.
**Constraints**:
- One file per PR (FR-003). No cross-file refactors.
- No behavior change, no API change, no dead-code removal beyond what an explicit compliance issue calls out (Out of Scope, spec).
- No new `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, `# pragma: no cover` (FR-010 / SC-006).
- 120-char line limit; Black + Ruff both green (FR-013).
- Inline `# WHY:` comment coverage >=80% on every remediated file (FR-012 / SC-007).
- Merge command: `gh pr merge <n> --squash --delete-branch --admin`, only after every gate is green (FR-008).
- Merges are strictly serial; the next PR is not opened until the previous is squash-merged (FR-004).
**Scale/Scope**: 99 files at authoring time. Expected effective PR count is lower due to transitive lift when shared helpers are extracted. The refresh-every-5-merges cadence is the mechanism that captures that lift.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applicability | Status |
|-----------|---------------|--------|
| I. Five-Item Rule | Direct target of the initiative -- the analyzer flags STRUCT-* issues for files that violate max-5 blocks, max-25 lines, max-5 params, etc. Each remediation PR resolves violations by helper extraction. | PASS -- this initiative *exists* to enforce the Five-Item Rule across the backlog. |
| II. Class-Based Architecture | Refactors MUST keep code inside its existing class or package; helper extraction MAY create module-private helpers but MUST NOT introduce standalone wrappers around class methods. | PASS -- convention codified in the per-file recipe (Phase 1). |
| III. Safety-First | No `input()`/`safe_input()` changes are in scope; destructive operations are untouched. | PASS -- Out of Scope covers behavior changes. |
| IV. Full Deployment Pipeline | Applies at merge time. Every merged PR triggers the container-build workflow; the standard pipeline (validate -> commit -> push -> CI -> pull -> restart -> verify) is unchanged. | PASS -- reused as-is; no per-file deviation. |
| V. Observability & Logging | Refactors that touch a function without action-logging MUST add before/after `logging.info` / `logging.debug` per Constitution VII when the analyzer flags the omission. Refactors MUST NOT strip existing logging. | PASS -- covered by inline-comment + WHY: rules in Phase 1. |
| VI. Inline Comments (NON-NEGOTIABLE) | Direct target. Every remediated file MUST reach >=80% inline `# WHY:` coverage (FR-012). | PASS -- enforced by the analyzer and by the per-file recipe. |
| VII. Action Logging (NON-NEGOTIABLE) | See V above. Any function touched by helper extraction MUST retain (or gain) `logging.info` before / `logging.debug` after. | PASS -- per-file recipe includes this step. |

No constitutional violations identified. **Complexity Tracking is empty (no justifications required).**

## Project Structure

### Documentation (this feature)

```text
specs/1009-compliance-backlog-remediation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (entities: BacklogRow, RemediationPR, ComplianceScan)
├── quickstart.md        # Phase 1 output (operator runbook for the per-file loop)
├── contracts/           # Phase 1 output
│   ├── per-file-pr.md         # Contract for the shape of every remediation PR
│   ├── backlog-refresh.md     # Contract for the refresh-every-5-merges cadence
│   └── done-definition.md     # Contract for "when is a file done"
├── checklists/          # (existing)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

No new source paths are introduced by this initiative. The remediation loop operates on the existing tree:

```text
src/
├── mist_ideas_analyzer/        # rank-1 target; provenance gate (FR-015)
├── site/                       # rank 2 (site_config_manager.py)
├── analytics/                  # rank 3 (zone_analyzer.py)
├── inventory/                  # rank 4 (csv_comparator.py)
├── device/                     # rank 5 (prompt_utils.py)
├── gateway/                    # rank 6 (template_config.py)
├── reports/                    # rank 7 (e911_bssid.py)
├── maps/                       # ranks 8, 9, ...
└── ...                         # 90 more files distributed across existing packages

tools/
└── compliance_analyzer/        # existing scorer -- treated as fixed input

data/                            # gitignored; local-only backlog artifact lives here
└── compliance_backlog.tsv       # regenerated after every 5 merges

tests/                           # existing pytest tree; targeted files run per-file
```

**Structure Decision**: Single-project layout, unchanged. This initiative does not add packages, modules, or top-level directories. The only per-PR artifact under version control is the diff on the one file being remediated; the backlog TSV under `data/` is local-only and is not shipped with any PR.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No Constitution Check violations. This table is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | (n/a)      | (n/a)                                |
