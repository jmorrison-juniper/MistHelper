# Specification Analysis Report: Ruff (lint) check failure from the mando 0.8.2 pin

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| --- | --- | --- | --- | --- |
| DEF-01 | High | PR #4888 moves mando from 0.7.1 to 0.8.2. Radon 6.0.1 requires mando below 0.8. The pip install step fails with a resolver conflict in 26 jobs. | RV-04, RV-02, RV-24, `quickstart.md` section 2 | Keep the pin at 0.7.1 (D-1). Keep PR #4888 open (D-3). |
| DEF-02 | Medium | The Dependabot pip update block has no ignore entry for mando, although radon blocks the bump. The repository has an npm ignore precedent. | RV-15, RV-16, RV-52 | Add the ignore entry (D-2, T003). |
| DEF-03 | Low | `documentation/quality-gates.md` omits the `dependency_lock` job ID from its job list. This record verifies that one missing ID only. | RV-17, RV-18 | Out of scope. Track it in a separate issue. |
| DEF-04 | Medium | `changelog.d/README.md` says to add no fragment for an internal-only change. The constitution and the PR template require one fragment for each change. | RV-19, RV-20, RV-21, RV-62 | Add the fragment (D-5, T004). Track the README conflict in a separate issue. |
| DEF-05 | Medium | Constitution Principle IV steps 10 to 12 assume a product change. No rule covers a CI-only change. | RV-36, RV-37 | Record the steps as not triggered (D-6). Track the rule gap in a separate issue. |
| DEF-06 | Low | The issue title names the gate `ruff`, not the failing step. A reader can expect a lint finding. | Issue #4891 title and body, `quickstart.md` QS-02 | FR-006 requires the record to name the step. The title change is out of scope. |
| DEF-07 | Medium | `tests/guardrails` holds 79 direct children, which exceeds the five-item limit. The folder is grandfathered debt. | RV-43, RV-44, RV-46 | Record the debt in `plan.md`, Complexity Tracking. Track the split in a separate issue. |
| DEF-08 | Info | `pytest (coverage gate)` and `E2E smoke tests` fail at aggregator steps that read upstream results. | RV-13, RV-14 | No change. The fix clears their upstream failure. |

## Coverage Summary

| Requirement | Tasks | Test or verification |
| --- | --- | --- |
| FR-001 | T001 | Export guard `tests/guardrails/test_dependency_export.py` (RV-23), with RV-01 and RV-05 |
| FR-002 | T002, T003 | Guard case 1, the minor-update case |
| FR-003 | T002, T003 | Guard case 2, the patch-update case |
| FR-004 | T002, T003 | Guard case 3, the failing-path case, and the printed count |
| FR-005 | T004 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-006 | T005 | `quickstart.md` QS-02 and QS-03, with the expected output |
| FR-007 | T-PR, T-MERGE | `quickstart.md` QS-08, read-only state check |
| FR-008 | T-LOCAL-GATES, T-PR, T-REMOTE-CI | `quickstart.md` sections 4 and 5 |
| FR-009 | T002, T-LOCAL-GATES | Checklist item CHK-09 in `design\checklists\requirements.md` |

Success criteria mapping:

- SC-001 and SC-002 map to T-REMOTE-CI.
- SC-003 maps to T002 and T003.
- SC-004 maps to T003.
- SC-005 maps to T-MERGE.
- SC-006 maps to the metrics below and to the counts in `4891-STATUS.json`.

## Constitution Alignment

- All seven Core Principles pass in design. The reasons are in `plan.md`, Constitution Check.
- Principles VI and VII are checked again in T002 and T003.
- Principle I records the existing debt in `tests/guardrails` (DEF-07).
- Principle IV steps 10 to 12 are not triggered for this change (D-6, DEF-05).

## Unmapped Tasks

None. Each task maps to at least one requirement in the coverage table of `tasks.md`.

## Metrics

- Requirements (FR): 9.
- Success criteria (SC): 6.
- Tasks: 9.
- Guard cases: 3.
- Decisions: 7. Human decisions: 0.
- Remote checks: 62, listed in `design\research.md`, section 7.
- Failed jobs in run 45064243269: 28. Jobs with the resolver conflict: 26.
- Applicable local gates: 6 (Lint, Format, Tests, Full tests, Test quality, Symbols). The other gates are not applicable, with reasons in `design\research.md`, section 8.

## Convergence After Implementation

Not applicable before implementation. T-REMOTE-CI and T-MERGE record the result. Their results are added to issue #4891, not to this record.

## Unresolved Items

- U-01 to U-08 in `design\research.md`, section 10.
- PR #4888 stays open after this change (D-3). Its state is recorded in T-MERGE.
- DEF-03, DEF-04, DEF-05, and DEF-07 need separate issues. This record does not file them.
