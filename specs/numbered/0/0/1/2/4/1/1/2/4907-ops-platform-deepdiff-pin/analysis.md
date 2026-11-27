# Specification Analysis Report: Ops Platform Deepdiff Pin

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/contracts/pin-guard-output.md`, the constitution, `AGENTS.md`, and `.github/copilot-instructions.md`, all read at remote `main` head `f03c6c9`.

**Method**: A read-only pass built the requirement inventory, the task coverage map, and the remote evidence map. The pass checked each claim against the remote blob or commit that holds it. No file in the repository changed.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| F1 | Coverage gap | HIGH | `tests/guardrails/test_dependency_export.py` lines 98 to 120 and `.github/workflows/ci.yml` lines 634 to 650 | The job `Dependency lock and exports` passed on PR #4889. It checks exports against `uv.lock` and does not check ops pins against declared constraints. | FR-001 to FR-003 and T003 add the check to the same job. |
| F2 | Stale comment | LOW | `.github/workflows/ci.yml` line 1135 | The ops job comment says the gate runs 300 tests. Line 119 says 398 tests are collected, and line 121 sets the floor at 390. | Out of scope. Track it in the separate remediation issue. |
| F3 | Stale rationale | MEDIUM | `mist-ops-platform/pyproject.toml` line 31 | The comment cites PyO3 and Python 3.15 for the cap. The release notes quoted in PR #4889 say cachebox 6.1.2 and later ship cp315 wheels. | The constraint stays. Research U-1 records the question. |
| F4 | Unknown origin | MEDIUM | `.github/dependabot.yml`, rows 20 and 21 of research | PR #4889 changes `mist-ops-platform/requirements.txt`. The Dependabot policy has no `/mist-ops-platform` stream, and the base commit `00d9a16e` has none either. | No configuration change (D-3). Research U-2 records the open question. |
| F5 | Rule conflict | MEDIUM | `.specify/memory/constitution.md` line 409 and `changelog.d/README.md` line 58 | The constitution requires one fragment for each change. The README exempts internal-only changes. | D-4 adds the fragment. The constitution supersedes practice documents (line 529). |
| F6 | Rule conflict | MEDIUM | `.github/copilot-instructions.md` line 533 and D-3 | The instructions say not to close update pull requests. D-3 closes PR #4889 after the merge. | The rule sits in the pull request title section. This record limits it to title remedies. The closing comment keeps the work. Caution in T-MERGE. |
| F7 | Pipeline conflict | MEDIUM | `.specify/memory/constitution.md` lines 145 and 175, and `.github/workflows/container-build.yml` lines 6 to 19 | The constitution says the full pipeline MUST run after any code change. The image build has path filters, and no path of this change matches them. | D-5 records the result. Research U-6 asks the owner to confirm it. |
| F8 | Five-Item Rule | MEDIUM | `tests/guardrails` (research row 39) | The folder holds 79 direct children, which is a grandfathered violation. A new file would add a child to it. | D-2 edits an existing file instead. The separate remediation action tracks the folder. |
| F9 | Coupling | LOW | `tests/guardrails/test_pr_title_workflow.py` lines 295 and 299 (research row 21) | The test pins the full Dependabot policy and asserts exactly three streams. Any stream change needs a test change in the same commit. | D-3 avoids a configuration change. |
| F10 | Provenance | LOW | `fd94cfcb` in the issue body (research rows 40 and 41) | The issue names `fd94cfcb`. The run head is `9d464066`. | The spec gives each SHA its role. Research U-7 records the inference about the merge commit. |
| F11 | Capacity | LOW | `tests/guardrails/test_dependency_export.py` line 98 (research row 23) | `TestDependencyExport` has four methods, so the new method uses the last slot. | Future guard tests need a compliant package. The separate remediation action covers this. |

## Coverage Summary

| Requirement | Task | Test or check | Notes |
|-------------|------|---------------|-------|
| FR-001 | T003 | The new method compares each pin with its declared constraint | Reads both files with `DependencyExport.read_export`. |
| FR-002 | T003 | The new method asserts that the defect list equals `deepdiff` for the synthetic copy | Negative proof. |
| FR-003 | T003 | The new method asserts that the examined count is at least one | Prevents a silent pass. |
| FR-004 | T003 | The printed summary line | Read in T-REMOTE-CI through `-s`. |
| FR-005 | T-LOCAL-GATES, T-PR | `tests/guardrails/test_ci_gate_triggers.py` and `tests/guardrails/test_pr_title_workflow.py` pass, and the diff against `origin/main` lists only the file map paths | The existing guards hold the workflow and Dependabot values. |
| FR-006 | T004 | `tests/guardrails/test_changelog_fragment_policy.py` | The policy guard reads `changelog.d`. |
| FR-007 | T-MERGE | `gh pr view 4889 --json state,mergedAt` as a read-only state check | Expected `CLOSED` and `null`. No code test can observe a GitHub merge state. |

## Consistency Checks

- The spec holds 7 functional requirements. `STATUS.json` reports 7.
- The tasks hold 8 entries. `STATUS.json` reports 8.
- The decisions hold 6 entries, and none needs a human decision. `STATUS.json` reports 6.
- The research remote table and `STATUS.json` each hold 44 rows, and `summary.md` reports 44.
- Every task names an exact path, an acceptance statement, and a verification command.
- Every constitution rule in `plan.md` carries a result and a reason.

## Unresolved Items

- U-1: The cachebox Python 3.15 status. Research row 43 and the release-notes quote in PR #4889 disagree in detail.
- U-2: The update stream that opened PR #4889. No stream on main covers `/mist-ops-platform`.
- U-3: Whether Dependabot reopens a 9.x pull request. No Dependabot command was read.
- U-4: The runtime effect of deepdiff 9.2.1 on `DiffService`. No test run was allowed.
- U-5: The result of `uv lock --check` on the change pull request. CI runs the check.
- U-6: Whether constitution Principle IV steps 10 to 12 apply to a change with no image path.
- U-7: Whether GitHub builds `fd94cfcb` as the merge commit of the pull request event.

## Result

No blocking defect remains in the plan. The rule conflicts F5 to F7 have decisions and recorded causes. The open items U-1 to U-7 do not block the change. The change keeps the current pins and leaves the 9.x decision to the owner.
