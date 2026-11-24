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
