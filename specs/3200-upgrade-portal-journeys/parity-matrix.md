# Parity matrix: single-site and multi-site upgrade journeys

**Feature**: #3200 | **Reviewed**: 2026-10-30 | **Code baseline**: `0b04cda81c8ef75096f3bedae0885038c775d665`

The status baseline comes from the C01-C54 inventory in `spec.md`. This update reflects current `main` and local journey evidence.
The journeys use stand-in cloud data and loopback only. They do not contact Mist cloud or production stores.
The JSON `evidence` entries keep the original P01-P54 references and status as historical data.
The `journeys` entries link current local tests.

Status words: `proven` means the capability is present. `partial` means it is incomplete.
`missing` means the mode has no capability. `defect` means a local contract or strict-xfail journey confirmed a defect.

## Summary

| Mode | Proven | Partial | Missing | Defect |
| - | - | - | - | - |
| Single-site | 53 | 0 | 0 | 1 |
| Multi-site | 48 | 1 | 1 | 4 |
| Full parity | 48 of 54 (88.9%) | | | |

## Capability inventory

| Identifier | Capability | Single-site | Multi-site | Families | Journeys | Verdict | Issue |
| - | - | - | - | - | - | - | - |
| C01 | Select the organization and the mode | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_selection_reaches_the_capture_page`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C02 | Select one site or several sites | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_selection_reaches_the_capture_page`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C03 | Show the inventory with the firmware mismatch mark and the unsupported mark | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_selection_reaches_the_capture_page`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C04 | Select all, one, or more device families | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_selection_reaches_the_capture_page`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C05 | Classify each gateway as Junos or SSR and use the route of its class | `proven` | `proven` | Junos gateway, SSR gateway | `TestSingleSiteJourneys.test_selection_reaches_the_capture_page`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C06 | Keep each Mist Edge device out of the plan | `proven` | `proven` | Mist Edge | `TestSingleSiteJourneys.test_selection_reaches_the_capture_page`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C07 | Hold a site lock, name the holder, release the lock, and take over after the cooldown | `proven` | `defect` | gateway, switch, access point | `test_locks_heartbeat_conflict_and_release`<br>`TestMultiSiteFamilyJourneys.test_running_operation_reads_as_running`<br>`TestMultiSiteFamilyJourneys.test_running_operation_keeps_its_site_locks`<br>`TestMultiSiteSessionJourneys.test_busy_site_refusal_links_to_the_running_job` | `gap` | #4540 |
| C08 | Run the pre-check capture at the standard tier and the extra tier, with a download | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C09 | Refuse the start until a verified pre-check exists | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C10 | Select a version for each device from the available versions | `proven` | `defect` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_checked_switch_with_empty_version_stays_in_the_durable_plan`<br>`test_options_page_pair_has_the_same_main_controls` | `gap` | #3394 |
| C11 | Select the strategy: canary, big bang, RRM, or serial | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C12 | Set the canary phases | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`TestMultiSiteSessionJourneys.test_invalid_phases_follow_through_to_the_start` | `parity` | - |
| C13 | Select the reboot after the write | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C14 | Set the reboot-at interval | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C15 | Select the Junos file action | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`TestMultiSiteOptionsJourneys.test_back_from_confirm_keeps_every_choice` | `parity` | - |
| C16 | Force the write when a device runs the selected version | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C17 | Select the stable version | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C18 | Set the P2P choice, the P2P cluster size, and the P2P parallelism | `proven` | `proven` | access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C19 | Set the RRM node sequence, the slow ramp, the first batch, and the maximum batch | `proven` | `proven` | access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C20 | Select the mesh upgrade | `proven` | `proven` | access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C21 | Select the SSR channel | `proven` | `proven` | SSR gateway | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C22 | Set the maximum failures and the maximum failure percentage | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C23 | Set the start time | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C24 | Show the warning list for mixed gateway classes and for a version that runs now | `proven` | `missing` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `gap` | #3200 |
| C25 | Show the confirmation summary with the scope, the versions, the options, and the call count | `proven` | `defect` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`TestMultiSiteConfirmJourneys.test_confirm_page_names_the_sites_and_the_schedule` | `gap` | #3222 |
| C26 | Type `CONFIRM` before the start | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_options_and_confirm_pages_of_a_prepared_run`<br>`test_options_page_pair_has_the_same_main_controls` | `parity` | - |
| C27 | Show the Mist account label before the write | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C28 | Run the cascade of gateways, switches, access points, and clients with the settle gate | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C29 | Show the status and the version check of each device | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C30 | Refresh the progress page by the automatic poll and by the refresh control | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C31 | Show the age of the last update and the stale-run badge | `proven` | `partial` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `gap` | #3200 |
| C32 | Show the failure alert with the device and the reported cause | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C33 | Show the operator address on the progress page | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C34 | Stop with the typed word `STOP` and show the three outcome lists | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_run_page_of_each_seeded_state`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C35 | Cancel work that did not get to the cloud | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C36 | Retry the failed devices with the saved options | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C37 | Set a new start time for work that did not start | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C38 | Reconcile an uncertain status with a typed confirmation | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C39 | Run the post-check capture with no operator action | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C40 | Compare the pre-check and the post-check, with the statistics and the downloads | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C41 | Show the work on the history page with its status, operator, account, and links | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C42 | Retry, cancel, or clear several runs from the history page | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C43 | Show the audit rows of each action | `proven` | `proven` | gateway, switch, access point, wireless client | `TestSingleSiteJourneys.test_history_and_comparison_pages`<br>`test_progress_page_pair_has_the_same_run_controls` | `parity` | - |
| C44 | Send one write for each planned write or child, and refuse a replay | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C45 | Keep an uncertain write unknown and do not send it again | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C46 | Keep each result visible after a partial submission | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C47 | Check the owner before each control action | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C48 | Check the CSRF token of each browser write | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C49 | Refuse a write from an operator address on a reserved domain | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C50 | Refuse a write after the session expires | `proven` | `proven` | gateway, switch, access point | `TestSingleSiteJourneys.test_start_reaches_a_completed_run`<br>`TestMultiSiteFamilyJourneys.test_family_combination_reaches_a_final_state` | `parity` | - |
| C51 | Show the navigation menu on each page | `proven` | `proven` | gateway, switch, access point | `test_navigation_selection_switching_and_themes`<br>`test_navigation_selection_switching_and_themes` | `parity` | - |
| C52 | Pass the basic accessibility checks on each page | `proven` | `proven` | gateway, switch, access point | `test_sign_in_sign_out_and_signed_out_errors`<br>`test_navigation_selection_switching_and_themes`<br>`test_navigation_selection_switching_and_themes` | `parity` | - |
| C53 | Show each control at a narrow viewport | `defect` | `defect` | gateway, switch, access point | `test_sign_in_page_fits_narrow_viewport`<br>`test_sign_in_page_fits_narrow_viewport` | `gap` | #4539 |
| C54 | Show a plain error page with a way back | `proven` | `proven` | gateway, switch, access point | `test_missing_run_error_page_offers_back_link`<br>`test_unknown_url_error_page_offers_back_link` | `parity` | - |

## Confirmed defects

| Capability | Mode | Issue | Evidence |
| - | - | - | - |
| C07 Hold a site lock, name the holder, release the lock, and take over after the cooldown | multi | #4540 | `test_upj_multisite_journeys.py::test_second_start_on_busy_sites_explains_the_lock`, `test_upj_multisite_journeys.py::test_busy_site_refusal_links_to_the_running_job` |
| C10 Select a version for each device from the available versions | multi | #3394 | `test_org_upgrade_routes.py::test_checked_switch_with_empty_version_stays_in_the_durable_plan`, `test_parity_pages.py::test_options_page_pair_has_the_same_main_controls` |
| C25 Show the confirmation summary with the scope, the versions, the options, and the call count | multi | #3222 | `test_upj_multisite_journeys.py::test_confirm_page_names_the_sites_and_the_schedule` |
| C53 Show each control at a narrow viewport | single | #4539 | `test_crosscut_journeys.py::test_sign_in_page_fits_narrow_viewport` |
| C53 Show each control at a narrow viewport | multi | #4539 | `test_crosscut_journeys.py::test_sign_in_page_fits_narrow_viewport` |

## Method

The inventory matches the feature specification. The local journeys confirm completed runs, fault refusal, and current strict-xfail defects.
The `journeys` field names the closest existing test. It does not claim that every portal capability has a dedicated browser assertion.
The issue column links unresolved gaps to their active tracking issue. Fixed issue references remain in the JSON evidence for traceability.
