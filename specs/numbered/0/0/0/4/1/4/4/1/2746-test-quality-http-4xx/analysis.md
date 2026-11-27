# Analysis: HTTP 4xx Test-Quality Findings

## Consistency Review

- Spec and plan: Requirements FR-001 to FR-010 each map to at least one task in `tasks.md`. Each task names one verification command.
- Plan and research: Each row of the change map names a remote or local row in `design/research.md`.
- Tasks and remote code: The 38 class rows match RC-35 to RC-72. Seven comment paths are absent on main (RC-28 to RC-34).
- Counts: Remote checks total 80. The `design/research.md` table has 80 rows. The `remote_checks` array in `2746-STATUS.json` has 80 objects. `2746-summary.md` states 80.
- Classes: Class A has 12 entries. Class B has 24 entries. Class C has 2 entries. The total is 38.
- Report agreement: Classes A and C total 14 entries. The latest comment report lists 14 findings (comment 98, 2026-11-13). That count implies that the 24 class B entries match no finding. Task T002 confirms it.

## Defects in Existing Work

| # | Defect | Evidence | Effect | Remedy |
| - | - | - | - | - |
| 1 | The issue body states 71 findings. | Issue #2746 body. Comment 14 counts 38. Comment 98 counts 14. | The body count is outdated. | Working set uses the 38 baseline entries (D-2). |
| 2 | Seven of 14 named test paths are absent on main. | RC-28 to RC-34. | Comment paths cannot identify entries. | Use the baseline paths (D-2). |
| 3 | Comment 98 says the WLAN radius test has a 503 case only. | RC-53. Main has 4xx status values at lines 284, 334, 721, 749, 803, and 874. | The module has 4xx coverage. The finding is an attribution gap. | Class C (D-5). |
| 4 | Comment 77 names `test_an_http_401_response_falls_back`. | RC-48. No test has that name. The 401 status is in the parametrized list at line 122. | The name claim is wrong. | Class C (D-5). |
| 5 | Comment 14 names `--prune-baseline` as the removal tool. | RC-78 and RC-79. Prune removes absent-file entries only. | Prune cannot clear class B entries. | Exact key removal (D-4). |
| 6 | Comments 76 and 98 name pin `e8e093d205428b5503887267b6a9751fa7354be7`. | RC-13 shows pin `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` at line 197. | The named commit is outdated. | Use RC-13 (D-2). |
| 7 | Comment 81 names installed misthelper-devtools 0.6.3. | RC-80 shows the installed version is 0.6.4 at commit `2239e7bd`. | The version claim is outdated. | Use RC-80 (D-9). |
| 8 | Comment 3 states that the CLI shell status logs at DEBUG only. | RC-25. Line 111 logs at ERROR inside the error-status branch that starts at line 110. | The defect is resolved on main. | No new issue (D-6). |
| 9 | Comment 33 states that the WAN probe config fetch accepts a refused body. | RC-26. Line 532 rejects non-200 status. | The defect is resolved on main. | No new issue (D-6). |
| 10 | Issue #4560 reports rogue DHCP acceptance of HTTP 503 data. | RC-27. Line 147 accepts only 2xx evidence. Issue #4560 is closed. | The defect is resolved on main. | No new issue (D-6). |
| 11 | Merged repairs left 24 class B entries in the baseline. | RC-35 to RC-72 (class B rows). Comment 14 requires removal in the same pull request. | The backlog overstates the work. | Task T004 (D-4). |
| 12 | Automation closed issue #2746 twice. | Comments 22 and 39. | A closing keyword in a partial pull request closes the issue early. | `Part of` in interim pull requests (D-7). |
| 13 | The task message names `missing_fm_http_5xx` for issue #2746. | Issue #2747 title is "Test quality: repair remaining missing_fm_http_5xx findings". Issue #2746 title names 4xx. | The routing message conflicts with the issue. | Scope is 4xx (D-1). The orchestrator must confirm the routing. |

## Classification Table

Class A: no HTTP request or status literal in the test module. Class B: a 4xx test exists on main. Class C: 4xx tests exist but the analyzer cannot attribute them. Row numbers match `design/research.md`.

| # | Path | Class | Line | Basis | Action |
| - | - | - | - | - | - |
| 1 | `mist-ops-platform/tests/unit/api/test_session_security.py` | B | 161 | 401 test. PR 4612 (merged 2026-11-06). | T004 |
| 2 | `mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py` | A | 0 | No HTTP literal. Registry test. | T005 and T006 |
| 3 | `mist-ops-platform/tests/unit/mist/test_registry_validation.py` | A | 0 | No HTTP literal. Registry test. | T005 and T006 |
| 4 | `tests/test_upgrade_portal_mist.py` | B | 117 | 4xx test. PR 4324 (merged 2026-10-20). | T004 |
| 5 | `tests/unit/firmware/test_bulk_ap_running_version.py` | B | 211 | 403 test. PR 4403 (merged 2026-10-23). | T004 |
| 6 | `tests/unit/firmware/test_firmware_manager_config.py` | B | 291 | 403 test. PR 4398 (merged 2026-10-22). | T004 |
| 7 | `tests/unit/gateway/test_device_template_cloner_extended.py` | B | 96 | 403 test. PR 4553 (merged 2026-11-05). | T004 |
| 8 | `tests/unit/gateway/test_wan2_migration_manager.py` | B | 141 | 400 test. PR 4341 (merged 2026-10-20). | T004 |
| 9 | `tests/unit/gateway/test_wan2_migration_manager_extended.py` | B | 1014 | 403 test. PR 4370 (merged 2026-10-20). | T004 |
| 10 | `tests/unit/gateway/test_wan_probe_device_override_manager.py` | B | 151 | 403 test. PR 4383 (merged 2026-10-21). | T004 |
| 11 | `tests/unit/inventory/test_org_device_inventory_summary.py` | B | 292 | 403 test. PR 4402 (merged 2026-10-22). | T004 |
| 12 | `tests/unit/inventory/test_org_device_inventory_summary_wave8.py` | B | 728 | 404 test. PR 4551 (merged 2026-10-31). | T004 |
| 13 | `tests/unit/org/test_org_config_migration_conflicts.py` | B | 507 | 403 test. PR 4390 (merged 2026-10-21). | T004 |
| 14 | `tests/unit/org/test_org_config_migration_workflow.py` | C | 122 | Parametrized 4xx statuses. Fixture-driven. | T005 and T006 |
| 15 | `tests/unit/refactors/test_app_context_session_state.py` | A | 0 | No HTTP literal. Session test. | T005 and T006 |
| 16 | `tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py` | A | 0 | No HTTP literal. Local helper test. | T005 and T006 |
| 17 | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` | A | 0 | No HTTP literal. Entry point test. | T005 and T006 |
| 18 | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py` | A | 0 | No HTTP literal. Argument parsing test. | T005 and T006 |
| 19 | `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | C | 284 | 4xx responses at lines 284, 334, 721, 749, 803, and 874. Helper-driven. | T005 and T006 |
| 20 | `tests/unit/security/rogue_dhcp/test_scanner.py` | B | 249 | Parametrized 403 and 503. PR 4604 (merged 2026-11-09). | T004 |
| 21 | `tests/unit/site/address_audit/test_audit_engine.py` | B | 391 | Parametrized 403 status. No PR in the search. | T004 |
| 22 | `tests/unit/ssh/test_cli_shell_manager.py` | B | 540 | 403 test. PR 4478 (merged 2026-10-26). | T004 |
| 23 | `tests/unit/config/standalone/foundation/support/utilities/network/test_address_utils.py` | B | 1227 | 429 test. PR 4351 (merged 2026-10-20). | T004 |
| 24 | `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils_wave3.py` | A | 0 | No HTTP literal. Configuration test. | T005 and T006 |
| 25 | `tests/unit/test_issue_2971_census_repairs.py` | B | 165 | 403 test. PR 4374 (merged 2026-10-21). | T004 |
| 26 | `tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py` | A | 0 | No HTTP literal. Logging test. | T005 and T006 |
| 27 | `tests/unit/test_prompt_network_device_utils.py` | B | 1068 | 403 test. PR 4368 (merged 2026-10-20). | T004 |
| 28 | `tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py` | B | 966 | Parametrized 403 and 503. PR 4614 (merged 2026-11-06). | T004 |
| 29 | `tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py` | B | 733 | 403 test. PR 4378 (merged 2026-10-21). | T004 |
| 30 | `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` | B | 630 | Parametrized 403 status. PR 4497 (merged 2026-10-30). | T004 |
| 31 | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_device_prompt_rename_guard.py` | A | 1 | Only 4xx-range matches are the issue number 431 in text. | T005 and T006 |
| 32 | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_interactive_display_utils.py` | A | 0 | No HTTP literal. Dispatch test. | T005 and T006 |
| 33 | `tests/unit/ui/test_level_discoverer.py` | A | 0 | No HTTP literal. Module discovery test. | T005 and T006 |
| 34 | `tests/unit/ui/test_prompt_utils.py` | B | 958 | 403 response. PR 4357 (merged 2026-10-20). | T004 |
| 35 | `tests/unit/upgrade_portal/test_upgrade_service_classify.py` | A | 27 | Imports `FirmwareManager` and uses only its classifier. Class-level scope. | T005 and T006 |
| 36 | `tests/unit/utils/test_tls_policy.py` | B | 131 | 403 test. PR 4387 (merged 2026-10-21). | T004 |
| 37 | `tests/unit/web_portal/test_operations_silent_failure.py` | B | 244 | 403 test. PR 4385 (merged 2026-10-21). | T004 |
| 38 | `tests/unit/websocket/test_service_ping_discovery.py` | B | 342 | Parametrized 4xx statuses. PR 4514 (merged 2026-11-05). | T004 |

## Unresolved Items

- The complete report has not run. Task T002 confirms the counts in this table.
- The misthelper-devtools repair is not released. Issue #67 is open.
- The route script `spec-route.ps1` has not run. The route equals the base-5 digits of 2746, as plan.md shows.
- The titles and merge dates of PRs 4604 and 4514 are verified. Their changed files are not read.
