# Specification Analysis Report: MSP Profile Lookup Failure

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, the contracts, the checklists, and the remote evidence of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only pass compared the requirement list with the task list, the design, and the remote code. Each finding names its evidence by remote check ID (RC-nn). The IDs refer to `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A1 | Inconsistency | HIGH | `test_msp_privilege_detection.py` fixtures at lines 404, 412, 446, 452, and 489 (RC-27, RC-28) | The success fixtures omit `status_code`. The SDK always sets it (RC-53). The fixtures pass only because the code ignores the status. | T004 adds `status_code=200` to the five fixtures. |
| A2 | Coverage | HIGH | `login_orchestrator.py` line 248 (RC-17) and `operator-guide.md` lines 593 and 594 (RC-36) | The login summary prints "No MSP privileges detected (org-level access only)" after a failed lookup. | Out of scope (D-5). T008 adds an operator note. T011 files the follow-up. |
| A3 | Coverage | HIGH | `org_config_exporter.py` line 71 (RC-25) and `firmware_manager.py` line 43 (RC-24) | Two readers treat an empty grant list as no access. | Out of scope (D-5). T011 files the follow-up. |
| A4 | Stale claim | MEDIUM | Issue #4713 body names #4607 and draft #4358 as holds | GitHub shows both as MERGED on 2026-11-13. The holds named in the issue changed state after the issue was written. | The design leaves `MistHelper.py` unchanged, so the #4607 hold does not apply. The rename target stays unverified (research, Unverified item 6). |
| A5 | Ambiguity | MEDIUM | OpenAPI `admin_privileges` declares `minItems: 1` (RC-47) | The schema does not allow an empty list. Organization-only accounts may still return one. | D-1. A 2xx response with an empty list is confirmed absence. A missing or non-list value is a failed lookup. |
| A6 | Conflict risk | HIGH | Issue #4708 is in progress and owns `org_device_inventory_msp.py` and its test module (RC-07, RC-29) | T007 and T005 edit the same files. | Gate T001 before T005 and T007. Rebase onto `main` before push. |
| A7 | Defect in touched code | LOW | `msp_privilege_detection.py` line 176 writes through the root logger (RC-06). `detect_msp_privileges` spans 35 lines (RC-01). | The logger is inconsistent. The function exceeds the 25-line limit. | T006 uses the module logger in the touched block. The function shrinks to one statement. |
| A8 | Coverage | MEDIUM | The safe sweep runs menu 13 (RC-62) | Menu 13 without a session prints the failure message after the change. The sweep output changes. | T-LOCAL-GATES runs the sweep and records the menu 13 line. |
| A9 | Inconsistency | LOW | PR #4358 body says "Do not merge or enable auto-merge", but the PR state is MERGED | The body predates the merge. | Record only. No action. |
| A10 | Ambiguity | LOW | The issue says a failure-state contract must be agreed. | No agreement record exists on #4713 or #4708. | D-2 defines the contract. The rule for human decisions does not cover this item. Gate T001 covers the file hold. |
| A11 | Hygiene | LOW | The local working tree has five modified files that this change does not touch (`git status --porcelain`) | A staging mistake can add unrelated changes. | T002 uses a new worktree. Stage files by explicit path only. |
| A12 | Coverage | LOW | `MSPInventoryExporter._build_site_lookup` logs failures at debug level (RC-15) | A failed site lookup looks like an empty result. This defect belongs to issue #4762. | Out of scope. Issue #4762 owns the file. |

## Coverage Summary

| Requirement | Has task | Task IDs | Tests |
| - | - | - | - |
| FR-001 | Yes | T004, T006 | Cases 1, 2, 3, and 5 of T004 |
| FR-002 | Yes | T004, T006 | Case 1 of T004 |
| FR-003 | Yes | T004, T006 | Case 7 of T004 |
| FR-004 | Yes | T004, T006 | Case 6 of T004 |
| FR-005 | Yes | T004, T006 | Case 8 of T004 |
| FR-006 | Yes | T004, T006 | Cases 1 to 7 of T004 |
| FR-007 | Yes | T004, T006 | Case 8 of T004 |
| FR-008 | Yes | T005, T007 | Case 3 of T005 |
| FR-009 | Yes | T005, T007 | Cases 1 and 2 of T005 |
| FR-010 | Yes | T005, T007 | The updated test and case 1 of T005 |
| FR-011 | Yes | T005, T007 | Case 1 of T005 |
| FR-012 | Yes | T005, T007 | Case 2 of T005 |
| FR-013 | Yes | T006, T007, T010 | Case 6 of T004 |
| FR-014 | Yes | T001, T009 | Existing callers' tests in T-LOCAL-GATES step 5 |
| FR-015 | Yes | T009 | Manifest check |
| FR-016 | Yes | T004, T005, T-LOCAL-GATES | Every test case named in T004 and T005 |
| FR-017 | Yes | T003, T008 | Read and guard tests in T008 |
| SC-001 | Yes | T004, T005 | Cases 1 and 2 of T005 |
| SC-002 | Yes | T-LOCAL-GATES | Step 5 of T-LOCAL-GATES |
| SC-003 | Yes | T005 | Case 3 of T005 |
| SC-004 | Yes | T-LOCAL-GATES | Steps 1 to 19 |
| SC-005 | Yes | T009 | Manifest check |
| SC-006 | Yes | T004, T010 | Case 6 of T004 |

## Unresolved Items

- The unverified items list in `design/research.md` holds nine items. None blocks the record. Each item names the gate that resolves it.
- The follow-up issues from T011 are not filed. The orchestrator files them.
