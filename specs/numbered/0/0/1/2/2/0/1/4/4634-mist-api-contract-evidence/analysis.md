# Specification Analysis Report: Mist API Contract Evidence for the Cisco Converter

This report checks the spec, plan, tasks, and remote code against each other. It lists each defect in existing work. Each finding cites its evidence. Remote evidence uses the RV identifiers in `design\research.md`.

## Findings

| ID | Severity | Area | Evidence | Impact and action |
| --- | --- | --- | --- | --- |
| A-01 | High | Issue evidence | Issue comment 1 cites `tests/unit/gateway/overrides`. The path is absent on `main` (RV-19). The real path is `tests/unit/marvis/mist/resources/gateway/overrides/` (RV-18). Record 4649 (F-02) repeats the error. | Readers cannot find the cited test. The issue owner corrects the comment. Record 4649 owner corrects F-02. |
| A-02 | High | Parity contract | `design/contracts/mist.md` omits `deleteOrgServicePolicy` (RV-03). OpenAPI and SDK expose it (W-22). | The write inventory has a gap. Decision D-4 excludes the operation and keeps it disabled. |
| A-03 | High | SDK retry | `__api_request.py` line 209 runs the retry loop for all verbs. Line 229 retries HTTP 429 for writes (RV-64). Record 4644 (F-05) found the same behavior. | A create can repeat after HTTP 429. Decision D-5 counts repeats as one attempt. Task T010 pins the count. |
| A-04 | High | SDK timeout | `mist_post`, `mist_put`, and `mist_delete` pass no timeout argument (RV-66, lines 298, 300, 322, 324, and 343). | A write call can wait without a bound. The behavior status is partial. Record 4644 (D-8) bounds each write in the executor. |
| A-05 | High | SDK logging | `__api_request.py` line 296 logs the POST body at DEBUG. Line 320 logs the PUT body at DEBUG (RV-65). | Secret-bearing fields could reach logs. Decision D-13 keeps secret-bearing families disabled. |
| A-06 | Medium | Schema | Most write body schemas allow unknown top-level fields. Only the device and device profile subtypes set `additionalProperties` to false. | The schema cannot reject an unknown field for those objects. Decision D-6 adds a local allowlist. Task T015 tests it. |
| A-07 | Medium | Schema | `service` and `org_service_policy` define no required field. An empty body passes the schema. | An empty create would pass the schema. Decision D-18 requires `name` in the local rule. Task T015 tests it. |
| A-08 | Medium | Schema | Create responses reference object schemas. The `id` property is present but not required (for example `site`, `network`, and `service`). | A missing created ID passes the schema. Record 4644 (D-12) treats a missing ID as indeterminate. |
| A-09 | Medium | Schema | `mac_addresses.macs` requires at least one unique string. It defines no MAC pattern. | A malformed MAC address passes the schema. The converter sends no MAC address in this change. |
| A-10 | Medium | Schema | `site.sitetemplate_id` allows the type string or null. The description does not define null. | Null could mean unassignment. Decision D-8 refuses null. Record 4645 (D-3) asks the owner. |
| A-11 | Medium | Pin drift | Constitution line 279 says mistapi 0.59 or newer (RV-44). `.github\copilot-instructions.md` line 21 says 0.64.0 or newer (RV-45). `documentation\development-setup.md` line 14 says 0.64.0, less than 0.65 (RV-80). `pyproject.toml` line 29 says 0.64.1 or newer (RV-46). `requirements.txt` line 129 pins 0.64.1 (RV-48). | Five files state three mistapi versions. Decision D-11 uses 0.64.1. A separate issue corrects the text. |
| A-12 | Medium | Issue evidence | Issue comments dated 2026-11-08 and 2026-11-10 say the contract file remains in open PR 4596. PR 4596 merged on 2026-11-13 (RV-07). | The comments are stale. The issue owner corrects them. The contract file now exists on `main` (RV-01). |
| A-13 | Medium | Sibling record | Record 4636 summary states 60 remote checks. Its STATUS file records 24 remote checks. Both files were read in the spec-drafts folder. | The sibling counts disagree. The 4636 owner corrects the summary or the STATUS file. This record changes neither. |
| A-14 | High | Test placement | Records 4644 (F-01), 4645 (F-02), and 4649 (F-03) cite `tests/contract/cisco_config_converter/`. `tests/contract` holds 17 children (RV-31). Record 4649 (F-04) projects the converter integration folder at five children. | Adding a child breaks the five-item rule. Decision D-9 places the tests under `tests\contract\web_portal\cisco_config_converter`. |
| A-15 | Medium | Structure | `tests/unit/marvis/mist/resources/gateway/overrides` holds five children (RV-33). `src/interfaces/portals/cisco_config_converter` holds five children (RV-34). | A new file in either folder breaks the five-item rule. This change adds no file to either folder. |
| A-16 | Low | Coverage catalog | `MIST_API_MISSING_ENDPOINTS.md` line 3 says it compares OpenAPI GET endpoints with current `MistHelper.py` usage (RV-43). | The word "missing" describes MistHelper coverage. It does not show that the API lacks the operation. This record reads the file as coverage data only. |
| A-17 | Medium | Issue evidence | Issue comment 2 reports 16 synthetic cases. Issue comment 3 reports 12 synthetic cases and two format controls. The probe is not in the repository. | The results cannot be reproduced here. Unverified item U-13 records the gap. |
| A-18 | Low | Parity contract | `mist.md` cites Context7 documentation for `/tmunzer/mistapi_python`. This record cannot reproduce that source. | The claim is unverified. Unverified item U-11 records the gap. |
| A-19 | Medium | Inventory operation | The OpenAPI description of `inventory_update_operation` says `delete` removes inventory records. It says `delete` also unassigns an assigned device. | An enabled `delete` value removes inventory. Write operation W-03 keeps all values disabled. |
| A-20 | Medium | Field semantics | The OpenAPI description of `dns_servers` says `ip_config` and `oob_ip_config` DNS settings overwrite the global list. | A device can use DNS values other than the template list. The payload contract records this semantic limit. |
| A-21 | Medium | Converter scope | `conversion.py` lines 15 to 30 build one gateway template with `name`, `type`, and optional `dns_servers`. No other family has converter code. | Only the gateway template family has a current mapping. The other families stay disabled. |
| A-22 | Low | Signature | The SDK annotates create and assign functions with `body: dict \| list`. The OpenAPI file declares object bodies for these operations. | Array support is unverified. Decision D-7 refuses list bodies. |
| A-23 | Low | Confirmed | The issue-cited commit `7b7d5406ca7b95a96edf42702ee0049e0c7c2d64` exists (RV-38). The OpenAPI JSON blob at that commit equals the blob on `main` (RV-39). | The OpenAPI citations in the issue comments refer to the same file content as `main`. |

## Consistency Review

- The spec, plan, and tasks name the same 22 write operations and 18 read operations. The tables in `design\contracts` use the same identifiers.
- The spec states 32 planned tests. The tasks name the same 32 test functions. The plan states the same total.
- The spec requires 21 functional requirements. Each requirement maps to a task in the coverage table below.
- The plan states that the converter test folder holds five children at most. The change map adds one child to `tests\contract\web_portal`.
- The research file states 80 remote checks. The STATUS file and the summary state the same count.
- The tasks name the local gates. Each gate reference matches the table in `.github\copilot-instructions.md`.
- The family IDs F-01 to F-08 match record 4644. The read roles match the reference needs in record 4645.

## Coverage Summary

| Requirement | Tasks | Test or check |
| --- | --- | --- |
| FR-001 | T001, T006 | Test 1 and test 2 |
| FR-002 | T001, T007 | Tests 5 and 6 |
| FR-003 | T001, T006, T007 | Tests 1, 2, 3, and 5 |
| FR-004 | T001, T008 | Tests 7, 8, and 9 |
| FR-005 | T001, T006 | Test 2 checks the three status fields |
| FR-006 | T013 | Tests 20 to 24 |
| FR-007 | T014, T015 | Tests 25 to 30 |
| FR-008 | T010, T011 | Tests 13 to 16 |
| FR-009 | T010 | Tests 13 and 14 |
| FR-010 | T009 | Tests 10 and 11 |
| FR-011 | T013 | Test 20 |
| FR-012 | T012, T-LOCAL-GATES | Test 18 and the changed-path listing |
| FR-013 | T005, T011 | Test 17 and the autouse socket block |
| FR-014 | T006 | Test 2 |
| FR-015 | T002, T012 | Test 19 |
| FR-016 | T002, T015 | Test 31 |
| FR-017 | T004 | Check C-01 (remote count comparison) |
| FR-018 | T-PR, T-LOCAL-GATES | Guardrail tests in `tests\guardrails` |
| FR-019 | T016 | `tests\guardrails\test_changelog_fragment_policy.py` |
| FR-020 | T003 | Check C-02 (findings A-01 to A-13 cite owners) |
| FR-021 | T003 | Check C-03 (family and read roles match records 4644 and 4645) |

Check C-01 compares the remote check count in the STATUS file, the research table, and the summary. Check C-02 confirms each stale fact has an owner. Check C-03 compares the family IDs and the read roles with the sibling records.

## Constitution Alignment

Each rule of the constitution has a result in `plan.md`. No rule fails. The plan records three conditions. Each condition applies to the test code, and the tasks name the control for each one.

## Unmapped Tasks

No task lacks a requirement. The four final tasks map to the release process in `AGENTS.md` and to requirement FR-012 or FR-017.

## Metrics

| Metric | Count |
| --- | --- |
| Write operations (in scope) | 21 |
| Write operations (excluded) | 1 |
| Read operations | 18 |
| Contract rows | 40 |
| Functional requirements | 21 |
| Success criteria | 7 |
| Tasks | 21 |
| Planned test functions | 32 |
| Decisions | 18 |
| Human decisions | 2 |
| Remote checks | 80 |
| Unverified items | 18 |
| Findings | 23 |

## Unresolved Items

- Unverified items U-01 to U-18 in `design\research.md` remain open.
- Human decisions D-4 and D-8 remain open until the owner answers.
- Findings A-01, A-12, and A-13 need correction by their owners.

## Convergence After Implementation

- The registry in `conftest.py` matches the contract tables in `design\contracts`.
- All 32 planned tests pass. No socket opens during the run.
- No file under `src\` changed in the branch.
- All write operations stay disabled.
- The remote check count matches in the STATUS file, the research table, and the summary.
