# Specification Analysis Report: CodeQL register check fails on pull request 4888

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, and the constitution (version 1.9.0).

**Method**: A read-only pass built the requirement inventory, the task coverage map, and the remote check map. The findings below show the state after the review.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Defect | HIGH | Pull request #4888 diff of `requirements-dev.txt` line 179. `uv.lock` lines 1300-1301. | The pull request edits a file that its header says uv generates. The lock still pins `mando` 0.7.1. The export and lock guards reject the bump even when pip resolves it. | Fixed by keeping the pin at 0.7.1 (decision D-1). The change regenerates no file. |
| A2 | Defect | HIGH | `requirements-dev.txt` line 365. Installed radon metadata line 31. | Radon 6.0.1 requires `mando` below 0.8. The PyPI read lists no newer radon release. The bump cannot resolve. | Decision D-1 closes pull request #4888 unmerged. |
| A3 | Inconsistency | LOW | Issue #4904 body. Research RC-19. | The issue names merge commit `5bb4b385`, not the head commit `e86098cd`. | Recorded as a clarification. The root cause is the same. |
| A4 | Coverage gap | MEDIUM | `.github/copilot-instructions.md` lines 50-77. Research RC-28. | The local gates table has no row for the register check or its install step. | Task T004 documents the cause in `quality-gates.md`. A row in the shared table needs its own review, so it is a follow-up. |
| A5 | Coverage gap | MEDIUM | `tests/guardrails/test_dependency_lock_file.py`. | No guard fails when a pin falls outside the ceiling of a dependent package. | Task T003 adds the guard (FR-005). |
| A6 | Underspecification | MEDIUM | `tests/guardrails/test_pr_title_workflow.py` line 295. | A change to `dependabot.yml` fails the complete-policy snapshot unless the snapshot changes too. | Task T002 updates the snapshot (FR-003). |
| A7 | Process debt | MEDIUM | `changelog.d/` holds 335 children. `tests/guardrails/` holds 80 children. | Both parents exceed five children. | Existing debt. The change adds one fragment only. A separate remediation action tracks the debt. |
| A8 | Unverified | MEDIUM | Dependabot behavior on a transitive pin. Research U-1. | An ignore entry on a transitive pin is not verified by a Dependabot run. | Success criterion SC-005 checks the behavior after the merge. |
| A9 | Process | LOW | Pull request #4888 and the labels of issue 4904. | The close, the label, and the merge actions need owner authorization. | Listed as process actions in `plan.md`. Open until the orchestrator acts. |
| A10 | Cascade | LOW | Research RC-33 and RC-34. | 26 failed jobs and two Windows runs print the same resolver conflict. | The same fix addresses each job. Success criterion SC-002 checks the result. |

## Coverage Summary

| Requirement | Has task | Task IDs | Has test | Test or gate |
|-------------|----------|----------|----------|--------------|
| FR-001 | Yes | T003, T-REMOTE-CI | Yes | `test_pinned_mando_satisfies_installed_radon_requirement`, and the install step of CI |
| FR-002 | Yes | T003, T-LOCAL-GATES | Yes | `test_requirements_exports_match_the_lock`, and `test_lock_satisfies_every_requirement` |
| FR-003 | Yes | T001, T002 | Yes | `test_pip_stream_ignores_mando_minor_and_major`, and `test_complete_policy` |
| FR-004 | Yes | T006 | Yes | `test_the_name_and_independent_execution_are_stable`, and `test_the_gate_runs_exactly_the_shipped_check` |
| FR-005 | Yes | T003 | Yes | `test_radon_check_rejects_mando_0_8` |
| FR-006 | Yes | T005 | Yes | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-007 | Yes | T004, T-LOCAL-GATES | Yes | The `ste-linter` gate |

## Consistency Checks

- Requirements: 7 in `spec.md`, in `tasks.md`, and in the status file.
- Tasks: 10 in `tasks.md`, in the status file, and in the summary.
- New test cases: 3 in `tasks.md`, in `plan.md`, and in the status file.
- Remote checks: 34 rows in `design/research.md`, 34 entries in the status file, and 34 in the summary.
- Each task names exact paths and one verification command from the local gates table. T-PR uses the Compile gate, and the other tasks use the Tests or STE gates.

## Unresolved Items

- A4 and A9 remain open. Task T004 does not change the shared table. The owner authorizes the close of pull request #4888.
- Research items U-1 through U-5 remain open until the named mitigation runs.
