# Tasks: Integrate Mist Cisco Config Converter

**Input**: [Spec](spec.md), [plan](plan.md), [research](design/research.md), and [analysis](analysis.md).

**Task source**: Parity tasks T001 to T033 come from the parity record in PR #4596 (R-86). The child issue map comes from the issue #4224 comment of 2026-11-07. Final tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE close this record.

**Format**: Each task names its child issue, its requirements, its exact paths, and its acceptance statement. Each task also names one verification command from the local gates table (R-50) and its status. The statuses are open, verified-present, partial, or absent. Status `open` means no acceptance evidence exists on `main` and no artifact is complete. Status `partial` means some acceptance evidence exists. Status `absent` means no acceptance evidence exists on `main`.

**Shared-file rule**: `web_portal/app.py` and `web_portal/templates/base.html` change only after gate G3 (D-11).

**Legal rule**: No protected source expression is copied before gate G1 closes (D-17).

## Phase 1: Setup and gates

### T001 [P] Obtain the integration-owner handover

- Parity source: T001, child issue 4633 (CLOSED).
- Requirements: FR-029, FR-033.
- Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
- Acceptance: The research file names the approved owner and each approved shared file.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
- Status: open. PR #4208 is an open draft and lists both shared files (S-4). No handover is recorded.
- Prerequisites: none.

### T002 [P] Obtain the G1 legal review

- Parity source: T002, child issue 4635 (OPEN).
- Requirements: FR-031, SC-009.
- Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
- Acceptance: The research file records the legal decision for independent authorship and distribution (D-17).
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`
- Status: open. Child 4635 holds seven licensing decisions, and none is recorded on `main` (S-10).
- Prerequisites: none.

### T003 [P] Verify each mapping against the contracts

- Parity source: T003, child issue 4634 (OPEN).
- Requirements: FR-030, FR-032.
- Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md`
- Acceptance: The contract file lists each mapping with its OpenAPI path, schema pointer, installed signature, and one positive and one negative fixture.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md`
- Status: open. Child 4634 holds the drafted evidence (S-10). No merged G2 evidence is verified. Gateway template evidence exists at R-28 to R-31 and R-73 to R-80.
- Prerequisites: none.

### T004 Inventory package capacity

- Parity source: T004, child issue 4636 (OPEN).
- Requirements: FR-029.
- Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md`
- Acceptance: The plan lists the capacity of each folder, the bounded replacement paths, and each import update. It adds no compatibility shim.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md`
- Status: open. The capacity inventory is drafted in child 4636 only (S-10). The converter root holds five children today (R-94).
- Prerequisites: T001.

### T005 [P] Record the DNS baseline

- Parity source: T005, child issue 4632 (CLOSED).
- Requirements: FR-029, FR-030.
- Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md`
- Acceptance: The analysis file records the DNS unit, route, and browser baseline with exact results. It protects the preview, review, and export behavior.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md`
- Status: partial. The legacy quickstart on `main` records local results (R-06). The live analysis baseline is not verified (U-06).
- Prerequisites: none.

## Phase 2: Foundation

### T006 Define private state types

- Parity source: T006, child issue 4636 (OPEN).
- Requirements: FR-017, FR-028.
- Paths: `src/interfaces/portals/cisco_config_converter/state/` (add), `src/interfaces/portals/cisco_config_converter/models.py` (delete after `state/` exists), `tests/integration/web_portal/cisco_config_converter/state/test_state_records.py` (add)
- Acceptance: The state package defines source, review, proposal, approval, operation, and backup types. Tests cover digest, ownership, redaction, expiry, and transitions. The approval design waits for D-16.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_records.py`
- Status: partial. `models.py` defines the DNS types (R-12). The `state/` package is absent (R-90).
- Prerequisites: T001, T004, T005.

## Phase 3: User story 1 (input and review)

### T007 [P] Add input contract tests

- Parity source: T007, child issue 4637 (OPEN).
- Requirements: FR-002.
- Paths: `tests/integration/web_portal/cisco_config_converter/state/input/test_input_contract.py` (add)
- Acceptance: The tests cover six suffixes, the exact 16 MiB boundary, and one extra byte. They also cover strict UTF-8, null bytes, traversal, drive paths, symbolic links, upload collisions, and failed-review invalidation.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/input/test_input_contract.py`
- Status: partial. The DNS unit tests cover the suffix and size boundary (R-17, lines 19 to 36).
- Prerequisites: T006.

### T008 Add the catalog and validated upload

- Parity source: T008, child issue 4637 (OPEN).
- Requirements: FR-001, FR-002, FR-010.
- Paths: `src/interfaces/portals/cisco_config_converter/routes.py` (modify), `src/interfaces/portals/cisco_config_converter/state/intake/` (add)
- Acceptance: The catalog uses opaque IDs and private prepopulation. Storage is transient by default. The upload never overwrites silently.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/input/test_input_routes.py`
- Status: partial. The upload and preview routes exist (R-34). The catalog is absent.
- Prerequisites: T007.

### T009 [P] Add parser review tests

- Parity source: T009, child issue 4637 (OPEN).
- Requirements: FR-004.
- Paths: `tests/integration/web_portal/cisco_config_converter/state/input/test_observations.py` (add)
- Acceptance: The tests cover banners, masks, duplicate directives, unknown syntax, redacted identity data, and the absence of cloud calls.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/input/test_observations.py`
- Status: partial. The DNS parser tests exist (R-17, lines 50 and 78).
- Prerequisites: T006.

### T010 Add the sectioned review

- Parity source: T010, child issue 4637 (OPEN).
- Requirements: FR-003, FR-004, FR-008.
- Paths: `src/interfaces/portals/cisco_config_converter/routes.py` (modify), `src/interfaces/portals/cisco_config_converter/presentation/converter.html` (modify)
- Acceptance: The review shows every observed family. It separates unsupported conversion from parsed observations.
- Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
- Status: partial. The DNS review exists (R-34 and R-41). The sectioned review is absent.
- Prerequisites: T008, T009.

## Phase 4: User story 2 (hardware, network, management, and proposal)

### T011 [P] Add role and model tests

- Parity source: T011, child issue 4638 (OPEN).
- Requirements: FR-005, FR-006.
- Paths: `tests/integration/web_portal/cisco_config_converter/conversion/hardware/test_hardware.py` (add)
- Acceptance: The tests cover Branch, Hub, Standalone, SRX, SSR, inventory evidence, unsupported models, duplicate ports, stale models, and invalidation after a selection change.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/hardware/test_hardware.py`
- Status: absent. The converter supports DNS only (R-40).
- Prerequisites: T003, T006.

### T012 Add role, family, model, and port selection

- Parity source: T012, child issue 4638 (OPEN).
- Requirements: FR-005, FR-006, FR-014.
- Paths: `src/interfaces/portals/cisco_config_converter/presentation/converter.html` (modify), `src/interfaces/portals/cisco_config_converter/presentation/converter.js` (modify), `src/interfaces/portals/cisco_config_converter/conversion/hardware/mapping.py` (add), `src/interfaces/portals/cisco_config_converter/conversion/hardware/register.py` (add)
- Acceptance: The operator selects a role, a family, a model, and a port. Unknown models and conflicting assignments block apply. This task lands in one change with T014 (D-14).
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/hardware/test_hardware.py`
- Status: absent. No role or model selection exists on `main`.
- Prerequisites: T010, T011.

### T013 [P] Add conversion tests

- Parity source: T013, child issue 4640 (OPEN).
- Requirements: FR-007.
- Paths: `tests/integration/web_portal/cisco_config_converter/conversion/network/test_network.py` (add), `tests/integration/web_portal/cisco_config_converter/conversion/network/test_routing.py` (add)
- Acceptance: The tests cover C08 to C12, WAN and LAN ambiguity, addressing, VLAN and aggregation, DHCP exclusions, routes, BGP, VRF, DNS, NTP, and variables.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/network/test_network.py`
- Status: partial. The DNS conversion tests exist (R-17, line 50).
- Prerequisites: T003, T006.

### T014 Implement the network and routing transforms

- Parity source: T014, child issue 4640 (OPEN).
- Requirements: FR-007, FR-036.
- Paths: `src/interfaces/portals/cisco_config_converter/conversion/__init__.py` (add), `src/interfaces/portals/cisco_config_converter/conversion/common/dns.py` (add), `src/interfaces/portals/cisco_config_converter/conversion/network/dhcp.py` (add), `src/interfaces/portals/cisco_config_converter/conversion/network/interfaces.py` (add), `src/interfaces/portals/cisco_config_converter/conversion/network/ntp.py` (add), `src/interfaces/portals/cisco_config_converter/conversion/network/routing.py` (add), `src/interfaces/portals/cisco_config_converter/conversion.py` (delete after the package exists)
- Acceptance: Each transform is verified. Uncertain fields are omitted with a stated reason. The DNS behavior stays unchanged. This task creates the package that T012 and T016 use (D-14).
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/network/test_network.py`
- Status: partial. DNS conversion exists in `conversion.py` (R-11 and R-40). The package and network transforms are absent.
- Prerequisites: T013.

### T015 [P] Add management and security tests

- Parity source: T015, child issue 4639 (OPEN).
- Requirements: FR-008.
- Paths: `tests/integration/web_portal/cisco_config_converter/conversion/management/test_management.py` (add)
- Acceptance: The tests cover C13 to C17, secret redaction, one-way hashes, syslog placement, parser-only families, and the prohibition on raw-command generation.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/management/test_management.py`
- Status: absent.
- Prerequisites: T003, T006.

### T016 Implement the management mappings

- Parity source: T016, child issue 4639 (OPEN).
- Requirements: FR-008, FR-036.
- Paths: `src/interfaces/portals/cisco_config_converter/conversion/management/` (add)
- Acceptance: Each mapping is contract-verified. Display-only limits are explicit. The task never reconstructs a hash and never decodes a secret.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/management/test_management.py`
- Status: absent.
- Prerequisites: T014, T015.

### T017 [P] Add proposal and export tests

- Parity source: T017, child issue 4641 (OPEN).
- Requirements: FR-009, FR-011, FR-035.
- Paths: `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_assembly.py` (add), `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py` (add)
- Acceptance: The tests cover object changes, omissions, unavailable checks, the version shape, altered scope, the exact reviewed export, and zero secrets in the output.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py`
- Status: partial. The DNS export route exists (R-34, line 62).
- Prerequisites: T006.

### T018 Add the structured proposal review

- Parity source: T018, child issue 4641 (OPEN).
- Requirements: FR-009, FR-017, FR-035.
- Paths: `src/interfaces/portals/cisco_config_converter/routes.py` (modify), `src/interfaces/portals/cisco_config_converter/presentation/proposal_review.js` (add), `src/interfaces/portals/cisco_config_converter/presentation/converter.js` (modify), `src/interfaces/portals/cisco_config_converter/state/proposal.py` (add)
- Acceptance: The review becomes invalid after each source, model, target, or proposal change. Typed EXPORT gates the export.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py`
- Status: partial. The DNS review route exists (R-34, line 63). The versioned proposal is absent.
- Prerequisites: T010, T014, T016, T017.

## Phase 5: User story 3 (target discovery)

### T019 [P] Add discovery tests

- Parity source: T019, child issue 4642 (OPEN).
- Requirements: FR-012, FR-013.
- Paths: `tests/integration/web_portal/cisco_config_converter/operations/discovery/test_discovery.py` (add)
- Acceptance: The tests cover C19 to C21, all pages, unavailable, denied, and failed states, duplicate site names, assigned and unassigned gateways, and organization membership.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/discovery/test_discovery.py`
- Status: absent.
- Prerequisites: T003, T006.

### T020 Add read-only discovery

- Parity source: T020, child issue 4642 (OPEN).
- Requirements: FR-012, FR-013, FR-015.
- Paths: `src/mist/access/targets/` (add), `src/interfaces/portals/cisco_config_converter/routes.py` (modify)
- Acceptance: Discovery uses the existing credential service and explicit SDK arguments. A lookup never creates a site or a gateway.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/discovery/test_discovery.py`
- Status: absent.
- Prerequisites: T018, T019.

## Phase 6: User story 4 (gated apply)

### T021 [P] Add apply tests

- Parity source: T021, child issue 4644 (OPEN).
- Requirements: FR-016, FR-018, FR-019.
- Paths: `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_gates.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_executor.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_reconcile.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_routes.py` (add)
- Acceptance: The tests cover C22 to C24, the exact word APPLY, and permission. They also cover the 15-minute expiry, changed scope, and an incomplete backup. They cover duplicate submission, locks, stale state, HTTP 4xx, 5xx, and 429, timeout, partial results, and indeterminate writes.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_gates.py`
- Status: absent.
- Prerequisites: T003, T006.

### T022 Implement the approved apply

- Parity source: T022, child issue 4644 (OPEN).
- Requirements: FR-015, FR-016, FR-018, FR-019.
- Paths: `src/interfaces/portals/cisco_config_converter/state/execution.py` (add), `src/interfaces/portals/cisco_config_converter/state/lifecycle/approval.py` (add), `src/interfaces/portals/cisco_config_converter/routes.py` (modify)
- Acceptance: Apply writes only verified fields. A refused approval writes nothing. An unknown write is never retried. Each family stays disabled until gates G2, G4, and G5 pass and D-15 is approved.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_executor.py`
- Status: absent. `routes.py` defines no apply route (R-42), and the converter imports no mistapi module (R-36).
- Prerequisites: T001, T002, T020, T021, T024.

## Phase 7: User story 5 (administration and recovery)

### T023 [P] Add backup and catalog tests

- Parity source: T023, child issue 4643 (OPEN).
- Requirements: FR-021, FR-028.
- Paths: `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_writer.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_catalog.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_capture.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_directory.py` (add)
- Acceptance: The tests cover C26 and C27, complete pagination, private storage, UTC manifests, checksums, a wrong organization, a wrong family, and symbolic link escapes. Private paths stay out of listings, previews, downloads, output scans, and logs.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_writer.py`
- Status: absent.
- Prerequisites: T003, T006.

### T024 Implement the private backup and catalog

- Parity source: T024, child issue 4643 (OPEN).
- Requirements: FR-020, FR-021, FR-028, FR-029.
- Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py` (add), `web_portal/services/data_browser.py` (modify after G3, R-47), `web_portal/services/output_scan.py` (modify after G3)
- Acceptance: The backup writes only under the private folder. An incomplete page or an invalid manifest blocks recovery and destructive execution.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_catalog.py`
- Status: absent.
- Prerequisites: T001, T023.

### T025 [P] Add administration tests

- Parity source: T025, child issue 4645 (OPEN).
- Requirements: FR-023, FR-024.
- Paths: `tests/integration/web_portal/cisco_config_converter/operations/administration/test_permission.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/administration/test_scope.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/administration/test_execute.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/administration/test_administration_page.py` (add)
- Acceptance: The tests cover C25, C29, and C30. They cover disabled mode, exact scope, two confirmations, the exact word CONFIRM, changed references, backup failure, and zero refused writes.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/administration/test_permission.py`
- Status: absent.
- Prerequisites: T003, T006.

### T026 Implement scoped deletion and unassignment

- Parity source: T026, child issue 4645 (OPEN).
- Requirements: FR-023, FR-024, FR-015.
- Paths: `src/interfaces/portals/cisco_config_converter/state/administration/` (add), `src/interfaces/portals/cisco_config_converter/presentation/administration/` (add), `src/interfaces/portals/cisco_config_converter/routes.py` (modify)
- Acceptance: Each object outcome is recorded. Service-policy deletion stays excluded until D-15 is approved. The administration engine sits under `state/` (D-10).
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/administration/test_execute.py`
- Status: absent.
- Prerequisites: T001, T002, T024, T025.

### T027 [P] Add restore tests

- Parity source: T027, child issue 4646 (OPEN).
- Requirements: FR-020, FR-022.
- Paths: `tests/integration/web_portal/cisco_config_converter/operations/recovery/test_recovery.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/recovery/test_restore_decisions.py` (add), `tests/integration/web_portal/cisco_config_converter/operations/recovery/test_restore_execution.py` (add)
- Acceptance: The tests cover C28 and C31, create and update decisions, duplicate names, partial apply, unknown outcomes, unrelated changes, expired approval, and failed rollback.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/recovery/test_restore_decisions.py`
- Status: absent.
- Prerequisites: T003, T006.

### T028 Implement reviewed restore

- Parity source: T028, child issue 4646 (OPEN).
- Requirements: FR-020, FR-022.
- Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/` (add), `src/interfaces/portals/cisco_config_converter/routes.py` (modify)
- Acceptance: Restore uses recorded natural IDs and a fresh approval. An object absent from a backup is preserved.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/recovery/test_restore_execution.py`
- Status: absent.
- Prerequisites: T001, T002, T022, T026, T027.

## Phase 8: User story 1 and 2 (browser journeys)

### T029 [P] Add browser journey tests

- Parity source: T029, child issue 4647 (OPEN).
- Requirements: FR-025, FR-027, FR-034, FR-035.
- Paths: `tests/e2e/web_portal/test_portal_smoke.py` (modify). No new file is added (D-9, R-93). The parity path `tests/e2e/web_portal/test_cisco_parity.py` (R-91) is not created.
- Acceptance: The tests cover selection, review, proposal, typed confirmation, cancel and reset, states, themes, focus, safe text, and failure traces.
- Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
- Status: partial. Two isolated DNS journeys exist (R-20).
- Prerequisites: T006.

### T030 Author the presentation independently

- Parity source: T030, child issue 4647 (OPEN).
- Requirements: FR-025, FR-026, FR-027, FR-031.
- Paths: `src/interfaces/portals/cisco_config_converter/presentation/converter.html` (modify), `src/interfaces/portals/cisco_config_converter/presentation/converter.js` (modify), `src/interfaces/portals/cisco_config_converter/presentation/converter.css` (add)
- Acceptance: The presentation is authored independently. The theme reads host tokens. No source template, style, screenshot, prose, or animation is copied.
- Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
- Status: partial. The DNS presentation exists (R-14 and R-15).
- Prerequisites: T018, T020, T029.

## Phase 9: Cross-cutting acceptance

### T031 [P] Add integration, privacy, and parity tests

- Parity source: T031, child issue 4648 (OPEN).
- Requirements: FR-028, FR-029, FR-030, FR-032.
- Paths: `tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py` (add)
- Acceptance: The tests cover C36 to C39, CSRF and converter-prefix negotiation, safe responses, debug defaults, logs, zero live requests, and every comparison row.
- Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py`
- Status: partial. The DNS integration tests cover CSRF and the 413 boundary (R-43).
- Prerequisites: T006.

### T032 Integrate the shared portal

- Parity source: T032, child issue 4648 (OPEN).
- Requirements: FR-001, FR-029, FR-033.
- Paths: `web_portal/app.py` (modify after G3, R-44), `web_portal/templates/base.html` (modify after G3, R-23)
- Acceptance: The converter tab appears. The portal sets `ConverterRequest` and `CSRFProtect` before registration. Health checks, credentials, and services stay unchanged. The change adds no service to `compose.yml`.
- Verification: `python -m pytest tests/e2e/web_portal`
- Status: absent. The portal registers no converter blueprint (R-22) and shows no converter navigation entry (R-23).
- Prerequisites: T001, T022, T028, T030, T031.

### T033 Refresh the evidence record

- Parity source: T033, child issue 4649 (OPEN).
- Requirements: FR-030, FR-031.
- Paths: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` (modify), `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md` (modify)
- Acceptance: Each row cites evidence. Each owner decision is recorded. Full parity requires every row accepted or an approved unsupported disposition. The converter guide waits for documentation approval (D-18).
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md`
- Status: absent. Child 4649 reports 40 rows open at baseline (S-10).
- Prerequisites: T002, T032.

## Phase 10: Final tasks for this record

### T-LOCAL-GATES Run the applicable local gates

- Parity source: Not applicable. This is a final task for this record.
- Requirements: FR-030, FR-032.
- Paths: The eleven Markdown files in `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/`.
- Acceptance: Each gate in the local gates table that applies to the changed files passes. For this record, the STE gate applies. Each implementation change runs the full table in `.github/copilot-instructions.md`.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/analysis.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/research.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/data-model.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/quickstart.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/contracts/portal-routes.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/contracts/mist-gateway-template.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/checklists/requirements.md specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/design/checklists/security.md`
- Status: open. No gate has run for this record.
- Prerequisites: all tasks in this record are complete.

### T-PR Commit, push, and open the pull request

- Parity source: Not applicable. This is a final task for this record.
- Requirements: FR-030.
- Paths: `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/` (the eleven Markdown files in the record folder).
- Acceptance: The commit uses a Conventional Commit subject with the type `docs`. The branch is `feat/4224-cisco-config-converter`. The pull request body names the record path and the open decisions D-15 to D-18. The pull request body carries `Closes #4224`, as the repository template requires (analysis A-26).
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 <the same eleven record files as T-LOCAL-GATES>`
- Status: open.
- Prerequisites: T-LOCAL-GATES.

### T-REMOTE-CI Watch the remote CI run

- Parity source: Not applicable. This is a final task for this record.
- Requirements: FR-030.
- Paths: `.github/workflows/ci.yml` (read only, R-70).
- Acceptance: Each required check reports success. The run adds no change to `main`. The reviewer confirms the Principle V reading (D-12).
- Verification: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
- Status: open.
- Prerequisites: T-PR.

### T-MERGE Enable auto-merge after the authorization

- Parity source: Not applicable. This is a final task for this record.
- Requirements: FR-030.
- Paths: `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/` (the record that this pull request merges). The task changes no other path.
- Acceptance: Auto-merge turns on only after remote CI passes and the orchestrator authorizes the merge. The `needs-human-review` label stays on the pull request until a human reviews it.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` (expected: `gate: 0 new findings vs baseline`)
- Status: open.
- Prerequisites: T-REMOTE-CI and the orchestrator authorization.

## Requirement Traceability

Each row lists the tasks and the tests for one requirement. Each test path lies under `tests/` in the repository.

| Requirement | Tasks | Tests |
|---|---|---|
| FR-001 | T008, T032 | `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/e2e/web_portal/test_portal_smoke.py` |
| FR-002 | T007, T008 | `tests/integration/web_portal/cisco_config_converter/state/input/test_input_contract.py` |
| FR-003 | T010 | `tests/e2e/web_portal/test_portal_smoke.py` |
| FR-004 | T009, T010 | `tests/integration/web_portal/cisco_config_converter/state/input/test_observations.py` |
| FR-005 | T011, T012 | `tests/integration/web_portal/cisco_config_converter/conversion/hardware/test_hardware.py` |
| FR-006 | T011, T012 | `tests/integration/web_portal/cisco_config_converter/conversion/hardware/test_hardware.py` |
| FR-007 | T013, T014 | `tests/integration/web_portal/cisco_config_converter/conversion/network/test_network.py` |
| FR-008 | T015, T016 | `tests/integration/web_portal/cisco_config_converter/conversion/management/test_management.py` |
| FR-009 | T017, T018 | `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py` |
| FR-010 | T008, T031 | `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py` |
| FR-011 | T017, T018 | `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py` |
| FR-012 | T019, T020 | `tests/integration/web_portal/cisco_config_converter/operations/discovery/test_discovery.py` |
| FR-013 | T019, T020 | `tests/integration/web_portal/cisco_config_converter/operations/discovery/test_discovery.py` |
| FR-014 | T014, T016 | `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_assembly.py` |
| FR-015 | T020, T022, T026 | `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_gates.py`, `tests/integration/web_portal/cisco_config_converter/operations/administration/test_scope.py` |
| FR-016 | T021, T022 | `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_gates.py` |
| FR-017 | T006, T018 | `tests/integration/web_portal/cisco_config_converter/state/test_state_transitions.py`, `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py` |
| FR-018 | T021, T022 | `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_executor.py` |
| FR-019 | T021, T022 | `tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_reconcile.py` |
| FR-020 | T024, T027, T028 | `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_catalog.py`, `tests/integration/web_portal/cisco_config_converter/operations/recovery/test_recovery.py` |
| FR-021 | T023, T024 | `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_writer.py` |
| FR-022 | T027, T028 | `tests/integration/web_portal/cisco_config_converter/operations/recovery/test_restore_execution.py` |
| FR-023 | T025, T026 | `tests/integration/web_portal/cisco_config_converter/operations/administration/test_execute.py` |
| FR-024 | T025, T026 | `tests/integration/web_portal/cisco_config_converter/operations/administration/test_permission.py` |
| FR-025 | T029, T030 | `tests/e2e/web_portal/test_portal_smoke.py` |
| FR-026 | T030 | `tests/e2e/web_portal/test_portal_smoke.py` |
| FR-027 | T029, T030 | `tests/e2e/web_portal/test_portal_smoke.py` |
| FR-028 | T006, T023, T031 | `tests/integration/web_portal/cisco_config_converter/state/test_state_records.py`, `tests/integration/web_portal/cisco_config_converter/operations/backup/test_backup_writer.py`, `tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py` |
| FR-029 | T001, T024, T032 | `tests/e2e/web_portal` (regression), `tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py` |
| FR-030 | T003, T005, T031, T033 | `tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py` |
| FR-031 | T002, T030, T033 | `tests/integration/web_portal/cisco_config_converter/conversion/parity/evidence/test_register_audit.py` |
| FR-032 | T003, T031 | `tests/integration/web_portal/cisco_config_converter/conversion/parity/test_parity.py` |
| FR-033 | T001, T032 | `tests/e2e/web_portal` (regression) and a file-list check that `compose.yml` does not change |
| FR-034 | T029 | `tests/e2e/web_portal/test_portal_smoke.py` (failure screenshots) |
| FR-035 | T017, T018, T029 | `tests/integration/web_portal/cisco_config_converter/conversion/proposals/test_proposal_routes.py`, `tests/e2e/web_portal/test_portal_smoke.py` |
| FR-036 | T014, T016 | `tests/integration/web_portal/cisco_config_converter/conversion/network/test_network.py`, `tests/integration/web_portal/cisco_config_converter/conversion/management/test_management.py` |

## Dependencies and Execution Order

| Task | Prerequisites |
|---|---|
| T001 | None |
| T002 | None |
| T003 | None |
| T004 | T001 |
| T005 | None |
| T006 | T001, T004, T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T006 |
| T010 | T008, T009 |
| T011 | T003, T006 |
| T012 | T010, T011 (lands with T014, D-14) |
| T013 | T003, T006 |
| T014 | T013 (lands with T012, D-14) |
| T015 | T003, T006 |
| T016 | T014, T015 |
| T017 | T006 |
| T018 | T010, T014, T016, T017 |
| T019 | T003, T006 |
| T020 | T018, T019 |
| T021 | T003, T006 |
| T022 | T001, T002, T020, T021, T024 |
| T023 | T003, T006 |
| T024 | T001, T023 |
| T025 | T003, T006 |
| T026 | T001, T002, T024, T025 |
| T027 | T003, T006 |
| T028 | T001, T002, T022, T026, T027 |
| T029 | T006 |
| T030 | T018, T020, T029 |
| T031 | T006 |
| T032 | T001, T022, T028, T030, T031 |
| T033 | T002, T032 |
| T-LOCAL-GATES | T001 to T033 |
| T-PR | T-LOCAL-GATES |
| T-REMOTE-CI | T-PR |
| T-MERGE | T-REMOTE-CI and the orchestrator authorization |

The parallel groups are T001, T002, T003, and T005. After T006, the parallel groups run in this order. First, T007 and T009. Second, T011, T013, and T015. Third, T017. Fourth, T019 and T021. Fifth, T023, T025, and T027. Last, T029 and T031. The edits to `routes.py`, `models.py`, `conversion.py`, and the presentation files do not run in parallel.
