# Specification Analysis Report: Virtual Chassis Menu Guidance

This report checks `spec.md`, `plan.md`, and `tasks.md` against each other and against the remote code. Evidence IDs (RC-nn) refer to the table in `design/research.md`.

## Findings

- **F-1 (high)**: Three printed lines name menus 92 and 94 for virtual chassis operations (RC-06, RC-07, RC-08). Menu 92 selects a site, menu 93 shows site inventory, and menu 94 shows device statistics (RC-22 to RC-24). The registered conversion menus are 161, 162, and 14 (RC-25 to RC-27). The two inline WHY comments on lines 420 and 421 repeat the stale numbers. They are fixed in T003.
- **F-2 (medium)**: Thirteen more module lines name stale menus. They include the module docstring (RC-04) and the menu launchers (RC-05). The issue asks for stale comments and docstrings but lists none of them. T004 fixes them.
- **F-3 (low)**: The root test names option 92 in its docstring and in a comment (RC-44, RC-45). The issue does not name this file. T005 fixes it under D-5.
- **F-4 (medium)**: No existing unit test asserts the usage-note or rollback text (RC-41). The suite cannot detect the defect. T002 adds the guards.
- **F-5 (low)**: The issue links MistHelper.py lines 5426 to 5444 for the menu entries. At commit 0d88, those lines held menus 92 to 94 (RC-28). On `main`, the entries moved to lines 5255 to 5394 (RC-22 to RC-27), and lines 5426 to 5444 hold other menus (RC-29). The link is stale. The defect description is correct.
- **F-6 (low, contradicted)**: The issue says draft PR #4358 renames `tests/unit/test_virtual_chassis.py`. PR #4358 merged on 2026-11-13. Its files, and its previous-file names, contain no virtual chassis path (RC-49). The file keeps its path on `main`. The rename claim is stale. The spec excludes the rename (Out of Scope).
- **F-7 (partial)**: The issue says #2863 includes the module in a safety-sensitive queue. The body of #2863 names no file. It cites issue #2753 and an inventory. The cited inventory lists the module (RC-50). The queue claim is partly supported. T001 checks the overlap again.
- **F-8 (info)**: The rollback guidance prints only after a single conversion (RC-13, RC-15). The bulk path prints none. The issue does not state this. The spec keeps the bulk path unchanged (D-14).
- **F-9 (low)**: Three test names cite module lines 102 to 184 (RC-42). A line insertion above line 184 would make those names misleading. The plan keeps the line count (D-6).
- **F-10 (grandfathered)**: The module declares more than five top-level names (RC-18). `VirtualChassisManager` holds more than five methods (RC-19). The change adds no member. A separate issue handles the remediation.
- **F-11 (grandfathered)**: The unit test module declares more than five test classes (RC-43). The change adds no class. A separate issue handles the remediation.

## Coverage Summary

| Requirement | Task | Test or gate |
| - | - | - |
| FR-001 | T002, T003 | TG-1 `test_status_usage_notes_name_conversion_menus` |
| FR-002 | T002, T003 | TG-1 `test_status_usage_notes_name_conversion_menus` |
| FR-003 | T002, T003 | TG-2 `test_success_guidance_names_status_menu` |
| FR-004 | T002, T003, T004 | TG-1, TG-2, and TG-4 |
| FR-005 | T004 | TG-4 `test_virtual_chassis_sources_name_no_stale_menus` |
| FR-006 | T005 | TG-4 `test_virtual_chassis_sources_name_no_stale_menus` |
| FR-007 | T002 | TG-3 `test_named_menus_match_registered_operations` |
| FR-008 | T002 | TG-1, TG-2, and TG-3 call only offline helpers (RC-10, RC-103) |
| FR-009 | None (no change) | Existing confirmation tests (RC-104) |
| FR-010 | None (no change) | Existing API call tests (RC-105) and the registry guard (RC-46) |
| FR-011 | T006 | Changelog policy guard (RC-48) |
| FR-012 | T-LOCAL-GATES | Destructive menu docs guard (RC-94) and the menu reference gate (RC-61) |

Unmapped tasks: none. Every task maps to at least one requirement.

## Constitution Alignment

- Principle I: Pass with grandfathered debt (F-10, F-11). The new test methods keep their classes at five or fewer members (D-3).
- Principles II and VII: Pass. No wrapper is added. The changed helper performs no listed action.
- Principles III, V, and VI: Pass. Confirmations, ASCII output, and inline comments are kept (plan Constitution Check).
- Principle IV: Pass by plan. The pipeline tasks carry the proof.
- Destructive menus: Pass. The categories of menus 161, 162, and 14 do not change (RC-34 to RC-36).

## Metrics

- Functional requirements: 12.
- Success criteria: 7.
- Tasks: 10 (six numbered, four named final tasks).
- New tests: 4 (TG-1 to TG-4).
- Repository files changed: 4 (3 modified, 1 added).
- Stale lines to replace: 18 (16 in the module, 2 in the root test).
- Remote checks: 106 (see `design/research.md`).
- Decisions: 14. Open decisions: 0. Human decisions: 0.
- Five-item members after the change: `TestCheckStatus` 5, `TestHandleConversionResponse` 4.

## Convergence After Implementation

The following must hold after T003 to T006. T-LOCAL-GATES checks each item.

- The four new tests pass, and they failed before T003 and T004.
- TG-4 finds no stale menu number in either file.
- `git diff --numstat` shows equal added and deleted line counts for `virtual_chassis.py`.
- `git diff --numstat` shows no change in `operation_registry.py`, `MistHelper.py`, or any generated page.
- The menu reference commands leave no changed file.
- `TestCheckStatus` holds five methods, and `TestHandleConversionResponse` holds four.
- Remote CI passes on the pull request before any merge authorization.

## Unresolved Items

- U-1: The owner of the #2863 queue has not confirmed a decision. The issue names the queue, but the cited body names no file. T001 repeats the overlap check. The reviewer confirms the result.
- U-2: Human review is pending. The `needs-human-review` label stays on the issue until the review finishes.
- U-3: The remote CI result is pending. T-REMOTE-CI records it.
- U-4: The ste-linter score for the changelog fragment is pending. T006 records it.
- U-5: The bulk path has no rollback guidance (F-8). A separate issue can decide whether to add it.
