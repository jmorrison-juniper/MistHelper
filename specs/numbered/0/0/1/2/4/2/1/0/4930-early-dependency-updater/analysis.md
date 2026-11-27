# Specification Analysis Report: Early dependency check without half-removed packages

## Findings

Each finding cites its remote evidence in `design/research.md`.

| ID | Finding | Evidence | Severity | Handling |
| - | - | - | - | - |
| A-01 | The import probe loads each requirement in the process, and an upgrade then locks the loaded files. | R-14, R-15 | High | Fixed by D-1 and D-2 (T005, T006). |
| A-02 | The import map has no key for `charset-normalizer`, and the pin name is used as the import name. A hyphenated name fails the import, so the check reports a present package as missing. | R-23, R-15 | High | Fixed by D-1 (presence from metadata) and D-6 (field removed). |
| A-03 | The auto-upgrade flag defaults to `true`, and the PyPI lookup then runs for each installed package. The lookup imports `requests` in-process. | MistHelper.py line 1360 (blob 98d78284), R-27 | Medium | Kept by D-7. The loaded-package skip covers the modules that the lookup loads. |
| A-04 | `dependency_check.py` exceeds the five-item limit: 27 constants, two classes, and 22 methods. | R-19 | Medium | Recorded in Complexity Tracking. A separate issue owns the split. |
| A-05 | `package_installer.py` exceeds the five-item limit: 16 constants and one class. | R-21 | Medium | Recorded in Complexity Tracking. The same separate issue owns it. |
| A-06 | `changelog.d/` holds 335 children. | R-07 | Low | Process folder debt. The change adds one unique record. |
| A-07 | `documentation/operator-guide.md` does not name the repair command or the workaround. | R-39 | Medium | Fixed by T012. |
| A-08 | `documentation/development-setup.md` does not name the repair command or the workaround. Issue #4879 covers a related drift. | R-40, issue #4879 | Medium | Not changed here. Issue #4879 owns the file. |
| A-09 | The legacy method `_upgrade_all_dependencies` has no call site. | R-29 | Low | Dead code outside this change. A separate issue can remove it. |
| A-10 | The instruction file names the mistapi floor as 0.64.0, and `pyproject.toml` names 0.64.1. The brief for this record also states 0.64.0. | R-30, R-31 | Medium | Not changed here. Open a separate issue to correct the instruction file. The record uses the `pyproject.toml` value. |
| A-11 | The number in the folder `specs/1020-safe-test-clean-run` is a feature number. Issue #1020 is an unrelated Mist API issue. | R-48, R-49 | Low | Naming hazard. The record uses no issue number from a folder name. |
| A-12 | CI runs on `ubuntu-latest`, so the Windows lock behavior has no CI case. | R-44 | High | Manual check in `design/quickstart.md`, and SC-004. |
| A-13 | The mistapi pin appears in `requirements.txt` (R-25) and `pyproject.toml` (R-30). The change edits neither file. | R-25, R-30 | Low | No action. FR-009 keeps both files unchanged. |

## Coverage Summary

Each requirement maps to at least one task and at least one test case.

| Requirement | Tasks | Test cases |
| - | - | - |
| FR-001 | T001, T003, T006 | TC-01 |
| FR-002 | T001, T003, T005, T009 | TC-02, TC-10 |
| FR-003 | T003, T005 | TC-03, TC-04 |
| FR-004 | T001, T004, T007 | TC-07, TC-08, TC-09, TC-10 |
| FR-005 | T006 | TC-05, TC-06 |
| FR-006 | T006, T007, T008 | TC-05, TC-09 |
| FR-007 | T008 | TC-11 |
| FR-008 | T005, T010 | TC-12 |
| FR-009 | T002, T013 | TC-13, the changelog guard |
| FR-010 | T011, T012 | The STE gate on each file |
| FR-011 | T009 | `py_compile`, and the symbol diff |

Each success criterion maps to a check:

| Criterion | Check |
| - | - |
| SC-001 | TC-01 |
| SC-002 | TC-05 |
| SC-003 | TC-07 |
| SC-004 | The manual Windows check in `design/quickstart.md` |
| SC-005 | T-LOCAL-GATES and T-REMOTE-CI |

Each task maps to at least one requirement. No task is unmapped.

## Consistency Review

- Dependencies in `tasks.md` have no cycle. T004 follows T003 because both edit `package_installer.py`. T007 follows T004 and T006. T009 follows T003 and T005. T010 follows T009.
- The status `partial` appears on T005, T009, and T010, because the targets exist on `main`. The status `absent` appears on the other new-behavior tasks.
- The spec says that the pins equal the versions in `uv.lock` (Assumptions). TC-13 tests this claim, so the claim holds only after T002 passes.
- The spec sets the threshold at five (FR-005). A fresh environment with more than five missing packages now stops. The plan records this risk, and the bootstrap sync (R-35) is the fix.
- The brief for this record states `mistapi>=0.64.0,<0.65`. The repository states `>=0.64.1,<0.65` (R-30). The record uses the repository value (A-10).

## Constitution Alignment

- Principle I: the two classes and the method count increase are recorded in Complexity Tracking. The record holds the separate remediation action.
- Principles V, VI, and VII: T008 and each changed line require ASCII text, inline comments, and action logs.
- Principle III: no secret reaches a log record. No Mist endpoint is called.
- Principle IV: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 12.
- The branch name, labels, and file overlap check follow the Multi-Agent Git Workflow section.

## Metrics

- Requirements: 11 (FR-001 to FR-011).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 17 (T001 to T013, plus T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE).
- Test cases: 13 (TC-01 to TC-13).
- Decisions: 8 (D-1 to D-8). Human decisions: 0.
- Remote checks: 52. Present: 47. Absent: 4 (R-03, R-23, R-39, R-40). Stale: 1 (R-31).
- Findings: 13 (A-01 to A-13). High: 3. Medium: 6. Low: 4.

## Unresolved Items

- U-1: The Windows lock behavior has no CI case. The manual check (SC-004) must pass before the merge.
- U-2: The threshold of five packages (D-3) is a decision. A reviewer can challenge the value.
- U-3: The live run log that the issue body describes is not in the repository. Unverified items 1 and 2 cover it.
- U-4: `packages_distributions()` is not reliable for some editable installs (D-2, risk). The fail-closed rule covers the unmapped case.
- U-5: The messages in `design/contracts/startup-messages.md` must pass the STE gate after T011 and T012. The contract names the text, and the gate checks the prose in the documentation.

## Convergence After Implementation

Each remote row that is not `present` has an expected state after the change.

| Row | Current | Expected after the change | Reason |
| - | - | - | - |
| R-03 | absent | stale after the record lands | The record creates the route folder. |
| R-07 | 335 children | 336 children | One fragment is added (T013). |
| R-19 | 22 methods | at most 25 methods | T005 to T008 add at most three methods. |
| R-23 | absent | absent | The import map is unchanged. |
| R-31 | stale | stale | The instruction file is out of scope (A-10). |
| R-39 | absent | present | T012 adds the repair text. |
| R-40 | absent | absent | `documentation/development-setup.md` is out of scope (A-08). |
