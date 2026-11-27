# Privacy Checklist: Private Configuration Backup and Verified Catalog

**Purpose**: Check each surface where backup content or catalog metadata could leave the private directory.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

Each item names its evidence. An unchecked item names the step that closes it.

## Surfaces

- [x] Browser route: the feature registers no route (D-10). Evidence: the portal application registers no converter blueprint (R-12), and this change adds none.
- [ ] Browser listing: the output scan and the data browser exclude the directory name. Closes at the integration pull request (T013, the two integration tests in `contracts/shared-exclusions.md`).
- [ ] Browser preview and download: the same exclusion closes these surfaces. Closes at T013.
- [x] Output scan: no operation writes a report into the backup directory. The exclusion closes the walk, and T013 adds `test_output_scan_prunes_converter_backup_directory`.
- [x] Ordinary export: the feature adds no export (FR-019).
- [x] Cookie and browser storage: the feature writes no value to a session or to browser storage. The converter session keeps only digests (R-11).
- [x] Log line: the feature logs only the action, family, backup ID, counts, and refusal reason (FR-024). Test `test_writer_keeps_unverified_file_and_logs_without_bodies` checks the captured log records.
- [x] Error message: the refusal text names the check and omits the content. The capture never includes a response body in a message (`mist-list-reads.md`, section Request Admission and Status).
- [x] API response: the catalog returns the five metadata keys only (`catalog-output.md`). Test `test_catalog_returns_only_allowlisted_metadata` checks the key set.
- [x] File name: the name is an opaque identifier. The name holds no organization ID and no family (D-9).

## Storage

- [x] The directory is under `data/`, which `.gitignore` line 95 ignores (R-29).
- [x] The directory and each file carry the owner-only access rules (FR-002, FR-003).
- [x] Symbolic links, hard links, reparse points, and traversal names are refused (FR-004). Tests `test_directory_refuses_symbolic_link_root`, `test_directory_refuses_traversal_and_foreign_file_names`, and `test_directory_refuses_hard_linked_backup_file` cover them.
- [ ] Explained: a valid private mode does not prove encryption at rest. Decision D-19 is a human decision, and the record keeps it open.

## Contents

- [x] A backup file holds complete settings. The file is private, and no route reads it (FR-001, FR-019).
- [ ] Explained: the complete objects can hold secret-bearing fields. Open item U-14 requires owner review of the issue 4634 schemas before enablement.
