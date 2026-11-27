# Security Requirements Quality Checklist: Compliant Converter Package and State Model

**Purpose**: Confirm that the security, secret, and persistence requirements are complete and testable before implementation starts.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Credential and Secret Handling

- [x] CHK014 The store refuses writes and reads when `PORTAL_SECRET_KEY` is empty. Source: `design/contracts/state-store.md`, Key Derivation and Failure Rules. Test: `test_write_refused_without_portal_secret`.
- [x] CHK015 The sealing key differs from the Flask session key. Source: `design/contracts/state-store.md`, Key Derivation.
- [x] CHK016 No log line names a secret, a sealing key, or a seal value. Source: `design/contracts/state-records.md`, Logging Rules and `design/contracts/state-store.md`, Privacy. Test: `test_write_logs_before_and_after_without_secret`.
- [x] CHK017 The shared `PORTAL_SECRET_KEY` fallback stays unchanged in this change. Source: `plan.md`, Dependencies and D-15 in `design/research.md`.

## Consent and Command Safety

- [x] CHK018 Write-capable approvals refuse every unverified operator. Source: `design/data-model.md`, ApprovalRecord. Test: `test_approval_refused_without_verified_operator`.
- [x] CHK019 Each approval binds one operator, one proposal digest, one scope digest, one expiry, and one use. Source: `design/data-model.md`, ApprovalRecord. Tests: `test_approval_refused_for_changed_proposal_or_scope` and `test_two_processes_consume_one_approval_once`.
- [x] CHK020 No cloud write, restore, delete, or unassign path exists in this change. Source: `spec.md`, Mist Cloud Transport Requirements, and FR-018.
- [x] CHK021 An indeterminate operation cannot start execution. Source: `design/data-model.md`, Guard rules. Test: `test_indeterminate_operation_cannot_start_execution`.

## Data Exposure and Limits

- [x] CHK022 Public views remove source text and redact secret keys. Source: `design/contracts/state-records.md`, Public View. Tests: `test_public_view_redacts_secret_fields` and `test_public_view_omits_source_text`.
- [x] CHK023 Record identifiers match `^[0-9a-f]{32}$` before any path is built. Source: `design/contracts/state-store.md`, Write Sequence, step 4.
- [x] CHK024 A symbolic link or a regular file at the root refuses writes. Source: `design/contracts/state-store.md`, Write Sequence, step 5. Test: `test_write_refused_when_data_path_is_a_file`.
- [x] CHK025 Private state stays under the git-ignored `data/` directory. Source: `.gitignore` line 95 and `design/contracts/state-store.md`, Privacy.
- [x] CHK026 Tests use synthetic data and `tmp_path`. No test reads a live credential. Source: `spec.md`, FR-022.

## Persistence Safety

- [x] CHK027 The store reports success only after a read-back verifies the seal and the digest. Source: `design/contracts/state-store.md`, Write Sequence, step 12. Test: `test_read_back_mismatch_reports_no_success`.
- [x] CHK028 A tampered record fails the seal check. Source: `design/contracts/state-store.md`, Read Sequence. Test: `test_tampered_record_fails_seal_check`.
- [x] CHK029 Production writes stay disabled until owner approval. Source: `design/contracts/state-store.md`, Construction. Test: `test_default_store_refuses_production_writes`.
- [x] CHK030 Backup coverage and Windows directory permissions remain open. Source: `analysis.md`, U-4 and U-5. These items need owner evidence before production.
