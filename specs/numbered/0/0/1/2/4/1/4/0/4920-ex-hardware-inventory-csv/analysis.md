# Specification Analysis Report: EX Hardware Inventory CSV

**Date**: 2026-11-24

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/data-model.md`, and the constitution (version 1.9.0).

**Method**: A read-only pass built the requirement inventory, the task coverage map, and the constrained-field citation map. The first pass found nine findings. The author fixed seven of them at once and accepted two with a reason. This report shows the state after the fixes.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| I1 | Inconsistency | HIGH | `spec.md` FR-023, `design/data-model.md`, `design/contracts/report-csv.md` | FR-023 required a MAC address, but the data model and the contract hold no MAC column. The picker identity carries no MAC. | Fixed. FR-023 now names the identifier and the host name. |
| I2 | Inconsistency | MEDIUM | `plan.md` Source Code | The edit list omitted `assembly/collaborators.py`, which T046 edits. The settings tests sit in `live/sessions/`, not in `web/`. | Fixed in the plan. |
| C1 | Coverage | MEDIUM | `tasks.md` T014 | `data-model.md` `ReportRow.item_type` had no citation in an implementing task. | Fixed. T014 cites it. |
| U1 | Underspecification | MEDIUM | `spec.md` FR-041, T016, T025 | No task tied the CLI report to the size limit. | Fixed. T016 takes the byte limit and both front ends pass 64 MiB. |
| U2 | Underspecification | MEDIUM | `spec.md` FR-039, T032, T035 | No task mapped a discovery error such as HTTP 429 to a reported organization failure. | Fixed in T032 and T035. |
| C2 | Coverage | LOW | `spec.md` SC-008 | No explicit regression check for the XML, JSON, and both outputs. | Fixed. T037 adds the regression case. |
| U3 | Underspecification | LOW | `spec.md` Edge Cases | No task covered an existing report name. | Fixed. T025 adds a numeric suffix. |
| A1 | Ambiguity | LOW | `tasks.md` T046 | "Smallest edit" in `collaborators.py` stays open until the code is read under the structure limits. | Accepted. The plan Risks section gives the fallback. |
| C3 | Coverage | LOW | `spec.md` Edge Cases | The CLI and the portal run the action at the same time. | Accepted. They run in separate processes, so no code is needed. |

## Coverage Summary

| Requirement | Has task | Task IDs | Notes |
|-------------|----------|----------|-------|
| FR-001 | Yes | T026, T027, T047 | |
| FR-002 | Yes | T026, T033, T034 | |
| FR-003 | Yes | T031, T034 | |
| FR-004 | Yes | T030, T033 | |
| FR-005 | Yes | T031, T034 | |
| FR-006 | Yes | T031, T034 | |
| FR-007 | Yes | T032, T035 | |
| FR-008 | Yes | T022, T024 | Reuses the target filter of issue #4769. |
| FR-009 | Yes | T021, T026 | Reuses the preview exclusions. |
| FR-010 | Yes | T009, T013 | |
| FR-011 | Yes | T031, T034 | The pickers already read every page. |
| FR-012 | Yes | T022, T024 | Reuses the status re-check. |
| FR-013 | Yes | T021, T026 | Reuses the target limit. |
| FR-014 | Yes | T037, T042 | |
| FR-015 | Yes | T024 | |
| FR-016 | Yes | T006, T007, T045, T049, T050 | |
| FR-017 | Yes | T007, T045, T047, T050 | |
| FR-018 | Yes | T021, T032, T052 | |
| FR-019 | Yes | T011, T015 | |
| FR-020 | Yes | T012, T016 | |
| FR-021 | Yes | T009, T013, T015 | |
| FR-022 | Yes | T011, T015 | |
| FR-023 | Yes | T011, T015 | |
| FR-024 | Yes | T009, T013 | |
| FR-025 | Yes | T010, T011, T014, T015 | |
| FR-026 | Yes | T010, T014, T052 | |
| FR-027 | Yes | T020, T025, T037, T041 | |
| FR-028 | Yes | T008, T020, T025 | |
| FR-029 | Yes | T021, T026 | |
| FR-030 | Yes | T021, T027 | |
| FR-031 | Yes | T055, T057 | |
| FR-032 | Yes | T040, T042, T047 | |
| FR-033 | Yes | T037, T041, T043, T044 | |
| FR-034 | Yes | T039, T045, T046 | |
| FR-035 | Yes | T040, T047 | |
| FR-036 | Yes | T037, T060 | |
| FR-037 | Yes | T052, T061, T063 | |
| FR-038 | Yes | T061 | |
| FR-039 | Yes | T030, T032, T035 | |
| FR-040 | Yes | T063 | |
| FR-041 | Yes | T012, T016, T041, T052 | |
| FR-042 | Yes | T021, T026 | |
| FR-043 | Yes | T068 | Added after the live run. |
| FR-044 | Yes | T069, T070 | Added after the second live run. |

Success criteria that need build work: SC-001 (T021), SC-002 (T022), SC-003 (T052), SC-004 (T049), SC-005 (T063), SC-006 (T032), SC-007 (T010, T052), SC-008 (T037). All have a task.

## Constrained-Field Coverage

| Field | Canonical location | Implementing tasks | Notes |
|-------|--------------------|--------------------|-------|
| `OrganizationRef.org_id`, `org_name`, `msp_id`, `source` | `data-model.md` OrganizationRef | T034 | |
| `ScopeDecision.mode`, `organizations`, `notes` | `data-model.md` ScopeDecision | T034 | |
| `ScopeDecision.credential_type`, `account_kind` | `data-model.md` ScopeDecision | T033 | |
| `StreamSettings.hardware_concurrency` | `data-model.md` HardwareConcurrency | T007 | |
| `TargetResult.identity`, `org_name`, `state`, `reason`, `xml_text` | `data-model.md` TargetResult | T015 | |
| `FlattenedItem.level`, `path`, `item_type`, `fields` | `data-model.md` FlattenedItem | T013 | |
| `ReportRow.report_run_utc`, `org_id`, `org_name`, `site_id`, `site_name`, `device_id`, `device_name`, `collection_detail`, `device_cli_banner`, `item_path` | `data-model.md` ReportRow | T015 | |
| `ReportRow.scope`, `record_type`, `collection_status`, `item_level`, `item_type`, `item_<field>` | `data-model.md` ReportRow | T014 | |
| `ReportFile.name`, `partial` | `data-model.md` ReportFile | T025, T041 | |
| `ReportFile.row_count`, `size_bytes` | `data-model.md` ReportFile | T016, T025, T041 | |
| `RunSummary.organizations`, `targets`, `counts`, `report_path` | `data-model.md` RunSummary | T026 | |

Every constrained field has a citation. No task states a constraint that contradicts the canonical definition.

## Constitution Alignment

No finding violates a MUST principle.

- Principle I: the plan keeps each directory at five children or fewer, adds no method to a full class, and runs the structure guard after each WebSocket edit (T048, T058).
- Principles VI and VII: T061 audits comments and logging.
- Output Backends and Database Keys: T008, T025.
- Deviation, recorded in the plan: the README menu table step is not applied, because issue #4916 removed menu text from the README. T062 files the follow-up.
- Principle IV steps 9 to 12 need the owner. T066 and T067 hand them over.

## Unmapped Tasks

None. Each task maps to a requirement, a story, or a gate.

## Metrics

- Total requirements: 42 functional and 8 success criteria.
- Total tasks: 67.
- Coverage: 100 percent of functional requirements have at least one task.
- Ambiguity count: 1 (accepted).
- Duplication count: 0.
- Critical issues: 0.

## Convergence After Implementation

**Date**: 2026-11-25

**Method**: A second pass compared the specification, the plan, the tasks, and the contracts with the code, the tests, the gate results, and the live run on the test organization. Each finding below has its resolution.

| ID | Source | Severity | Summary | Resolution |
|----|--------|----------|---------|------------|
| F1 | Full guardrail run | HIGH | The symbol preservation guard counted the removed `BatchTargetPickerService` import of the service factory as a lost name. The factory now builds `ScopeAwareTargets`, a subclass. | Fixed. A reviewed removal entry in `INTENTIONAL_SYMBOL_REMOVALS` names the module, the symbol, and the reason. No other module imports the name from the factory. |
| F2 | Live run | HIGH | The configured token is an organization token with the read-only role. Mist refused each of the 15 shell sessions with HTTP 403 (`shell access not allowed for this user`). Every switch then failed with a generic detail, and nothing told the operator why. | Fixed for the message. FR-043 and T068 add the step 1 note, the detail points to the log, and the guide, the contract, and the release note say it. The success path was proven live later, with an admin-role token (F6). |
| F3 | Test quality ratchet | MEDIUM | The ratchet reported 20 findings in the new tests: three weak assertions, eight numeric edge cases, and nine failure modes. | Fixed with real tests and no baseline edit: HTTP 4xx and 5xx on four reads, three transport faults, restart cleanup with an empty and a damaged manifest, and limits of 0 and -1. The helper `uuid` is now `make_uuid`, the documented fixture-builder prefix. |
| F4 | Pylint | LOW | Four `protected-access` notes in `run/routing.py`: the router reads `_apisession` and `_org_id` of the picker. | Accepted. The score is 9.73 against a floor of 9.5. A public accessor on the picker needs a change of shared WebSocket code and a new structure count. |
| F5 | Full-suite ratchet | LOW | The full-suite ratchet prints 18 findings in `tests/test_upgrade_portal_audit.py` and `tests/unit/test_ssh_host_key_tofu.py`. This branch does not change those files, and they match `origin/main`. | Out of scope. The required check scans only the changed files and prints 0. |
| F6 | Second live run | HIGH | With the admin-role token, 14 of 15 switches collected. One manifest replace in a OneDrive folder got a Windows permission error. The store marked the whole batch record as failed, so the last switch was refused, and the report called its reply invalid. A loop in the same folder reproduced the error: 89 of 1500 replaces failed, and a wait of 50 ms cleared 87 of them. | Fixed in issue #4926 with FR-044 and T069. `Metadata.replace` tries up to five times and retries a permission error only. The report names a failed save. The run after the fix collected 15 of 15 (T070). |

Requirement changes: FR-043 is new (T068), and FR-044 is new (T069). FR-040 holds: both live runs used a read-only command on one organization. SC-005 is met live (T070): the report and the 15 saved replies hold the same 114 serial numbers, and each switch has as many rows as its reply has chassis elements.

Metrics after the pass:

- Total requirements: 44 functional and 8 success criteria.
- Total tasks: 70. Tasks T001 through T064 and T068 through T070 are done. T065 and T066 close with this pass and the pull request. T067 needs the owner.
- Coverage: 100 percent of functional requirements have at least one task.
- Critical issues: 0. Open items for the owner: the MSP test.
