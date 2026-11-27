# Specification Analysis Report: Gated Converter Administration and Unassignment

## Result

The record covers the administrative scope of issue 4645 and tasks T025 and T026 of the full-parity task map.
The analysis compares the specification, the plan, the tasks, the contracts, the research, and the remote code on `main`.
Sixteen findings remain. Three need an owner decision. Two need a structural change in issue 4636.
Documentation readiness is not product readiness. Each live write stays blocked by gates G2, G3, G4, and G5.

## Findings

| ID | Category | Severity | Location | Summary | Required disposition |
| --- | --- | --- | --- | --- | --- |
| F-01 | Structure | HIGH | `plan.md` source map. Constitution Principle I. RC-07 and RC-08. | The converter root holds five children. Issue 4636 fills the root with `state/`. The administration package needs a sixth root child. | Decision D-6. Issue 4636 moves `conversion.py` into `engine/` in its T004 change. Task T002. |
| F-02 | Structure | HIGH | Live `tasks.md` line 90 (RC-39). RC-13. | The T025 path `tests/contract/cisco_config_converter/test_administration.py` adds a direct child to `tests/contract/`. That folder holds 17 children. | Decision D-5. Tests use the converter integration folder. This matches issue 4636 decision D-2. |
| F-03 | Contract | HIGH | RC-31, RC-30, RC-32, RC-34, RC-38. | The live contract has no site-template operation. The OpenAPI sends site-template assignment through `updateSiteInfo` and the `sitetemplate_id` field. The null value that unassigns is unverified. | Decision D-3, human. The path is refused under FR-015. Task T003. |
| F-04 | Contract | HIGH | RC-35 and RC-70. UV-01 and UV-09. | Network deletion needs reference reads, such as `listOrgNetworkTemplates`. The live contract has no network template row. | Issue 4634 adds verified reads before task T010. The scope review blocks each unverified reference (FR-007). |
| F-05 | Scope | MEDIUM | RC-33 and RC-65. Issue 4634 comment dated 2026-11-10. | Operation `deleteOrgServicePolicy` exists in the OpenAPI file and the SDK. The live contract omits it. Issue 4634 asks whether the converter needs it. | Decision D-13. The operation stays out of scope. Issue 4649 records the owner disposition. |
| F-06 | Scope | MEDIUM | Live `research.md` line 113 (RC-43). | Row C29 names templates without a family. The live contract maps template deletion to gateway templates only. | Decision D-4. Only gateway templates are in scope. |
| F-07 | Identity | HIGH | Issue 4636 decision D-10 (local draft). Issue 4633 coordinator decision (2026-11-08). | Issue 4636 records that no operator identity provider exists in the repository. Production cannot verify an operator. | Decision D-1, human. Production refuses every identity (FR-003). |
| F-08 | Dependency | MEDIUM | Issue body lists prerequisites 4633, 4634, 4635, and 4643. Live `tasks.md` line 149 (RC-39). | Issue 4645 omits issue 4636. Tasks T025 and T026 depend on the state types that issue 4636 defines (task T006). | Issue 4636 is added to `depends_on_issues`. |
| F-09 | Scope | MEDIUM | Issue 4645 section UI Behavior. Live `tasks.md` lines 90 and 91 (RC-39, RC-40). | The issue requires scope display, backup status, and no stale execution. Neither live task names a UI file. | Tasks T008 and T012 add the page (decision D-15). |
| F-10 | Test location | MEDIUM | RC-14 and the repository rule for UI tests under `tests/e2e/`. | `tests/e2e/` already holds five children. A new folder breaks the rule. | Decision D-5. The page test uses the Flask test client in the feature folder. Issue 4647 confirms the location. |
| F-11 | Class limit | MEDIUM | RC-05. Live `tasks.md` line 91 (RC-40). | Class `ConverterRoutes` already holds five members. The live task names `routes.py` only. | Decision D-6. Class `AdministrationRoutes` holds four members in `routes.py`. Logic sits in `engine/administration/`. |
| F-12 | Merge policy | HIGH | RC-48. Repository rule in AGENTS.md lines 230 and 231. | A merge plan that adds `auto-merge` after orchestrator approval conflicts with the rule for destructive-operation changes. | Decision D-14. The pull request gets no `auto-merge` label. A human reviews the change. |
| F-13 | Unverified references | HIGH | UV-01, UV-02, RC-23, RC-24, RC-25. | The OpenAPI descriptions do not state reference behavior for a deletion. The live contract names no reference field. | The scope review blocks any reference that it cannot verify (FR-007). Task T003 closes UV-01 and UV-02. |
| F-14 | Pending draft | MEDIUM | RC-08 and RC-09. Issue 4636 draft in a local record. | This record names `state/` types from issue 4636. Those files are not on `main`. | Task T001 blocks task T010 until issue 4636 merges. |
| F-15 | Route capacity | LOW | RC-47. | The route ancestor `specs/numbered/0/0/1/2/2` holds three children. This record adds one. | Pass. No action required. |
| F-16 | Shared portal | MEDIUM | RC-15 and RC-57. | `web_portal/app.py` has no converter registration. PR 4208 owns the shared files. | Decision D-16. Registration waits for issue 4648. |

## Coverage Summary

| Requirement | Tasks | Tests or verification |
| --- | --- | --- |
| FR-001 | T005, T009, T011 | `test_admin_routes_return_404_when_mode_disabled` |
| FR-002 | T005, T009 | `test_family_disabled_refuses_with_403` |
| FR-003 | T005, T010 | `test_missing_operator_identity_refuses_with_403` |
| FR-004 | T005, T011 | `test_csrf_failure_refuses_before_any_read` |
| FR-005 | T006, T010 | `test_scope_accepts_explicit_ids_and_computes_digest`, `test_scope_rejects_empty_duplicate_malformed_and_oversize` |
| FR-006 | T006, T010 | `test_scope_digest_changes_when_any_object_changes` |
| FR-007 | T006, T010 | `test_reference_outside_scope_blocks_review` |
| FR-008 | T006, T010 | `test_missing_or_unverified_backup_blocks_review`, `test_wrong_organization_or_family_backup_blocks_review` |
| FR-009 | T007, T010 | `test_missing_or_wrong_typed_confirm_refuses_without_writes`, `test_missing_scope_confirmation_refuses_without_writes` |
| FR-010 | T007, T010 | `test_approval_expires_at_fifteen_minutes_inclusive`, `test_reused_approval_refuses` |
| FR-011 | T007, T010 | `test_changed_before_state_stops_run` |
| FR-012 | T006, T010 | `test_unavailable_store_refuses_before_write` |
| FR-013 | T007, T010 | `test_device_profile_unassign_sends_only_reviewed_macs` |
| FR-014 | T007, T010 | `test_delete_calls_one_sdk_function_per_object_with_explicit_arguments` |
| FR-015 | T003, T007, T010 | `test_site_template_unassign_refuses_until_verified` |
| FR-016 | T007, T010 | `test_unknown_write_result_is_indeterminate_without_retry` |
| FR-017 | T007, T010 | `test_failed_write_stops_and_marks_remaining_not_attempted` |
| FR-018 | T007, T010 | `test_outcome_recorded_per_object_and_redacted` |
| FR-019 | T007, T010 | `test_device_profile_unassign_sends_only_reviewed_macs`, `test_delete_calls_one_sdk_function_per_object_with_explicit_arguments` |
| FR-020 | T007, T010 | `test_outcome_recorded_per_object_and_redacted` (asserts the log lines) |
| FR-021 | T008, T012 | `test_page_shows_scope_digest_and_backup_state` |
| FR-022 | T008, T012 | `test_page_shows_scope_digest_and_backup_state` (asserts `data-testid` values) |
| FR-023 | T011, T-MERGE | Quickstart Scenario 8 (no match in `web_portal/app.py`) |
| FR-024 | T005, T006, T007 | Each refusal test asserts zero SDK write calls. Test 5 covers the set. |
| FR-025 | T002, T010 | `python -m pytest tests/guardrails/test_move_module_guidance.py` |
| FR-026 | T003, T010 | `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` |
| FR-027 | T009 | Quickstart Scenario 6 (`Select-String` on `deploy\.env.example`) |
| FR-028 | T013 | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` |

| Success criterion | Tasks | Evidence |
| --- | --- | --- |
| SC-001 | T005, T008 | Tests 1 and 24 |
| SC-002 | T005, T006, T007 | Zero-call assertions in each refusal test |
| SC-003 | T007 | Tests 13, 14, and 15 |
| SC-004 | T007 | Test 23 |
| SC-005 | T007 | Tests 18 and 19 |
| SC-006 | T008 | Test 26 |
| SC-007 | T-LOCAL-GATES | Existing tests in `test_routes.py` |

Tasks T005 to T008 plan 26 tests. Each planned test appears in the coverage table.

## Constitution Alignment

- Principle I. Pass after the `engine/` move. The folders hold five children or fewer.
- Principle II. Pass. Behavior sits in classes with descriptive names.
- Principle III. Pass. Typed confirmation, refusal before writes, and read-back.
- Principle IV. Pass for this record. Pending for implementation. The final tasks cover each pipeline step.
- Principles V, VI, and VII. Pass by task requirements. Each task requires ASCII logs, inline comments, and action logs.
- Technology constraints. Pass. The design uses mistapi functions only.
- Task verification. Tasks T001, T009, and the final tasks use a check that the local gate table does not list. T001 reads issue state. T009 matches text in the environment template, because no gate reads that file. The final tasks read pull request state. Each check appears in `design/quickstart.md`.

## Unresolved Items

| ID | Owner | Item | Blocks |
| --- | --- | --- | --- |
| O-1 | Owner | Operator identity and authorization policy (decision D-1) | Any run in production |
| O-2 | Owner | Enablement of each family, recovery limits, and retention (decision D-2) | Any live write |
| O-3 | Owner | Site-template unassignment semantics (decision D-3) | The site-template path |
| O-4 | Issue 4634 owner | Verified contract rows in `design/contracts/mist-administration.md` (task T003) | Each write family |
| O-5 | Issue 4636 owner | `engine/` move and capacity slot (decision D-6, task T002) | Task T010 |
| O-6 | Issue 4643 owner | Backup manifests with complete prior state (UV-11) | The backup gate |
| O-7 | Issue 4648 owner | Shared portal registration after PR 4208 releases the files (decision D-16) | Operator access |
| O-8 | Issue 4647 owner | Confirmation of the page test location (finding F-10) | The page test location |

## Metrics

| Measure | Count |
| --- | --- |
| Functional requirements | 28 |
| Success criteria | 7 |
| User stories | 4 |
| Tasks, including final tasks | 17 |
| Planned tests | 26 |
| Remote checks | 72 |
| Decisions | 16 |
| Human decisions | 3 |
| Findings | 16 |
| Open items | 8 |

## Convergence After Implementation

The implementation converges when each planned test passes. Each finding needs a recorded disposition in the pull request. Each open item needs a closed state or an owner acceptance. Re-run the coverage table after T010 and T011. Re-run the remote checks after each merge to `main`.
