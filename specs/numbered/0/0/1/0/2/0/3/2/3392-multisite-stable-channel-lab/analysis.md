# Specification Analysis Report: Multi-site stable word and router channel lab verification

Audit date: 2026-11-26. Each finding cites a remote check row (RC-nn) from `design/research.md`.

## Findings: Defects and Stale Content

| ID | Finding | Evidence | Action |
| - | - | - | - |
| A-1 | Issue #3392 cites `src/firmware/aggregate_upgrade_service.py`, which is absent on main. The current file is under `src/operations/execution/firmware/`. | RC-58, RC-27 | Owner edits the issue text. The agent cannot write to GitHub. |
| A-2 | PR #3391 lists `src/firmware/` and `src/upgrade_portal/` paths. Both are absent on main. The PR is merged, so the list is historical. | RC-59 | No action. The record uses the current paths (D-5). |
| A-3 | Parity row C17 says `parity` for all families, including access points. The save refuses the stable word for access points. | RC-98, RC-99, RC-42 | T017 sets a gap for the access point family until L-AP-STABLE has an accepted verdict. |
| A-4 | Parity row C21 says `parity` and cites `org_options.html` line 35 as absent. The router channel control is at line 535. | RC-101, RC-102, RC-45 | T017 cites line 535 as the multi-site evidence. |
| A-5 | The constitution says mistapi 0.59 or newer. `requirements.txt` pins 0.64.1 exactly. The instructions name the range from 0.64.0 to below 0.65. | RC-12, RC-25, RC-04 | Owner amends the constitution text through its amendment procedure (a PATCH change). A follow-up issue tracks it. |
| A-6 | The installed mistapi function `getOrgSsrUpgrade` requests the cancel path with a GET call. | RC-117 | The owner reads router jobs with `listOrgSsrUpgrades` (D-10). The SDK defect is reported upstream by the owner, if the owner chooses. |
| A-7 | The typed word is UPGRADE in the constitution example and in the CLI rule. The portal uses CONFIRM. | RC-11, RC-08, RC-52 | Owner decides whether to align the documents. The record uses CONFIRM for lab writes (D-3). |
| A-8 | The STE row names a fixed list of Markdown files. The list omits specs records. | RC-06 | D-12 runs the STE gate on changed Markdown files as well. |
| A-9 | The `speckit-task-audit` step is advisory. CI does not block a format error in a task file. | RC-24 | The owner or the implementing agent runs the audit before the pull request. |
| A-10 | The organization device upgrade schema marks the top-level strategy field as deprecated. | RC-70 | The lab body omits the field (D-13). Whether the production body still sends it is not part of this audit (see U-3). |
| A-11 | The operator guide has no entry for the write gate ORG_UPGRADE_WRITES_ENABLED. The search covered the local copy only. | Unverified item 3 in `design/research.md` | Owner decides on a documentation follow-up. |
| A-12 | Legacy record `specs/3383-multisite-advanced-controls` sits at the specs root and is grandfathered. | RC-26 | Owner decides on a migration. The migration is separate from this issue. |
| A-13 | The multi-site save refuses the stable word for access points. The portal therefore cannot send the lab check for access points. | RC-41, RC-42, RC-43 | The access point lab check uses one SDK call (D-14). |

## Coverage Summary

Each functional requirement maps to at least one task and at least one TST item. A TST item is a repository test or an audit.

| Requirement | Tasks | TST items |
| - | - | - |
| FR-001 Keep the access point refusals until an accepted answer | T006, T011, T012 | TST-01, TST-02 |
| FR-002 The agent makes no cloud call | T005 to T010 | TST-13 |
| FR-003 The owner types CONFIRM before a write | T005, T006 to T009 | TST-12 |
| FR-004 Sanitized fields only in each lab answer | T006 to T010, T019 | TST-13 |
| FR-005 Accepted branch removes the refusals and offers the stable build | T011, T016 | TST-03, TST-04, TST-10 |
| FR-006 Refused branch keeps the refusals and records the answer | T012, T019 | TST-01, TST-13 |
| FR-007 Offer only the channel values that every router accepts | T007 to T009, T013 to T016 | TST-05, TST-06 |
| FR-008 Channel only in router bodies | T016 | TST-07, TST-08 |
| FR-009 Parity fixture shows the access point gap | T017 | TST-11 |
| FR-010 Remote citations match main | T002, T003, T019 | TST-14 |
| FR-011 Managed numbered route and five-child folders | T001 | TST-15, TST-16 |
| FR-012 Local gates pass on changed files | T-LOCAL-GATES, T018, T-PR, T-REMOTE-CI | TST-17, TST-18, and the Local gates table |

### TST Items

| ID | Item | Location | Kind | Branch |
| - | - | - | - | - |
| TST-01 | Refused case for stable with an access point plan | `tests/contract/upgrade_portal/test_org_advanced_options.py` line 133 (RC-84) | Existing test | Both |
| TST-02 | Refused request and refusal test for the access point body | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py` lines 96 and 158 (RC-91, RC-92) | Existing test | Both |
| TST-03 | Stable word reaches each access point body | `tests/contract/upgrade_portal/test_org_advanced_options.py`, a new function beside line 381 | New test | Accepted |
| TST-04 | Stable build with an access point reaches the confirm page | `tests/e2e/upgrade_portal/test_org_advanced_options.py` line 231 (RC-94) | Updated test | Accepted |
| TST-05 | SSR channel stable value | `tests/unit/upgrade_portal/test_upgrade_ssr_options.py` lines 158 and 165 (RC-90) | Updated test | Refused |
| TST-06 | Single-site channel loop over the three values | `tests/contract/upgrade_portal/test_upgrade_options.py` line 1358 (RC-96) | Updated test | Refused |
| TST-07 | Router channel reaches only the router body | `tests/contract/upgrade_portal/test_org_advanced_options.py` line 394 (RC-86) | Existing test | Both |
| TST-08 | Channel control shows only for a router | `tests/contract/upgrade_portal/test_org_advanced_options.py` line 405 (RC-87) | Existing test | Both |
| TST-09 | Stable choice replaces each picked version | `tests/unit/upgrade_portal/test_upgrade_advanced_options.py` line 365 (RC-89) | Existing test | Both |
| TST-10 | Stable build needs a body that names it | `tests/unit/upgrade_portal/test_org_advanced_summary.py` line 150 (RC-88) | Existing test | Both |
| TST-11 | Parity page test for the corrected rows | `tests/e2e/upgrade_portal/journeys/test_parity_pages.py` (RC-103, RC-111) | Existing test | Both |
| TST-12 | Organization write needs the exact confirmation | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` line 633 (RC-97) | Existing test | Both |
| TST-13 | Evidence audit of the four lab answers | `design/quickstart.md`, section 7 | Audit | Both |
| TST-14 | Citation audit of the remote table | `design/quickstart.md`, section 8 | Audit | Both |
| TST-15 | Spec route contract | `tests/guardrails/test_spec_route_contract.py` (RC-104) | Guard | Both |
| TST-16 | Five-child rule for each folder | `tests/guardrails/test_process_folder_structure.py` (RC-105) | Guard | Both |
| TST-17 | Changelog fragment policy | `tests/guardrails/test_changelog_fragment_policy.py` (RC-106) | Guard | Accepted or refused with a change |
| TST-18 | SDK compatibility for each changed call | `tests/integration/test_mistapi_sdk_compatibility.py` (RC-107) | Guard | Only when a call changes |

## Unresolved Items

| ID | Item | Owner of the answer | Effect while unresolved |
| - | - | - | - |
| U-1 | Whether the cloud accepts the stable word on the access point route | Owner (T006) | The refusals stay (FR-001). |
| U-2 | Whether the cloud accepts each channel value on the router route | Owner (T007 to T009) | Each value stays. |
| U-3 | Whether the access point route needs a strategy field for an accepted call | Owner (T006 reads the field error) | The lab body omits the field (D-13). EC-1 repeats the check once. |
| U-4 | Whether the router route accepts the stable word as the version | Not in this issue. The multi-device schema has no stable word and no default for version (RC-75). The single-device schema defaults version to stable (RC-73). | This issue sends no version to the router route. An owner check can follow in a later issue. |
| U-5 | Whether one channel value behaves the same on every router model | Owner (T007 to T009) | EC-3 keeps a value only when every lab router accepts it. |
| U-6 | Which field of a job read names the resolved build | Owner (T006 to T009) | The answer records the field that the owner reads. |
| U-7 | Whether the single-site stable build on access points has run live | Not in this issue | The single-site page stays as it is. |

## Consistency Review

- C-1: The FR-005 wording, the plan change map, and T011 name the same five files. Each file appears with its lines.
- C-2: The task count is 23 in `tasks.md` and in STATUS.json.
- C-3: The remote check count is 120 in `design/research.md`, in STATUS.json, and in the summary. SC-004 in `spec.md` names the same count. T019 keeps it.
- C-4: The issue acceptance criteria map to tasks. Criterion 1 maps to T006 and T010. Criterion 2 maps to T007 to T010. Criterion 3 maps to T011, T016, and T017.
- C-5: T-MERGE follows two rules. The brief allows the merge after remote CI and orchestrator authorization. The issue label needs-human-review requires an owner review first. T-MERGE requires both.
- C-6: The lab steps appear in `tasks.md` as absent owner-only steps. The spec and the plan name the same owner-only steps.
- C-7: Each gated branch names one lab answer (T006 to T009). No branch depends on a second answer.
- C-8: D-12 requires the STE gate on changed Markdown files. T002 names the same command on `design/research.md`.
- C-9: The plan change map names the same lines that the research rows cite (RC-27 to RC-57 and RC-84 to RC-103).
