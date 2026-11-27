# Specification Analysis Report: Organization Config Export Refusal

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/` artifacts, and the repository state on `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only review. It compares the requirements, the tasks, and the remote code. It cites remote checks by ID from `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| --- | --- | --- | --- | --- | --- |
| F-01 | Defect | High | `src/mist/resources/org/org_config_migration_manager.py` line 202 | `_fetch_config_type` returns an empty list after an exception (RC-19). | Fixed by T005 and T006. |
| F-02 | Defect | High | Same file, line 208 | `_extract_response_data` sends every reply to `mistapi.get_all` without a status check (RC-20). The SDK helper returns an empty list for a body without `results` (RC-57). | Fixed by T005. |
| F-03 | Defect | High | Same file, line 114 | `export_config` logs completion without a verification gate (RC-21). | Fixed by T006. |
| F-04 | Defect | High | Same file, line 309 | The structural check validates keys only, so it accepts a bundle without fetch status (RC-23). | Fixed by T007. |
| F-05 | Defect | High | Same file, line 377 | The import conflict cache uses the same silent fetch (RC-24). A refused destination fetch hides conflicts. The issue body does not name this path. | Fixed by T007. |
| F-06 | Defect | Medium | `mistapi/__pagination.py` line 62 | `get_all` extends a list reply with dictionary keys on a later page (RC-58). A refused follow-up page can add a key name as an object. The issue body does not name this path. | Avoided by the own page loop in T005 (FR-015). |
| F-07 | Documentation drift | Low | `.github/copilot-instructions.md` line 21, `.specify/memory/constitution.md` line 279, `pyproject.toml` line 29 | The mistapi pin text differs: `>=0.64.0` in the repository rules (RC-03), `0.59+` in the constitution (RC-05), and `>=0.64.1` in `pyproject.toml` (RC-42). | Out of scope. The spec uses the enforced pin. A separate issue must align the text. |
| F-08 | Stale issue data | Low | Issue #4707 body and comment | The body cites main `3964d21d`, and the comment cites main `b7a18b7e`. Remote main is `f03c6c9b` (RC-52, RC-53, RC-54). | The spec uses remote main. |
| F-09 | Stale issue data | Medium | Issue #4707 body | The body says draft #4404 owns the manager file. PR #4404 merged on 2026-11-13 (RC-55). The owner comment keeps the holds. | Hold kept as precondition P-1 and decision D-10. |
| F-10 | Existing test encodes the defect | Medium | `tests/unit/org/test_org_config_migration_conflicts.py` lines 602 and 637. `tests/unit/org/test_org_config_migration_workflow.py` line 379. | Tests assert an empty list for a failed fetch (RC-31, RC-32) and a saved bundle after fetch failures (RC-33). | Replaced or updated by T002, T003, and T008. |
| F-11 | Existing debt | Medium | `src/mist/resources/org/org_config_migration_manager.py` | The module holds 747 lines. The manager class holds 49 methods (`^    def ` count). Both exceed the five-item limit. | Recorded in `plan.md` Complexity Tracking. The fix lowers the method count to 47. |
| F-12 | Existing debt | Low | Same file | The manager writes the bundle without `DataExporter` (constitution, Output Backends). | Recorded in `plan.md` Complexity Tracking. Out of scope. |
| F-13 | Handover record | Low | `.github/copilot-handoff.md` | The handoff file holds no entry for issue #4707 and no handover (RC-44). | Hold kept. The owner records the handover (P-1). |
| F-14 | Route check | Information | `.specify/scripts/powershell/spec-route.ps1` line 17 | The base is 5, and eight segments hold the route. Issue 4707 in base 5 is `122312`, padded to `00122312`, which matches the route (research R9). | No change. |
| F-15 | Record location | Information | `specs/numbered/0/0/1/2/2/3/1/2` | The route folder is absent on main (RC-50). A new record adds the folder. | Created during T-PR. |

## Coverage Matrix

| Requirement | Tasks | Tests |
| --- | --- | --- |
| FR-001 | T003, T005 | `test_a_list_reply_is_verified`, `test_a_verified_empty_reply_has_no_objects` |
| FR-002 | T003, T005 | `test_status_boundaries_decide_verification`, `test_a_missing_status_is_unavailable` |
| FR-003 | T003, T005 | `test_a_reply_without_a_list_is_invalid`, `test_a_missing_follow_up_page_is_unavailable`, `test_an_exception_is_not_verified_and_logs_the_type_only` |
| FR-004 | T003, T005, T006 | `test_a_verified_empty_reply_has_no_objects`, `test_a_verified_fetch_records_the_fetch_status` |
| FR-005 | T003, T005 | `test_a_refused_follow_up_page_fails_the_whole_type` |
| FR-006 | T002, T006 | `test_a_partial_fetch_saves_no_bundle` |
| FR-007 | T002, T006 | `test_a_partial_fetch_saves_no_bundle`, updated `test_fetch_failures_do_not_expose_exception_text_in_any_export_log` |
| FR-008 | T002, T006 | `test_a_partial_fetch_never_logs_completion` |
| FR-009 | T002, T006 | `test_a_verified_fetch_records_the_fetch_status`, updated `test_the_schema_version_is_stamped` |
| FR-010 | T004, T007 | `test_a_legacy_bundle_is_refused`, `test_a_refused_bundle_stops_before_the_prompt` |
| FR-011 | T004, T007 | `test_a_legacy_bundle_is_refused` (checks the instruction text in the log) |
| FR-012 | T004, T007 | `test_an_unverified_destination_caches_nothing_and_returns_false`, `test_an_unverified_destination_stops_before_any_create` |
| FR-013 | T008 | Existing `TestImportConfig` flows (updated) |
| FR-014 | T003, T011 | `test_each_list_call_uses_the_documented_path`, SDK compatibility guard |
| FR-015 | T003, T005 | `test_a_refused_follow_up_page_fails_the_whole_type` (patches `mistapi.get_next`) |
| FR-016 | T003, T009 | `test_an_exception_is_not_verified_and_logs_the_type_only`, updated export privacy test |
| FR-017 | T001, T008 | Existing `TestGetOrgName` and `TestCreateWithoutIdentifier` |
| FR-018 | T002, T003, T004 | All 20 new test functions |
| FR-019 | T009, T010 | `test_every_fragment_uses_an_allowed_name` (`tests/guardrails/test_changelog_fragment_policy.py` line 151), Docstrings row |

Every requirement maps to at least one task and one test. Every task names exact paths and one verification command from the Local gates table.

## Consistency Checks

- The spec names three new behaviors: the export gate, the import gate, and the destination gate. Each has a task and a test.
- The plan names five top-level names in the module. The tasks add three, and the total stays within the five-item limit.
- The plan lowers the manager method count from 49 to 47. Task T005 removes two methods, and no task adds one.
- The record respects the five-child limit. The root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. The `design/` folder holds five children, and each of its subfolders holds two. The shared meta folder held 169 files from other issues before this run. It sits outside the record layout.
- The spec states the menu categories, prompts, and file names stay unchanged. Task T008 keeps the existing tests that cover them.
- The record uses the route from the brief. The route equals base-5 `122312` padded to eight digits (research R9).

## Unresolved Items

- **U-1**: The handover for the manager file is pending. Precondition P-1 blocks T002 until the handover exists.
- **U-2**: The symbol gate may treat added top-level names as a change. The tool source is not inspected. The fallback is to record the tool output and stop. Do not suppress the gate.
- **U-3**: No live Mist response confirms the refusal body. The tests use native SDK response objects.
- **U-4**: Operators may hold legacy bundles in `data/`. The import rejects them, and the operator must run menu 58 again.
- **U-5**: The SDK guard counts after the change are not measured. Task T011 measures them.
- **U-6**: The pylint score and the coverage after the change are not measured. Task T-LOCAL-GATES measures them.
