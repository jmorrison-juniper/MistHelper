# Tasks: Private Configuration Backup and Verified Catalog

**Input**: `spec.md`, `plan.md`, and the supporting artifacts under `design/`.

**Prerequisites**: Issue 4633 is closed. Its decisions allow offline code and synthetic tests. Issue 4634 is open. Issue 4636 is open and must merge before any implementation task starts. PR 4596 is merged.

**Rules for this list**: Each task names exact repository paths and one verification command from the local gates table. Mark a task done only after its verification passes and its evidence exists. Status values are `open`, `verified-present`, `partial`, or `absent`.

## Format

- `[P]`: The task can run in parallel with other `[P]` tasks. It uses different files and has no shared dependency.
- `FR-###`: The requirement IDs in `spec.md` that the task satisfies.
- `Depends on`: The tasks or prerequisites that must pass first.

## Phase 1: Prerequisites and Evidence

- [ ] T001 [P] Record the approval chain and the open gates in this record.
  - Requirements: FR-026
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/3/3/4643-private-config-backup-catalog/spec.md`, `specs/numbered/0/0/1/2/2/0/3/3/4643-private-config-backup-catalog/design/research.md`
  - Acceptance: The record cites both owner comments by ID, the coordinator decisions in issues 4633 and 4636, and each open gate.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 spec.md`
  - Status: partial. The offline scope and the storage approval are verified. Gate G2 and the issue 4636 gate are open.

- [ ] T002 [P] Run the reused firmware SDK contract test before any edit.
  - Requirements: FR-023, FR-027
  - Depends on: None
  - Paths: `tests/contract/firmware_policy/recovery/test_sdk.py`, `src/operations/execution/firmware_policy/sdk.py`, `src/operations/execution/firmware_policy/recovery/backup.py`
  - Acceptance: The test file passes on the unchanged `main` tree. The pull request records the test count.
  - Verification: `python -m pytest tests/contract/firmware_policy/recovery/test_sdk.py`
  - Status: open. This drafting pass ran no tests.

- [ ] T003 Record the list-operation evidence and the relationship fields for each family.
  - Requirements: FR-007, FR-013, FR-023
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/3/3/4643-private-config-backup-catalog/design/contracts/mist-list-reads.md`, `specs/numbered/0/0/1/2/2/0/3/3/4643-private-config-backup-catalog/design/data-model.md`
  - Acceptance: The contract file gives, for each operation, the OpenAPI path and line, the SDK signature, the header evidence, and the item evidence. The data model gives the relationship rows. The owner records the open items on issue 4634.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 design/contracts/mist-list-reads.md`
  - Status: partial. Method identity, signatures, and OpenAPI paths are verified. Header and item evidence are absent.

## Phase 2: Tests First

Caution: write each test module before its production code. Each test must fail before its implementation task passes.

- [ ] T004 [P] Write the capture tests before the capture code.
  - Requirements: FR-007, FR-008, FR-009, FR-010, FR-013, FR-022, FR-023, FR-026, FR-027
  - Depends on: T001, T003, issue 4636 merged
  - Paths: `tests/integration/web_portal/cisco_config_converter/backup/__init__.py`, `tests/integration/web_portal/cisco_config_converter/backup/test_backup_capture.py`
  - Acceptance: The module holds these ten test functions: `test_capture_reads_every_page_with_explicit_page_numbers`, `test_capture_refuses_absent_or_invalid_reported_total`, `test_capture_refuses_empty_page_before_reported_total`, `test_capture_refuses_repeated_object_identifier`, `test_capture_refuses_total_change_between_pages`, `test_capture_refuses_failed_or_malformed_page`, `test_capture_refuses_family_outside_scope`, `test_capture_calls_only_list_functions_with_explicit_arguments`, `test_capture_opens_no_network_socket`, and `test_capture_refuses_ambiguous_or_missing_relationship_target`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_capture.py`
  - Status: absent.

- [ ] T005 [P] Write the directory tests before the directory code.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-027
  - Depends on: T001, issue 4636 merged
  - Paths: `tests/integration/web_portal/cisco_config_converter/backup/test_backup_directory.py`
  - Acceptance: The module holds seven test functions: `test_directory_refuses_symbolic_link_root`, `test_directory_refuses_traversal_and_foreign_file_names`, `test_directory_refuses_hard_linked_backup_file`, `test_directory_refuses_inexact_modes_and_keeps_permissions`, `test_directory_propagates_unprovable_access_refusal`, `test_directory_checks_real_windows_acl`, and `test_directory_creates_missing_root_only_under_existing_data_directory`. The POSIX-only and Windows-only tests print a skip reason on other platforms.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_directory.py`
  - Status: absent.

- [ ] T006 [P] Write the writer tests before the writer code.
  - Requirements: FR-006, FR-014, FR-015, FR-021, FR-024, FR-025
  - Depends on: T001, issue 4636 merged
  - Paths: `tests/integration/web_portal/cisco_config_converter/backup/test_backup_writer.py`
  - Acceptance: The module holds four test functions: `test_writer_creates_exclusive_opaque_file_and_never_overwrites`, `test_writer_reports_success_only_after_readback_matches`, `test_writer_refuses_without_seal_key_and_creates_no_file`, and `test_writer_keeps_unverified_file_and_logs_without_bodies`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_writer.py`
  - Status: absent.

- [ ] T007 [P] Write the catalog tests before the catalog code.
  - Requirements: FR-016, FR-017, FR-018, FR-027
  - Depends on: T001, issue 4636 merged
  - Paths: `tests/integration/web_portal/cisco_config_converter/backup/test_backup_catalog.py`
  - Acceptance: The module holds four test functions: `test_catalog_lists_only_verified_matching_entries`, `test_catalog_refuses_corrupt_or_oversize_files_before_content_use`, `test_catalog_refuses_tampered_or_incomplete_backup_files`, and `test_catalog_returns_only_allowlisted_metadata`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_catalog.py`
  - Status: absent.

## Phase 3: Implementation

- [ ] T008 Implement `BackupDirectory` in the state lifecycle module.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005
  - Depends on: T002, T005, issue 4636 merged
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py`
  - Acceptance: `NAME` equals `.cisco-config-converter-backups`. The class calls `BackupAccess.verify` for the root and for each file. The class never calls `chmod` and never changes an owner. It creates only a missing directory, with mode 0700, under an existing data directory. The module holds five top-level names.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_directory.py`
  - Status: absent.

- [ ] T009 Implement `BackupCapture` in the state lifecycle module.
  - Requirements: FR-007, FR-008, FR-009, FR-010, FR-013, FR-023
  - Depends on: T003, T004, T008
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py`
  - Acceptance: The class reads pages with `listOrgNetworks`, `listOrgServices`, or `listOrgServicePolicies`. Each call uses `limit=1000` and an explicit `page`. The class uses `PolicyAdmission.request` and `PolicyResponse.request`, reads `X-Page-Total` on every page, and refuses each failure in FR-008. It wraps each read in `SettingsRequestGuard`. It never calls `PolicyResponse.collect`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_capture.py`
  - Status: absent.

- [ ] T010 Implement `BackupWriter` in the state lifecycle module.
  - Requirements: FR-006, FR-011, FR-012, FR-014, FR-015, FR-021, FR-024, FR-025
  - Depends on: T006, T008, T009
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py`
  - Acceptance: The writer reads `PORTAL_SECRET_KEY` from the environment only. It refuses when the variable is empty. It creates the file with `os.open`, `O_EXCL`, and mode 0600. It reads the file back and recomputes every digest, the count, each relationship, and the seal before it reports success. A failed read-back keeps the file.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_writer.py`
  - Status: absent.

- [ ] T011 Implement `BackupCatalog` in the state lifecycle module.
  - Requirements: FR-011, FR-016, FR-017, FR-018
  - Depends on: T007, T008, T010
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py`
  - Acceptance: The method `entries` returns metadata only. It counts each exclusion by reason. It checks the file size before any read. It refuses duplicate keys, non-finite numbers, unknown schema versions, incomplete pagination, and a bad seal. The class constant `MAX_BYTES` equals 134217728.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_catalog.py`
  - Status: absent.

- [ ] T012 Run the SDK compatibility guard and the nested package guard.
  - Requirements: FR-023, FR-028
  - Depends on: T009, T011
  - Paths: `tests/integration/test_mistapi_sdk_compatibility.py`, `tests/guardrails/test_nested_package_structure.py`
  - Acceptance: Both guards pass. The nested guard reports its examined count and no new violation.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py`
  - Status: open.

## Phase 4: Integration (separate pull request)

- [ ] T013 Add the shared-file exclusions and their two tests in a separate integration pull request.
  - Requirements: FR-019, FR-020
  - Depends on: T011 merged, issue 4633 handover, feature pull request merged
  - Paths: `web_portal/services/output_scan.py`, `web_portal/services/data_browser.py`, `tests/unit/web_portal/test_output_scan_runtime_files.py`, `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py`, `changelog.d/pr-<number>.md`
  - Acceptance: `EXCLUDED_DIR_NAMES` contains `BackupDirectory.NAME`. The data browser refuses any path that contains the directory name. The two integration tests in `contracts/shared-exclusions.md` pass. The pull request touches no other shared file.
  - Verification: `python -m pytest tests/unit/web_portal/test_output_scan_runtime_files.py`
  - Status: absent.

## Phase 5: Final Tasks

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files.
  - Requirements: FR-025, FR-027, FR-028
  - Depends on: T008, T009, T010, T011, T012
  - Paths: the feature pull request files listed in `plan.md`
  - Acceptance: Each applicable gate in `design/quickstart.md` passes. The pull request lists each command and its result. Each gate that does not apply carries its reason.
  - Verification: `python -m ruff check .`
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request for the feature change.
  - Requirements: FR-025
  - Depends on: T-LOCAL-GATES
  - Paths: the feature pull request files only. Add each file by its explicit path.
  - Acceptance: The commit subject uses Conventional Commits, for example `feat(converter): add private backup catalog`. The body holds `Closes #4643` and the Copilot co-author trailer. The pull request body lists each local gate result. The `in-progress` label is set before the branch starts.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/backup`
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks for the pull request.
  - Requirements: FR-028
  - Depends on: T-PR
  - Paths: none
  - Acceptance: Each required check reports success. A failed check gets a new issue with the full error output before any fix.
  - Verification: `gh pr checks <number> --watch`
  - Status: open. This command watches the remote gate. It is not a local gate.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-026
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: none
  - Acceptance: The `auto-merge` label is added only after every required check passes. The pull request holds no destructive operation. T013 stays in its own pull request.
  - Verification: `gh pr checks <number>`
  - Status: open.

## Dependency Summary

- T004 to T007 depend on T001 and T003, and they need issue 4636 merged for their imports.
- T008 depends on T005. T009 depends on T004 and T008. T010 depends on T006, T008, and T009. T011 depends on T007, T008, and T010.
- T013 depends on the feature pull request and the issue 4633 handover. It runs in a separate pull request.
- Task count: 17. Thirteen numbered tasks and four final tasks.
