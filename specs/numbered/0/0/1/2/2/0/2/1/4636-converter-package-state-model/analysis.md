# Specification Analysis Report: Compliant Converter Package and State Model

## Result

The specification, plan, tasks, data model, contracts, and research agree on the layout, the test paths, and the gate list. The change keeps the converter root at five children. It replaces `models.py` with a compliant `state/` package. It adds no route, no shared portal file, and no Mist call.

The record finds fourteen defects in existing work. Four are high severity. Two of the defects change the T004 and T006 paths in the merged full-parity record. Fifteen decisions appear in `design/research.md`. Three decisions need a human owner.

Nothing was executed in this drafting pass. The repository rules forbid tests, linters, and builds here. The read-only checks in `design/research.md`, section R4, ran against GitHub `main`.

## Metrics

| Measure | Value |
| --- | --- |
| Functional requirements | 23 (FR-001 to FR-023) |
| Success criteria | 7 (SC-001 to SC-007) |
| User stories | 6 (3 at P1, 3 at P2) |
| Tasks | 17 (13 implementation or audit tasks and 4 final tasks) |
| Planned test functions | 25 |
| Decisions | 15, of which 3 need a human owner (D-10, D-14, D-15) |
| Remote checks | 60 rows in `design/research.md`, section R4 |
| Defects in existing work | 14 |
| Unresolved items | 13 (U-1 to U-13 in `design/research.md`) |

## Defects in Existing Work

| ID | Severity | Location | Summary | Disposition |
| --- | --- | --- | --- | --- |
| E-01 | HIGH | `src/interfaces/portals/cisco_config_converter/models.py`, lines 13, 21, 29, 38, 84. Full-parity `tasks.md`, line 36. | `models.py` holds five top-level classes, which is the limit. Full-parity T006 places six new types in the same file. | D-1. T004 replaces the file with `state/`. |
| E-02 | HIGH | Full-parity `tasks.md`, lines 36 and 44. Remote folder `tests/contract/` holds 17 children. | The T006 path adds a direct child to a noncompliant parent. T007 to T031 place at least eleven test files in one folder. | D-2. The tests use `tests/integration/web_portal/cisco_config_converter/state/`. |
| E-03 | HIGH | `web_portal/services/config.py`, line 113. | Without `PORTAL_SECRET_KEY`, each process uses a random key. Sessions and review records fail after a restart and across workers. | D-5 and D-15. The store refuses writes when the variable is empty. The shared fallback changes only after owner approval. |
| E-04 | HIGH | `deploy/.env.example`, line 155. | The portal has no user authentication. No verified operator identity exists, so no write-capable approval can be trusted. | D-10. The approval refuses unverified operators. The owner must approve an identity design. |
| E-05 | MEDIUM | `models.py`, line 51. Full-parity `spec.md`, line 111. Unit test, line 39. | The converter accepts `standalone` and `spoke`. FR-005 requires `Branch`, `Hub`, and `Standalone`. The unit test asserts that `hub` is refused. | D-11. The change keeps the current values until T011 and T012. |
| E-06 | MEDIUM | Parent record `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md`, lines 15 and 93. | The parent cites Python 3.13. The repository rule requires 3.15 (`.github/copilot-instructions.md`, line 20). The parent also cites `tests/unit/gateway/overrides/`, which is absent on `main`. | Corrected in a separate documentation change. This record does not edit the parent. |
| E-07 | MEDIUM | Full-parity `plan.md`, lines 79, 80, and 84. | The plan names the old unit test folder. It also says the layout is unresolved. This record resolves the layout. | The full-parity owner updates the path. This record supersedes the layout for the converter package. |
| E-08 | MEDIUM | Full-parity `tasks.md`, T029. Remote folder `tests/e2e/web_portal/` holds 32 children. Folder `tests/e2e/` holds five. | T029 proposes a new file in an overfull folder. | Remediation R-3. |
| E-09 | MEDIUM | Full-parity `design/data-model.md`, lines 43 to 50. | The transition diagram omits edges that the same file's prose requires, for input change, target change, and failed recovery. | D-12. The added edges appear in `design/data-model.md`, section Added edges. |
| E-10 | MEDIUM | `routes.py` has zero `#` comments. `conversion.py` has zero. `models.py` has one. | AGENTS.md, line 97, and constitution Principle VI require an inline comment on each executable line. | T004 and T012 add comments to each touched and new line. |
| E-11 | MEDIUM | `models.py` has zero logger calls. | AGENTS.md, line 104, and constitution Principle VII require action logs. | T010 logs each store action. T012 audits the change. |
| E-12 | LOW | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`. PR #4358 moved the file on 2026-11-13. | The converter test sits in a folder that does not match its subject. | Observation only. No move in this change. |
| E-13 | LOW | Nested package guard, `tests/guardrails/test_nested_package_structure.py`, lines 89 to 117. | The guard counts three children for the converter root. The constitution counts five. | Both counts appear in `plan.md`. |
| E-14 | MEDIUM | Coordinator comments on issue 4636 cite main `3964d21` and "open PR #4596". | Main is now `f03c6c9`, dated 2026-11-26. PR #4596 is merged, dated 2026-11-13. | This record uses current `main`. The comments remain historical. |

## Remediation Actions

These actions track structure debt that this change does not touch. Each action belongs in a separate issue.

- R-1: `src/interfaces/portals/` holds six physical children, including `__init__.py`. Group `guest_authorizations.py` under a compliant subpackage in a separate issue.
- R-2: `tests/contract/` holds 17 children. Group the children into compliant subfolders in a separate issue.
- R-3: `tests/e2e/web_portal/` holds 32 children. `tests/e2e/` holds five. The owner of task T029 must reduce `tests/e2e/` or choose a path under an existing feature folder.

## Unresolved Items

| ID | Owner | Action |
| --- | --- | --- |
| U-1 | Implementer | Run the lock contention check on Windows during T011. |
| U-2 | Owner | Confirm that stdlib key=value logs meet the constitution's "structlog or equivalent" rule. |
| U-3 | Owner | Declare or decline an operational store under gate G4. |
| U-4 | Owner | Confirm that the data backup covers `data/cisco_config_converter/state/`. |
| U-5 | Owner | Confirm the Windows ACL for the private directory. |
| U-6 | Implementer | Record the symbol gate result for the removed `models.py` in the pull request. |
| U-7 | Implementer | Measure the runtime of the two-process tests on CI. |
| U-8 | Orchestrator | Decide whether the new Markdown files join the STE gate. |
| U-9 | Owner | Approve an identity and authorization design before any cloud write. Decision D-10. |
| U-10 | Owner | Resolve the license question under issue 4635. Decision D-14. |
| U-11 | Owner | Report whether production sets `PORTAL_SECRET_KEY`. Decision D-15. |
| U-12 | Implementer | Read the `MYPY_PATHS`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` values from `.github/workflows/ci.yml` before T-LOCAL-GATES. |
| U-13 | Orchestrator | Note that the mistapi evidence is local to `.venv`. No SDK call is made in this change. |

## Coverage Summary

Each requirement maps to at least one task and at least one test.

| Requirement | Tasks | Tests or gate |
| --- | --- | --- |
| FR-001 | T003, T012, T013 | `test_structure_stays_within_five_children`, nested package guard |
| FR-002 | T003 | Nested package guard. The inventory appears in `plan.md`. |
| FR-003 | T004, T013 | Unit test `test_cisco_config_converter.py`, move guard |
| FR-004 | T005, T006 | Record tests in `test_state_records.py` |
| FR-005 | T005, T006 | `test_digest_matches_existing_review_digest`, `test_digest_changes_when_any_proposal_field_changes` |
| FR-006 | T006, T009, T010 | `test_tampered_record_fails_seal_check`, `test_changed_secret_refuses_existing_records` |
| FR-007 | T005, T006, T009 | `test_public_view_redacts_secret_fields`, `test_public_view_omits_source_text`, `test_write_logs_before_and_after_without_secret` |
| FR-008 | T005, T006 | `test_review_expires_at_fifteen_minutes_utc`, `test_naive_timestamp_is_refused` |
| FR-009 | T005, T006, T007, T010, T011 | `test_approval_refused_for_changed_proposal_or_scope`, `test_expired_or_consumed_approval_cannot_start_execution`, `test_two_processes_consume_one_approval_once` |
| FR-010 | T005, T006 | `test_approval_refused_without_verified_operator` |
| FR-011 | T007, T008 | `test_documented_transitions_are_accepted`, `test_undocumented_transitions_are_refused` |
| FR-012 | T007, T008 | `test_indeterminate_operation_cannot_start_execution` |
| FR-013 | T009, T010 | `test_write_refused_without_portal_secret`, `test_write_refused_when_data_path_is_a_file`, `test_default_store_refuses_production_writes` |
| FR-014 | T009, T010 | `test_read_back_mismatch_reports_no_success` |
| FR-015 | T009, T010 | `test_restart_reads_records_and_keeps_expiry`, `test_changed_secret_refuses_existing_records` |
| FR-016 | T010, T011 | `test_two_processes_consume_one_approval_once`, `test_lock_holder_exit_releases_ownership` |
| FR-017 | T005, T006 | `test_backup_manifest_rejects_incomplete_pagination`, `test_backup_manifest_rejects_count_checksum_organization_or_family_defects` |
| FR-018 | T001, T013 | `test_complete_offline_journey` in `test_routes.py`, move guard, empty diff for shared files |
| FR-019 | T002, T004 | `test_routes.py` and the unit test, both unchanged in behavior |
| FR-020 | T006, T010, T012 | `test_write_logs_before_and_after_without_secret`, complexity gate, manual comment audit |
| FR-021 | T009, T010 | `test_default_store_refuses_production_writes` |
| FR-022 | T005, T009, T011 | Each test uses `tmp_path`. The output scan test `tests/unit/web_portal/test_output_scan_runtime_files.py` runs in T-LOCAL-GATES. |
| FR-023 | T003, T005, T013 | `test_structure_stays_within_five_children` counts the new test folder and its child package |

The structure test in `test_state_records.py` must count the `state/` package, its two subpackages, and the new test folder. Task T005 states this requirement.

## Success Criteria Coverage

| Criterion | Evidence |
| --- | --- |
| SC-001 | Nested package guard and the structure test |
| SC-002 | Test run of all four modules, with 25 functions and no skip |
| SC-003 | `test_complete_offline_journey` blocks sockets. The state tests use no network call. |
| SC-004 | `test_undocumented_transitions_are_refused` covers every undocumented pair in its parameter list |
| SC-005 | `test_two_processes_consume_one_approval_once`, repeated 20 times in T-LOCAL-GATES |
| SC-006 | `test_restart_reads_records_and_keeps_expiry` and `test_changed_secret_refuses_existing_records` |
| SC-007 | Coverage gate in T-LOCAL-GATES |

## Consistency Review

| Check | Result |
| --- | --- |
| Spec requirements appear in the plan and tasks | Pass. Every FR appears in the coverage table. |
| Each plan file path appears in a task | Pass. `models.py`, the six state modules, the storage modules, the three edited files, and the four test modules each appear in a task. |
| Test counts agree across documents | Pass. The spec, tasks, and STATUS file all state 25. |
| Module names agree across plan, contracts, and data model | Pass. The contract table and the plan symbol map list the same names in the same modules. |
| Transition table references agree | Pass. `tasks.md` T008 and `design/data-model.md` both name the documented edges and the added edges. |
| Remote facts match the record | Pass. Each remote row in `design/research.md`, section R4, records a blob SHA equal to local `HEAD`. |
| Directory counts match the remote listing | Pass. Counts appear in `plan.md` and `design/research.md`, section R6. |
| Dates and PR states match the remote record | Pass. PR #4596, PR #4358, and PR #4226 are merged. PR #4208 is open. |
| Writing style of the record | Pass after self-review. Each deliverable file was searched for semicolons, contractions, Latin abbreviations, unfinished markers, and long sentences. |

## Constitution Alignment

The constitution check in `plan.md` lists each rule with its result. Two rules fail until open items close. Principle V (structured logs) waits for U-2. Principle VI (inline comments) and Principle VII (action logging) fail on existing code and pass after the tasks in this record run.

## Validation Commands and Results

| Command | Result |
| --- | --- |
| `python -m ruff check .` | Not run. Reason: the drafting rules forbid linters in this pass. |
| `python -m black --check .` | Not run. Reason: the drafting rules forbid formatters in this pass. |
| `python -m mypy $MYPY_PATHS --config-file pyproject.toml` | Not run. Reason: the drafting rules forbid type checks in this pass. |
| `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py` | Not run. Reason: the drafting rules forbid tests in this pass. |
| `python -m pytest tests/guardrails/test_nested_package_structure.py` | Not run. Reason: the drafting rules forbid tests in this pass. |
| `git -C <repo> ls-tree`, `git rev-parse HEAD:<path>`, and `gh api` reads | Run. Results appear in `design/research.md`, section R4, and in the local listings. |
| `Select-String` and directory listing on the local checkout | Run. Results appear in `design/research.md`, sections R5 and R6. |

The T-LOCAL-GATES task in `tasks.md` names every command that the implementer must run before the pull request.
