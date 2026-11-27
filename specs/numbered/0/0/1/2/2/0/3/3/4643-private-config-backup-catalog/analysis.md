# Specification Analysis Report: Private Configuration Backup and Verified Catalog

## Result

The specification, plan, tasks, data model, contracts, checklists, and research agree on the layout, the test names, the decision IDs, and the remote evidence counts. The change adds no route, no shared portal file, and no Mist write. Every directory that the change touches keeps five children or fewer. The record finds thirteen defects in existing work. Two of them (E-01 and E-02) block the full-parity T023 and T024 paths as written. Two amendments to draft 4636 (A-1 and A-2) are required before implementation. Fourteen items remain unresolved. Two decisions need a human owner (D-18 and D-19).

Nothing was executed in this drafting pass. The repository rules forbid tests, linters, and builds here. The remote and local reads ran in full, as `design/research.md` records.

## Metrics

| Measure | Value |
| --- | --- |
| Functional requirements | 28 (FR-001 to FR-028) |
| Success criteria | 7 (SC-001 to SC-007) |
| User stories | 5 (3 at P1, 2 at P2) |
| Tasks | 17 (13 numbered tasks and 4 final tasks) |
| Planned test functions | 27 (25 in the feature folder, 2 in the integration pull request) |
| Decisions | 19 (17 decided, 2 human: D-18 and D-19) |
| Remote checks | 80 rows in `design/research.md`, of which 75 are present and 5 are absent |
| Defects in existing work | 13 (E-01 to E-13) |
| Actions | 10 (amendments A-1 to A-4 and structure items R-01 to R-06) |
| Unresolved items | 14 (U-01 to U-14) |

## Consistency Review

| Check | Result |
| --- | --- |
| Requirements in `spec.md` match the requirement table and the checklist | Pass. All 28 IDs appear in the table and in the coverage table below. |
| Each requirement maps to at least one task and at least one test or gate | Pass. The coverage table below lists each mapping. |
| Test names agree across `spec.md`, `tasks.md`, `plan.md`, and the contracts | Pass. The 25 feature test names appear in `tasks.md` T004 to T007 and in the contract test tables. |
| Decision IDs agree across `plan.md`, `research.md`, and the STATUS file | Pass. D-1 to D-19 appear in `research.md`. The STATUS file lists the same 19 IDs. |
| Remote row count agrees across the research table, the STATUS file, and the summary | Pass at drafting time. Each document reports 80 rows. Phase 3 of the drafting pass re-counts them. |
| Directory counts agree with the remote listing | Pass. Rows R-67 to R-71 record the counts for the five parent folders. The state and backup folders are absent (R-72, R-73). |
| Owner comment IDs and dates agree with the issue timeline | Pass. The two owner comments on issue 4643 and the coordinator decisions on issues 4633 and 4636 appear with their dates in `research.md`. |
| Relationship rows agree between the data model and the remote evidence | Pass. The data model cites R-52, R-53, R-54, and R-74. |
| Analysis IDs used in `plan.md` and `tasks.md` exist here | Pass. The plan cites E-01, E-04, U-08, U-09, U-13, R-01, R-05, and R-06. Each appears in this record. |
| Path rules: managed roots, five children, and no new child in a noncompliant parent | Pass. The change adds one new folder group under `tests/integration/web_portal/cisco_config_converter/` and edits one existing module. |
| Writing style of the record | Pass after the Phase 3 checks. The checks search for forbidden tokens, semicolons, and contractions. |

## Coverage Table

| Requirement | Tasks | Tests or gates |
| --- | --- | --- |
| FR-001 storage root | T005, T008 | `test_directory_creates_missing_root_only_under_existing_data_directory`, `test_directory_refuses_traversal_and_foreign_file_names` |
| FR-002 POSIX owner and modes | T005, T008 | `test_directory_refuses_inexact_modes_and_keeps_permissions` |
| FR-003 Windows owner and ACL | T005, T008 | `test_directory_propagates_unprovable_access_refusal`, `test_directory_checks_real_windows_acl` |
| FR-004 link, reparse, traversal, and outside-path refusals | T005, T008 | `test_directory_refuses_symbolic_link_root`, `test_directory_refuses_hard_linked_backup_file`, `test_directory_refuses_traversal_and_foreign_file_names` |
| FR-005 no permission change and no parent creation | T005, T008 | `test_directory_refuses_inexact_modes_and_keeps_permissions`, `test_directory_creates_missing_root_only_under_existing_data_directory` |
| FR-006 opaque name and exclusive creation | T006, T010 | `test_writer_creates_exclusive_opaque_file_and_never_overwrites` |
| FR-007 explicit page reads | T004, T009 | `test_capture_reads_every_page_with_explicit_page_numbers` |
| FR-008 completeness refusals | T004, T009 | `test_capture_refuses_absent_or_invalid_reported_total`, `test_capture_refuses_empty_page_before_reported_total`, `test_capture_refuses_repeated_object_identifier`, `test_capture_refuses_total_change_between_pages` |
| FR-009 page failure refusals | T004, T009 | `test_capture_refuses_failed_or_malformed_page` |
| FR-010 family scope | T004, T009 | `test_capture_refuses_family_outside_scope` |
| FR-011 identity fields | T006, T010, T011 | `test_writer_reports_success_only_after_readback_matches`, `test_catalog_lists_only_verified_matching_entries` |
| FR-012 completeness fields | T006, T010 | `test_writer_reports_success_only_after_readback_matches`, `test_capture_reads_every_page_with_explicit_page_numbers` |
| FR-013 relationship rule | T004, T009 | `test_capture_refuses_ambiguous_or_missing_relationship_target` |
| FR-014 seal and key refusal | T006, T010 | `test_writer_refuses_without_seal_key_and_creates_no_file`, `test_catalog_refuses_tampered_or_incomplete_backup_files` |
| FR-015 read-back before success | T006, T010 | `test_writer_reports_success_only_after_readback_matches` |
| FR-016 catalog scope and counts | T007, T011 | `test_catalog_lists_only_verified_matching_entries` |
| FR-017 catalog refusals | T007, T011 | `test_catalog_refuses_corrupt_or_oversize_files_before_content_use`, `test_catalog_refuses_tampered_or_incomplete_backup_files` |
| FR-018 output allowlist | T007, T011 | `test_catalog_returns_only_allowlisted_metadata` |
| FR-019 no browser exposure | T013 | The two integration tests in `contracts/shared-exclusions.md`. Privacy checklist. |
| FR-020 shared exclusions in a separate pull request | T013 | The two integration tests in `contracts/shared-exclusions.md`. Gating checklist. |
| FR-021 no automatic deletion | T006, T010 | `test_writer_keeps_unverified_file_and_logs_without_bodies` |
| FR-022 no restore, delete, unassign, or Mist write | T004 | `test_capture_calls_only_list_functions_with_explicit_arguments` |
| FR-023 list functions with explicit arguments and admission | T002, T004, T009, T012 | `test_capture_calls_only_list_functions_with_explicit_arguments`, the SDK compatibility guard |
| FR-024 logs | T006, T010 | `test_writer_keeps_unverified_file_and_logs_without_bodies` |
| FR-025 inline comments and action logging | T-LOCAL-GATES | Pylint, pydocstyle, and interrogate gates. Review of each new line. |
| FR-026 no production caller and gates | T001, T-PR | Gating checklist |
| FR-027 synthetic tests and no socket | T004, T005, T006, T007 | `test_capture_opens_no_network_socket`, test-quality ratchet |
| FR-028 five children | T012 | `test_nested_package_structure.py` guard |

Each requirement has at least one test or gate. The success criteria map as follows. SC-001 maps to the table above. SC-002 maps to the refusal tests. SC-003 maps to the test count. SC-004 maps to `test_capture_opens_no_network_socket` and the call recorder. SC-005 maps to the two integration tests. SC-006 maps to T012. SC-007 maps to the coverage gate.

## Defects in Existing Work

| ID | Severity | Location | Defect | Disposition |
| --- | --- | --- | --- | --- |
| E-01 | HIGH | Full-parity `tasks.md`, line 88 (R-60). The contract folder holds 17 children (R-68). | T023 names `tests/contract/cisco_config_converter/test_backup.py`. That path adds a direct child to a noncompliant folder. | D-12. The tests go under the converter integration tier. |
| E-02 | HIGH | Full-parity `tasks.md`, line 89 (R-61). Issue 4636 replaces `models.py` (five classes at the limit). | T024 names `routes.py` and `models.py` for backup behavior. A catalog route conflicts with the owner block. | D-10 and D-11. No route is added. The classes go into `state/lifecycle/backup.py`. |
| E-03 | HIGH | Draft 4636 `design/data-model.md`, section Persistence Keys (kind `backup`). Owner comment IC_kwDOQltU8c8AAAABkRDV7A. | Draft 4636 stores manifests under `data/cisco_config_converter/state/backup/`. The owner requires `data/.cisco-config-converter-backups/`. | D-1. Action A-1. |
| E-04 | HIGH | Draft 4636 `design/data-model.md`, section Backup, `BackupManifest`. | The manifest lacks `page_limit` and `reported_total`. The completeness proof needs both values. | D-3. Action A-2. |
| E-05 | HIGH | Firmware `PolicyResponse.collect`, `sdk.py`, line 219 (R-22). | The collector follows the `next` link only and drops the reported total. A short page passes without a signal. | D-3. The capture uses its own loop. Action R-03. |
| E-06 | MEDIUM | Firmware `BackupAccess.verify`, `backup.py`, line 162 (R-15). | The check refuses group and other bits only. A narrower mode such as 0500 passes. | D-2 adds the exact-mode check. Action R-04. |
| E-07 | MEDIUM | Firmware `PolicyBackup._create_file`, `backup.py`, line 211 (R-16). | The writer calls `chmod(0o700)` on an existing root. The owner forbids a permission change. | D-2. The converter never changes a mode. |
| E-08 | HIGH | `web_portal/services/output_scan.py`, line 85 (R-24). `web_portal/services/data_browser.py`, line 154 (R-25). | Both files exclude the firmware directory name only. A converter backup directory stays visible until the integration pull request merges. | D-13 and FR-020. Persistence waits for the merge. |
| E-09 | MEDIUM | `web_portal/services/config.py`, line 113 (R-31). | The portal secret falls back to a random value at each start. A seal key from configuration would change at each restart. | D-8. The seal key comes from the environment only. |
| E-10 | MEDIUM | Draft 4636 `summary.md` and `analysis.md` state 60 remote checks. Its `_meta/4636-STATUS.json` lists 24 entries. | The counts of the draft disagree with each other. | This record reports one count in all three files (80). Action A-3. |
| E-11 | MEDIUM | Coordinator decision on issue 4633, 2026-11-08T23:37:56Z. PR 4615 merged on 2026-11-13T06:20:12Z. | The decision names PR 4615 as the current owner of `data_browser.py`. The owner has since merged. | D-13 uses the merged state and the drafting-time scan of open pull requests. |
| E-12 | MEDIUM | Draft 4636 `analysis.md`, unresolved item U-4. | Draft 4636 asks whether the data backup covers `data/cisco_config_converter/state/`. The owner also requires backup coverage for `data/.cisco-config-converter-backups/`. | Action A-4. |
| E-13 | MEDIUM | `state/lifecycle/backup.py` after issue 4636. | The module holds five top-level names, which is the limit. | D-11. A sixth name needs a structure decision. |

## Actions

Each amendment belongs to the owner of the named issue or record. No action edits a file in another owner's scope in this pass.

- A-1 (issue 4636 amendment): Remove the `backup` kind from the state store. Name `data/.cisco-config-converter-backups/` as the backup directory (E-03).
- A-2 (issue 4636 amendment): Add `page_limit` and `reported_total` to `BackupManifest` before T010 starts (E-04).
- A-3 (draft 4636 correction): Use one remote-check count in the summary, the analysis, and the STATUS file (E-10).
- A-4 (issue 4636 scope): Extend the backup coverage question to `data/.cisco-config-converter-backups/` (E-12).
- R-01 (structure debt): `src/interfaces/portals/` holds six children. Group `guest_authorizations.py` in a separate issue. This record does not touch the folder (issue 4636, R-1).
- R-02 (structure debt): `tests/contract/` holds 17 children (R-68). Group them in a separate issue.
- R-03 (firmware helper follow-up): Add a reported-total check to `PolicyResponse.collect` in a separate issue (E-05).
- R-04 (firmware helper follow-up): Add an exact-mode check to `BackupAccess.verify` in a separate issue (E-06).
- R-05 (structure debt): `tests/unit/web_portal/` holds 52 children (R-69). The integration pull request adds functions to existing modules only.
- R-06 (structure debt): `documentation/` holds 73 children (R-70). This record adds no document there.

## Unresolved Items

| ID | Owner | Action |
| --- | --- | --- |
| U-01 | Issue 4634 | Record whether `X-Page-Total` appears on the three list operations live. |
| U-02 | Issue 4634 | Record whether each list item holds the complete object body. |
| U-03 | Issue 4634 (T003) | Record the reference fields of the service family and the target families of the service-policy references. |
| U-04 | Owner (issue 4636, U-11) | Confirm that production sets `PORTAL_SECRET_KEY`. |
| U-05 | Issue 4646 | Resolve live name collisions to IDs before any restore write. |
| U-06 | Issue 4634 and the operator | Record the live 429 and quota behavior of page reads. |
| U-07 | Implementer | Run test `test_directory_checks_real_windows_acl` on the owner Windows host. |
| U-08 | Implementer | Run the container steps in `design/quickstart.md` and record the owner and mode of the mounted directory. |
| U-09 | Owner (G4) | Confirm that the 128 MiB bound fits the expected object sizes. |
| U-10 | Orchestrator (issue 4636, U-8) | Decide whether these record files join the STE gate. |
| U-11 | Issue 4635 (G1) | Confirm the legal basis for any future reuse. This record reuses no external source. |
| U-12 | Issue 4634 | Decide whether the converter needs `deleteOrgServicePolicy`. |
| U-13 | Owner (issue 4636, U-2) | Accept standard `logging` as equivalent to the structured log rule, or require structlog. |
| U-14 | Owner, with the issue 4634 review | List each secret-bearing field in the complete objects before enablement. |

## Validation Commands and Results

| Command or check | Result | Reason |
| --- | --- | --- |
| `python -m ruff check .`, `python -m black --check .`, the type check and the pytest commands listed in `design/quickstart.md` | Not run | The drafting rules forbid tests, linters, formatters, and type checks in this pass. |
| `gh api` tree reads, `gh issue view`, `gh pr view`, and `gh pr list` | Run | Results are in `design/research.md`. |
| `git hash-object` on cited local files | Run | Results match the remote blob SHAs for each cited local file. |
| Local `Select-String` and `grep` reads of cited files | Run | Line numbers come from these reads after the hash check. |
| `ste-linter` on the record files | Not run | The drafting rules forbid linters. The Phase 3 check searches the record for forbidden tokens instead. |
