# Security Requirements Quality Checklist: Gated Converter Administration and Unassignment

**Purpose**: Confirm that the security and safety requirements are complete, clear, and testable before implementation.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Access and Gating

- [x] SEC-01 Administrative mode stays disabled by default. Source: FR-001. Setting: `CISCO_CONVERTER_ADMIN_MODE` (decision D-9, RC-53).
- [x] SEC-02 Each family stays disabled unless the owner lists it. Source: FR-002. Setting: `CISCO_CONVERTER_ADMIN_FAMILIES`.
- [x] SEC-03 Each administrative route refuses a request without a verified operator identity. Source: FR-003. Production refuses every identity until decision D-1.
- [x] SEC-04 The existing CSRF guard runs before each POST. Source: FR-004, RC-03.
- [x] SEC-05 The shared portal does not register the routes in this issue. Source: FR-023, decision D-16, RC-15.

## Scope and Confirmation

- [x] SEC-06 The operator selects objects by explicit IDs. The scope holds one to 25 unique values. Source: FR-005.
- [x] SEC-07 A live reference from an outside object blocks the review. The portal does not detach it. Source: FR-007, decision D-7.
- [x] SEC-08 Each family needs a verified backup manifest that covers each selected object. Source: FR-008, decision D-11.
- [x] SEC-09 The approval needs a scope confirmation that equals the scope digest. Source: FR-009.
- [x] SEC-10 The run needs the exact typed word `CONFIRM`. The server compares the value. Source: FR-009, RC-49.
- [x] SEC-11 Each approval binds one operator, one scope digest, and one use. It expires after 15 minutes, inclusive. Source: FR-010, decision D-10.

## Execution Safety

- [x] SEC-12 The executor reads each object before its write. A changed object stops the run. Source: FR-011.
- [x] SEC-13 The operation record persists before the first write. A failed persistence stops the run with 503. Source: FR-012.
- [x] SEC-14 Each unknown outcome becomes `indeterminate`. The run stops. No write repeats. Source: FR-016, FR-017, decision D-12.
- [x] SEC-15 Device profile unassignment sends only the reviewed MAC addresses. Source: FR-013.
- [x] SEC-16 Each deletion calls one SDK function for one object with explicit arguments. Source: FR-014, FR-026.
- [x] SEC-17 The site-template path stays refused until decision D-3 and issue 4634 close. Source: FR-015.

## Secrets, Logs, and Storage

- [x] SEC-18 Responses hold no token, password, or raw Mist body. Source: FR-018.
- [x] SEC-19 Logs hold no typed word, token, or request body. Each action writes an `info` line before and a `debug` line after. Source: FR-020.
- [x] SEC-20 Records and manifests stay under `data/`, which `.gitignore` ignores. Source: RC-52, `design/data-model.md`, Persistence keys.
- [x] SEC-21 The shared secret fallback creates a random key for each process. The store refuses writes when `PORTAL_SECRET_KEY` is unset. Source: RC-16, issue 4636 decision D-5.
- [x] SEC-22 The record adds no credential source. Source: A-7.

## Refusal Coverage

Each refusal test proves zero SDK write calls (FR-024). Each row below names one refusal case.

- [x] SEC-23 Administrative mode disabled. Test 1, `test_admin_routes_return_404_when_mode_disabled`.
- [x] SEC-24 Family disabled. Test 2, `test_family_disabled_refuses_with_403`.
- [x] SEC-25 No verified identity. Test 3, `test_missing_operator_identity_refuses_with_403`.
- [x] SEC-26 CSRF failure. Test 4, `test_csrf_failure_refuses_before_any_read`.
- [x] SEC-27 Invalid scope. Test 7, `test_scope_rejects_empty_duplicate_malformed_and_oversize`.
- [x] SEC-28 Digest mismatch. Test 8, `test_scope_digest_changes_when_any_object_changes`.
- [x] SEC-29 Missing or unverified backup. Test 10, `test_missing_or_unverified_backup_blocks_review`.
- [x] SEC-30 Wrong organization or family in a backup. Test 11, `test_wrong_organization_or_family_backup_blocks_review`.
- [x] SEC-31 Reference from an outside object. Test 9, `test_reference_outside_scope_blocks_review`.
- [x] SEC-32 Store unavailable. Test 12, `test_unavailable_store_refuses_before_write`.
- [x] SEC-33 Wrong or missing typed word. Test 13, `test_missing_or_wrong_typed_confirm_refuses_without_writes`.
- [x] SEC-34 Missing scope confirmation. Test 14, `test_missing_scope_confirmation_refuses_without_writes`.
- [x] SEC-35 Expired approval. Test 15, `test_approval_expires_at_fifteen_minutes_inclusive`.
- [x] SEC-36 Reused approval. Test 16, `test_reused_approval_refuses`.
- [x] SEC-37 Changed before-state. Test 17, `test_changed_before_state_stops_run`.
- [x] SEC-38 Site-template path. Test 22, `test_site_template_unassign_refuses_until_verified`.

## Notes

- Each item is checked. The source column names the requirement, the decision, or the evidence row.
- Items SEC-23 to SEC-38 list the refusal cases that `tasks.md` tasks T005 to T007 implement.
