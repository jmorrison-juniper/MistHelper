# Analysis: Ordered Multi-Site Firmware Families

This review checks the spec, the plan, the tasks, and the remote code against each other. Remote row numbers refer to the table in `design/research.md`, section 4.

## 1. Requirement Coverage

Each requirement maps to at least one task and at least one test. The test names appear in `tasks.md`, phase 5.

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 Family order | T001, T003, T005 | Test 1, Test 2 |
| FR-002 No later family before upstream proof | T006, T008 | Test 3 |
| FR-003 Portal-neutral gate interface | T004, T011 | Test 3 |
| FR-004 Reuse the phase limit | T008, T011 | Test 6 |
| FR-005 Missing, failed, or unknown gate is a stop | T008, T011 | Test 6, Test 7 |
| FR-006 Empty family skips | T008 | Test 8 |
| FR-007 Refusal stops its family and later families | T007, T016 | Test 4, rewritten test T016 |
| FR-008 Unknown outcome stops the run | T007 | Test 5 |
| FR-009 No resend | T007 | Test 5 |
| FR-010 Stop record before the run ends | T009 | Test 10 |
| FR-011 Lock loss and cancellation stop writes | T007, T017 | Rewritten test T017, existing cancel tests in T021 |
| FR-012 No client firmware | T003 | Test 9 |
| FR-013 No parent claim during a wait | T006 | Test 3 |
| FR-014 Locks renew during a wait | T014 | Test 14 |
| FR-015 Route returns before a wait | T012, T020 | Test 15 |
| FR-016 Watch reads the stored result | T013 | Test 13 |
| FR-017 Stop sentences name the next action | T015 | Test 12 |
| FR-018 No resume | Review in T-PR | Test 10 reads the stop record that issue #4022 needs |
| FR-019 Process loss | T010 | Test 11 |
| FR-020 Changed defect tests | T016, T017, T021 | Rewritten tests |

Result: every requirement has at least one task. FR-018 is a negative requirement. Its test proves the record shape that issue #4022 needs. Review confirms that no resume path exists.

## 2. Defects in Existing Code

Each defect below has a remote row. The change repairs each defect.

| Id | Defect | Evidence | Repair |
| - | - | - | - |
| A-01 | The aggregate build places access point children before the other children. | Rows 2 and 3 | T005 |
| A-02 | The submit loop continues after a child refusal. | Row 1 | T007 |
| A-03 | An unknown child outcome returns to the submit loop, and the loop sends the next child. | Row 4 | T007 |
| A-04 | The aggregate module has no family gate between families. | Row 7 (absent) | T004, T006, T008 |
| A-05 | A test asserts the continuation after a refusal. | Rows 30 and 31 | T016 |
| A-06 | A test assumes that the access point child writes first. | Row 32 | T017 |
| A-07 | The route runs the whole aggregate send in the HTTP request. A family gate can last up to 1800 seconds. | Rows 20, 24, 25, 26, 27 | T020 |
| A-08 | The route maps every unexpected aggregate fault to one operator text. The background run needs one stop text for each reason. | Row 86 | T015, T021 |
| A-09 | The phase watch docstring says that the watch observes and sends no firmware request. After the change, the watch reads stored results only, and the docstring must say so. | Row 85 | T023 |

## 3. Stale or Inconsistent Statements

| Id | Statement | Current fact | Resolution |
| - | - | - | - |
| S-01 | Issue #4021 says the phase order is `gateways`, `switches`, `aps`, `clients`. | That order exists (row 23). The plan order constant uses device types `gateway`, `switch`, `ap` (row 9). | Decision D-1 maps the two names. |
| S-02 | The issue comment of 2026-11-10 says that PR #4701 currently changes both manifest files. | PR #4701 merged on 2026-11-13. | The spec uses the merged state of `main` at commit `f03c6c9b`. |
| S-03 | The issue body says the proposal-time overlap check found zero overlap. | The current check finds zero overlap with seven open pull requests (`design/research.md`, section 8). | The overlap check repeats in T-PR. |
| S-04 | The module comment in `upgrade_service.py` names mistapi 0.63.3. | The pinned version is 0.64.1 (row 68). | Separate issue R-4. The change does not edit that comment. |
| S-05 | Issue #4021 says that ten existing tests lock the defect. | This review verifies two tests (rows 30 to 32). | Unverified item U-1. |
| S-06 | Issue #4021 lists two production files in its manifest. | The route and the watch must change (decision D-9). | The owner reviews the expanded manifest before merge. |

## 4. Cross-Artifact Counts

The counts below must match across the record files.

| Item | Value | Where it appears |
| - | - | - |
| Remote checks | 87 | `design/research.md`, section 4 table rows, `META/4021-STATUS.json` `remote_checks`, `META/4021-summary.md` |
| Decisions | 15 | `design/research.md`, section 5, STATUS `decisions`, summary |
| Requirements | 20 | `spec.md`, STATUS `requirements` |
| Tasks | 27 | `tasks.md`, STATUS `tasks`, summary |
| Tests planned | 17 | `tasks.md` note and phase 5, STATUS `tests_planned` |
| Human decisions | 0 | STATUS `decisions` (all false), summary |

## 5. Unresolved Items

| Id | Item | Reason it stays open |
| - | - | - |
| UR-1 | The eight other tests in the issue count of ten. | The brief limits this review to verified claims. The list appears in `design/research.md`, section 7 (U-1). |
| UR-2 | Live cloud order of the access point child. | The sandbox rules forbid live Mist requests. Tests use doubles only. |
| UR-3 | Behavior of the 13 affected test files under the new rules. | The brief forbids running tests during this research. Task T021 runs them. |
| UR-4 | Existence of the STE configuration file. | Named in the local gates table, not row-verified. Listed in U-6. |
| UR-5 | Duration of cloud firmware jobs. | No repository source gives a measured duration. The phase limit of 1800 seconds stays unchanged (row 20). |

## 6. Verdict

The design meets the issue requirements and the owner decisions on #4020. The change needs one human review because it changes a destructive write boundary. The change requires no human decision under section 6 of the brief.
