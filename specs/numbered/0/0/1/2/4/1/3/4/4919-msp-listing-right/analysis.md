# Specification Analysis Report: MSP organization list skipped without the listing right

## Findings

- **A1 (defect in existing code)**: `discover_organizations` treats every profile grant with a non-empty `msp_id` as an MSP grant. It calls `_discover_msp` without a scope test. Evidence: `client.py` main lines 99 and 100 (remote row R02). The menu 309 profile reader accepts only scope `msp` as MSP. Evidence: `profile.py` main line 136 (remote row R13). Resolution: tasks T001 to T003.
- **A2 (defect in documentation)**: `documentation/api/msps/GET_msps_msp_id_orgs.md` line 183 states "Not currently used by MistHelper directly." Nine `src` call sites exist (A3). Resolution: remediation R-3, separate issue.
- **A3 (same pattern in other callers)**: A local search of the working tree found nine `listMspOrgs` call sites in `src`. They sit in `interfaces/portals/licensing_comparison/api.py`, `mist/access/auth/interactive/msp_org_selector.py`, `mist/intelligence/reports/subscription_expiry/client.py`, `mist/resources/inventory/org_device_inventory_msp.py`, `operations/execution/firmware/firmware_manager.py`, `operations/execution/firmware/org_ap_upgrader.py`, `operations/exporting/export/msp_inventory_exporter.py`, `operations/exporting/export/org_config_exporter.py`, and `operations/exporting/ex_hardware_inventory/scope/resolver.py`. Only the menu 309 resolver receives a scope-filtered profile list. Resolution: remediation R-2, separate issue. The line numbers of the other callers are unverified against `main` (U7).
- **A4 (same pattern in the detector)**: `_msp_parse_one_privilege` accepts any grant with `msp_id` and records `scope` without testing it. Evidence: `msp_privilege_detection.py` main lines 84 and 90. The detector output feeds `msp_privileges`, which `org_device_inventory_msp.py` uses. Resolution: remediation R-2, separate issue. Issue #4713 owns the detector contract, so this change leaves that file alone.
- **A5 (documentation drift in the mistapi pin)**: `.github/copilot-instructions.md` line 21 states `mistapi>=0.64.0,<0.65`. `pyproject.toml` line 29 states `>=0.64.1,<0.65`, and `requirements.txt` line 129 pins `==0.64.1`. The installed copy is 0.64.1, which satisfies every statement. Resolution: remediation R-4, separate issue.
- **A6 (existing length debt)**: `discover_organizations` spans main lines 79 to 106 (28 lines). `_print_summary` spans main lines 494 to 519 (26 lines). Both exceed the 25-line limit in the constitution. The change keeps the first unchanged and adds at most two lines to the second. Resolution: remediation R-1.
- **A7 (naming of a count)**: The console label "Organizations discovered" counts every status row, including MSP failure rows (main line 505). The change excludes skipped rows only (FR-008). Resolution: a separate naming issue, if the maintainers want one.
- **A8 (divergent defaults)**: The `mist-ops-platform` reader treats a missing `scope` key as not MSP (`auth.py` main line 164). The menu 309 reader treats a missing key as MSP (`profile.py` main line 136). Decision D3 follows the MistHelper reader. The `mist-ops-platform` reader stays unchanged.
- **A9 (uncommitted work)**: The local working copy differs from `main` in `client.py` and `test_client.py`. The difference adds `_warn_msp_list_failed`, `HTTP_FORBIDDEN`, `_sdk_error_lines_muted`, and a 403 warning test. Remote rows R04 to R06 and R21 show that `main` lacks these items. Seven open pull requests touch no related file. The issue number and the owner of the pending change are unknown (U5). Resolution: decision D6.
- **A10 (issue evidence)**: Issue #4919 states that the call returns HTTP 403 on every run. The issue gives no log, request, or response. Unverified item U4 records this gap.
- **A11 (skill check)**: No local skill applies. The issue concerns Mist cloud API calls and Python code, not Podman or Juniper devices.

## Consistency Review

| Requirement | Tasks | Test or gate check |
| - | - | - |
| FR-001 | T001, T002 | Test functions 1 and 2 in T005 |
| FR-002 | T001 | Test functions 3 and 4 in T005 |
| FR-003 | T002 | Test function 2 in T005 |
| FR-004 | T003 | Test function 6 in T005 |
| FR-005 | T003 | Test function 2 in T005 and the contract `status-rows.md` |
| FR-006 | T003 | Test function 2 in T005 and the contract `msp-listing-right.md` |
| FR-007 | T004 | Test function 7 in T006 |
| FR-008 | T004 | Test function 7 in T006 |
| FR-009 | T002 | Test function 1 in T005 and the existing test at main line 104 |
| FR-010 | T-000, T003, and T009 | Test function 2 in T005 checks the return shape and the six status columns. The `model.py` diff is empty (SC-006). |
| FR-011 | T003 and T004 | Test function 2 in T005 checks the info and debug log lines. Review checks the inline comments. |
| FR-012 | T007 | STE gate in T007 |
| FR-013 | T008 | STE gate in T008 |
| FR-014 | T005 and T006 | Test functions 1 to 8 |

- Every requirement maps to at least one task and at least one test or check.
- Every task names exact repository paths and one verification command.
- No task lacks a requirement ID.

## Constrained-Field Coverage

- `request_status` takes the value `skipped` in the new rows. Existing consumers read `success`, `partial`, `failed`, and `unavailable`. The console summary counts only those values. The new value does not change those counts.
- `source` takes the value `msp`. The existing failure rows use the same value.
- `scope` is read from the profile. The mistapi OpenAPI lists the enum values `msp`, `org`, `orggroup`, `site`, and `sitegroup` (remote rows R48 and R49).

## Constitution Alignment

- Principle I: pass with debt R-1 (A6).
- Principle II: pass. New methods sit in classes.
- Principle III: pass. No input or destructive action is added.
- Principle IV: pass. Steps 10 to 12 run after T-MERGE.
- Principle V: pass. ASCII text only.
- Principle VI: pass by requirement FR-011. Review checks the inline comments.
- Principle VII: pass by requirement FR-011.
- Escalation rule: pass. This record exists because the change touches several files.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

- Requirements: 14 (FR-001 to FR-014).
- Success criteria: 6 (SC-001 to SC-006).
- Tasks: 14 (T-000, T001 to T009, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE).
- Tests planned: 8 test functions (6 in `test_client.py`, 2 in `test_operation.py`).
- Files modified: 5 (two source files, two test files, and one document). Files added: 1. Files with no change in the change map: 3.
- Remote checks: 51 rows in `design/research.md` and 51 entries in `remote_checks`.

## Unresolved Items

- U1: The role that the listing call needs is unverified (see `design/research.md`).
- U2: Live organization-scope grants may or may not carry `msp_id`. The change has no effect when they do not.
- U5: The owner and the issue number of the pending warning change are unknown.
- D8: Scheduling needs a human answer. HUMAN-DECISION-REQUIRED.

## Convergence After Implementation

After T003 and T004, these checks must hold:

- No code path calls `listMspOrgs` for a grant whose `scope` is not `msp`.
- Each skipped source appears once in the status CSV and once in the console summary.
- `model.py` has no diff in the pull request.
- The test count in `test_client.py` and `test_operation.py` grows by eight test functions.
