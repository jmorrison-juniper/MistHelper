# Specification Analysis Report: Mando Pin Conflict Behind the pydocstyle Gate Failure

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| A-01 | High | The issue names the pydocstyle rule, but no pydocstyle rule ran. The pip install step failed, and the docstring step was skipped. | Job 137336719204, steps 4 and 5 (design/research.md, E-2). | Record the failing step (FR-008). |
| A-02 | High | Pull request 4888 pins mando 0.8.2. Radon 6.0.1 requires mando below 0.8. | `requirements-dev.txt` line 179 at the head (research row 5). Radon metadata line 31 (research Sources). | Keep mando 0.7.1 (decision D-1). |
| A-03 | High | The failure covers 28 directly failing jobs in three workflows, and two downstream jobs fail after them. | Failing-job table (design/research.md, E-4). | Verify all 30 in T-REMOTE-CI (SC-001). |
| A-04 | Medium | Pull request 4888 changed only `requirements-dev.txt`. Sibling Dependabot pip updates also changed `uv.lock`. | Changed-file lists of pull requests 4802 to 4806 and 4888 (design/research.md, E-6). | Decline the update (D-1). The export guard flags a stale export once the resolver passes (Unverified U-1). |
| A-05 | Medium | Issue 4900 cites commit 5bb4b385. That commit is a GitHub test-merge commit. Its parents are 00d9a16e and e86098cd. The run head is e86098cd. | Commit lookups and compare API (design/research.md, E-6). | Record both commits (FR-008, FR-009). |
| A-06 | Medium | The Dependabot pip entry has no ignore block. Dependabot can reopen the update on each weekly run after a close. | `.github/dependabot.yml` lines 3 to 11 (research row 12). | Add the ignore block (decision D-2). |
| A-07 | Low | The policy guard snapshot must match the YAML policy exactly. | `tests/guardrails/test_pr_title_workflow.py` lines 18 to 30 (research row 13). | Land T002 and T003 together. |
| A-08 | Medium | Conflict. The constitution requires one fragment for each change (line 409). `changelog.d/README.md` rule four allows no fragment for an internal change (line 58). | Research rows 20, 21, and 22. | Add the fragment (decision D-3). A separate issue changes the README. |
| A-09 | Medium | `changelog.d/` holds 335 direct children, above the five-item limit. | Local directory listing on 2026-11-26. | Record the debt in plan.md. A separate issue owns the remediation. |
| A-10 | Medium | The pip-audit gate reads `requirements.txt` only. Development-only packages, such as mando and radon, get no vulnerability scan. | `documentation/quality-gates.md` line 57 (research row 26). `.github/copilot-instructions.md` line 68. | Record as an unresolved item. A separate issue owns the scope. |
| A-11 | Low | Main passes the same jobs at commit f03c6c9. | Run 45774119357 (research row 17, E-5). | Use the main run as the expected result in T-REMOTE-CI. |
| A-12 | Low | After each merge, auto-merge dispatches `container-build.yml`. Principle IV steps 10 and 11 run although no product file changes. | `auto-merge.yml` line 65 (research row 24). `container-build.yml` paths on line 6 (research row 23). | Record the timing in plan.md. |
| A-13 | Low | No newer radon release exists. | PyPI project page (research Sources). | Make no radon change (decision D-5). |
| A-14 | Info | Local HEAD equals main at f03c6c9. The cited blob IDs match the remote tree. | `git rev-parse HEAD`, `git ls-files -s`, and the Git trees API (research E-1). | None. |
| A-15 | Info | The route for issue 4900 is 0 0 1 2 4 1 0 0. | `.specify/scripts/powershell/spec-route.ps1` lines 7, 17, 31, and 51 (research row 19). The base-5 digits of 4900 are 1 2 4 1 0 0 after padding with zeros to eight digits. | None. |
| A-16 | Low | The two Windows workflows run the same install step. They fail with the same resolver error. | Logs of runs 45064235051 and 45064235097 (research rows 15 and 16). | Covered by T-REMOTE-CI. |

## Coverage Summary

| Requirement | Tasks | Test or gate |
| - | - | - |
| FR-001 | T-LOCAL-GATES, T-REMOTE-CI | Docstrings row. Remote pydocstyle job. |
| FR-002 | T001, T-LOCAL-GATES, T-REMOTE-CI | `TestDependencyExport::test_requirements_exports_match_the_lock` |
| FR-003 | T002, T003, T-MERGE | `TestDependabotPolicy::test_complete_policy` |
| FR-004 | T002, T003 | `TestDependabotPolicy::test_complete_policy`, which lists minor and major only |
| FR-005 | T-REMOTE-CI | Remote job results against SC-001 |
| FR-006 | T-PR, T-LOCAL-GATES | Changed-file list check in T-PR |
| FR-007 | T004 | `TestFragmentNaming::test_every_fragment_uses_an_allowed_name` and `TestFragmentContent::test_every_fragment_holds_a_heading_and_a_bullet` |
| FR-008 | T005, T-LOCAL-GATES | STE row. Symbols row for the test module. |
| FR-009 | T-MERGE | Pull request state check after the merge |
| FR-010 | T001, T-PR, T-REMOTE-CI | Conventional Commits pull request title check |
| FR-011 | T005 | `test_numeric_feature_route_remains_stable` |

## Constitution Alignment

Every principle in plan.md has a result. Principles VI and VII are non-negotiable. The plan requires an inline comment on each new line and no new action. Principle IV steps 10 and 11 run through the post-merge dispatch (A-12). Principle I records existing debt (A-09).

## Unmapped Tasks

None. Each of the nine tasks maps to at least one requirement.

## Metrics

- Requirements: 11 (FR-001 to FR-011).
- Success criteria: 7 (SC-001 to SC-007).
- Tasks: 9.
- Tests planned: 5.
- Decisions: 5. Decisions that need a human: 0.
- Remote checks: 27.
- Failing jobs in the failing runs: 30, with 28 direct failures and 2 downstream failures.

## Unresolved Items

- Radon blocks mando 0.8. A follow-up issue owns the choice between replacing radon and waiting for a release (decision D-5).
- Development-only packages get no vulnerability scan (A-10). A follow-up issue owns the scope change.
- The README rule four conflicts with the constitution (A-08). A follow-up issue owns the README change.
- The changelog folder holds 335 children (A-09). A follow-up issue owns the remediation.
- Dependabot patch updates may omit uv.lock (Unverified U-3). The export guard reports the drift when it happens.

## Convergence After Implementation

After T-MERGE, main keeps mando 0.7.1, and the Dependabot pip entry ignores mando minor and major updates. Pull request 4888 reads CLOSED. Run 45774119357 on main already shows the expected passing jobs. T-REMOTE-CI confirms the same jobs pass on the fix pull request before the merge.
