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
| FR-045 | Yes | T072 | Added after the live portal run. |
| FR-046 | Yes | T073 | Added after the live portal run. |
| FR-047 | Yes | T071 | Added after the live portal run. |
| FR-048 | Yes | T074 | The audit of the list calls. |
| FR-049 | Yes | T075, T078, T080 | Added after the owner request (issue #4931). |
| FR-050 | Yes | T075, T076, T077 | |
| FR-051 | Yes | T075 | |
| FR-052 | Yes | T075, T076 | |
| FR-053 | Yes | T078, T080 | |
| FR-054 | Yes | T081 | Added after the live check of the table (issue #4932). |
| FR-055 | Yes | T087, T088, T093 | Added after the customer request (issue #4933). |
| FR-056 | Yes | T083, T084, T093 | |
| FR-057 | Yes | T083, T086 | |
| FR-058 | Yes | T083, T084 | |
| FR-059 | Yes | T082, T083 | |
| FR-060 | Yes | T083, T091 | |
| FR-061 | Yes | T084, T091, T092 | |
| FR-062 | Yes | T083, T091 | |
| FR-063 | Yes | T085, T088 | |
| FR-064 | Yes | T083, T085, T088, T091 | |
| FR-065 | Yes | T088, T093 | |
| FR-066 | Yes | T089, T093 | |
| FR-067 | Yes | T086, T094 | |
| FR-068 | Yes | T088, T091 | |
| FR-069 | Yes | T087, T094 | |

Success criteria that need build work: SC-001 (T021), SC-002 (T022), SC-003 (T052), SC-004 (T049), SC-005 (T063), SC-006 (T032), SC-007 (T010, T052), SC-008 (T037), SC-009 (T091), SC-010 (T093), SC-011 (T093), SC-012 (T092). All have a task.

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
| F7 | Live portal run in a browser | HIGH | The local `--web-portal` mode built the portal with no organization, so the WebSockets tab was not ready. | Fixed in issue #4929 with FR-047 and T071. The launcher resolves the organization like the interactive mode. |
| F8 | Live portal run in a browser | MEDIUM | The hardware action emptied the Targets card, so the operator could not choose sites. | Fixed in issue #4927 with FR-045 and T072. The card stays, and a subset goes to the existing site resolver. |
| F9 | Live portal run in a browser | MEDIUM | The page did not name the confirmation word near its box, and did not say that the preview comes first. | Fixed in issue #4928 with FR-046 and T073. |
| F10 | Owner request | MEDIUM | The portal offered the combined CSV report as a download only. The owner asked to read the report in the browser, as a preview or a table, like the other tools of the owner. | Done in issue #4931 with FR-049 through FR-053 and T075 through T080. The progress card shows a table with a filter and page buttons. The route reads the report through the same checked read as the download. Live: the table equals the file cell for cell. |
| F11 | Live check of the table | MEDIUM | The page opened the batch parent of the hardware action as a terminal. The portal answered HTTP 409 `not_terminal` on the terminal read and on the resize, and the output panel showed `State: Connecting` for ever on the first tab. | Fixed in issue #4932 with FR-054 and T081. The page no longer reads a `multi_site` parent as a terminal. |
| F12 | Customer request | HIGH | The customer added a requirement on 2026-11-25: one XML file that holds the XML of all the switches, valid to the XML standard so that other programs read it with no repair. The tool had the CSV report and one XML file for each switch. | Done in issue #4933 with FR-055 through FR-069, SC-009 through SC-012, and T082 through T094. A strict builder, a second verifier that writes nothing, and a read-back of the file make the file valid or absent. Live: nine readers that the tool does not use accepted the files of both front ends, and the 114 serial numbers equal those of the saved replies. |
| F13 | Complexity gate | MEDIUM | The first run of `radon cc` on the new module found three functions at cyclomatic complexity 16, 14, and 11, against a limit of 10. | Fixed in T090. `XmlWriter.Space`, `MasterXmlBuilder.Entry.of`, and `MasterXmlBuilder._counts` took the branches, and the tests did not change. |
| F14 | Test quality ratchet | MEDIUM | The ratchet reported 13 findings in the three new test files: four weak `is not None` assertions, one test with no `assert`, and edge cases and failure modes (an empty input, a None input, an empty body, malformed JSON). | Fixed with tests that exercise the real behavior and no baseline edit: an empty file, an empty and a damaged saved reply, a damaged manifest after a restart, an empty scope, and a missing scope. The verifier no longer uses JSON, so the module needs no malformed-JSON test. |
| F15 | Fault injection | MEDIUM | A run of 52 small faults found seven that the tests did not catch (T092): the `xml:space` rule in two places, the case folding at the three sort levels, the byte limit for multi-byte text, and the numbered name of the XML file. | Fixed with seven tests that fail without the code. A second run caught all seven. |
| F16 | Full guardrail run | LOW | Three failures that the baseline of 23 does not hold. One was real: the menu identity pin of `test_endpoint_catalog.py` hashes the menu block, so the new title of menu 309 changed it. Two were `e2e_timeout_budget` timing tests that measure real pytest runs, and they failed while other work loaded the machine. | The pin has the new digest and a comment that names issue #4933. The two timing tests pass alone (7 passed). |
| F17 | Owner question | MEDIUM | The owner asked how MSP mode signs in when the MSP and the organization require 2FA, in the CLI and in the portals. The review found no code defect: the CLI login asks for the code, `--login --web-portal` hands that session to the portal, and a login session opens a shell with cookies. It found three outdated statements (`MSP-Support.md` said an MSP grant cannot use a token, and two API notes said that MistHelper never signs in with a password), no sign-in section for menu 309, and four claims with no test. | Fixed in FR-070, FR-071, T095 through T099, and research R17. The documentation now tells the operator how to sign in for each front end. Four tests cover the claims, and four faults in the source made them fail. The one real gap, a browser sign-in with 2FA for the operations portal (port 8055), is out of scope and tracked in issue #4936. Not verified live: nobody typed a 2FA code or used an MSP account in this change. |

Requirement changes: FR-043 and FR-044 are new (T068, T069). FR-045 through FR-048 are new (T071 through T074). FR-049 through FR-054 are new (T075 through T081). FR-055 through FR-069 are new (T082 through T094). FR-070 and FR-071 are new (T095 through T099). FR-040 holds: every live run used a read-only command on one organization. SC-005 is met live for the CLI (T070) and for the portal (T071): the report and the saved replies hold the same 114 serial numbers, and each switch has as many rows as its reply has chassis elements. SC-009 through SC-012 are met (T091, T093, T092).

Metrics after the pass:

- Total requirements: 71 functional and 12 success criteria.
- Total tasks: 99. Tasks T001 through T064 and T068 through T099 are done. T065 and T066 close with this pass and the pull request. T067 needs the owner.
- Coverage: 100 percent of functional requirements have at least one task.
- Critical issues: 0. Open items for the owner: the MSP test with a 2FA sign-in, and a run of the master XML in MSP scope. The customer parsers are not known, so the file was checked with the readers that the tool does not use.
