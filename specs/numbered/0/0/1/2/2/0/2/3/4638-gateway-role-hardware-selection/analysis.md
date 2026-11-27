# Specification Analysis Report: Add explicit gateway role and hardware selection

## Summary

The spec, plan, tasks, contracts, and research agree on the selection model, the blocker codes, and the test list. Twenty findings were recorded during the analysis. Each HIGH finding has a decision that removes it from the implementation. No finding blocks the spec. Implementation waits for the prerequisites in the Unresolved Items section.

## Findings

| ID | Severity | Location | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F-01 | HIGH | Parity task T011, full-parity `tasks.md` line 57 | The path `tests/contract/cisco_config_converter/test_hardware.py` adds an eighteenth child to `tests/contract/`, which holds 17 (R18). Constitution Principle I forbids that addition (R32). | D-12. The test module goes to the integration folder. |
| F-02 | HIGH | `conversion.py`, lines 6 to 53 (R03, R05) | The module holds two top-level names. Adding the register and the mapping breaks the five-name and five-member limits. Issue 4640 E-1 records the same limit. | D-14. The `conversion/` package hosts `hardware/`. |
| F-03 | HIGH | OpenAPI lines 80785 to 80790 (R47) | The gateway deployment type enum has no hub value. Parity task T012 and FR-005 name Hub. | D-4. Hub stays blocked. |
| F-04 | HIGH | Full-parity FR-005 line 111 (R36) and OpenAPI lines 80785 to 80790 | Branch appears in FR-005. No local line names Branch as a deployment type (UV-01). | D-3. Branch stays blocked until issue 4634 records evidence. |
| F-05 | MEDIUM | OpenAPI lines 75110 to 75121 (R44) | The discriminator maps the gateway schema to the switch schema and the reverse. The defect is in the Mist documentation text. | Reported to issue 4634. This record does not use the discriminator (UV-12). |
| F-06 | MEDIUM | OpenAPI lines 29757 to 29788 (R54) | The SRX1500 cabling sections name different cluster members for the same model. | D-8. SRX1500 is blocked with `model_evidence_conflict`. |
| F-07 | MEDIUM | OpenAPI lines 29771 to 29776 | The cabling text for SRX340, SRX345, and VSRX is mixed. The SRX550 and SRX4100 sections repeat in the document. | The register cites clean sections only. The mixed block is unverified (UV-08). |
| F-08 | MEDIUM | Copilot instructions line 303 (R30), `tests/e2e/` (R19), `tests/e2e/web_portal/` (R20) | The web UI rule requires a test under `tests/e2e/`. Both folders are at or over the limit, so a new file cannot go there. | D-12 and T013. The browser test is a function in the existing smoke file after issue 4647 merges. |
| F-09 | MEDIUM | Draft 4641 `plan.md` line 103 and draft 4644 `tasks.md` line 35 | Draft 4641 says `converter.js` stays unchanged. Draft 4644 names `converter.js` as a file that issue 4647 edits. This record also edits `converter.js`. | The sequencing in `plan.md` applies. The second merge rebases. |
| F-10 | MEDIUM | Draft 4640 `spec.md` line 150 and `research.md` D-17 | Draft 4640 uses `role` for the WAN or LAN value and lists one family in each port assignment. The gateway role uses the same word. | D-15 keeps the value name `usage`. Family stays on the selection. Issue 4640 must align (U-7). |
| F-11 | LOW | `conversion.py` line 27 (R04) | The known gap says hardware mappings remain unsupported. The statement becomes false. | T005 changes the sentence. The count of three known gaps stays. |
| F-12 | LOW | Unit test lines 16, 22, and 39 (R13, R14) | The unit test uses Branch as the template name. The test passes the kind argument. | T004 removes the argument. Names stay unchanged. |
| F-13 | MEDIUM | Integration folder children (R16) | After issues 4636, 4640, and this record, the folder holds five children. Draft 4642 plans a discovery test in the same folder (its `analysis.md` line 18). A sixth child would break Principle I. | Issue 4642 must not add a sixth child (U-10). |
| F-14 | LOW | Issue 4636 decision D-13 and remote check R24 | Route registration and shared portal files stay out of scope. | FR-018 and TST-25 keep the rule. |
| F-15 | LOW | Issue 4636 decision D-11 | Issue 4636 keeps the role values until tasks T011 and T012 change the contract. | This record makes that change. Issue 4636 needs no code change. |
| F-16 | MEDIUM | Full-parity portal contract line 16 (R40 context) | The contract forbids silent reinterpretation of names and types. | D-2. The `type` field is retired and returns HTTP 400. |
| F-17 | LOW | OpenAPI lines 50625, 55277, 58160, and 99932 (R56) | SSR120 appears only in examples. No port role exists. | D-9. SSR stays blocked. |
| F-18 | LOW | Issue 4638 test plan | The issue asks for tests before implementation. | Phase 2 in `tasks.md` writes the tests first. |
| F-19 | MEDIUM | Issue 4636 `state/proposal.py` and draft 4640 `tasks.md` line 131 | Issue 4636 makes `gateway_template.type` required. This record makes it `NotRequired`. Issue 4640 also edits the same TypedDict. | Sequencing. The second merge rebases the keys. |
| F-20 | LOW | `models.py` top-level classes (R01, R02) | The module holds five classes, which is the limit. | Issue 4636 removes the module. No action here. |

## Coverage Summary

- Requirements: 20 (FR-001 to FR-020). Each requirement appears in the Requirement Coverage table in `tasks.md` with at least one task and at least one test.
- Tasks: 18, including T001 to T014 and four final tasks.
- Planned tests: 26, from TST-01 to TST-26.
- Success criteria: 7. Each criterion maps to a test in the list below or to a gate in T-LOCAL-GATES.

## Test Catalog

| ID | Test | File | Requirements |
| --- | --- | --- | --- |
| TST-01 | `test_standalone_srx300_is_verified_with_named_ports` | `test_hardware.py` | FR-001, FR-003, FR-004, FR-005, FR-010 |
| TST-02 | `test_standalone_srx320_is_verified_with_closed_range_lan` | `test_hardware.py` | FR-003, FR-010 |
| TST-03 | `test_six_role_family_combinations_have_one_decision` | `test_hardware.py` | FR-001, FR-002, SC-001 |
| TST-04 | `test_branch_is_blocked_as_unverified_role` | `test_hardware.py` | FR-005, FR-007 |
| TST-05 | `test_hub_is_blocked_without_deployment_type` | `test_hardware.py` | FR-001, FR-006 |
| TST-06 | `test_models_without_inventory_sample_are_blocked` | `test_hardware.py` | FR-003, FR-008 |
| TST-07 | `test_srx1500_conflicting_evidence_is_blocked` | `test_hardware.py` | FR-008 |
| TST-08 | `test_unknown_model_including_vsrx_is_blocked` | `test_hardware.py` | FR-003, FR-008 |
| TST-09 | `test_ssr_family_is_blocked_without_port_roles` | `test_hardware.py` | FR-009 |
| TST-10 | `test_ha_role_ports_are_not_selectable` | `test_hardware.py` | FR-004, FR-010 |
| TST-11 | `test_duplicate_mist_port_is_blocked` | `test_hardware.py` | FR-011 |
| TST-12 | `test_duplicate_source_interface_is_blocked` | `test_hardware.py` | FR-011 |
| TST-13 | `test_source_interface_must_exist_in_file` | `test_hardware.py` | FR-011 |
| TST-14 | `test_missing_wan_or_lan_is_blocked` | `test_hardware.py` | FR-011 |
| TST-15 | `test_stale_evidence_revision_is_blocked` | `test_hardware.py` | FR-012 |
| TST-16 | `test_verified_rows_cite_inventory_and_port_lines` | `test_hardware.py` | FR-020, SC-007 |
| TST-17 | `test_hardware_module_makes_no_network_call` | `test_hardware.py` | FR-019, SC-003 |
| TST-18 | `test_blocked_proposal_cannot_be_reviewed` | `test_routes.py` | FR-013, SC-002 |
| TST-19 | `test_changed_selection_invalidates_earlier_review` | `test_routes.py` | FR-014, SC-004 |
| TST-20 | `test_retired_type_field_is_rejected` | `test_routes.py` | FR-016 |
| TST-21 | `test_invalid_selection_fields_return_400` | `test_routes.py` | FR-001, FR-002, FR-003, FR-004 |
| TST-22 | `test_page_exposes_stable_selectors` | `test_routes.py` | FR-017, SC-005 |
| TST-23 | `test_dns_output_is_unchanged_for_verified_selection` | `test_routes.py` | FR-015, SC-006 |
| TST-24 | `test_verified_review_and_export_round_trip` | `test_routes.py` | User Story 1 |
| TST-25 | `test_shared_portal_registers_no_converter_routes` | `test_routes.py` | FR-018 |
| TST-26 | Browser selector journey in `test_portal_smoke.py` | `tests/e2e/web_portal/` | FR-017, SC-005 |

The existing unit test file keeps its test names. Its imports and arguments change in T004 (FR-015).

## Constrained-Field Coverage

| Field | Constraint | Tests |
| --- | --- | --- |
| `role` | One of `branch`, `hub`, or `standalone`. | TST-21, TST-03 |
| `family` | One of `srx` or `ssr`. | TST-21 |
| `model` | 1 to 32 visible characters. Register membership decides the row. | TST-21, TST-08 |
| `ports` | A JSON list of at most 16 assignment objects. | TST-21 |
| `mist_port` | Matches the `ge` or `xe` grammar. Must be a WAN or LAN name in the row. | TST-21, TST-10 |
| `usage` | `wan` or `lan`. Both usages must appear. | TST-21, TST-14 |
| `source_interface` | 1 to 64 characters. Must appear in the uploaded file. | TST-13, TST-21 |
| `evidence_revision` | Equals `CURRENT_REVISION` for each row. | TST-15 |
| `status` | `verified` only when `blockers` is empty. | TST-01, TST-03 |
| `blockers` | Codes from `proposal-json.md`, each reported once per failing port. | TST-04 to TST-15 |

## Constitution Alignment

- Principle I: The converter root holds five children. The `conversion/` root holds three children after this record. The `hardware/` package holds three children. The integration test folder holds four children after this record and five after issue 4640.
- Principle II: `HardwareRegister`, `HardwareMapping`, and `ConverterInput` carry the behavior. No function wraps a class method.
- Principle III: Each selection field is validated before use. No destructive operation is added.
- Principle IV: The pipeline runs in the order of the final tasks.
- Principle V: New log text uses ASCII. The structured logging question stays with issue 4636 (U-2).
- Principle VI and VII: T014 audits inline comments and action logs.

## Unmapped Tasks

None. Each task maps to at least one requirement in `tasks.md`.

## Metrics

- Requirements: 20. Decisions: 18. Human decisions: 0.
- Tasks: 18. Planned tests: 26.
- Remote checks: 62, with 57 present, 5 absent, 0 partial, and 0 stale.
- Blockers in the register: 10 rows in total. Two rows are verified (SRX300 and SRX320). Eight rows are blocked.

## Unresolved Items

| ID | Owner | Action | Blocks |
| --- | --- | --- | --- |
| U-1 | Issue 4634 | Record field semantics for each verified row, including the `defaults` keys (UV-04). | T006 |
| U-2 | Issue 4634 | Record Branch mapping evidence (UV-01). | Branch review |
| U-3 | Issue 4634 | Record inventory samples for SRX340, SRX345, SRX380, SRX550, SRX1600, and SRX4100 (UV-08). | Those rows |
| U-4 | Issue 4634 | Record SSR port roles or confirm that none exist (UV-09). | SSR rows |
| U-5 | Issue 4636 owner | Merge the `state/` package. | T008 |
| U-6 | Issue 4637 owner | Merge the review section and route changes. | T009 and T010 |
| U-7 | Issue 4640 owner | Use `usage` for the WAN or LAN value. Keep family on the selection. Drop the DNS move. | Issue 4640 implementation |
| U-8 | Issue 4641 owner | Read the `hardware` key. Replace the statement that `converter.js` stays unchanged. | Issue 4641 implementation |
| U-9 | Issue 4647 owner | Merge the visual journey changes. | T013 |
| U-10 | Issue 4642 owner | Put discovery tests in a folder that keeps the integration folder at five children. | Issue 4642 implementation |
| U-11 | Owner of the layout | Approve the `conversion/` layout from issue 4640 (assumption A-2). | T005 |
