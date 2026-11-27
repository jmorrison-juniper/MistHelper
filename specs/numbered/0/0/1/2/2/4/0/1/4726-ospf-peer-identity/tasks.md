# Tasks: OSPF Peer Identity Keys

**Input**: Design documents in `specs/numbered/0/0/1/2/2/4/0/1/4726-ospf-peer-identity/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: The specification (FR-001 to FR-018) and the constitution (Principle IV) require tests. Each test task comes before its implementation task, and each new test fails first.

**Status legend**:

- `absent`: The required deliverable is not on `main`. Remote checks RV-86 to RV-88 and RV-01 confirm it.
- `verified-present`: The deliverable already exists on `main`. Remote checks confirm it.
- `open`: The task is a process step with no code deliverable yet.

**Format**: `[ID] [P?] [Requirements] Description. Paths. Acceptance. Verify. Status.`

## Phase 1: Failing Tests

- [ ] T001 [P] [FR-001 to FR-005, FR-013 to FR-015, SC-006] Write sixteen identity tests in `tests/unit/db/test_ospf_peer_identity.py`. Acceptance: the file has these test functions. `test_identity_key_is_stable_for_the_same_identity`, `test_identity_key_differs_when_neighbor_differs`, `test_identity_key_differs_when_vrf_name_differs`, `test_identity_key_differs_when_port_id_differs`, `test_absent_scope_is_distinct_from_literal_unknown`, `test_empty_scope_string_is_treated_as_absent`, `test_peer_ip_is_used_only_when_neighbor_is_absent`, `test_missing_required_component_is_rejected`, `test_timestamp_forms_produce_one_key`, `test_invalid_timestamp_is_rejected`, `test_applies_only_to_the_two_ospf_endpoints`, `test_storage_table_name_adds_v2_suffix`, `test_attach_returns_copies_and_keeps_input_unchanged`, `test_strategy_entries_name_the_identity_key_as_primary_key`, `test_other_endpoints_keep_their_primary_keys`, and `test_attach_logs_count_without_identity_values`. The tests fail before T004. Verify: `python -m pytest tests/unit/db/test_ospf_peer_identity.py`. Status: absent.

- [ ] T002 [P] [FR-003, FR-006 to FR-008, FR-018, SC-001, SC-003, SC-004] Add four SQLite storage tests to `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py`. Acceptance: the file adds `test_ospf_records_with_same_mac_and_timestamp_keep_distinct_neighbors`, `test_ospf_legacy_table_is_unchanged_after_v2_write`, `test_ospf_v2_table_with_wrong_primary_key_fails_closed`, and `test_ospf_batch_with_missing_neighbor_writes_no_rows`. Each test uses `tmp_path`. The tests fail before T006. Verify: `python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py`. Status: absent.

- [ ] T003 [P] [FR-003, FR-009 to FR-011, SC-002] Add two router tests to `tests/unit/config/standalone/foundation/persistence/database/test_router.py`. Acceptance: the file adds `test_ospf_composite_write_uses_identity_key_for_redis_and_arango` and `test_ospf_invalid_record_returns_failed_write_without_backend_calls`. Both tests use fake Redis and fake ArangoDB backends. The tests fail before T007. Verify: `python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py`. Status: absent.

## Phase 2: Identity Class and Strategy

- [ ] T004 [FR-001 to FR-005, FR-015] Add class `OspfPeerIdentity` in `src/foundation/persistence/identity/ospf_peer.py` and the package marker in `src/foundation/persistence/identity/__init__.py`. Acceptance: the class offers `applies`, `storage_table_name`, `identity_key`, `attach`, and `verify_primary_key`. Each line has an inline comment. Each action logs an info line before and a debug line after. The T001 tests pass. Depends on T001. Verify: `python -m pytest tests/unit/db/test_ospf_peer_identity.py`. Status: absent.

- [ ] T005 [FR-013, FR-014] Change the `primary_key` of `searchSiteOspfStats` and `searchOrgOspfStats` to `["misthelper_ospf_peer_key"]` in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`. Acceptance: the two entries name the identity key. The `searchOrgBgpStats` entry is unchanged. Contingency: if `tests/contract/test_arango_declared_indexes.py` fails, add the identity key to both `indexes` lists and record the cause in the pull request. Depends on T004. Verify: `symbol-diff --base origin/main src/foundation/support/refactors/endpoint_primary_key_strategies.py`. Status: absent.

## Phase 3: Writer Integration

- [ ] T006 [FR-006 to FR-008, FR-015, FR-018] Modify `src/foundation/support/refactors/sqlite_database_writer.py`. `_process_data` renames the table to `<name>_v2` and attaches keys for OSPF endpoints. `_create_table_and_indexes` calls `OspfPeerIdentity.verify_primary_key` before `_create_schema_table`. Acceptance: the T002 tests pass. No legacy table receives a write. Depends on T002, T004, and T005. Verify: `python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py`. Status: absent.

- [ ] T007 [FR-003, FR-009 to FR-011] Modify `src/foundation/persistence/db/router.py`. `write` attaches keys after `_resolve_strategy` for OSPF endpoints. A `ValueError` returns `_error_write_result` before any leg runs. Acceptance: the T003 tests pass. Depends on T003, T004, and T005. Verify: `python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py`. Status: absent.

- [ ] T008 [FR-012, SC-005] Confirm the CSV contracts of menus 55, 70, and 225 with the existing export tests. No file changes. Acceptance: the three existing files pass without edits. Tests are `test_ospf_stats` in `tests/unit/export/test_org_export_utils.py`, `test_ospf_stats_invokes_generic_exporter` in `tests/unit/export/test_site_export_utils_extended.py`, and the OSPF row of `tests/unit/export/test_site_search_exporter.py`. Depends on T006 and T007. Verify: `python -m pytest tests/unit/export/test_site_search_exporter.py tests/unit/export/test_site_export_utils_extended.py tests/unit/export/test_org_export_utils.py`. Status: verified-present.

## Phase 4: Documentation

- [ ] T009 [P] [FR-016, FR-017] Add a paragraph after the SQLite row of the output table in `documentation/operator-guide.md`. Name the two table patterns: `SiteOspfStats_<site>_v2` for menus 70 and 225, and `OrgOspfStats_v2` for menu 55. State that legacy tables stay unchanged. Add `changelog.d/issue-4726-ospf-peer-identity.md` with one `### Fixed` heading and one bullet that names issue #4726. Depends on T006 and T007. Verify: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md documentation/operator-guide.md changelog.d/issue-4726-ospf-peer-identity.md`. Status: absent.

## Final Tasks

- [ ] T-LOCAL-GATES [FR-001 to FR-018, SC-006] Run each applicable row of the Local gates table on the changed files. Record the exact output of each command. Acceptance: each applicable gate passes. The gate rows that do not apply carry the reason in `design/checklists/gates.md`. Depends on T008 and T009. Verify: `python -m ruff check .`, then `python -m black --check .`, `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`, then `python -m pytest tests/guardrails`. Status: open.

- [ ] T-PR [FR-017, SC-006] Create branch `fix/4726-ospf-peer-identity` from `main`. Commit with `fix(persistence): key OSPF peer records by identity`. Put `Closes #4726` in the body. Open a pull request with the same title and the gate results. Repeat the Preconditions check first. Depends on T-LOCAL-GATES. Verify: `python -m pytest tests/guardrails`. Status: open.

- [ ] T-REMOTE-CI [SC-006] Watch the remote checks of the pull request until each required check passes. Depends on T-PR. Verify: `gh pr checks <number> --watch`. Status: open.

- [ ] T-MERGE [SC-006] Add the `auto-merge` label only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Depends on T-REMOTE-CI. Verify: `gh pr view <number> --json state,mergedAt`. Status: open.

## Dependencies and Execution Order

- T001, T002, and T003 run in parallel. Each edits a different file.
- T004 depends on T001. T005 depends on T004.
- T006 depends on T002, T004, and T005. T007 depends on T003, T004, and T005.
- T008 depends on T006 and T007. T009 depends on T006 and T007.
- T-LOCAL-GATES depends on T008 and T009. T-PR, T-REMOTE-CI, and T-MERGE run in order.

## Requirement Coverage

- FR-001 to FR-005: T001, T004.
- FR-006 to FR-008 and FR-018: T002, T006.
- FR-009 to FR-011: T003, T005, T007.
- FR-012: T008.
- FR-013 and FR-014: T001, T005.
- FR-015: T001, T004, T006.
- FR-016 and FR-017: T009, with the STE check and the guardrail run in T-LOCAL-GATES.
