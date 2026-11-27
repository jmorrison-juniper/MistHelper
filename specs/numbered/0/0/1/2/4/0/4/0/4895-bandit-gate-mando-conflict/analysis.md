# Specification Analysis Report: Bandit Gate Dependency Conflict

## Findings

| ID | Finding | Evidence | Action |
| - | - | - | - |
| A-1 | PR #4888 changes one pin and leaves the lock stale. | The PR file list shows one changed file, `requirements-dev.txt`. `uv.lock` line 1301 still pins `mando` 0.7.1. | Close PR #4888 after the fix merges (T-MERGE). |
| A-2 | The Bandit job stopped before Bandit ran. Its result is unknown. | Steps 6 and 7 show `skipped` in run 45064243269, job 137336719159. `AGENTS.md` lines 306 to 309 require reading `skipped` as unknown. | Record the result as unknown. Confirm it on the fix head (T-REMOTE-CI). |
| A-3 | The issue cites a test-merge commit, not the PR head. | `commits/5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71` returns the message `Merge e86098cdc2b189d217805b3b4060ef609cbc37af into 00d9a16e998b0cb5e10b6ed77da0fa909670d64f`. | Use the head SHA in the record. The sync workflow owner should review the commit text (U-3). |
| A-4 | One cause opened 15 gate issues. | Issues 4891 to 4905 each name PR #4888 in the title. | Leave closure to the bot after the next `main` run (D-9). |
| A-5 | Dependabot has no ignore rule for a constrained package. | `.github/dependabot.yml` lines 3 to 11 contain no `ignore` key in the pip stream. | Add the ignore rule (T004). |
| A-6 | The constitution expects a container build after merge, but the workflow does not start. | Constitution lines 166 and 167 require the wait. `container-build.yml` lines 6 to 19 omit `requirements-dev.txt` and `.github/dependabot.yml`. | Record the run as not started (D-6). |
| A-7 | `tests/guardrails` already exceeds the five-item limit. | 77 files and 3 folders exist. Constitution lines 42 and 43 forbid a new direct child under a noncompliant parent. | Add cases to existing files only (D-4). Remediation is a separate action. |
| A-8 | The complete Dependabot snapshot test blocks a partial policy change. | `tests/guardrails/test_pr_title_workflow.py` line 295 compares the complete policy with the snapshot. | Add the same ignore entry to the snapshot (T003). |
| A-9 | One evidence call sent a POST request by mistake. Two GET calls failed. | One `gh api` call used `-f ref=main`, which sends a POST request. GitHub returned HTTP 404, and no change occurred. Two decode calls failed on PowerShell interpolation and returned HTTP 404 on GET requests. | Use GET query strings only. Record each call in `design/research.md` as process notes (P-1, P-2). |

## Coverage Summary

| Requirement | Task | Test |
| - | - | - |
| FR-001 | T001 | `tests/guardrails/test_dependency_export.py` |
| FR-002 | T002 | `test_pinned_mando_satisfies_installed_radon` |
| FR-003 | T002 | `test_radon_boundary_rejects_mando_0_8_2` |
| FR-004 | T004 | `tests/guardrails/test_pr_title_workflow.py` |
| FR-005 | T003 | `tests/guardrails/test_pr_title_workflow.py` |
| FR-006 | T005 | `python -m pytest tests/guardrails` |
| FR-007 | T002 and T-MERGE | `test_pinned_mando_satisfies_installed_radon` on the PR #4888 head content |
| FR-008 | T005 and T-LOCAL-GATES | `python -m pytest tests/guardrails` |
| FR-009 | T-LOCAL-GATES | `bandit -c pyproject.toml -r . -q` |

Success criteria map as follows. SC-001 maps to T-REMOTE-CI. SC-002 maps to T002 on the PR head content. SC-003 and SC-004 map to T-MERGE. SC-005 maps to T006 and to the self-review.

## Constrained-Field Coverage

Not applicable. The change adds no data field.

## Constitution Alignment

Principles I to VII pass. Principle IV has one recorded deviation, which finding A-6 describes. No principle requires a complexity exception beyond the grandfathered debt in `plan.md`.

## Unmapped Tasks

None. Each task maps to at least one requirement or success criterion.

## Metrics

- Requirements: 9 (FR-001 to FR-009).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 10 (T001 to T006, plus four final tasks).
- Tests planned: 3 (two new test functions and one updated snapshot test).
- Remote checks: 32 rows in `design/research.md` and in `STATUS.json`.
- Decisions: 9. Human decisions: 0.
- Failed jobs in run 45064243269: 28. Jobs with the pip conflict in the log: 26.

## Convergence After Implementation

After T004 and T005, run the commands in `design/quickstart.md` under "After the fix". Compare each count with the Metrics section. The Bandit job on the fix head must show `success` for step `Run Bandit`.

## Unresolved Items

- U-1: Dependabot can classify a 0.x release as major or minor. The ignore covers both types. The classification is not checked upstream.
- U-2: The Bandit result on the fix head is unknown until T-REMOTE-CI runs.
- U-3: The shared `reusable-quality-gate-issues.yml` workflow in `misthelper-devtools` was not read. The record uses `documentation/quality-gates.md` lines 160 to 165 only.
- U-4: The bot closure of the 15 gate issues is unobserved until T-MERGE runs.
- U-5: The container build did not start for this change, as finding A-6 states. The merge record states the result. No further action is planned.
