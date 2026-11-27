# Specification Analysis Report: Dash pytest plugin marker warning

This report checks `spec.md`, `plan.md`, and `tasks.md` against the remote code and the existing branch. Remote check IDs (RC-nn) point to the table in `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-01 | High | PR #4831 says the Dash plugin "has no effect" because the repository omits the `testing` extra. The premise is wrong. | The `pytest11` entry point loads the plugin module (RC-44). The marker runs at module load (RC-43). The plugin also registers fixtures such as `dash_duo` without the extra (RC-64). The owner observed a changed test result (RC-57). | The premise is rejected. The interim change keeps the plugin loaded (FR-001). |
| A-02 | High | The PR #4831 body reports `8 passed` for the unit file plus the guard. | The unit file defines 16 test functions (RC-01). The reported count does not match main. | Recorded as unverified in `research.md`. Task T-LOCAL-GATES records the real count. |
| A-03 | Medium | The issue body states Dash 4.5.0. | The repository pins `dash==4.5.1` (RC-09, RC-10). The local install is 4.5.1 (RC-43). | The record uses 4.5.1. The issue body is stale. |
| A-04 | Medium | The owner comment says the issue stays open "until Dash migrates its pytest11 entry point". | Upstream keeps the entry point at `setup.py` line 54 (RC-50, RC-51). The fix changes the marker at plugin line 104 (RC-48, RC-49). | Decision D-2 reads the trigger as the marker change. |
| A-05 | High | The upstream fix exists on `dev`, but no release contains it. | Commit `1ed9150a` changed the decorator on 2026-11-20 (RC-52). The latest release is v4.5.1 (RC-53). PyPI shows 4.5.1 (RC-54). `dev` diverges from `v4.5.1` (RC-55). | Decision D-1 waits for a release. Task T008 watches for it. |
| A-06 | Medium | Open pull request #4888 edits `requirements-dev.txt`. | The pull request lists `dependabot/pip/mando-0.8.2` (RC-63). | Task T009 waits for #4888 or rebases after it. |
| A-07 | Medium | The policy check sits in a contract module that reads the CI workflow (RC-36). | The contract folder holds 17 children (RC-37). The guardrails folder holds 79 (RC-38). | Decision D-3 accepts the narrow edit. Task T011 tracks the move. |
| A-08 | Low | The sibling project filters `ignore::DeprecationWarning` (RC-40). A copy in the root config would hide the warning. | `PytestRemovedIn10Warning` subclasses `PytestDeprecationWarning`, which subclasses `DeprecationWarning` (RC-46). | Policy test 3 rejects the category. |
| A-09 | Low | Legacy plan `specs/431-arch-delegate-cleanup/plan.md` shows `pytest -p no:dash --cov` (RC-41). | The policy check reads only the root configuration. The legacy text does not change any gate. | No edit to historical records. |
| A-10 | Medium | Branch `fix/4826-dash-pytest-hooks` and closed PR #4831 still carry the rejected approach. | Branch head `725510a3` (RC-59). PR #4831 is closed and unmerged (RC-58). | Decision D-6 keeps both. Task T010 decides later. |
| A-11 | Low | The global filter in `MistHelper.py` names only `SyntaxWarning`. | `MistHelper.py` lines 41 to 43 (RC-13). | The filter does not hide the marker warning. No change. |
| A-12 | Low | The issue body states "Current tests pass." | No test run is allowed in this record. | Recorded as unverified in `research.md`. |
| A-13 | Medium | The guard file from PR #4831 is absent on main. | `tests/guardrails/test_pytest_startup_removal_warning.py` is not in the tree (RC-39). | This record does not reuse the file. The policy check is new. |
| A-14 | Low | The route `0/0/1/2/3/3/0/1` matches the base-5 value of 4826 and the resolver. | `Resolve-SpecFeaturePath` joins the numbered segments (RC-25). The route folder is free (RC-28). | Consistent. No change. |
| A-15 | Low | The local `.venv` shows no `dash[testing]` packages. | No selenium, percy, or `dash_testing_stub` distribution exists (RC-45). `requirements-dev.txt` pins none of them (RC-12). | The marker still runs at module load. The testing extra stays absent. |

## Coverage Summary

| Requirement | Tasks | Test or verification |
| - | - | - |
| FR-001 Keep the plugin loaded | T003, T004, T-LOCAL-GATES | Policy tests 1 and 2 |
| FR-002 No warning filter | T004 | Policy tests 1 and 3 |
| FR-003 Fail closed on a missing table | T004 | Policy test 4 |
| FR-004 Document the warning | T005 | Policy test 5 |
| FR-005 No manifest change in the interim change | T002, T007, T009 | Diff check at task T007 |
| FR-006 Upgrade passes the warning gate | T008, T009 | Warning gate command in T009 |
| FR-007 Keep branch and PR history | T001, T010 | Branch verification at tasks T001 and T010 |
| FR-008 Pull request uses Refs | T-PR, T-MERGE | Body verification at task T-PR |

Every functional requirement maps to at least one task and one test or verification command.

## Constitution Alignment

The constitution check in `plan.md` passes. Its one debt item is the five-item rule for the contract folder. Task T011 records the incremental remediation. Principles VI and VII apply to the policy check. Task T004 acceptance covers both principles.

## Unmapped Tasks

Task T006 and the four delivery tasks map to the delivery pipeline in constitution Principle IV. They map to no functional requirement. Each delivery task names its own requirement IDs in `tasks.md`.

## Metrics

- Functional requirements: 8.
- Success criteria: 6.
- Tasks: 15 (11 numbered tasks and 4 delivery tasks).
- Test functions planned: 5, collecting 6 cases.
- Remote checks: 64.
- Decisions: 8. Human decisions: 0.
- Findings: 15. High: 3. Medium: 5. Low: 7.

## Convergence After Implementation

- The policy tests pass, and the synthetic cases fail for each forbidden entry.
- The warning evidence run shows PytestRemovedIn10Warning and exits with code 0.
- The interim diff lists no manifest change.
- T-REMOTE-CI shows each required check as successful.
- Task T009 runs only after an upstream release contains the fix.

## Unresolved Items

1. The owner observation that `-p no:dash` changes `test_complete_offline_journey` remains unverified (RC-57). A test run must confirm it or refute it.
2. The PR #4831 test count `8 passed` does not match main (A-02).
3. The upstream release date is unknown. Task T008 watches for it.
4. The disposition of `fix/4826-dash-pytest-hooks` waits for the replacement merge (T010).
5. The manifest owner handover is not yet recorded. Task T009 depends on it.
