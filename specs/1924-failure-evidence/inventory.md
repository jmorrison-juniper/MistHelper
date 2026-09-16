# Failure Evidence Audit Inventory

Issue #1924 inventory generated from the current branch.

## Repair Applied in This Branch

- The dependency manifest check inspected 56 runtime dependency entries.
- `origin/main` had 54 dependency entries with no upper bound.
- This branch adds upper bounds to those entries in `requirements.txt` and `pyproject.toml`.
- The remaining category 5 count below covers code defaults only.

## broad_handler_swallow

- Method: Issue #1794 baseline plus AST sample scan for bare except or except Exception with no log, no raise, and a benign exit.
- Count: 412
- File count: 43

### scripts\analyze_marvis_pcap.py
- Line 144: `except Exception:`
- Line 181: `except Exception:`
- Line 88: `except Exception:`

### scripts\mist_ideas_distiller_v2_pkg\__init__.py
- Line 246: `except Exception:`
- Line 293: `except Exception:`
- Line 314: `except Exception:`

### scripts\mist_ideas_scraper_auth.py
- Line 109: `except Exception:`

### scripts\probe_pk_strategy.py
- Line 573: `except Exception:`
- Line 275: `except Exception:`

### src\bootstrap\package_installer.py
- Line 55: `except Exception as error:  # WHY: broad catch protects import-time bootstrap from any failure mode`
- Line 154: `except Exception as error:  # WHY: broad catch protects import-time bootstrap from any failure mode`

### src\db\arango_writer.py
- Line 4166: `except Exception:  # WHY: preserve original 'swallow all errors' contract for compat`

### src\export\org_admin_exporter.py
- Line 110: `except Exception:  # nosec B110`

### src\export\org_template_exporter.py
- Line 141: `except Exception:  # nosec B110`
- Line 183: `except Exception:  # nosec B110`

### src\firmware\aggregate_upgrade_service.py
- Line 435: `except Exception as fault:  # Preserve a truthful stop reason without a cloud call.`

### src\firmware\bulk_ap_upgrader.py
- Line 688: `except Exception as error:  # WHY: recover from failure`
- Line 2020: `except Exception:  # WHY: recover from failure`

### src\firmware\bulk_switch_upgrader.py
- Line 243: `except Exception as exc:  # pylint: disable=broad-exception-caught`
- Line 664: `except Exception:  # pylint: disable=broad-exception-caught`

### src\firmware\firmware_manager.py
- Line 4036: `except Exception as exception:  # WHY: any error yields graceful notice`

### src\firmware\site_auto_upgrade.py
- Line 1593: `except Exception as error:  # WHY: fetch may raise mistapi errors - treat as failure.`

### src\gateway\overrides\device_data_fetcher.py
- Line 128: `except Exception as exception:  # Legacy contract: do not crash compliance report`

### src\gateway\template_config.py
- Line 230: `except Exception as error:  # pylint: disable=broad-exception-caught # WHY: mistapi raises many types`
- Line 301: `except Exception as error:  # pylint: disable=broad-exception-caught # WHY: filesystem errors vary`
- Line 337: `except Exception as error:  # pylint: disable=broad-exception-caught # WHY: file/JSON errors vary`
- Line 506: `except Exception as error:  # pylint: disable=broad-exception-caught # WHY: file/CSV errors vary`

### src\inventory\csv_comparator.py
- Line 1151: `except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: tolerate Nominatim failure.`

### src\maps\_maps_matplotlib.py
- Line 384: `except Exception:`

### src\maps\_maps_wizard.py
- Line 211: `except Exception as img_err:`
- Line 802: `except Exception as map_err:`
- Line 819: `except Exception as img_err:`

### src\maps\launcher\_viewer_clone.py
- Line 352: `except Exception:  # noqa: BLE001 - preserve original broad-except behavior`

### src\maps\launcher\_viewer_site_switch.py
- Line 549: `except Exception:  # WHY: mirror original bare-except behavior`

### src\network\routing_utils.py
- Line 185: `except Exception as error:  # WHY: log-and-continue on any mistapi error`

### src\refactors\maps_manager_launcher.py
- Line 102: `except Exception as error:  # prompt errors must never crash the menu`

### src\refactors\serial_cc\security_events.py
- Line 135: `except Exception:  # Any filesystem error means we cannot prove freshness. Fall through to refetch.`

### src\refactors\sqlite_database_writer.py
- Line 235: `except Exception as error:  # Handle unexpected errors.`
- Line 338: `except Exception as error:  # Per-row failure.`

### src\site\address_audit\ui_geocoder.py
- Line 498: `except Exception:  # a stale DOM node yields no text.`

### src\ssh\batch\batch_executor.py
- Line 144: `except Exception as run_error:  # top-level fallback mirrors original behavior`

### src\ssh\batch\interactive_batch_executor.py
- Line 287: `except Exception as session_error:  # top-level fallback (verbatim)`
- Line 531: `except Exception as step_error:  # per-step fallback (verbatim)`

### src\ssh\command\command_runner.py
- Line 147: `except Exception as run_error:  # top-level fallback mirrors original behavior`

### src\ssh\runtime\app_runner.py
- Line 85: `except Exception:  # nosec B110 - tracer must never break user flow`

### src\ssh\shell_execution\shell_executor.py
- Line 506: `except Exception:  # nosec B112 - cleanup is best-effort  # WHY: Any error during cleanup ends the drain`

### src\troubleshooting\marvis_troubleshoot_utils.py
- Line 885: `except Exception as endpoint_error:  # logged via helper.`

### src\ui\execution\debug_saver.py
- Line 104: `except Exception:  # nosec B112 — defensive guard against descriptor errors`

### src\upgrade_portal\runtime\pools.py
- Line 378: `except Exception as error:  # WHY: one failed call must not lose the answer of the other calls`

### src\utils\address_utils.py
- Line 946: `except Exception:  # WHY: catch-all so a bad response does not kill validation`
- Line 421: `except Exception:  # nosec B110  # WHY: on any fuzz failure, fall through to SequenceMatcher`

### src\utils\environment_utils.py
- Line 123: `except Exception:  # nosec B110`

### src\utils\logger_utils.py
- Line 148: `except Exception:  # never crash a logging filter`

### src\utils\zscaler_probe.py
- Line 332: `except Exception:  # pragma: no cover - best-effort cleanup`
- Line 393: `except Exception as exc:  # pragma: no cover - defensive`

### starlink_dashboard.py
- Line 126: `except Exception as error:`
- Line 203: `except Exception as error:`
- Line 279: `except Exception as error:`

### tests\integration\test_wan_vpn_builder_live.py
- Line 161: `except Exception:`

### tests\unit\test_bulk_ap_upgrader.py
- Line 2147: `except Exception:`

### tools\ste_linter\analysis\__init__.py
- Line 51: `except Exception as error:  # Any import or load problem means no spaCy backend.`

### web_portal\routes\maps.py
- Line 76: `except Exception:`
- Line 97: `except Exception:`
- Line 117: `except Exception:`
- Line 140: `except Exception:`
- Line 160: `except Exception:`

### web_portal\services\data_browser.py
- Line 154: `except Exception as exc:`
- Line 170: `except Exception as exc:`
- Line 402: `except Exception as exc:`
- Line 535: `except Exception as exc:`
- Line 566: `except Exception:`
- Line 581: `except Exception as exc:`

### MistHelper.py records not edited
- Line 5997: `try:  # Each option runs independently so one failure does not abort remaining tests`
- Line 6051: `try:  # CLI args presence + attribute lookup can both fail. Degrade safely.`
- Line 7059: `try:`
- Line 7300: `try:`
- Line 1352: `try:  # The pip install may fail (no network, restricted env)`
- Line 1394: `try:  # The update may fail. Treat most failures as non-critical`
- Line 1571: `try:  # Per-package failures must not abort the whole batch`
- Line 1618: `try:`
- Line 1758: `try:  # The install may still not satisfy the import in this Python session.`
- Line 2039: `try:  # The function may be an attribute or require a direct import`
- Line 2054: `try:  # The submodule may be an attribute or require a direct import`
- Line 2464: `state.get('msp_privileges', MainEntrypoint.context.msp_privileges)`
- Line 2467: `state.get('selected_msp', MainEntrypoint.context.selected_msp)`
- Line 2470: `state.get('org_id', MainEntrypoint.context.org_id)`
- Line 2521: `Interactive login succeeded`
- Line 2527: `Entering _handle_interactive_login_success()`
- Line 2673: `os.getenv('MIST_HOST', 'api.mist.com')`
- Line 3079: `Detecting auth method flags from successful constructor kwargs`
- Line 6225: `InteractiveTestRunner initialized successfully`
- Line 6302: `os.environ.get('CAPTURE_PORT', '8056')`
- Line 6302: `os.environ.get('CAPTURE_PORT', '8056')`
- Line 6395: `MIB_GENERATOR: Menu 243 started the generator`
- Line 6575: `_initialize_deferred_imports: complete`
- Line 6834: `_setup_runtime_flags: complete`
- Line 6887: `_initialize_dependencies: complete`
- Line 6913: `_establish_mist_session: session established successfully`
- Line 6951: `_establish_mist_session: session established successfully`
- Line 6988: `_configure_runtime_options: complete`
- Line 7003: `TUI_MODE: TUI mode completed successfully`
- Line 7184: `CLI execution complete. Exiting.`
- Line 7185: `EXIT: _run_cli_mode - CLI success`
- Line 7331: `EXIT: _run_interactive_mode - interactive success (direct mode)`
- Line 1544: `Successfully processed %s/%s packages`
- Line 1719: `self.import_name_mappings.get(module_name, module_name)`
- Line 1750: `self.import_name_mappings.get(module_name, module_name)`
- Line 1841: `_record_successful_import: caching '%s' and checking upgrade`
- Line 1843: `Successfully imported %s`
- Line 2015: `Successfully made imported modules available globally`
- Line 2532: `Successfully switched to interactive login session with %s MSP(s)`
- Line 2537: `Successfully switched to interactive login session (no MSP privileges)`
- Line 2984: `SUCCESS: API session initialized with filtered token kwargs=%s`
- Line 6002: `SYSTEMATIC_TEST: Successfully completed menu option %s`
- Line 6199: `SYSTEMATIC_TEST: All %s tested operations completed successfully in %.2fs`
- Line 7000: `TUI_DEBUG: [%s] TUI mode completed successfully - about to exit`
- Line 7306: `Menu option '%s' execution complete.`
- Line 7320: `Container mode: option '%s' completed successfully, returning to menu`
- Line 7327: `Session management option '%s' completed - returning to menu`
- Line 1210: `os.getenv('UPGRADE_CHECK_TIMEOUT', '30')`
- Line 1213: `os.getenv('CSV_FRESHNESS_MINUTES', '15')`
- Line 1215: `os.getenv('UV_UPDATE_CHECK_HOURS', '24')`
- Line 1426: `UV package manager updated successfully via pip`
- Line 1455: `Successfully installed %s with %s`
- Line 1527: `UV version check complete - assuming current version is adequate`
- Line 1621: `Successfully imported tqdm from package`
- Line 1762: `Successfully imported %s after installation`
- Line 6550: `Successfully imported real tqdm in deferred mode: %s`
- Line 833: `data.get('info', {})`
- Line 1360: `UV package manager installed successfully via pip`
- Line 1403: `UV package manager updated successfully`
- Line 1492: `Successfully installed %s with pip`
- Line 2163: `Successfully imported mistapi main module`
- Line 1207: `os.getenv('AUTO_UPGRADE_UV', 'true')`
- Line 1208: `os.getenv('AUTO_UPGRADE_DEPENDENCIES', 'true')`
- Line 1217: `os.getenv('DISABLE_UV_CHECK', 'false')`
- Line 1219: `os.getenv('DISABLE_AUTO_INSTALL', 'false')`
- Line 1631: `kwargs.get('desc', 'Processing')`
- Line 1632: `kwargs.get('unit', 'item')`
- Line 1767: `Optional package %s installation succeeded but import failed - likely needs system restart or different Python session`

## guard_cannot_fail

- Method: tools.guard_proof_audit after test_quality_analyzer generated detector metrics.
- Count: 0
- File count: 0

- Checked guard files: 36
- Checked analyzer rules: 1

## success_report_outruns_work

- Method: AST scan for success-word logging calls. This is a candidate list for manual follow-up.
- Count: 582
- File count: 201

### MistHelper.py
- Line 2521: `Interactive login succeeded`
- Line 2527: `Entering _handle_interactive_login_success()`
- Line 3079: `Detecting auth method flags from successful constructor kwargs`
- Line 6225: `InteractiveTestRunner initialized successfully`
- Line 6395: `MIB_GENERATOR: Menu 243 started the generator`
- Line 6575: `_initialize_deferred_imports: complete`
- Line 6834: `_setup_runtime_flags: complete`
- Line 6887: `_initialize_dependencies: complete`
- Line 6913: `_establish_mist_session: session established successfully`
- Line 6951: `_establish_mist_session: session established successfully`
- Line 6988: `_configure_runtime_options: complete`
- Line 7003: `TUI_MODE: TUI mode completed successfully`
- Line 7184: `CLI execution complete. Exiting.`
- Line 7185: `EXIT: _run_cli_mode - CLI success`
- Line 7331: `EXIT: _run_interactive_mode - interactive success (direct mode)`
- Line 1544: `Successfully processed %s/%s packages`
- Line 1841: `_record_successful_import: caching '%s' and checking upgrade`
- Line 1843: `Successfully imported %s`
- Line 2015: `Successfully made imported modules available globally`
- Line 2532: `Successfully switched to interactive login session with %s MSP(s)`
- Additional records: 19

### mist-ops-platform\src\api\routes\sync.py
- Line 495: `create_policy: policy_id=%s created for org_id=%s`

### mist-ops-platform\src\shared\mist\endpoints.py
- Line 280: `Pagination for %s stopped at the %d page limit. The result is incomplete.`

### mist-ops-platform\src\worker\sync\inventory.py
- Line 81: `Upsert of %d site rows is complete`
- Line 95: `Upsert of %d device rows is complete`

### mist-ops-platform\src\worker\tasks\audit_tasks.py
- Line 237: `Retention cleanup complete: %s`

### mist-ops-platform\src\worker\tasks\sync_tasks.py
- Line 203: `Daily backup complete: %s`

### scripts\bootstrap_worktree.py
- Line 381: `The bootstrap completed for %s`
- Line 183: `Created the virtual environment`
- Line 177: `Deleted the existing environment`

### scripts\generate_api_docs.py
- Line 710: `Created output directories under %s`
- Line 781: `Library scan complete: %d functions found`

### scripts\migrate_sqlite_to_polyglot.py
- Line 167: `Migration complete`
- Line 162: `DRY RUN -- no data written to backends`
- Line 212: `ArangoDB <- %s: %d written, %d failed`
- Line 236: `Redis TS <- %s: %d written, %d failed`

### scripts\mist_ideas_analyzer_pkg\__init__.py
- Line 2981: `Completed in %.1f seconds`
- Line 1537: `Markdown report written: %s`
- Line 1702: `JSON report written: %s`
- Line 1745: `CSV report written: %s`
- Line 1895: `[%s] Model %s pulled successfully`
- Line 2550: `Fleet health monitor started (check every %ds)`

### scripts\mist_ideas_scraper_auth.py
- Line 84: `4. The script will auto-detect login success`
- Line 125: `Login complete. Now run without --login to scrape.`
- Line 93: `Waiting for successful login (detecting idea content)...`

### scripts\probe_pk_strategy.py
- Line 368: `Written to %s — review before pasting into MistHelper.py`

### scripts\run_repository_analyzers.py
- Line 25: `Repository analyzer run completed with exit code %d`

### src\analytics\data_collection_manager.py
- Line 99: `  Loop %d completed successfully`
- Line 196: `Support package written for site %s`

### src\analytics\insight_metrics_utils.py
- Line 58: `! Warning: ConstInsightMetrics.csv was not created during dynamic export`

### src\analytics\site_analytics_configurator.py
- Line 569: `Site analytics configuration complete. %d sites updated.`
- Line 504: `Updated %s: %s`

### src\analytics\site_inventory_health_analyzer.py
- Line 72: `Site inventory health analysis complete.`

### src\analytics\zone_analyzer.py
- Line 82: `analyze completed successfully`
- Line 307: `Site configuration analysis complete. Exported CSV files with timestamp %s`

### src\api\api_data_fetcher.py
- Line 76: `EXIT: APIDataFetcher.execute - success`
- Line 118: `API call successful, retrieved %s raw records`
- Line 281: `Partial data saved: %s records written to %s`
- Line 325: `Despite the error, %s records were successfully saved to %s`
- Line 294: `Emergency save: %s partial records written to %s`

### src\api\api_fetch_utils.py
- Line 267: `! Completed fetching %s gateway device configs.`
- Line 58: `Successfully retrieved %s organization services`

### src\auth\interactive\login_orchestrator.py
- Line 148: `APISession created successfully`
- Line 220: `  + Login successful!`
- Line 221: `Interactive login successful for %s to %s`

### src\cache\cache_utils.py
- Line 164: `Support package written to %s`
- Line 225: `Cache cleared: %d file(s) deleted, %d error(s).`
- Line 251: `Deleted: %s`

### src\capture\_packet_capture_exec.py
- Line 90: `Site capture started: capture_id=%s, format=%s`
- Line 187: `Loop iteration %s: Capture started - ID=%s`
- Line 516: `PCAP save callback completed for %s`
- Line 272: `Capture %s completed (enabled=False)`
- Line 275: `Capture %s completed (duration reached)`

### src\capture\_packet_capture_org.py
- Line 488: `Org capture started: capture_id=%s`

### src\capture\_packet_capture_prompts.py
- Line 285: `Multi-AP capture started: id=%s, aps=%s`

### src\capture\client_pcap_downloader.py
- Line 119: `Menu 197 client PCAP downloader: flow complete`
- Line 311: `
  Complete: %d/%d files written to %s`
- Line 262: `  No completed PCAPs available (all still in progress).`

### src\capture\multi_ap_scan_workflow.py
- Line 294: `Multi-AP capture started: capture_id=%s ap_count=%s`
- Line 296: `Capture metadata export completed for capture_id=%s`
- Line 380: `Multi-AP scan capture function completed`
- Line 244: `%d capture(s) already in progress or recently completed`
- Line 280: `Site capture stream subscription completed for capture_id=%s`

### src\capture\org_pcap_wait_download_workflow.py
- Line 31: `Packet-capture download manager initialized successfully`
- Line 58: `Completed poll_and_download_pcap for org capture_id=%s`
- Line 68: `Completed org PCAP wait/download compatibility alias`

### src\capture\packet_capture.py
- Line 1077: `Multi-AP scan capture function completed`

### src\capture\packet_capture_download.py
- Line 104: `Loop iteration %s: Filtered %s completed PCAP entries`
- Line 127: `Checking %s completed PCAP(s) for pending downloads`
- Line 134: `Pending download scan completed with %s new file(s)`
- Line 301: `PCAP save callback completed for %s`
- Line 124: `No completed PCAPs were available for download`

### src\capture\site_capture_loop.py
- Line 69: `
%s
Loop iteration #%s complete`
- Line 85: `  Completed %s loop iteration(s)`

### src\capture\site_pcap_wait_download_workflow.py
- Line 31: `Packet-capture download manager initialized successfully`
- Line 58: `Completed poll_and_download_pcap for site capture_id=%s`
- Line 70: `Completed site PCAP wait/download compatibility alias`

### src\db\arango_writer.py
- Line 3930: `database_created`
- Line 3956: `graph_updated`
- Line 3990: `import_complete`
- Line 4294: `soft_deleted`
- Line 3943: `graph_created`
- Line 3963: `collection_created`

### src\device\_utility_commands_websocket.py
- Line 214: `-> Streaming started (session: %s...)`

### src\device\ap_profile_migration_manager.py
- Line 190: `Menu #207 DESTRUCTIVE: migrate APs started`
- Line 255: `Backup file written: %s`
- Line 360: `Menu #208 DESTRUCTIVE: revert AP profile migration started`
- Line 1078: `Discovery complete: %d APs bound to source profile`

### src\device\virtual_chassis.py
- Line 1017: `Bulk VC conversion completed: %d successful, %d failed`

### src\export\const_definitions_exporter.py
- Line 92: `Dynamic discovery completed: %s endpoints found`
- Line 771: `Dynamic const export completed: %s discovered, %s processed, %s skipped (fresh), %s updated, %s failed`

### src\export\data_exporter.py
- Line 398: `File I/O: Successfully wrote %s rows to %s`
- Line 399: `EXIT: DataExporter.write_to_csv - success`
- Line 294: `Polyglot write: backend=%s, written=%s, failed=%s`
- Line 442: `File I/O: Successfully wrote CSV header to %s`
- Line 429: `Row %s written: %s`

### src\export\gateway_test_exporter.py
- Line 170: `! Retry %s successful for device %s at site %s`
- Line 302: ` No synthetic test results found. CSV not created.`
- Line 303: `! No synthetic test results found. CSV not created.`

### src\export\license_export_utils.py
- Line 146: `Completed summary write for org %s`
- Line 166: `Completed detail write for org %s`

### src\export\msp_inventory_exporter.py
- Line 69: `Menu #144 complete: %s devices exported from %s orgs across %s MSPs`

### src\export\org_alarm_event_exporter.py
- Line 129: `Device events written to OrgDeviceEvents.csv (%s rows).`
- Line 132: `Menu #21: Device events export completed - %s events`
- Line 80: `Completed org alarms export and wrote results to OrgAlarms.csv.`
- Line 81: `EXIT: OrgAlarmEventExporter.alarms - success`

### src\export\org_device_stats_exporter.py
- Line 317: ` No port statistics collected. CSV not created.`
- Line 319: `! No port statistics collected. CSV not created.`
- Line 228: `! Retry %s successful for site %s (%s records)`

### src\export\org_export_utils.py
- Line 426: `
! Successfully exported %d organization insight metrics to 4 normalized CSV files`
- Line 487: `! Metric retrieval completed: %d successful, %d failed`
- Line 490: `Org insight metrics: %s retrieved successfully, %s failed`
- Line 320: `Successfully retrieved org insight data for metric: %s`
- Line 747: `Completed audit logs export and wrote results to OrgAuditLogs.csv.`
- Line 748: `Menu #22: Audit logs export completed - %s records`
- Line 749: `EXIT: OrgExportUtils.audit_logs - success`
- Line 359: `Successfully retrieved org sites SLE data for %s sites`

### src\export\org_inventory_exporter.py
- Line 92: `Completed organization inventory export and wrote results to OrgInventory.csv.`
- Line 114: `Completed organization devices export and wrote results to OrgDevices.csv.`
- Line 486: `! %s weekly CSV files created in data/CombinedInventory_ByWeek/ folder (%s total devices processed)`
- Line 626: `All device data written to AllDevicesWithSiteInfo.csv (%s records).`
- Line 708: `Gateway data written to GatewaysWithSiteInfo.csv`

### src\export\org_search_exporter.py
- Line 153: `Completed the %s prompts with %d filters`
- Line 139: `Completed the %s prompts with 0 filters`

### src\export\org_site_exporter.py
- Line 60: `Completed site list export and wrote results to %s.`
- Line 112: ` Full site data written to SitesWithLocations.csv`

### src\export\org_template_exporter.py
- Line 37: ` Organization templates export completed`

### src\export\self_account_exporter.py
- Line 152: `! Email address updated - the token was valid`

### src\export\site_anomaly_exporter.py
- Line 345: `Successfully retrieved %s client anomaly data for %s`
- Line 140: `Successfully retrieved %s %s for %s`

### src\export\site_asset_exporter.py
- Line 127: `Completed the %s prompt with value_present=%s`

### src\export\site_client_exporter.py
- Line 121: `Completed delegated wifi_clients export workflow`
- Line 156: `Completed delegated wan_client_events export workflow`
- Line 193: `Completed site_id prompt for getSiteBeacon with value_present=%s`
- Line 207: `Completed beacon_id prompt for getSiteBeacon with value_present=%s`
- Line 275: `getSiteBeacon call succeeded with %d normalized rows`

### src\export\site_device_exporter.py
- Line 69: `Device inventory written to %s (%s rows)`

### src\export\site_export_utils.py
- Line 289: `Site %s export completed - %s records saved to %s.`
- Line 315: `Site %s data written to %s (%s rows).`

### src\export\site_search_exporter.py
- Line 301: `Completed the %s prompt with value_present=%s`

### src\export\wan_client_events_exporter.py
- Line 180: `SiteList.csv cache check/generation completed`
- Line 185: `Site selection prompt completed with site_id=%s`
- Line 282: `No-data placeholder CSV written to %s`
- Line 307: `Completed stamping site identifiers on event rows`
- Line 345: `Multiline escaping completed for %d rows`
- Line 364: `%s write completed successfully`

### src\export\wifi_clients_exporter.py
- Line 102: `SiteList.csv cache check/generation completed`
- Line 107: `Site selection prompt completed with site_id=%s`
- Line 173: `No-data placeholder CSV written to %s`
- Line 300: `Multiline escaping completed for %d rows`
- Line 309: `%s write completed successfully`

### src\firmware\bulk_ap_upgrader.py
- Line 103: `Init complete; sites_override=%s`
- Line 244: `Execution done: success=%d failed=%d`
- Line 1949: `apply_family_version_choice complete family=%s`
- Line 2183: `save_upgrade_tracking complete`
- Line 2219: `write_tracking_file complete file=%s`
- Line 2298: `Upgrade results written to %s`

### src\firmware\bulk_switch_upgrader.py
- Line 1106: `Switch firmware upgrade operation completed: %s`

### src\firmware\firmware_manager.py
- Line 272: `FirmwareManager init complete for org %s`
- Line 376: `Status check completed scope=%s`
- Line 899: `Template mapping load complete count=%d`
- Line 1192: `MSP multi-org upgrade complete result_count=%d`
- Line 1689: `MSP upgrade plan complete stopped=%s results=%d`
- Line 1892: `MSP %supgrade summary: %s completed, %s failed, %s interrupted`
- Line 1979: `Status check dispatch complete`
- Line 2114: `SSR upgrade dispatch complete mode=%s`
- Line 2119: `Menu #100 DESTRUCTIVE: SSR firmware upgrade with mode selection started`
- Line 2183: `SSR mode dispatch complete mode=%s`
- Line 3287: `SSR bulk upgrade prep complete sites=%d`
- Line 3488: `Firmware upgrade status check completed successfully`
- Line 556: `Monitoring mode exiting - all upgrades complete`
- Line 3018: `Successfully initiated SSR firmware upgrade at %s`

### src\firmware\org_ap_upgrader.py
- Line 127: `OrgLevelAPFirmwareUpgrader init complete for org %s`
- Line 208: `OrgLevelAPFirmwareUpgrader workflow started, dry_run=%s`
- Line 212: `OrgLevelAPFirmwareUpgrader.run completed`
- Line 284: `_execute_msp_mode completed for %d orgs`
- Line 307: `MSP multi-org upgrade completed: %s organizations processed`
- Line 309: `MSP phase iterate complete for %d orgs`
- Line 435: `Organization %s: success=%s, failed=%s, devices=%s`
- Line 1782: `Upgrade configuration complete: %s`
- Line 2623: `_execute_upgrades completed with successful=%d failed=%d`
- Line 2652: `Org-level upgrade execution complete: successful=%s, failed=%s, total_devices=%s`
- Line 2799: `Upgrade results written to: %s`

### src\firmware\site_auto_upgrade.py
- Line 878: `Completed MSP apply across %d org(s)`
- Line 1391: `Updated auto-upgrade settings for site %s`
- Line 215: `MSP mode complete for %s: success=%s, sites=%s`

### src\gateway\_wan2_variable_device.py
- Line 358: `
  Device Override Migration Complete!`
- Line 362: `  Successfully Migrated: %s`
- Line 367: `Device override migration: %s successful, %s failed`
- Line 290: `Successfully migrated port overrides for device %s`

### src\gateway\_wan2_variable_reporting.py
- Line 167: `Menu #104 DESTRUCTIVE operation complete (%s mode): %s templates updated, %s failed`
- Line 177: `Device override migration (%s mode): %s successful, %s failed`

### src\gateway\_wan2_variable_template.py
- Line 246: `Successfully updated template %s`

### src\gateway\device_template_cloner.py
- Line 425: `Created gateway template with ID %s`
- Line 452: `CSV export complete for template_id %s`
- Line 454: `
Success: Created gateway template '%s' (ID: %s)`

### src\gateway\gateway_export_utils.py
- Line 395: `! Gateway management IP export completed:`
- Line 404: `Gateway management IP export completed. %d gateways processed, %d with management IPs.`

### src\gateway\gateway_stats_exporter.py
- Line 156: `! Retry %s successful for device %s at site %s`
- Line 296: `! All %s requests completed successfully`
- Line 306: ` No gateway device statistics found. CSV not created.`

### src\gateway\overrides\device_data_fetcher.py
- Line 60: `Merging %d successes + %d failures into cache`

### src\gateway\overrides\override_report_writer.py
- Line 47: `Header-only CSV written to %s`
- Line 49: `! Gateway override report written to %s`
- Line 87: `! Gateway override report written to %s with %d overridden ports from %d gateway devices.`
- Line 128: `! Gateway override report written to %s`

### src\gateway\template_config.py
- Line 85: `Menu #106 DESTRUCTIVE: Apply Gateway Template Configuration started`
- Line 104: `Menu #111 DESTRUCTIVE: Clone Gateway Templates by State/Country operation started`
- Line 475: `Menu #106 complete: %s templates updated, %s failed`
- Line 693: `Menu #111 complete: %s sites assigned, %s failed`
- Line 628: `Created template %s (ID: %s)`

### src\gateway\wan2_migration_manager.py
- Line 83: `WAN2 migration dependencies wired successfully`
- Line 185: `Menu #149: Set WAN2 Interface Site Variable operation started`
- Line 733: `Menu #149 complete: %s/%s sites configured`
- Line 628: `Successfully set wan2_interface variable for site %s`

### src\gateway\wan2_variable.py
- Line 134: `Menu #104 DESTRUCTIVE: Update Gateway Templates WAN2 Variable operation started`

### src\gateway\wan_probe_device_override_manager.py
- Line 163: `Menu #167 DESTRUCTIVE: Configure WAN Probe on Device Port Overrides started`
- Line 600: `Menu #167 DESTRUCTIVE operation complete: %s devices updated`
- Line 561: `Device %s: Updated %s probe config`
- Line 584: `Successfully updated device %s`

### src\inventory\csv_comparator.py
- Line 73: `Address comparison operation completed successfully`

### src\inventory\inventory_summary\pivot_renderer.py
- Line 156: `Pivot export complete: %s`

### src\inventory\org_device_inventory_msp.py
- Line 386: `Combined MSP pivot export complete (%d rows)`
- Line 513: `MSP inventory complete for %d orgs`
- Line 519: `Skipping combined reports: fewer than 2 orgs processed successfully`

### src\inventory\org_device_inventory_summary.py
- Line 84: `Switch physical inventory complete: %d logical devices org=%s`
- Line 119: `Gateway physical inventory complete: %d physical devices org=%s`
- Line 437: `Org device inventory summary for %s completed in %.1f seconds`
- Line 441: `
Summary for %s completed in %.1f seconds`

### src\maps\_maps_clone.py
- Line 388: `Successfully cloned map %s to %s at site %s (zones: %s)`

### src\maps\_maps_wizard.py
- Line 598: `wizard completed for %s: mode=%s errors=%d`

### src\maps\_plotly_viewer.py
- Line 995: `Static HTML map created: %s`

### src\maps\launcher\_viewer_clone.py
- Line 126: `Clone operation started - source: %s, new name: %s`
- Line 286: `Cloned map created: %s`
- Line 384: `Clone complete: %s (ID: %s), image=%s, zones=%s`

### src\maps\launcher\_viewer_drawing.py
- Line 485: `Drawing tool: All walls deleted from map %s`
- Line 567: `Drawing tool: Deleted zone '%s'`

### src\maps\launcher\_viewer_refresh.py
- Line 246: `Live data refresh: Client positions updated at %s - WiFi: %s, Wired: %s`
- Line 277: `Live data refresh: client fetch complete count=%d`
- Line 381: `Live data refresh: Updated WiFi clients trace with %s clients, coords sample: %s`
- Line 390: `Live data refresh: Updated Wired clients trace with %s clients`
- Line 411: `Live data refresh: Updated %s client label annotations`
- Line 586: `Live data refresh: RF coverage updated at %s - %s points`
- Line 758: `Live data refresh: Updated RF coverage heatmap with %s cells`

### src\maps\launcher\_viewer_site_switch.py
- Line 85: `Map scale updated: PPM %s -> %.2f (user calibration: %sm)`
- Line 477: `[SITE-SWITCH] Successfully loaded map %s`

### src\maps\launcher\_viewer_ui.py
- Line 487: `Map origin updated to (%.1f, %.1f)`
- Line 570: `Map '%s' (ID: %s) deleted successfully`
- Line 669: `Zone %s deleted successfully`

### src\maps\launcher\_viewer_url_switch.py
- Line 409: `URL map switch: Successfully switched to map '%s'`

### src\maps\maps_manager.py
- Line 867: `Batch download finished with %d successes`
- Line 1043: `Created map %s for site %s`
- Line 1264: `Updated map %s for site %s`
- Line 1400: `Deleted map %s from site %s`
- Line 1799: `Package %s check completed`
- Line 1850: `Successfully imported matplotlib for fallback mode`
- Line 1869: `Successfully imported plotly modules`

### src\marvis\marvis_utils.py
- Line 106: `Marvis data formatting complete: %d rows for analysis_type='%s'`
- Line 312: `Legacy Marvis fallback complete: %d rows`

### src\network\routing_utils.py
- Line 323: `WebSocket %s completed successfully for %s`
- Line 352: `[DEBUG] WebSocket cleanup completed`

### src\org\org_config_migration_manager.py
- Line 112: `Menu 176: Export complete, saved to %s`
- Line 142: `Menu 177: Import complete, %s objects processed`
- Line 642: `Created %s '%s' with ID %s`

### src\org\org_synthetic_probes_manager.py
- Line 849: `load-time CENR check complete; warned_cenr_hosts=%s`
- Line 911: `EXIT: manage_org_synthetic_probes - success`
- Line 2723: `load-time country_code check complete; warned_unmapped_codes=%s`

### src\org\org_ticket_manager.py
- Line 183: `Ticket created: id=%s, status=%s`
- Line 184: `
  Ticket created successfully!
  ID:      %s
  Subject: %s
  Type:    %s
  Status:  %s`
- Line 191: `Menu 189: Ticket creation complete, id=%s`
- Line 336: `Menu 192: Ticket detail view complete for %s`
- Line 58: `Completed org ticket list export`
- Line 59: `EXIT: OrgTicketManager.list_tickets - success`
- Line 243: `Ticket updated: %s`
- Line 244: `
  Ticket %s updated successfully!`
- Line 247: `Menu 191: Ticket update complete for %s`
- Line 357: `Menu 193: Full ticket detail export complete`

### src\org_data_collector.py
- Line 600: `Org Data Collector: complete -- %s/%s succeeded, %s failed, %sm %ss elapsed`
- Line 619: `
%s
  Org Data Collection Complete
%s
  Total:     %s
  Succeeded: %s
  Failed:    %s
  Skipped:   %s
  Duration:  %sm %ss
%s`

### src\refactors\connection_pool_executor.py
- Line 291: `! Processed %s %s successfully, %s failed`
- Line 297: `[POOL-EXECUTE] Pool execution finished: %s successful, %s failed`

### src\refactors\data_directory_checker.py
- Line 47: `DataDirectoryChecker init complete: test_file=%s`

### src\refactors\device_data_fetcher.py
- Line 82: `Completed device data fetch: %s`

### src\refactors\main_entrypoint.py
- Line 383: `Created the CLI application context: %s`

### src\refactors\maps_manager_launcher.py
- Line 29: `MapsManagerLauncher runtime dependencies resolved successfully`
- Line 54: `MapsManagerLauncher init complete`
- Line 72: `Menu #142: Maps Manager session completed`
- Line 81: `MapsManagerLauncher: MapsManager import succeeded`

### src\refactors\run_interactive_test.py
- Line 33: `RunInteractiveTestManager runtime dependencies resolved successfully`
- Line 63: `RunInteractiveTestManager init complete`
- Line 89: `Completed run_interactive_test with result=%s`

### src\refactors\run_systematic_test.py
- Line 46: `RunSystematicTestManager runtime dependencies resolved successfully`
- Line 71: `RunSystematicTestManager init complete`
- Line 137: `RunSystematicTestManager: sweep executed success=%d error=%d`

### src\refactors\serial_cc\import_initialization_service.py
- Line 60: `Import initialization completed in %.2f seconds`
- Line 61: `Required dependencies: %s/%s successful`
- Line 74: `Import initialization already completed, returning cached results`

### src\refactors\serial_cc\security_events.py
- Line 114: `Security data export completed (3 files generated)`
- Line 115: `Completed security policies, intelligence profiles, and rogue data export aggregate.`
- Line 275: `No rogue devices found across all sites (OrgRogueData.csv written empty).`

### src\refactors\serial_cc\sle_metrics.py
- Line 151: `Successfully retrieved specialized SLE data for metric: %s`
- Line 211: `Successfully aggregated SLE data for %s sites in category: %s`
- Line 291: `! SLE data retrieval completed: %s successful, %s failed`
- Line 294: `Org SLE data: %s retrieved successfully, %s failed`

### src\refactors\serial_cc\test_results_by_site.py
- Line 17: `Runtime dependencies resolved successfully`
- Line 117: `Fast-mode complete: ok_sites=%d fail_sites=%d total=%d records=%d elapsed=%.2fs`
- Line 143: `Sequential fetch complete: %d results across %d sites`
- Line 190: `GatewayTestResultsService export complete`
- Line 150: `No test results found; CSV not created`
- Line 152: `! No gateway test results found. CSV not created.`

### src\refactors\service_ping_launcher.py
- Line 37: `ServicePingLauncher runtime dependencies resolved successfully`
- Line 62: `ServicePingLauncher init complete`
- Line 98: `ServicePingLauncher: runtime dependencies wired successfully`
- Line 108: `ServicePingLauncher: ServicePingManager instantiated successfully`

### src\refactors\sqlite_database_writer.py
- Line 33: `SQLiteDatabaseWriter runtime dependencies resolved successfully`
- Line 76: `SQLiteDatabaseWriter init complete for table %s`
- Line 247: `Successfully connected to database: %s at %s`
- Line 265: `Table %s created/verified with hybrid %s schema - using natural business keys from API`
- Line 390: `Successfully wrote %s/%s rows to table %s in database %s using %s strategy at %s`
- Line 161: `Database directory created: %s at %s`
- Line 178: `Successfully processed data for SQLite compatibility at %s`
- Line 230: `EXIT: SQLiteDatabaseWriter.write - success`
- Line 279: `Created %s performance indexes for table %s with %s strategy`

### src\refactors\switch_to_interactive_login.py
- Line 34: `SwitchToInteractiveLoginManager runtime dependencies resolved successfully`
- Line 65: `SwitchToInteractiveLoginManager init complete`
- Line 101: `SwitchToInteractiveLoginManager: interactive login succeeded; session updated`

### src\refactors\tui_launcher.py
- Line 28: `TUILauncher runtime dependencies resolved successfully`
- Line 52: `TUILauncher init complete`
- Line 106: `>> API session initialized successfully`
- Line 107: `TUI_MODE: apisession initialized successfully`
- Line 173: `TUI_MODE: TUI mode completed successfully`
- Line 171: `TUI_DEBUG: [%s] TUI_MODE function completed - returning to caller`

### src\refactors\wan2_migration_launcher.py
- Line 43: `WAN2MigrationLauncher runtime dependencies resolved successfully`
- Line 69: `WAN2MigrationLauncher init complete`
- Line 108: `WAN2MigrationLauncher: runtime dependencies wired successfully`
- Line 118: `WAN2MigrationLauncher: WAN2MigrationManager instantiated successfully`

### src\refactors\wanprobe_config_manager.py
- Line 134: `Menu #166 DESTRUCTIVE: Configure WAN Probe Override operation started`
- Line 524: `Menu #166 DESTRUCTIVE operation complete: %s templates updated`
- Line 446: `Successfully updated template %s`
- Line 426: `Template %s: Updated %s probe config`

### src\refactors\wlanradius_timer_manager.py
- Line 857: `WLAN authentication timer management completed`
- Line 745: `Successfully updated site WLAN %s`
- Line 791: `Successfully updated site template WLAN %s in template %s`
- Line 845: `Successfully updated org WLAN %s`

### src\reports\e911_bssid.py
- Line 1047: `E911 BSSID report completed in %.1f seconds`
- Line 331: `Checkpoint saved: %d sites completed`

### src\reports\global_wired_client_report_generator.py
- Line 290: `Local report artifact written to %s`

### src\reports\offline_device_reporter.py
- Line 283: `Offline device report completed in %.1f seconds`

### src\reports\sfp_transceiver_data_processor.py
- Line 171: `EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - success`

### src\security\credential_redaction.py
- Line 140: `Redaction complete for %s record(s)`

### src\site\address_audit\address_corrector.py
- Line 145: `
Write-back complete: %d pushed, %d skipped, %d failed.`

### src\site\address_audit\audit_reporter.py
- Line 51: `Address-audit report written to %s`
- Line 80: `Address-correction report written to %s`

### src\site\address_audit\ui_geocoder.py
- Line 207: `CDP attach succeeded; %d context(s) present`
- Line 306: `UI autocomplete returned %d fresh suggestion(s)`
- Line 685: `Debuggable Edge started (pid=%s)`
- Line 266: `geocode_via_ui called before a successful connect(); returning None`

### src\site\bulk_radius_wlan_config_manager.py
- Line 384: `%s: %s success, %s failed`
- Line 635: `Bulk RADIUS WLAN Configuration completed successfully`
- Line 489: `Scan snapshot written to data/%s (%s rows)`

### src\site\site_config_manager.py
- Line 74: `Menu #171 DESTRUCTIVE: Create test sites from CSV operation started`
- Line 88: `Menu #171 complete: %s sites created, %s failed`
- Line 250: `Menu #172 DESTRUCTIVE: Create country RF templates operation started`
- Line 316: `Menu #172 complete: %s templates created, %s sites assigned, %s failed`
- Line 664: `Menu #173 DESTRUCTIVE: Create AP model device profiles operation started`
- Line 681: `Menu #173 complete: %s profiles created, %s failed`
- Line 880: `Menu #174 DESTRUCTIVE: Assign APs to device profiles operation started`
- Line 904: `Menu #174 complete: %s APs assigned, %s failed`

### src\ssh\batch\batch_executor.py
- Line 150: `[%s] SSH multi-command session completed`
- Line 332: `[%s] Command %d/%d completed: %s`
- Line 372: `[%s] All %d commands completed successfully`

### src\ssh\batch\interactive_batch_executor.py
- Line 295: `[%s] SSH interactive session completed`
- Line 587: `[%s] Step %d completed successfully`
- Line 731: `[%s] All %d interactive steps completed successfully`

### src\ssh\batch\multi_host_runner.py
- Line 330: `Successful: %d [OK]`
- Line 341: `Multi-host execution completed: %d/%d successful`
- Line 276: `[%s] Completed successfully: %s`
- Line 337: `
[OK] Successful hosts: %s`

### src\ssh\cli_shell_manager.py
- Line 187: `CLI shell receive thread started (alive=%s)`

### src\ssh\command\command_runner.py
- Line 254: `SingleCommandRunner: _execute_command returned success=%s stdout_len=%d stderr_len=%d`
- Line 152: `[%s] SSH single command session completed`
- Line 302: `[%s] Command completed successfully`

### src\ssh\connection\connector.py
- Line 108: `SshConnector.connect succeeded for %s:%s`
- Line 175: `SSH client created with TOFU enrollment and strict host key verification`
- Line 343: `Successfully connected to %s in %.2f seconds`
- Line 345: `[OK] Successfully connected to %s`

### src\ssh\shell_execution\shell_executor.py
- Line 195: `[STATUS] [%s] Command completed in %.2f seconds`
- Line 196: `ShellExecutor: command completed on %s in %.2fs`
- Line 439: `[OK] [%s] Data drain completed in %.1fs (%d chunks discarded)`
- Line 589: `Shell command completed in %.2f seconds`

### src\ssh\ssh_runner.py
- Line 415: `- [%s] Command completed with exit status: %s`
- Line 430: `Command completed%s in %.2f seconds with exit status: %s`

### src\ssh\ssh_runner_manager.py
- Line 569: `
! SSH execution completed:`
- Line 571: `  - Successful: %s`
- Line 573: `SSH by template: %s, %s/%s successful`
- Line 64: `Interactive SSH runner finished (success=%s)`

### src\ssid_consolidation\_ssid_template_cache.py
- Line 64: `Phase %d already completed (%d/%d). Re-running will overwrite.`
- Line 84: `Phase %d partially completed (%d/%d).`

### src\ssid_consolidation\_ssid_template_phase1.py
- Line 585: `Phase 1 complete: %d sites, %d eligible, %d deviations`

### src\ssid_consolidation\ssid_template_consolidation.py
- Line 649: `Updated group '%s' with %d new sites`
- Line 782: `Created template '%s' (id=%s)`
- Line 435: `All 5 phases completed successfully.`
- Line 514: `Site vars written for %s (%d vars)`
- Line 570: `Created group '%s' (id=%s)`
- Line 575: `Created group: %s`

### src\troubleshooting\interactive_test_runner.py
- Line 245: ` Starting interactive test of MistHelper menu options...
  Note: This tests read-only operations requiring site/device/client selection
! Te`
- Line 419: `   [SUCCESS] Option %s completed successfully`
- Line 423: `INTERACTIVE_TEST: Successfully completed menu option %s`
- Line 540: `Telemetry summary event emitted successfully`
- Line 543: `Telemetry emitter closed successfully`
- Line 546: `Telemetry retention policy enforcement completed`
- Line 557: `
%s
 Interactive Test Summary:
   Successful operations: %d
   Failed operations: %d
   Skipped operations: %d
   Total interactive read-onl`
- Line 580: `   All tested interactive operations completed successfully!`
- Line 581: `INTERACTIVE_TEST: All %s tested operations completed successfully in %.2fs`

### src\troubleshooting\marvis_troubleshoot_utils.py
- Line 278: ` Marvis AI analysis completed!
! Analysis results available.`
- Line 313: ` Marvis AI device analysis completed!`
- Line 341: ` Marvis AI network analysis completed!`

### src\ui\execution\function_executor.py
- Line 146: `TUI: %s completed`
- Line 145: `TUI: Execution complete - no grid display (data type: %s)`

### src\ui\execution\output_formatter.py
- Line 40: `TUI: result formatting complete for %s`

### src\ui\interactive_display_utils.py
- Line 64: `Completed device_stats execution.`
- Line 79: `Completed device_tests execution.`
- Line 93: `Completed device_config execution.`

### src\ui\layout\layout_builder.py
- Line 46: `TUI: layout build complete`

### src\ui\prompt_utils.py
- Line 96: `Device inventory for site_id written to %s`

### src\ui\runtime\level_discoverer.py
- Line 37: `TUI: discovery complete - %d items at %s`

### src\upgrade_portal\api\mist_client.py
- Line 86: `mist_list_sites_success`
- Line 147: `mist_list_devices_success`

### src\upgrade_portal\app\routes\audit.py
- Line 78: `audit_query_success`
- Line 135: `audit_operations_success`

### src\upgrade_portal\app\routes\capture.py
- Line 1189: `capture: started the capture %s of the site %s at tier %s`
- Line 1150: `capture: pre-upgrade capture for run %s completed with result`

### src\upgrade_portal\app\routes\comparison.py
- Line 125: `get_comparison_results_success`
- Line 314: `approve_comparison_success`

### src\upgrade_portal\app\routes\jwt_auth.py
- Line 108: `auth_login_success`
- Line 213: `auth_continue_success`

### src\upgrade_portal\app\routes\mist.py
- Line 64: `get_sites_success`
- Line 122: `get_site_devices_success`

### src\upgrade_portal\app\routes\runs.py
- Line 64: `get_run_success`
- Line 135: `update_run_success`
- Line 270: `create_run_success`

### src\upgrade_portal\app\routes\upgrade.py
- Line 1921: `upgrade: the run page render is complete`
- Line 2487: `upgrade: build a retry of the unsuccessful run %s`
- Line 2492: `upgrade: the retry %s came from the unsuccessful run %s`
- Line 2070: `upgrade: upgrade started for run %s with status %s`
- Line 2161: `upgrade: cancel completed for run %s with result`
- Line 1706: `upgrade: the run %s already started, so this call sent nothing`

### src\upgrade_portal\app\wiring.py
- Line 296: `wiring: the compare and replace of run %s succeeded`
- Line 1505: `wiring: install the complete E2E dependency set`
- Line 1590: `wiring: the capture store is absent, so the portal created no collection`

### src\upgrade_portal\audit\logger.py
- Line 276: `audit_query_complete`

### src\upgrade_portal\auth\session.py
- Line 95: `jwt_token_created`

### src\upgrade_portal\capture\service.py
- Line 490: `device_capture_fetch_complete`
- Line 119: `capture_fetch_complete`
- Line 147: `capture_pre_upgrade_success`
- Line 349: `capture_fetch_complete`
- Line 377: `capture_post_upgrade_success`
- Line 462: `device_capture_fetch_success`

### src\upgrade_portal\capture\store.py
- Line 625: `Upgrade portal created collection %s, edge=%s`

### src\upgrade_portal\compare\service.py
- Line 892: `inventory_delta_analysis_complete`
- Line 1110: `firmware_delta_analysis_complete`
- Line 1145: `radio_config_delta_analysis_complete`
- Line 1180: `policy_delta_analysis_complete`
- Line 1215: `neighbor_delta_analysis_complete`
- Line 229: `comparison_complete`
- Line 799: `delta_analysis_complete`

### src\upgrade_portal\persistence\actions\repository.py
- Line 114: `Created the upgrade action collection with three indexes`

### src\upgrade_portal\persistence\runs.py
- Line 129: `create_upgrade_run_success`
- Line 173: `get_upgrade_run_success`
- Line 229: `update_upgrade_run_success`

### src\upgrade_portal\runtime\containers.py
- Line 177: `containers: the container %s started`

### src\upgrade_portal\runtime\dependencies.py
- Line 270: `preflight: the portal started %s and %s now answers`

### src\upgrade_portal\runtime\lock.py
- Line 1480: `lock: the lock of run %s had already expired, so the release deleted nothing`

### src\upgrade_portal\runtime\pools.py
- Line 255: `[CAPTURE-POOL] Finished: %s successful, %s failed`

### src\upgrade_portal\runtime\runs.py
- Line 791: `run status: the created run holds a pre-check capture`

### src\upgrade_portal\settle\service.py
- Line 419: `settle_device_checks_complete`
- Line 194: `settle_gate_complete`

### src\upgrade_portal\upgrade\service.py
- Line 644: `upgrade_cancel_success`

### src\utils\file_path_utils.py
- Line 62: `Created template file: %s`

### src\utils\input_utils.py
- Line 94: `Completed the MSP prompt with value_present=%s`

### src\utils\rate_limiting.py
- Line 154: `File I/O: Successfully loaded PID tuning data from %s`
- Line 256: `File I/O: Successfully updated delay metrics in %s`
- Line 620: `AdaptivePacer created (enabled=%s, cache_present=%s)`
- Line 165: `File I/O: Successfully wrote PID tuning data to %s`

### src\utils\subprocess_runner.py
- Line 113: `SubprocessRunner completed %s rc=%s`

### src\utils\zscaler_catalogue.py
- Line 1328: `zscaler_catalogue: observation merge complete (cenr=%d, zcc=%d stamped)`

### src\wan_hub_group_manager.py
- Line 470: `  Updated %d paths for '%s' to pod %d.`
- Line 542: `  Warning: Paths for %s have mixed pod values (%s). All will be updated to the new value.`
- Line 488: `Updated %d paths in VPN '%s' to pod %d`

### src\wan_vpn_builder.py
- Line 162: `  VPN '%s' created successfully. ID: %s`
- Line 165: `VPN '%s' created with ID %s`
- Line 730: `  Profile updates: %d succeeded, %d failed.`
- Line 361: `VPN created via API: %s`
- Line 656: `Updated profile '%s' with vpn_paths for VPN '%s'`

### src\websocket\commands.py
- Line 223: `WebSocket show MAC table completed successfully`

### src\websocket\diagnostics\arp_executor.py
- Line 223: `WebSocket connect+subscribe succeeded for ARP`
- Line 283: `ARP wait completed; has_result=%s`
- Line 337: `WebSocket ARP completed successfully for %s`

### src\websocket\diagnostics\common.py
- Line 45: `%s POST completed with status=%s`

### src\websocket\diagnostics\ping_executor.py
- Line 181: `WebSocket connect+subscribe succeeded for ping`
- Line 270: `Ping wait completed; has_result=%s`
- Line 307: `WebSocket ping completed successfully for %s`

### src\websocket\manager.py
- Line 209: `WebSocket connection established successfully`
- Line 69: `[DEBUG] WebSocket cleanup completed`

### src\websocket\polling\message_router.py
- Line 158: `Successfully parsed JSON message: %s`
- Line 100: `Routing complete`

### src\websocket\polling\result_collector.py
- Line 282: `No new data for %ss, assuming command complete`

### src\websocket\polling\result_combiner.py
- Line 42: `Command completed with %s message segments`
- Line 89: `[DEBUG] Session %s result collection complete`

### src\websocket\service_ping_manager.py
- Line 371: `Service ping completed for device %s - Service: %s, Host: %s`
- Line 157: `Device lookup complete for %s, found=%s`
- Line 363: `Service ping completed for %s (%s) - Service: %s, Host: %s`

### starlink_dashboard.py
- Line 1750: `Starlink Dashboard started`
- Line 1210: `Successfully connected to Starlink terminal`

### tests\contract\test_pytest_coverage_gate.py
- Line 47: `Created the coverage workflow reader`

### tests\e2e\upgrade_portal\conftest.py
- Line 1715: `Built the complete E2E factory override set`
- Line 423: `The portal owner record was not written. Cause: %s`

### tests\e2e\upgrade_portal\test_capture.py
- Line 693: `The site release did not complete, so a later test may meet the lease. Cause: %s`

### tests\integration\upgrade_portal\run_controls\__init__.py
- Line 150: `Created one controlled action store collection`
- Line 164: `Started one controlled action store transaction`

### tests\support\upgrade_portal_e2e\__init__.py
- Line 94: `Build the complete E2E factory override set`
- Line 111: `Built the complete E2E factory override set`

### tests\test_performance_memory.py
- Line 24: `Created sink capacity=%s`
- Line 39: `Created sink max_bytes=%s`
- Line 54: `Created sink capacity=%s`
- Line 69: `Created sink with byte and entry limits`

### tests\unit\bootstrap\test_package_installer_wave9.py
- Line 58: `PackageInstaller built successfully`

### tests\unit\org\test_country_region_coverage.py
- Line 85: `test_iso_cover_2_complete: checking (M | G) >= I`
- Line 88: `test_iso_cover_2_complete: classified=%d missing=%s`

### tests\unit\scripts\test_browser_driver_bootstrap.py
- Line 125: `Checking the success line of the report`

### tests\unit\upgrade_portal\test_e2e_portal_owner.py
- Line 58: `Checking that a started portal writes its identifier`
- Line 98: `Checking the read of a written record`

### tools\compliance_analyzer\engine.py
- Line 56: `Created compliance analyzer in worker process`

### tools\performance_memory.py
- Line 195: `Completed %s memory measurements`

### tools\refactor_analyzer\analysis.py
- Line 102: `Analysis complete: %d candidates, %d LOC saveable`

### tools\test_quality_analyzer\__main__.py
- Line 353: `Analyzer run completed successfully`
- Line 670: `Output artifacts written: %s + %s`

### web_portal\app.py
- Line 161: `Event bus started for SSE streaming`
- Line 271: `Web portal shutdown complete`

### web_portal\routes\dashboard.py
- Line 105: `Readiness probe completed %d checks`
- Line 145: `Readiness probe completed %s check with ok=%s`

### web_portal\routes\webhooks.py
- Line 117: `Dispatch complete for topic '%s'`

### web_portal\services\event_bus.py
- Line 83: `Event bus heartbeat thread started`

### web_portal\services\operation.py
- Line 456: `Stop signal sent for run %s (stop_loop.txt created)`

## retry_fallback_hides_first_failure

- Method: AST scan for try blocks with retry or fallback language and no original-error wording.
- Count: 835
- File count: 270

### MistHelper.py
- Line 5997: `try:  # Each option runs independently so one failure does not abort remaining tests`
- Line 6051: `try:  # CLI args presence + attribute lookup can both fail. Degrade safely.`
- Line 7059: `try:`
- Line 7300: `try:`
- Line 1352: `try:  # The pip install may fail (no network, restricted env)`
- Line 1394: `try:  # The update may fail. Treat most failures as non-critical`
- Line 1571: `try:  # Per-package failures must not abort the whole batch`
- Line 1618: `try:`
- Line 1758: `try:  # The install may still not satisfy the import in this Python session.`
- Line 2039: `try:  # The function may be an attribute or require a direct import`
- Line 2054: `try:  # The submodule may be an attribute or require a direct import`

### mist-ops-platform\src\api\deps.py
- Line 35: `try:`

### mist-ops-platform\src\api\middleware\auth.py
- Line 211: `try:`

### mist-ops-platform\src\api\routes\health.py
- Line 45: `try:`
- Line 290: `try:`

### mist-ops-platform\src\shared\db.py
- Line 56: `try:`

### mist-ops-platform\src\shared\mist\endpoints.py
- Line 249: `try:`
- Line 269: `try:`

### mist-ops-platform\src\shared\mist\session.py
- Line 96: `try:`
- Line 137: `try:`
- Line 159: `try:`

### mist-ops-platform\src\shared\services\notification.py
- Line 88: `try:`
- Line 141: `try:`

### mist-ops-platform\src\worker\checks\post_checks.py
- Line 73: `try:`

### mist-ops-platform\src\worker\checks\pre_checks.py
- Line 111: `try:`
- Line 179: `try:`

### mist-ops-platform\src\worker\sync\inventory.py
- Line 60: `try:`

### mist-ops-platform\src\worker\tasks\sync_tasks.py
- Line 116: `try:`
- Line 127: `try:`
- Line 140: `try:`
- Line 152: `try:`
- Line 164: `try:`
- Line 217: `try:`

### scripts\analyze_marvis_pcap.py
- Line 177: `try:  # Preserve the old non-fatal ICMP layer check.`
- Line 83: `try:  # Keep the summary best-effort for malformed records.`

### scripts\cleanup_merged_worktrees.py
- Line 44: `try:`
- Line 67: `try:`

### scripts\cleanup_stale_worktree_admin_dirs.py
- Line 27: `try:`
- Line 41: `try:`

### scripts\generate_api_docs.py
- Line 449: `try:`

### scripts\mist_ideas_analyzer_pkg\__init__.py
- Line 1247: `try:`
- Line 2517: `try:  # Keep per-server exceptions isolated so one bad host does not stop the fleet.`
- Line 2672: `try:`
- Line 560: `try:`
- Line 2866: `try:`

### scripts\mist_ideas_distiller_v2_pkg\__init__.py
- Line 241: `try:`
- Line 281: `try:`
- Line 301: `try:`
- Line 398: `try:`

### scripts\mist_ideas_scraper_auth.py
- Line 299: `try:`
- Line 99: `try:`
- Line 255: `try:`

### scripts\mist_ideas_scraper_ssr.py
- Line 225: `try:`

### scripts\mist_ideas_scraper_standalone.py
- Line 201: `try:`
- Line 207: `try:`
- Line 177: `try:`

### scripts\mist_scraper_receiver.py
- Line 191: `try:`
- Line 204: `try:`

### scripts\probe_pk_strategy.py
- Line 389: `try:`
- Line 254: `try:`
- Line 568: `try:`

### src\analytics\data_collection_manager.py
- Line 53: `try:`
- Line 92: `try:`

### src\analytics\insight_metrics_utils.py
- Line 88: `try:`
- Line 130: `try:`

### src\analytics\site_analytics_configurator.py
- Line 149: `try:`
- Line 522: `try:`

### src\analytics\zone_analyzer.py
- Line 456: `try:  # WHY: isolate per-site failures so one bad site does not abort the loop`
- Line 504: `try:  # WHY: isolate per-site failures so one bad site does not abort the loop`

### src\api\api_data_fetcher.py
- Line 67: `try:`
- Line 115: `try:`
- Line 318: `try:`
- Line 289: `try:`

### src\api\api_fetch_utils.py
- Line 48: `try:`
- Line 97: `try:`
- Line 129: `try:  # The inventory fetch is the one hard dependency. Isolate its failure.`
- Line 139: `try:  # The site-name CSV is optional enrichment. Missing file is non-fatal.`
- Line 168: `try:  # Isolate per-device failures so one bad device does not abort the batch.`

### src\api\tenant_fetch.py
- Line 268: `try:`
- Line 284: `try:`
- Line 300: `try:`
- Line 316: `try:`

### src\audit\audit_analysis_ops.py
- Line 44: `try:`

### src\auth\interactive\credential_prompter.py
- Line 35: `try:`

### src\auth\interactive\login_orchestrator.py
- Line 52: `try:`
- Line 85: `try:`
- Line 229: `try:`

### src\auth\interactive\msp_org_selector.py
- Line 107: `try:`

### src\cache\cache_utils.py
- Line 97: `try:  # The generator may raise. Never let that crash the caller`

### src\capture\_packet_capture_exec.py
- Line 63: `try:  # WHY: broad guard so unexpected failures do not crash the CLI`
- Line 158: `try:  # WHY: catch API/network faults so the loop keeps running`
- Line 195: `try:  # WHY: any loop-level failure should not crash the CLI`
- Line 341: `try:  # WHY: isolate per-iteration errors`
- Line 352: `try:  # WHY: broad guard so stream errors surface cleanly`
- Line 490: `try:  # WHY: broad guard so keyboard interrupt shows a friendly message`

### src\capture\_packet_capture_org.py
- Line 79: `try:  # WHY: swallow SDK errors and surface as None sentinel`
- Line 100: `try:  # WHY: stats are advisory. Failures must not block capture`
- Line 305: `try:  # WHY: SDK may raise on transport errors`
- Line 466: `try:  # WHY: broad guard preserves legacy user-friendly error handling`
- Line 521: `try:  # WHY: swallow exporter errors so capture path continues`

### src\capture\_packet_capture_prompts.py
- Line 216: `try:  # WHY: wrap network call so upstream flow tolerates SDK errors`

### src\capture\client_pcap_downloader.py
- Line 149: `try:  # WHY: network/SDK errors must not crash the menu dispatcher.`
- Line 227: `try:  # WHY: network/SDK errors must not crash the menu dispatcher.`
- Line 326: `try:  # WHY: transfer + write must not crash the batch.`

### src\capture\multi_ap_scan_workflow.py
- Line 233: `try:`
- Line 323: `try:`

### src\capture\packet_capture.py
- Line 1023: `try:  # WHY: mistapi call may raise transient network/auth errors`
- Line 1305: `try:`

### src\capture\packet_capture_download.py
- Line 77: `try:  # WHY: Catch API/listing failures so loop mode can continue safely.`
- Line 195: `try:  # WHY: Catch transfer and file-write failures so caller can continue safely.`
- Line 265: `try:  # WHY: Catch cancellation and other errors without changing user-visible behavior.`
- Line 350: `try:  # WHY: Catch transient poll failures and continue retrying within same wait budget.`

### src\config\config_utils.py
- Line 61: `try:  # The module can run in tests before MistHelper finishes importing.`

### src\db\database_schema_utils.py
- Line 42: `try:`

### src\db\retention.py
- Line 215: `try:`
- Line 108: `try:`
- Line 136: `try:`
- Line 174: `try:`

### src\db\router.py
- Line 135: `try:`
- Line 147: `try:`
- Line 159: `try:`
- Line 315: `try:`
- Line 331: `try:`
- Line 444: `try:`

### src\device\_utility_commands_action.py
- Line 77: `try:`
- Line 101: `try:`
- Line 191: `try:`
- Line 223: `try:`
- Line 239: `try:`
- Line 265: `try:`
- Line 360: `try:`
- Line 434: `try:`
- Line 462: `try:`
- Line 485: `try:`

### src\device\_utility_commands_clear.py
- Line 73: `try:`
- Line 160: `try:`
- Line 207: `try:  # WHY: guard SDK/transport failures`
- Line 303: `try:  # WHY: guard SDK call so transport errors do not crash the wizard`
- Line 339: `try:`
- Line 386: `try:`
- Line 428: `try:`
- Line 493: `try:`
- Line 553: `try:`

### src\device\_utility_commands_selection.py
- Line 114: `try:  # WHY: mistapi may raise on network/auth failures`
- Line 147: `try:  # WHY: mistapi may raise on network/auth failures`
- Line 487: `try:  # WHY: mistapi may raise on network/auth failures`

### src\device\_utility_commands_websocket.py
- Line 110: `try:  # WHY: any SDK/WS error must fall through to disconnect`
- Line 194: `try:`

### src\device\ap_profile_migration_manager.py
- Line 624: `try:`
- Line 861: `try:`
- Line 953: `try:`
- Line 1047: `try:`
- Line 1785: `try:`
- Line 1058: `try:`
- Line 1265: `try:`
- Line 1880: `try:`

### src\device\arp_command_manager.py
- Line 200: `try:`
- Line 294: `try:`

### src\device\device_reboot_manager.py
- Line 130: `try:`
- Line 163: `try:`
- Line 226: `try:`
- Line 266: `try:`
- Line 360: `try:`
- Line 417: `try:`
- Line 107: `try:`

### src\device\device_utils.py
- Line 36: `try:`

### src\device\prompt_utils.py
- Line 186: `try:`
- Line 280: `try:`
- Line 398: `try:`
- Line 449: `try:`
- Line 494: `try:`

### src\device\utility_commands.py
- Line 191: `try:`

### src\device\virtual_chassis.py
- Line 433: `try:`
- Line 474: `try:`
- Line 581: `try:`
- Line 677: `try:`
- Line 689: `try:`
- Line 706: `try:`
- Line 729: `try:`
- Line 749: `try:`

### src\export\const_definitions_exporter.py
- Line 61: `try:`
- Line 102: `try:`
- Line 265: `try:`
- Line 303: `try:`
- Line 317: `try:`
- Line 346: `try:`
- Line 377: `try:`
- Line 476: `try:`
- Line 620: `try:`
- Line 365: `try:`
- Line 458: `try:`
- Line 591: `try:`

### src\export\count_exporter.py
- Line 228: `try:`

### src\export\data_exporter.py
- Line 26: `try:  # pragma: no cover - import guard mirrors MistHelper`
- Line 134: `try:`
- Line 452: `try:  # Wrap the write to translate I/O failures into the legacy diagnostic surface`

### src\export\device_events_52w_exporter.py
- Line 141: `try:`
- Line 301: `try:`
- Line 309: `try:`
- Line 228: `try:`

### src\export\endpoint_family_exporter.py
- Line 564: `try:`

### src\export\gateway_test_exporter.py
- Line 145: `try:`
- Line 266: `try:`

### src\export\msp_inventory_exporter.py
- Line 232: `try:`
- Line 314: `try:`
- Line 332: `try:`

### src\export\msp_license_exporter.py
- Line 177: `try:`

### src\export\org_admin_exporter.py
- Line 94: `try:`
- Line 106: `try:`

### src\export\org_alarm_event_exporter.py
- Line 71: `try:`

### src\export\org_client_security_exporter.py
- Line 123: `try:`
- Line 146: `try:`
- Line 161: `try:`

### src\export\org_config_exporter.py
- Line 144: `try:`

### src\export\org_cradlepoint_connection_exporter.py
- Line 132: `try:`

### src\export\org_device_stats_exporter.py
- Line 56: `try:`
- Line 106: `try:  # Filesystem metadata lookup should never crash export path`
- Line 155: `try:  # Prefer cached site CSV to avoid extra API call`
- Line 246: `try:`
- Line 431: `try:`

### src\export\org_export_utils.py
- Line 74: `try:`
- Line 193: `try:  # The constants call may fail offline -> degrade to no expansion`
- Line 218: `try:  # Per-choice failures must not abort the whole export`
- Line 281: `try:  # Isolate this category so one failure does not abort the others.`
- Line 330: `try:  # Any metric-level failure is caught here so the overall loop continues.`
- Line 509: `try:  # Guard the whole fetch-and-export so a failure still leaves consistent empty outputs.`
- Line 732: `try:`

### src\export\org_inventory_exporter.py
- Line 311: `try:  # One bad device row must not derail the full export`
- Line 515: `try:  # Cached CSV is preferred. Fall back to the API if it is missing or unreadable.`
- Line 531: `try:  # Cached CSV is preferred. Fall back to the API if it is missing or unreadable.`
- Line 714: `try:`

### src\export\org_inventory_search_exporter.py
- Line 77: `try:`

### src\export\org_search_exporter.py
- Line 215: `try:`

### src\export\org_sec_intel_profile_exporter.py
- Line 198: `try:`

### src\export\org_template_exporter.py
- Line 68: `try:`
- Line 129: `try:`
- Line 175: `try:`
- Line 137: `try:`
- Line 181: `try:`

### src\export\org_webhook_deliveries_exporter.py
- Line 87: `try:`

### src\export\self_account_exporter.py
- Line 145: `try:`

### src\export\self_export_utils.py
- Line 54: `try:`

### src\export\simple_endpoint_exporter.py
- Line 284: `try:`

### src\export\site_anomaly_exporter.py
- Line 59: `try:`
- Line 88: `try:`
- Line 130: `try:`
- Line 244: `try:`
- Line 281: `try:  # Hostname enrichment is best-effort. The MAC is an acceptable fallback.`
- Line 367: `try:  # Isolate per-metric failures so one bad metric does not abort the rest.`

### src\export\site_application_list_exporter.py
- Line 83: `try:`

### src\export\site_asset_exporter.py
- Line 150: `try:`
- Line 183: `try:`
- Line 219: `try:`

### src\export\site_client_exporter.py
- Line 73: `try:`
- Line 320: `try:  # WHY: top-level guard keeps menu operation from crashing on API/runtime failures.`
- Line 267: `try:  # WHY: isolate request failures so 429 can trigger adaptive retry path.`

### src\export\site_config_exporter.py
- Line 38: `try:`
- Line 53: `try:`

### src\export\site_device_exporter.py
- Line 147: `try:`
- Line 221: `try:`
- Line 290: `try:`
- Line 92: `try:`

### src\export\site_export_utils.py
- Line 254: `try:`
- Line 262: `try:`
- Line 302: `try:`
- Line 329: `try:`
- Line 392: `try:`
- Line 411: `try:`
- Line 430: `try:`
- Line 456: `try:`
- Line 484: `try:`

### src\export\site_guest_authorization_exporter.py
- Line 95: `try:`

### src\export\site_insights\device_metric_operation.py
- Line 129: `try:`
- Line 164: `try:`
- Line 249: `try:`
- Line 287: `try:`

### src\export\site_insights\site_metric_operation.py
- Line 103: `try:`
- Line 160: `try:`
- Line 194: `try:`

### src\export\site_mist_edge_events_exporter.py
- Line 95: `try:`

### src\export\site_nac_client_events_exporter.py
- Line 95: `try:`

### src\export\site_other_device_events_exporter.py
- Line 65: `try:  # WHY: keep SDK failures inside the menu operation.`

### src\export\site_search_exporter.py
- Line 128: `try:`
- Line 372: `try:`

### src\export\site_system_events_exporter.py
- Line 83: `try:`

### src\export\site_wan_usage_exporter.py
- Line 95: `try:`

### src\export\site_webhook_deliveries_exporter.py
- Line 170: `try:`

### src\export\sites_by_ap_model_exporter.py
- Line 76: `try:`

### src\export\wan_client_events_exporter.py
- Line 90: `try:`
- Line 207: `try:`

### src\export\wifi_clients_exporter.py
- Line 53: `try:`
- Line 117: `try:`

### src\firmware\aggregate_upgrade_service.py
- Line 433: `try:  # A missing or lost lock must stop this child and all later writes.`
- Line 445: `try:  # A transport failure after a write has an unknown outcome.`
- Line 572: `try:  # A read failure changes only this child's current reading.`
- Line 701: `try:  # A transport failure after a cancel stays unknown.`

### src\firmware\bulk_ap_upgrader.py
- Line 297: `try:`
- Line 313: `try:`
- Line 466: `try:`
- Line 588: `try:  # WHY: any network/parse failure yields empty lookup (matches pre-refactor behavior)`
- Line 683: `try:`
- Line 878: `try:  # WHY: parse index. ValueError triggers retry`
- Line 1433: `try:`
- Line 2012: `try:`
- Line 2068: `try:`
- Line 2175: `try:  # WHY: swallow disk errors so a tracking failure never breaks the upgrade run`
- Line 2276: `try:`
- Line 2117: `try:`

### src\firmware\bulk_switch_upgrader.py
- Line 174: `try:  # WHY: shield against transient API failures.`
- Line 241: `try:  # WHY: any parse error must degrade gracefully.`
- Line 489: `try:  # WHY: any IO error must fall back to API.`
- Line 540: `try:  # WHY: guard against API failures.`
- Line 566: `try:  # WHY: any file-system failure must not abort the workflow.`
- Line 655: `try:  # WHY: fall back to raw string on parse failure.`
- Line 838: `try:  # WHY: catch-all in case an unexpected error escapes site processing.`
- Line 872: `try:  # WHY: contain per-site errors so other sites still run.`

### src\firmware\firmware_manager.py
- Line 56: `try:`
- Line 284: `try:`
- Line 313: `try:`
- Line 618: `try:`
- Line 643: `try:  # WHY: guard API/import errors`
- Line 762: `try:`
- Line 890: `try:`
- Line 1359: `try:`
- Line 1566: `try:`
- Line 1730: `try:`
- Line 2194: `try:`
- Line 2246: `try:`
- Line 2292: `try:`
- Line 2495: `try:`
- Line 2542: `try:`
- Line 2559: `try:`
- Line 2677: `try:  # WHY: network call may raise`
- Line 2905: `try:  # WHY: response.body access can raise`
- Line 3038: `try:  # WHY: guard per-site failures`
- Line 3233: `try:`
- Additional records: 11

### src\firmware\org_ap_upgrader.py
- Line 612: `try:  # WHY: guard downstream API + UI code from unexpected exceptions`
- Line 1012: `try:`
- Line 1098: `try:  # WHY: broad guard preserves pre-refactor behavior`
- Line 1173: `try:`
- Line 1267: `try:`
- Line 1399: `try:`
- Line 2676: `try:`
- Line 2795: `try:`

### src\firmware\running_version.py
- Line 132: `try:  # WHY: a network call can raise, and a firmware flow must not stop here`

### src\firmware\site_auto_upgrade.py
- Line 1365: `try:`
- Line 1587: `try:`
- Line 319: `try:`
- Line 430: `try:`
- Line 514: `try:`

### src\gateway\_wan2_variable_device.py
- Line 144: `try:  # WHY: mistapi calls raise on transport failure`
- Line 190: `try:  # WHY: mistapi calls raise on transport failure`

### src\gateway\_wan2_variable_template.py
- Line 31: `try:  # WHY: mistapi calls raise on transport failure`
- Line 166: `try:  # WHY: mistapi calls raise on transport failure`

### src\gateway\device_template_cloner.py
- Line 505: `try:`

### src\gateway\gateway_export_utils.py
- Line 524: `try:`

### src\gateway\gateway_ha_exporter.py
- Line 89: `try:`
- Line 109: `try:`

### src\gateway\gateway_stats_exporter.py
- Line 363: `try:`
- Line 180: `try:`
- Line 224: `try:`

### src\gateway\overrides\device_data_fetcher.py
- Line 105: `try:`
- Line 122: `try:`

### src\gateway\template_config.py
- Line 171: `try:`
- Line 228: `try:`
- Line 271: `try:`
- Line 299: `try:`
- Line 331: `try:`
- Line 417: `try:`
- Line 503: `try:`
- Line 580: `try:`
- Line 618: `try:`
- Line 671: `try:`

### src\gateway\wan2_migration_manager.py
- Line 520: `try:  # WHY: outer guard around the API mutation.`

### src\gateway\wan_probe_device_override_manager.py
- Line 342: `try:`
- Line 475: `try:`

### src\input\prompt_client_utils.py
- Line 38: `try:`
- Line 209: `try:`

### src\inventory\csv_comparator.py
- Line 436: `try:`
- Line 451: `try:`
- Line 778: `try:`
- Line 1088: `try:`
- Line 1146: `try:`
- Line 1290: `try:`

### src\inventory\inventory_summary\version_per_model_fetcher.py
- Line 154: `try:`
- Line 174: `try:`

### src\inventory\org_device_inventory_msp.py
- Line 130: `try:`
- Line 452: `try:`

### src\inventory\org_device_inventory_summary.py
- Line 111: `try:  # WHY: inventory fetch errors must not abort the larger summary run`
- Line 145: `try:  # WHY: inventory fetch errors must not abort the larger summary run`
- Line 184: `try:  # WHY: supplemental fetch errors must not break the primary report`
- Line 246: `try:  # WHY: never abort the combined report on one type's failure`
- Line 257: `try:  # WHY: never abort the combined report on one type's failure`
- Line 267: `try:  # WHY: AP counting must never abort the combined report`
- Line 310: `try:  # WHY: supplemental counting must never break the primary report`
- Line 349: `try:  # WHY: API failures fall back to env / org id at higher level`

### src\maps\_container_detection.py
- Line 91: `try:  # pwd is Unix-only. Getuid absent on Windows`
- Line 106: `try:  # Some importers (frozen apps) may not expose __file__`
- Line 145: `try:  # Isolate per-probe failures so one broken check cannot mask others`

### src\maps\_flask_viewer.py
- Line 101: `try:`
- Line 131: `try:`
- Line 162: `try:`
- Line 231: `try:`

### src\maps\_maps_backup.py
- Line 114: `try:  # WHY: network I/O may raise. Caller wants graceful fallback`
- Line 154: `try:  # WHY: fetch is best-effort. Caller degrades gracefully`
- Line 186: `try:  # WHY: network I/O may raise. Caller wants graceful fallback`
- Line 352: `try:  # WHY: pipeline may raise. Wrapper degrades to warning`

### src\maps\_maps_clone.py
- Line 141: `try:`
- Line 176: `try:`
- Line 239: `try:`
- Line 258: `try:`
- Line 292: `try:`
- Line 420: `try:`

### src\maps\_maps_coverage.py
- Line 266: `try:  # WHY: result_def may omit expected columns. Fall back on legacy layout.`
- Line 300: `try:  # WHY: `api_session.mist_get` may raise on network errors.`

### src\maps\_maps_matplotlib.py
- Line 382: `try:`
- Line 173: `try:`

### src\maps\_maps_testing.py
- Line 111: `try:`
- Line 152: `try:`
- Line 248: `try:`
- Line 266: `try:`
- Line 281: `try:`

### src\maps\_maps_utils.py
- Line 115: `try:`

### src\maps\_maps_wizard.py
- Line 103: `try:`
- Line 121: `try:`
- Line 134: `try:`
- Line 206: `try:`
- Line 620: `try:`
- Line 798: `try:`
- Line 815: `try:`
- Line 490: `try:`

### src\maps\_plotly_viewer.py
- Line 76: `try:`

### src\maps\launcher\_viewer_clone.py
- Line 253: `try:`
- Line 300: `try:`

### src\maps\launcher\_viewer_drawing.py
- Line 447: `try:`
- Line 479: `try:`
- Line 503: `try:`
- Line 561: `try:`

### src\maps\maps_manager.py
- Line 90: `try:`
- Line 95: `try:`
- Line 118: `try:`
- Line 2707: `try:`
- Line 148: `try:`
- Line 305: `try:`
- Line 508: `try:`
- Line 611: `try:`
- Line 633: `try:`
- Line 684: `try:`
- Line 725: `try:`
- Line 748: `try:`
- Line 807: `try:`
- Line 908: `try:  # Wrap orchestrator to log any unexpected error to user.`
- Line 983: `try:`
- Line 1081: `try:`
- Line 1131: `try:`
- Line 1186: `try:`
- Line 1344: `try:`
- Line 1434: `try:`
- Additional records: 10

### src\marvis\marvis_utils.py
- Line 76: `try:  # WHY: Bad payloads must never crash the caller`

### src\metrics_gateway\collector.py
- Line 267: `try:  # A Mist fault must become a failed snapshot and never an exception in the refresh thread.`

### src\network\_routing_utils_display.py
- Line 217: `try:  # WHY: PrettyTable can fail with unusual terminals — fall back gracefully`
- Line 339: `try:  # WHY: PrettyTable can fail with unusual terminals — text fallback below`
- Line 459: `try:  # WHY: PrettyTable can fail with unusual terminals — text fallback below`

### src\network\_routing_utils_forwarding.py
- Line 70: `try:  # WHY: outer try wraps the whole flow so exceptions still hit cleanup`

### src\network\_routing_utils_payload.py
- Line 307: `try:  # WHY: mistapi raises broad exceptions on transport/protocol failures`

### src\network\_routing_utils_routing.py
- Line 368: `try:  # WHY: outer try wraps the whole flow so KeyboardInterrupt/Exception cleanup runs`

### src\network\_routing_utils_ssr.py
- Line 60: `try:  # WHY: outer try wraps happy-path so exceptions still hit cleanup`

### src\network\routing_utils.py
- Line 183: `try:  # WHY: mistapi calls may raise on network/auth failures`
- Line 345: `try:  # WHY: never let cleanup escalate to caller`

### src\org\org_config_migration_manager.py
- Line 151: `try:`
- Line 173: `try:`
- Line 635: `try:`

### src\org\org_synthetic_probes_manager.py
- Line 2759: `try:`
- Line 2972: `try:`
- Line 3003: `try:`

### src\org\org_ticket_manager.py
- Line 50: `try:`
- Line 198: `try:`
- Line 236: `try:`
- Line 391: `try:`
- Line 445: `try:`
- Line 465: `try:`

### src\org_data_collector.py
- Line 566: `try:`

### src\refactors\anomaly_metrics_discovery.py
- Line 61: `try:`

### src\refactors\connection_pool_executor.py
- Line 95: `try:  # Future.result() can raise if the worker threw an exception`
- Line 109: `try:  # tqdm.update can fail in some environments. Isolate that error`
- Line 180: `try:  # Best-effort capture. Serialization failure must not suppress the re-raise`
- Line 221: `try:  # Isolate each batch so a single failure does not silently skip remaining batches`

### src\refactors\data_directory_checker.py
- Line 56: `try:  # Attempt to validate write permission`

### src\refactors\device_data_fetcher.py
- Line 108: `try:  # Guard against transient API failures so we can log and return None`

### src\refactors\main_entrypoint.py
- Line 226: `try:  # python-dotenv can be absent before the dependency check repairs the environment.`

### src\refactors\maps_manager_launcher.py
- Line 98: `try:  # Wrap prompt so any exception is funneled through the fatal-error handler`

### src\refactors\msp_privilege_detection.py
- Line 55: `try:  # API call and payload parsing may fail. Degrade to None on any error`
- Line 157: `try:  # API or parsing failures must degrade to "no MSP access" rather than crash the session.`

### src\refactors\serial_cc\global_assignments_builder.py
- Line 33: `try:  # The shim module may not carry the attribute directly on all install paths`
- Line 47: `try:  # The module may not carry `fuzz` directly depending on import path`

### src\refactors\serial_cc\security_events.py
- Line 301: `try:  # Guard site-list reading + iteration. Failure here aborts this export only.`
- Line 128: `try:`

### src\refactors\serial_cc\site_client_insights.py
- Line 134: `try:`
- Line 168: `try:  # WHY: Client listing is best-effort. Failures are warned and yield an empty list`
- Line 206: `try:  # WHY: Per-metric failures are non-fatal and skip to the next metric`
- Line 310: `try:  # WHY: Guard the fetch+export so failures still write an empty file`

### src\refactors\serial_cc\sle_metrics.py
- Line 285: `try:  # Guard the whole retrieval+export so progress always completes`
- Line 126: `try:  # Per-category failures are non-fatal and skip to the next category`
- Line 179: `try:  # Whole-metric failures are non-fatal`
- Line 231: `try:  # Per-category failures are non-fatal`

### src\refactors\serial_cc\start_site_scan_capture.py
- Line 330: `try:  # WHY: Pre-check API failures are non-fatal - warn and proceed`

### src\refactors\serial_cc\switch_vc_stats.py
- Line 86: `try:  # Non-fatal API failures should not abort whole export`

### src\refactors\serial_cc\test_results_by_site.py
- Line 44: `try:`
- Line 197: `try:`

### src\refactors\service_ping_launcher.py
- Line 71: `try:  # Wrap the full flow so any runtime error is funneled through the fatal-error handler`

### src\refactors\sqlite_database_writer.py
- Line 174: `try:`
- Line 187: `try:`
- Line 223: `try:`
- Line 432: `try:`
- Line 442: `try:`

### src\refactors\tui_launcher.py
- Line 69: `try:  # Guarded run to guarantee handler restoration in finally`

### src\refactors\wan2_migration_launcher.py
- Line 78: `try:  # Wrap the full flow so any runtime error is funneled through the fatal-error handler`

### src\refactors\wanprobe_config_manager.py
- Line 281: `try:`
- Line 382: `try:`

### src\refactors\wlanradius_timer_manager.py
- Line 139: `try:`
- Line 173: `try:`
- Line 208: `try:`
- Line 219: `try:`
- Line 720: `try:`

### src\reports\e911_bssid.py
- Line 270: `try:  # WHY: any single template can fail without aborting the report`
- Line 897: `try:  # WHY: rate-limit is the only path that halts the batch`

### src\reports\global_wired_client_report_generator.py
- Line 125: `try:`

### src\reports\offline_device_reporter.py
- Line 295: `try:`

### src\reports\sfp_transceiver_data_processor.py
- Line 176: `try:`

### src\reports\wired_client_manufacturer_report_generator.py
- Line 53: `try:`

### src\site\address_audit\address_resolver.py
- Line 83: `try:`

### src\site\address_audit\audit_engine.py
- Line 347: `try:`
- Line 380: `try:`
- Line 411: `try:`

### src\site\address_audit\site_matcher.py
- Line 23: `try:  # Optional dependency: rapidfuzz powers the fuzzy fallback.`

### src\site\address_audit\ui_geocoder.py
- Line 177: `try:`
- Line 273: `try:`
- Line 425: `try:`
- Line 496: `try:`
- Line 600: `try:`
- Line 605: `try:`
- Line 638: `try:`
- Line 256: `try:`

### src\site\bulk_radius_wlan_config_manager.py
- Line 138: `try:`
- Line 430: `try:`
- Line 538: `try:`

### src\ssh\batch\batch_executor.py
- Line 389: `try:`
- Line 416: `try:`

### src\ssh\batch\interactive_batch_executor.py
- Line 284: `try:`
- Line 525: `try:`
- Line 713: `try:`
- Line 745: `try:`
- Line 762: `try:`

### src\ssh\cli_shell_manager.py
- Line 90: `try:`
- Line 165: `try:  # The socket may drop mid-send.`
- Line 199: `try:  # WHY: the socket may already be closed by the exit key handler.`
- Line 134: `try:  # A read error or close ends the receive loop.`

### src\ssh\command\command_runner.py
- Line 320: `try:`
- Line 347: `try:`

### src\ssh\config\env_loader.py
- Line 20: `try:`

### src\ssh\connection\connector.py
- Line 312: `try:`

### src\ssh\runtime\app_runner.py
- Line 126: `try:  # Tracer installation is best-effort and never fatal`
- Line 141: `try:  # Removal is best-effort and never fatal`
- Line 453: `try:  # Single try wraps the pipeline so we always restore the tracer`
- Line 82: `try:  # Defensive: never let tracer crash the run`

### src\ssh\ssh_runner.py
- Line 288: `try:`
- Line 300: `try:`
- Line 326: `try:`
- Line 394: `try:`

### src\ssh\ssh_runner_manager.py
- Line 61: `try:`
- Line 507: `try:`

### src\ssid_consolidation\ssid_template_consolidation.py
- Line 506: `try:`
- Line 563: `try:`
- Line 597: `try:`
- Line 686: `try:`
- Line 828: `try:`

### src\time\time_utils.py
- Line 37: `try:`

### src\troubleshooting\interactive_test_runner.py
- Line 355: `try:`
- Line 479: `try:`

### src\troubleshooting\marvis_troubleshoot_utils.py
- Line 176: `try:  # WHY: funnel SDK errors to user guidance.`
- Line 210: `try:  # WHY: funnel SDK errors to guidance.`
- Line 238: `try:  # WHY: funnel SDK errors to guidance.`
- Line 708: `try:  # WHY: funnel unexpected errors to shared handler.`
- Line 812: `try:  # WHY: bound errors from insight collection so usage guide still renders.`
- Line 879: `try:  # WHY: individual endpoint errors must not abort the loop.`

### src\ui\execution\debug_saver.py
- Line 25: `try:`
- Line 102: `try:`

### src\ui\execution\function_executor.py
- Line 42: `try:`
- Line 117: `try:`
- Line 191: `try:`

### src\ui\execution\item_executor.py
- Line 71: `try:`

### src\ui\prompt_utils.py
- Line 274: `try:`
- Line 290: `try:`
- Line 306: `try:`
- Line 321: `try:`
- Line 335: `try:`

### src\ui\runtime\level_discoverer.py
- Line 66: `try:`

### src\ui\runtime\tui_runner.py
- Line 30: `try:  # WHY: teardown must always run even on setup/loop errors`
- Line 74: `try:  # WHY: swallow restore errors to keep exit clean`

### src\ui\tui.py
- Line 148: `try:`

### src\upgrade_portal\api\mist_client.py
- Line 167: `try:`
- Line 195: `try:`
- Line 63: `try:`
- Line 122: `try:`

### src\upgrade_portal\api\run_controls\services\bulk.py
- Line 258: `try:`

### src\upgrade_portal\api\run_controls\services\reconciliation.py
- Line 477: `try:  # Evidence collection can fail through a cloud or store seam.`
- Line 494: `try:`

### src\upgrade_portal\api\run_controls\services\retry.py
- Line 92: `try:`

### src\upgrade_portal\app\factory.py
- Line 411: `try:  # No fault may leave this function.`
- Line 436: `try:  # No fault may leave this function.`
- Line 619: `try:  # The socket may already be broken.`

### src\upgrade_portal\app\routes\audit.py
- Line 48: `try:`
- Line 115: `try:`

### src\upgrade_portal\app\routes\auth.py
- Line 244: `try:  # The catalog lives outside this package, so an import fault must not stop the portal.`
- Line 703: `try:  # The template may arrive in a later stage of this phase.`
- Line 725: `try:  # A settings fault or a probe fault must not stop the operator signing in.`
- Line 1050: `try:  # The identity module names the variables in its own message, and shows no value.`
- Line 1069: `try:`
- Line 1096: `try:  # The library raises for a transport fault and answers a mapping for a refusal.`

### src\upgrade_portal\app\routes\comparison.py
- Line 51: `try:`
- Line 175: `try:`

### src\upgrade_portal\app\routes\jwt_auth.py
- Line 61: `try:`
- Line 174: `try:`

### src\upgrade_portal\app\routes\mist.py
- Line 40: `try:`
- Line 90: `try:`

### src\upgrade_portal\app\routes\org_upgrade.py
- Line 716: `try:`
- Line 905: `try:  # The service persists before and after every destructive action.`
- Line 1123: `try:`
- Line 1145: `try:  # Map validation and cloud read failures to the existing responses.`
- Line 1191: `try:  # Map validation and cloud read failures to the existing responses.`
- Line 1227: `try:`
- Line 1282: `try:  # The service persists before and after every destructive action.`
- Line 800: `try:  # Lock writes fail closed and use no memory fallback.`

### src\upgrade_portal\app\routes\review.py
- Line 798: `try:`
- Line 1035: `try:`

### src\upgrade_portal\app\routes\runs.py
- Line 41: `try:`
- Line 90: `try:`
- Line 161: `try:`

### src\upgrade_portal\app\routes\select.py
- Line 970: `try:  # A read page must survive a failed second call.`
- Line 1283: `try:  # The template arrives in a later stage of this phase.`
- Line 1950: `try:  # The session read needs a request, and a damaged field must not hide a page.`
- Line 1976: `try:  # `contracts/site-lock.md:138` says a read never needs the lock store.`
- Line 2005: `try:  # The identity read needs a request, and a page must render without one.`
- Line 2057: `try:  # `read_site_locks` absorbs a dead store, and the seam lookup itself may still fail.`
- Line 2081: `try:  # A banner render must survive a store fault.`

### src\upgrade_portal\app\routes\upgrade.py
- Line 616: `try:  # The cloud or the test seam may return no body, or raise.`
- Line 906: `try:`
- Line 1290: `try:  # The reader reaches the cloud, and the cloud refuses and times out.`
- Line 1342: `try:`
- Line 1374: `try:`
- Line 1511: `try:  # The builder reaches the cloud, and the cloud refuses and times out.`
- Line 1557: `try:  # The builder reaches the cloud, and the cloud refuses and times out.`
- Line 1667: `try:  # A session read and a session write must never end a start that already passed every rule.`
- Line 2113: `try:  # UpgradeService call may fail due to database or transient errors`
- Line 2154: `try:  # UpgradeService call may fail due to API, database, or transient errors`
- Line 2351: `try:  # A damaged record names a state outside the model.`
- Line 2542: `try:  # The reader names the control and states the rule on a refusal.`

### src\upgrade_portal\app\seam_shapes.py
- Line 251: `try:  # The module may be absent in a trimmed install.`

### src\upgrade_portal\app\wiring.py
- Line 186: `try:  # A broken module may raise anything at all while it loads.`
- Line 599: `try:  # A stored row may hold a value that no rule maps.`
- Line 675: `try:  # A read outside a request, or a seam that raises, must not stop the run.`
- Line 1055: `try:`
- Line 1142: `try:`
- Line 1228: `try:`
- Line 1315: `try:`
- Line 226: `try:  # The store sits on a network and may not answer.`
- Line 253: `try:  # The store sits on a network and may not answer.`
- Line 273: `try:  # The database action is one atomic AQL statement.`
- Line 317: `try:  # The scan is one query on a network store.`
- Line 395: `try:  # The store sits on a network and may not answer.`
- Line 469: `try:  # The read of a whole site holds this thread for minutes and touches a network.`
- Line 548: `try:  # One cloud call, which may time out or refuse.`
- Line 1537: `try:`
- Line 1543: `try:`

### src\upgrade_portal\audit\logger.py
- Line 67: `try:`
- Line 237: `try:`

### src\upgrade_portal\auth\session.py
- Line 68: `try:`
- Line 120: `try:`
- Line 200: `try:`
- Line 383: `try:`
- Line 460: `try:`
- Line 206: `try:`

### src\upgrade_portal\capture\assembly.py
- Line 718: `try:`

### src\upgrade_portal\capture\collector.py
- Line 552: `try:  # The read reaches a network, so it may raise.`

### src\upgrade_portal\capture\devices.py
- Line 159: `try:`
- Line 321: `try:`

### src\upgrade_portal\capture\extras.py
- Line 228: `try:`
- Line 278: `try:`
- Line 412: `try:`

### src\upgrade_portal\capture\service.py
- Line 100: `try:`
- Line 330: `try:`
- Line 526: `try:`
- Line 455: `try:`

### src\upgrade_portal\capture\store.py
- Line 556: `try:`
- Line 622: `try:`
- Line 654: `try:`
- Line 676: `try:`
- Line 978: `try:`
- Line 1657: `try:`
- Line 1680: `try:`
- Line 2056: `try:`

### src\upgrade_portal\compare\service.py
- Line 137: `try:`

### src\upgrade_portal\locking\session_lock.py
- Line 221: `try:`
- Line 307: `try:`
- Line 398: `try:`

### src\upgrade_portal\persistence\actions\replay.py
- Line 184: `try:  # Each refusal below must become a safe final result, never a false success.`

### src\upgrade_portal\persistence\actions\transactions.py
- Line 121: `try:  # A failure must roll back the action and run together.`

### src\upgrade_portal\persistence\runs.py
- Line 96: `try:`
- Line 195: `try:`

### src\upgrade_portal\runtime\lock.py
- Line 560: `try:`
- Line 662: `try:`
- Line 1037: `try:`
- Line 1156: `try:`

### src\upgrade_portal\runtime\pools.py
- Line 376: `try:  # The call reaches a network, so it may raise`
- Line 406: `try:  # The call reaches a network, so it may raise`

### src\upgrade_portal\settle\service.py
- Line 143: `try:`
- Line 380: `try:  # WHY: keep one bad check from stopping the others`
- Line 447: `try:`
- Line 507: `try:`
- Line 559: `try:`
- Line 605: `try:`

### src\upgrade_portal\upgrade\driver.py
- Line 601: `try:`
- Line 658: `try:`
- Line 841: `try:`
- Line 983: `try:`
- Line 1385: `try:`

### src\upgrade_portal\upgrade\events.py
- Line 234: `try:`
- Line 429: `try:`

### src\upgrade_portal\upgrade\gate.py
- Line 870: `try:`

### src\upgrade_portal\upgrade\options.py
- Line 456: `try:`

### src\upgrade_portal\upgrade\phase_gate.py
- Line 852: `try:`
- Line 878: `try:`

### src\upgrade_portal\upgrade\service.py
- Line 136: `try:`
- Line 502: `try:`

### src\upgrade_portal\upgrade\stop.py
- Line 177: `try:`
- Line 229: `try:`

### src\utils\address_utils.py
- Line 332: `try:  # WHY: the heuristic parser can raise on pathological input`
- Line 378: `try:  # WHY: library parsing can raise on malformed input`
- Line 937: `try:  # WHY: any transport error retries or gives up`
- Line 1058: `try:  # WHY: any error yields an empty-result payload`
- Line 419: `try:  # WHY: fuzz can throw on odd unicode`

### src\utils\environment_utils.py
- Line 117: `try:`

### src\utils\logger_utils.py
- Line 139: `try:`

### src\utils\rate_limiting.py
- Line 19: `try:  # WHY: numpy is optional. Fall back to pure-Python stdev when absent.`
- Line 66: `try:  # WHY: creation may fail on read-only filesystems. Fall back cleanly.`
- Line 132: `try:  # WHY: any decode/read failure falls back to defaults.`
- Line 190: `try:  # WHY: numpy path may still raise on exotic inputs. Be defensive.`
- Line 560: `try:  # WHY: any downstream failure must degrade gracefully to fallback.`

### src\utils\tqdm_wrapper.py
- Line 22: `try:  # Prefer the real progress-bar package when installed.`

### src\utils\zscaler_catalogue.py
- Line 1095: `try:`
- Line 1225: `try:`

### src\utils\zscaler_probe.py
- Line 345: `try:`
- Line 385: `try:`
- Line 732: `try:`

### src\wan_hub_group_manager.py
- Line 142: `try:  # WHY: any mistapi failure must degrade gracefully to empty list.`
- Line 164: `try:  # WHY: mistapi/network faults must degrade to empty tuple, not raise.`
- Line 296: `try:  # WHY: non-numeric choices must fall through to retry.`
- Line 486: `try:  # WHY: isolate per-VPN failure from the loop.`

### src\wan_vpn_builder.py
- Line 329: `try:  # WHY: any transport / auth error should degrade gracefully to an empty list.`
- Line 344: `try:  # WHY: mirror _fetch_profiles' graceful degradation.`
- Line 358: `try:  # WHY: convert any API error into a None return so run() can bail out cleanly.`
- Line 650: `try:  # WHY: guard the whole flow so any API/parse error becomes a soft failure.`

### src\websocket\commands.py
- Line 41: `try:`

### src\websocket\diagnostics\arp_executor.py
- Line 62: `try:  # WHY: mirror legacy try/except/finally so cleanup always runs.`
- Line 114: `try:  # WHY: legacy swallows errors so ARP attempt still proceeds.`
- Line 415: `try:  # WHY: match legacy fallback phrasing on JSON parse failure.`

### src\websocket\diagnostics\ping_executor.py
- Line 74: `try:  # WHY: mirror legacy try/except/finally so cleanup always runs.`
- Line 154: `try:  # WHY: parse user input as integer. Revert to default on failure.`

### src\websocket\manager.py
- Line 62: `try:  # WHY: Cleanup must never propagate — it runs from `finally` blocks.`
- Line 201: `try:  # WHY: Any low-level failure is reported and returned as False.`
- Line 252: `try:  # WHY: Guard against transient send errors.`

### src\websocket\service_ping_discovery.py
- Line 121: `try:`
- Line 244: `try:`
- Line 460: `try:`

### src\websocket\service_ping_manager.py
- Line 143: `try:  # WHY: mistapi failures must not crash the workflow.`
- Line 261: `try:  # WHY: guard the API round-trip so error path is uniform.`
- Line 405: `try:  # WHY: cleanup must never raise into the menu loop.`
- Line 461: `try:  # WHY: wrap workflow so cleanup always runs even on failure.`

### starlink_dashboard.py
- Line 112: `try:`
- Line 160: `try:`
- Line 236: `try:`
- Line 311: `try:`
- Line 1193: `try:`
- Line 1491: `try:`
- Line 1623: `try:`
- Line 1639: `try:`

### tests\contract\upgrade_portal\test_page_links_resolve.py
- Line 144: `try:`

### tests\e2e\upgrade_portal\test_history_layout.py
- Line 186: `try:`

### tests\integration\test_wan_vpn_builder_live.py
- Line 145: `try:`
- Line 159: `try:`

### tests\test_issue_433_src_g_no_regress.py
- Line 46: `try:`

### tests\unit\firmware\test_aggregate_upgrade_service.py
- Line 187: `try:  # One worker must lose the parent claim.`

### tests\unit\firmware\test_firmware_manager_config.py
- Line 222: `try:`

### tests\unit\test_bulk_ap_upgrader.py
- Line 2145: `try:`

### tests\unit\utils\test_zscaler_catalogue.py
- Line 1147: `try:`

### tools\ste_linter\analysis\__init__.py
- Line 42: `try:  # The import fails when the optional package is not installed.`

### tools\ste_linter\parsing\python_source.py
- Line 60: `try:  # Try the full parse for docstrings.`

### web_portal\routes\maps.py
- Line 70: `try:`
- Line 82: `try:`
- Line 103: `try:`
- Line 123: `try:`
- Line 146: `try:`

### web_portal\routes\operations.py
- Line 349: `try:`

### web_portal\routes\webhooks.py
- Line 138: `try:`
- Line 126: `try:`

### web_portal\services\data_browser.py
- Line 149: `try:`
- Line 395: `try:`
- Line 525: `try:`
- Line 557: `try:`
- Line 571: `try:`

### web_portal\services\operation.py
- Line 664: `try:`

### wsgi.py
- Line 37: `try:`
- Line 60: `try:`
- Line 81: `try:`

## default_masks_missing_input

- Method: AST scan for .get(default), getenv defaults, and dependency declarations without an upper bound. Dependency manifests are repaired in this branch.
- Count: 3860
- File count: 407

### MistHelper.py
- Line 2464: `state.get('msp_privileges', MainEntrypoint.context.msp_privileges)`
- Line 2467: `state.get('selected_msp', MainEntrypoint.context.selected_msp)`
- Line 2470: `state.get('org_id', MainEntrypoint.context.org_id)`
- Line 2673: `os.getenv('MIST_HOST', 'api.mist.com')`
- Line 6302: `os.environ.get('CAPTURE_PORT', '8056')`
- Line 6302: `os.environ.get('CAPTURE_PORT', '8056')`
- Line 1719: `self.import_name_mappings.get(module_name, module_name)`
- Line 1750: `self.import_name_mappings.get(module_name, module_name)`
- Line 1210: `os.getenv('UPGRADE_CHECK_TIMEOUT', '30')`
- Line 1213: `os.getenv('CSV_FRESHNESS_MINUTES', '15')`
- Line 1215: `os.getenv('UV_UPDATE_CHECK_HOURS', '24')`
- Line 833: `data.get('info', {})`
- Line 1207: `os.getenv('AUTO_UPGRADE_UV', 'true')`
- Line 1208: `os.getenv('AUTO_UPGRADE_DEPENDENCIES', 'true')`
- Line 1217: `os.getenv('DISABLE_UV_CHECK', 'false')`
- Line 1219: `os.getenv('DISABLE_AUTO_INSTALL', 'false')`
- Line 1631: `kwargs.get('desc', 'Processing')`
- Line 1632: `kwargs.get('unit', 'item')`

### diag_rbo.py
- Line 10: `raw.get('results', raw)`
- Line 13: `entry.get('message', '')`
- Line 17: `entry.get('before', {})`
- Line 18: `entry.get('after', {})`
- Line 19: `entry.get('timestamp', 0)`
- Line 34: `before.get('routing_policies', {})`
- Line 35: `after.get('routing_policies', {})`
- Line 26: `entry.get('admin_name', '?')`
- Line 43: `vb.get('terms', [])`
- Line 44: `va.get('terms', [])`

### mist-ops-platform\src\api\middleware\auth.py
- Line 235: `request.cookies.get(SESSION_COOKIE_NAME, '')`
- Line 158: `row.get('msp_id', '')`
- Line 252: `privs.raw.get('privileges', [])`
- Line 156: `row.get('scope', '')`
- Line 300: `privs.raw.get('privileges', [])`

### mist-ops-platform\src\api\routes\audit.py
- Line 224: `included.get('total_records', 0)`

### mist-ops-platform\src\api\routes\deploy.py
- Line 336: `t.get('entity_type', '')`

### mist-ops-platform\src\api\routes\health.py
- Line 366: `request.cookies.get(SESSION_COOKIE_NAME, '')`
- Line 386: `request.cookies.get(SESSION_COOKIE_NAME, '')`
- Line 254: `privs.org_names.get(oid, oid)`
- Line 255: `db.get(Organization, org_uuid)`
- Line 316: `privs.org_names.get(oid, oid)`

### mist-ops-platform\src\api\routes\webhooks.py
- Line 46: `request.headers.get('X-Mist-Signature-v2', '')`

### mist-ops-platform\src\shared\config\settings.py
- Line 40: `os.environ.get(name, default)`
- Line 40: `os.environ.get(name, default)`

### mist-ops-platform\src\shared\mist\endpoints.py
- Line 58: `self.data.get('detail', str(self.data))`

### mist-ops-platform\src\shared\services\auth.py
- Line 126: `data.get('first_name', '')`
- Line 127: `data.get('last_name', '')`
- Line 125: `data.get('privileges', [])`
- Line 128: `data.get('email', '')`
- Line 130: `data.get('email', '')`
- Line 147: `priv.get('scope', '')`

### mist-ops-platform\src\shared\services\compliance.py
- Line 88: `by_type.get(record.change_type, 0)`
- Line 89: `by_actor.get(record.actor, 0)`

### mist-ops-platform\src\shared\services\diff.py
- Line 137: `raw.get('values_changed', [])`
- Line 193: `raw.get('type_changes', [])`
- Line 156: `raw.get(key, [])`
- Line 175: `raw.get(key, [])`

### mist-ops-platform\src\shared\services\notification.py
- Line 31: `os.getenv(SMTP_TIMEOUT_ENV_VAR, '')`

### mist-ops-platform\src\shared\services\session_store.py
- Line 188: `data.get('token', '')`
- Line 189: `data.get('privileges', {})`
- Line 190: `data.get('verified_at', 0.0)`

### mist-ops-platform\src\shared\services\template.py
- Line 47: `schema.get('required', [])`
- Line 76: `params.get(key, text)`
- Line 80: `params.get(key, match.group(0))`

### mist-ops-platform\src\worker\checks\post_checks.py
- Line 121: `device_index.get(device_id, {})`
- Line 122: `device_data.get('status', 'unknown')`

### mist-ops-platform\src\worker\checks\pre_checks.py
- Line 226: `device_data.get('status', 'unknown')`
- Line 264: `check_def.get('type', '')`

### mist-ops-platform\src\worker\deploy\dry_run.py
- Line 160: `payload.get('radio_config', {})`
- Line 208: `rules.get('blocked_keys', [])`
- Line 162: `radio_cfg.get(band_key, {})`
- Line 215: `payload.get('target_count', 0)`

### mist-ops-platform\src\worker\deploy\rollout.py
- Line 145: `health.get('passed', False)`

### mist-ops-platform\src\worker\sync\events.py
- Line 68: `event.get('obj_type', 'unknown')`
- Line 55: `event.get('admin_name', 'unknown')`
- Line 56: `event.get('message', 'change')`

### mist-ops-platform\src\worker\sync\inventory.py
- Line 134: `data.get('connected', False)`
- Line 117: `data.get('name', '')`
- Line 141: `data.get('type', 'ap')`
- Line 142: `data.get('model', 'unknown')`
- Line 143: `data.get('serial', '')`

### mist-ops-platform\src\worker\sync\status.py
- Line 59: `data.get('status', 'unknown')`
- Line 60: `data.get('num_clients', 0)`

### mist-ops-platform\src\worker\sync\webhook.py
- Line 46: `payload.get('topic', 'unknown')`
- Line 47: `payload.get('events', [])`

### mist-ops-platform\src\worker\tasks\audit_tasks.py
- Line 262: `mapping.get(table, 'created_at')`
- Line 203: `by_type.get(record.change_type, 0)`

### mist-ops-platform\src\worker\tasks\check_tasks.py
- Line 184: `item.get('name', '')`

### mist-ops-platform\src\worker\tasks\deploy_tasks.py
- Line 282: `result.get('passed', False)`
- Line 263: `post_result.get('passed', False)`
- Line 363: `result.get('passed', False)`
- Line 237: `payload.get('target_entity_ids', [])`
- Line 241: `payload.get('auto_rollback_on_failure', True)`

### mist-ops-platform\tests\unit\shared\test_schema_agreement.py
- Line 179: `parents.get('config_revisions', '')`
- Line 189: `parents.get(table_name, '')`

### scripts\audit_csv.py
- Line 101: `row.get('url', '')`
- Line 112: `row.get('idea_id', '')`
- Line 161: `row.get('status', '')`
- Line 61: `row.get('votes', '0')`
- Line 102: `row.get('title', '')`
- Line 115: `row.get('description_full', '')`
- Line 161: `row.get('status', '')`
- Line 80: `row.get(field, '0')`
- Line 75: `row.get(field, '')`

### scripts\bootstrap_worktree.py
- Line 124: `SCHEME_PORTS.get(parsed.scheme, 443)`

### scripts\build_zen_city_metadata.py
- Line 175: `data.get('by_city', {})`
- Line 275: `data.get('city_metadata', {})`

### scripts\check_device_profiles.py
- Line 16: `first.get('before', {})`
- Line 17: `first.get('after', {})`
- Line 26: `last.get('after', {})`
- Line 39: `je.get('before', {})`
- Line 40: `je.get('after', {})`
- Line 21: `p.get('name', '?')`
- Line 30: `p.get('name', '?')`
- Line 8: `e.get('message', '')`
- Line 8: `e.get('message', '')`
- Line 46: `p.get('name', '?')`
- Line 53: `p.get('name', '?')`

### scripts\check_device_profiles_orig.py
- Line 13: `e.get('before', {})`
- Line 9: `e.get('message', '')`
- Line 19: `p.get('name', f"ref:{p.get('servicepolicy_id', '?')[:12]}")`
- Line 23: `p.get('tenants', [])`
- Line 19: `p.get('servicepolicy_id', '?')`

### scripts\check_exclusion_drift.py
- Line 49: `payload.get('entries', [])`
- Line 187: `payload.get('results', [])`

### scripts\check_vpn_flags.py
- Line 12: `e.get('message', '')`
- Line 14: `e.get('before', {})`
- Line 15: `e.get('after', {})`
- Line 16: `before.get('vpn_access', {})`
- Line 17: `after.get('vpn_access', {})`

### scripts\codeql_verdict_register.py
- Line 354: `counts.get(row.verdict, 0)`

### scripts\compare_test_runs.py
- Line 227: `event.get('duration_seconds', 0.0)`
- Line 169: `event_a.get('status', 'absent')`
- Line 170: `event_b.get('status', 'absent')`
- Line 71: `event.get('event_type', '')`
- Line 162: `ev.get('timestamp', '')`
- Line 187: `event_b.get('error_message', '')`
- Line 76: `event.get('menu_option', '')`
- Line 206: `event_a.get('status', '')`
- Line 207: `event_b.get('status', '')`

### scripts\filter_orgaudit.py
- Line 43: `entry.get('before', {})`
- Line 44: `entry.get('after', {})`
- Line 50: `entry.get('message', '')`

### scripts\generate_api_docs.py
- Line 76: `raw.get('tags', [])`
- Line 77: `raw.get('security', [])`
- Line 284: `param.get('schema', {})`
- Line 285: `param.get('name', '')`
- Line 286: `schema.get('type', 'string')`
- Line 302: `body.get('content', {})`
- Line 337: `resp.get('description', '')`
- Line 338: `resp.get('content', {})`
- Line 354: `operation.get('operation_id', '')`
- Line 592: `param.get('name', '')`
- Line 593: `param.get('in', 'query')`
- Line 596: `param.get('description', '')`
- Line 754: `category_counts.get(category, 0)`
- Line 164: `self.schemas.get(ref_name, {})`
- Line 259: `param.get('in', 'query')`
- Line 350: `operation.get('tags', ['Utilities'])`
- Line 359: `p.get('name', '')`
- Line 490: `self._SECTION_LOCATION.get(section_name, 'query')`
- Line 751: `category_counts.get(category, 0)`
- Line 75: `raw.get('components', {})`
- Additional records: 24

### scripts\generate_menu_wiki.py
- Line 84: `registry.get(menu_id, 'unregistered')`
- Line 85: `_CATEGORY_TITLES.get(category, category)`
- Line 153: `_CATEGORY_TITLES.get(category, category)`
- Line 154: `_CATEGORY_SUMMARIES.get(category, '')`

### scripts\migrate_sqlite_to_polyglot.py
- Line 85: `strategy.get('type', '')`
- Line 165: `classification.get('arango', [])`
- Line 166: `classification.get('redis', [])`
- Line 210: `self._strategies.get(table, {})`
- Line 234: `self._strategies.get(table, {})`

### scripts\mist_ideas_analyzer_pkg\__init__.py
- Line 1406: `title_to_analysis.get(canonical, {})`
- Line 1422: `title_to_idea.get(canonical, {})`
- Line 1945: `ps_data.get('models', [])`
- Line 1976: `ps_data.get('models', [])`
- Line 355: `os.environ.get('GITHUB_TOKEN', '')`
- Line 355: `os.environ.get('GITHUB_TOKEN', '')`
- Line 358: `os.environ.get('AI_MODEL', 'gpt-4o-mini')`
- Line 358: `os.environ.get('AI_MODEL', 'gpt-4o-mini')`
- Line 373: `os.environ.get('AVA_API_URL', '')`
- Line 373: `os.environ.get('AVA_API_URL', '')`
- Line 376: `os.environ.get('AI_MODEL', 'llama3.3')`
- Line 376: `os.environ.get('AI_MODEL', 'llama3.3')`
- Line 377: `os.environ.get('AVA_API_KEY', 'ava')`
- Line 377: `os.environ.get('AVA_API_KEY', 'ava')`
- Line 392: `os.environ.get('AI_API_KEY', '')`
- Line 392: `os.environ.get('AI_API_KEY', '')`
- Line 395: `os.environ.get('AI_API_BASE_URL', 'https://api.openai.com/v1')`
- Line 395: `os.environ.get('AI_API_BASE_URL', 'https://api.openai.com/v1')`
- Line 399: `os.environ.get('AI_MODEL', 'gpt-4o-mini')`
- Line 399: `os.environ.get('AI_MODEL', 'gpt-4o-mini')`
- Additional records: 81

### scripts\mist_ideas_distiller_v2_pkg\__init__.py
- Line 151: `idea.get('themes', [])`
- Line 229: `os.environ.get('OLLAMA_SERVERS', '')`
- Line 229: `os.environ.get('OLLAMA_SERVERS', '')`
- Line 385: `config.get('num_ctx', OLLAMA_NUM_CTX_DEFAULT)`
- Line 654: `idea.get('source_title', 'Unknown')`
- Line 655: `idea.get('source_description', '')`
- Line 656: `idea.get('source_comments', [])`
- Line 657: `idea.get('demand_signal', 0)`
- Line 658: `idea.get('is_foundational', False)`
- Line 1002: `scores.get('buildable_via_api', True)`
- Line 166: `idea.get('possible_duplicate_titles', [])`
- Line 168: `idea.get('unlocks', [])`
- Line 286: `data.get('models', [])`
- Line 306: `data.get('models', [])`
- Line 597: `idea.get('themes', [])`
- Line 955: `cluster.get(field, '')`
- Line 991: `scores.get(field, 5)`
- Line 1155: `EFFORT_MAP.get(cluster.get('effort', 'M'), 2)`
- Line 1176: `entry.get('name', '')`
- Line 1205: `cluster.get('api_feasibility', 5)`
- Additional records: 99

### scripts\mist_ideas_scraper_auth.py
- Line 315: `data.get('description', '')`
- Line 320: `data.get('title', '')`
- Line 324: `data.get('category', '')`
- Line 325: `data.get('status', '')`
- Line 326: `data.get('submitter', '')`
- Line 327: `data.get('submitter_url', '')`
- Line 328: `data.get('submit_date', '')`
- Line 329: `data.get('tags', '')`
- Line 322: `data.get('votes', 0)`
- Line 330: `data.get('comments', [])`
- Line 323: `data.get('comments', [])`

### scripts\mist_ideas_scraper_standalone.py
- Line 237: `data.get('title', '')`
- Line 238: `data.get('description', '')`
- Line 241: `data.get('category', '')`
- Line 242: `data.get('status', '')`
- Line 243: `data.get('submitter', '')`
- Line 244: `data.get('submitterUrl', '')`
- Line 245: `data.get('submitDate', '')`
- Line 246: `data.get('tags', '')`
- Line 239: `data.get('votes', 0)`
- Line 247: `data.get('comments', [])`
- Line 240: `data.get('comments', [])`
- Line 254: `data.get('description', '')`

### scripts\mist_scraper_receiver.py
- Line 177: `self.headers.get('Content-Length', 0)`
- Line 206: `row.get('url', '')`
- Line 224: `row.get('title', '')`

### scripts\probe_pk_strategy.py
- Line 185: `type_labels.get(strategy, strategy)`
- Line 406: `data.get('results', [])`
- Line 374: `strategy.get('type', 'unknown')`
- Line 424: `data.get('privileges', [])`
- Line 442: `target.get('id', '')`
- Line 520: `first.get('id', '')`
- Line 610: `os.environ.get('MIST_ORG_ID', '')`
- Line 610: `os.environ.get('MIST_ORG_ID', '')`
- Line 616: `os.environ.get('MIST_SITE_ID', '')`
- Line 616: `os.environ.get('MIST_SITE_ID', '')`
- Line 375: `counts.get(stype, 0)`
- Line 443: `target.get('name', '')`
- Line 439: `s.get('name', '')`

### scripts\probe_zscaler_endpoints.py
- Line 74: `doc.get('roles', [])`
- Line 98: `doc.get('proxy_hostnames', [])`
- Line 75: `role.get('fqdns', [])`

### scripts\report_stranded_branches.py
- Line 239: `raw.get('committer', {})`
- Line 137: `body.get('ahead_by', 0)`
- Line 136: `body.get('merge_base_commit', {})`

### scripts\scrape_mist_ideas_test.py
- Line 46: `anchor.get('href', '')`
- Line 60: `anchor.get('href', '')`

### specs\010-endpoint-usage-audit\_build_menu_map.py
- Line 84: `cs.get('containing_function', '')`
- Line 114: `cs.get('containing_function', 'unknown')`

### src\analytics\insight_metrics_utils.py
- Line 70: `row.get('scopes', '')`
- Line 71: `row.get('metric_name', '')`
- Line 205: `metric_data.get('rt', '')`
- Line 297: `metric_data.get('sites_data', [])`
- Line 131: `metric_data.get('metric_type', 'unknown')`
- Line 177: `metric_data.get('data_source', '')`
- Line 178: `metric_data.get('start', '')`
- Line 179: `metric_data.get('end', '')`
- Line 180: `metric_data.get('interval', '')`
- Line 181: `metric_data.get('limit', '')`
- Line 182: `metric_data.get('total_sites', '')`
- Line 183: `metric_data.get('page', '')`
- Line 184: `metric_data.get('sle_category', '')`
- Line 185: `metric_data.get('original_metric', '')`
- Line 186: `metric_data.get('roaming', '')`
- Line 187: `metric_data.get('total', '')`
- Line 188: `metric_data.get('totalTunnelCount', '')`
- Line 213: `metric_data.get(field_name, '')`

### src\analytics\site_analytics_configurator.py
- Line 163: `site.get('name', 'Unnamed Site')`
- Line 176: `settings.get('rtsa', {})`
- Line 191: `settings.get('rogue', {})`
- Line 206: `settings.get('engagement', {})`
- Line 217: `settings.get('analytic', {})`
- Line 232: `settings.get('occupancy', {})`
- Line 247: `settings.get('wifi', {})`
- Line 301: `current.get('dwell_tags', {})`
- Line 316: `current.get('dwell_tag_names', {})`
- Line 335: `current.get('hours', {})`

### src\analytics\site_inventory_health_analyzer.py
- Line 171: `device.get('id', '')`
- Line 172: `device.get('mac', '')`
- Line 93: `site.get('name', 'Unnamed Site')`
- Line 156: `device.get('site_id', '')`
- Line 176: `device.get('name', device_mac or device_id or 'Unknown')`
- Line 177: `device.get('model', 'Unknown')`
- Line 178: `device.get('serial', 'Unknown')`
- Line 218: `site_lookup.get(site_id, 'Unknown Site')`
- Line 285: `site_lookup.get(site_id, 'Unknown Site')`
- Line 159: `device.get('type', '')`

### src\analytics\zone_analyzer.py
- Line 386: `occupancy_analysis.get('total_sites', 0)`
- Line 387: `occupancy_analysis.get('analytic_enabled_count', 0)`
- Line 388: `occupancy_analysis.get('analytic_disabled_count', 0)`
- Line 455: `site.get('name', 'Unnamed Site')`
- Line 471: `data.get('engagement', {})`
- Line 503: `site.get('name', 'Unnamed Site')`
- Line 790: `data.get('engagement', {})`
- Line 791: `engagement.get('dwell_tags', {})`
- Line 792: `engagement.get('dwell_tag_names', {})`
- Line 793: `engagement.get('hours', {})`
- Line 883: `data.get('occupancy', {})`
- Line 884: `data.get('analytic', {})`
- Line 886: `analytic.get('enabled', False)`
- Line 895: `occupancy.get('min_duration', 'N/A')`
- Line 906: `zone_analysis.get('common_zones', set())`
- Line 920: `zone_analysis.get('sites_missing_common_zones', {})`
- Line 934: `zone_analysis.get('zone_count_deviations', {})`
- Line 952: `engagement_analysis.get('most_common_config', (None, []))`
- Line 953: `engagement_analysis.get('dwell_tag_configs', {})`
- Line 970: `engagement_analysis.get('sites_with_dwell_deviations', {})`
- Additional records: 109

### src\api\api_data_fetcher.py
- Line 225: `response.data.get('data', [])`
- Line 385: `item.get(field, '')`
- Line 372: `x.get(sort_key_str, '')`

### src\api\api_fetch_utils.py
- Line 96: `site.get('name', 'Unnamed Site')`
- Line 159: `site_name_lookup.get(site_id, 'Unknown')`
- Line 144: `row.get('name', 'Unnamed Site')`
- Line 77: `service.get('name', 'unnamed')`
- Line 78: `service.get('type', 'custom')`
- Line 79: `service.get('description', '')`

### src\api\tenant_fetch.py
- Line 193: `policy.get('tenants', [])`
- Line 196: `policy.get('services', [])`
- Line 224: `router.get('tenants', [])`
- Line 226: `router.get('tenant_profiles', {})`
- Line 255: `tmpl.get('name', 'unnamed')`
- Line 256: `tmpl.get('router', {})`
- Line 238: `network.get('tenants', {})`
- Line 262: `tmpl.get('networks', [])`

### src\audit\_renderer_html.py
- Line 223: `entry.get('timestamp', 0)`
- Line 225: `entry.get('message', '')`

### src\audit\_renderer_mermaid.py
- Line 87: `entry.get('timestamp', 0)`
- Line 88: `entry.get('message', '')`

### src\audit\analyzer.py
- Line 131: `entry.get('admin_id', 'unknown')`
- Line 132: `entry.get('timestamp', 0)`
- Line 165: `entry.get('message', '')`
- Line 181: `entry.get('timestamp', 0)`
- Line 182: `entry.get('admin_name', 'Unknown')`
- Line 184: `entry.get('before', {})`
- Line 185: `entry.get('after', {})`
- Line 104: `e.get('timestamp', 0)`
- Line 136: `entry.get('admin_name', 'Unknown')`

### src\audit\filter.py
- Line 107: `entry.get('before', {})`
- Line 108: `entry.get('after', {})`
- Line 45: `entry.get('message', '')`

### src\audit\time_parser.py
- Line 65: `UNIT_LABELS.get(unit, unit)`

### src\auth\interactive\login_orchestrator.py
- Line 178: `login_result.get('error', {})`
- Line 205: `login_result.get('error', 'Unknown error')`
- Line 209: `error_field.get('detail', str(error_field))`
- Line 200: `login_result.get('authenticated', False)`

### src\auth\interactive\msp_org_selector.py
- Line 26: `self.state.get('msp_privileges', [])`
- Line 99: `msp.get('msp_name', 'Unknown')`
- Line 225: `org.get('name', 'Unknown')`
- Line 90: `msp.get('msp_name', 'Unknown')`
- Line 91: `msp.get('role', 'unknown')`
- Line 183: `org.get('name', 'Unknown')`
- Line 184: `org.get('id', 'N/A')`
- Line 136: `org.get('name', '')`

### src\bootstrap\dependency_check.py
- Line 167: `self.package_import_map.get(name.lower(), name)`

### src\bootstrap\uv_runtime.py
- Line 47: `comparisons.get(operator, True)`

### src\capture\_packet_capture_exec.py
- Line 83: `result.get('id', 'unknown')`
- Line 84: `result.get('format', 'unknown')`
- Line 182: `result.get('id', 'unknown')`
- Line 183: `result.get('duration', 600)`
- Line 268: `capture.get('enabled', True)`
- Line 269: `capture.get('timestamp', 0)`
- Line 434: `msg.get('data', {})`
- Line 127: `details.get('detail', '')`
- Line 99: `result.get('duration', 600)`
- Line 88: `result.get('duration', 0)`
- Line 89: `result.get('expiry', 'unknown')`
- Line 206: `payload.get('duration', 60)`
- Line 424: `msg.get('data', {})`

### src\capture\_packet_capture_org.py
- Line 178: `mxedge.get('name', 'Unnamed MxEdge')`
- Line 179: `mxedge.get('id', 'No ID')`
- Line 180: `mxedge.get('model', 'Unknown')`
- Line 181: `stats_map.get(mxedge_id, {})`
- Line 193: `stat.get('status', 'unknown')`
- Line 194: `stat.get('uptime', 0)`
- Line 210: `stat.get('service_stat', {})`
- Line 288: `mxedge.get('id', '')`
- Line 289: `mxedge.get('name', 'Unnamed MxEdge')`
- Line 293: `stats_data.get('port_stat', {})`
- Line 400: `mxedge.get('id', '')`
- Line 439: `payload.get('duration', 0)`
- Line 440: `payload.get('num_packets', 0)`
- Line 444: `payload.get('format', 'stream')`
- Line 482: `result.get('id', 'unknown')`
- Line 489: `result.get('format', 'pcap')`
- Line 226: `port_info.get('speed', 0)`
- Line 228: `port_info.get('mac', 'N/A')`
- Line 501: `result.get('duration', 60)`
- Line 211: `service_stat.get('mxagent', {})`
- Additional records: 9

### src\capture\_packet_capture_prompts.py
- Line 177: `_BAND_MAP.get(choice, '5')`
- Line 181: `_CHANNEL_PROMPT.get(band, _CHANNEL_PROMPT['6'])`
- Line 207: `_BW_MAP.get(choice, '20')`
- Line 277: `result.get('id', 'unknown')`
- Line 278: `result.get('ap_count', 0)`
- Line 303: `error_details.get('detail', '')`
- Line 347: `payload.get('num_packets', 0)`
- Line 400: `payload.get(config_key, {})`
- Line 427: `payload.get('tcpdump_expression', '')`
- Line 353: `payload.get('includes_mcast', False)`
- Line 402: `mac_config.get('ports', {})`
- Line 284: `result.get('expiry', 'unknown')`
- Line 329: `payload.get('client_mac', 'N/A')`
- Line 337: `payload.get('duration', 0)`
- Line 386: `payload.get('ap_mac', 'N/A')`
- Line 387: `payload.get('band', 'N/A')`
- Line 388: `payload.get('channel', 'N/A')`
- Line 389: `payload.get('bandwidth', 'N/A')`
- Line 390: `payload.get('duration', 0)`
- Line 391: `payload.get('num_packets', 0)`
- Additional records: 4

### src\capture\multi_ap_scan_workflow.py
- Line 83: `_BAND_CHOICES.get(choice, _BAND_DEFAULT)`
- Line 89: `_CHANNEL_SPECS.get(band, _CHANNEL_SPECS['6'])`
- Line 114: `_BW_CHOICES.get(choice, _BW_DEFAULT)`
- Line 286: `result.get('id', 'unknown')`
- Line 287: `result.get('ap_count', len(ap_macs))`
- Line 305: `error_details.get('detail', '')`
- Line 293: `result.get('expiry', 'unknown')`

### src\capture\packet_capture.py
- Line 1306: `capture_data.get('id', 'unknown')`

### src\capture\packet_capture_download.py
- Line 158: `pcap.get('id', '')`
- Line 159: `pcap.get('pcap_url', '')`

### src\capture\site_capture_loop.py
- Line 40: `payload.get('duration', _DEFAULT_LOOP_DURATION)`

### src\config\runtime_settings.py
- Line 17: `os.getenv('MISTHELPER_DB_PATH', 'data/mist_data.db')`
- Line 13: `os.getenv('CSV_FRESHNESS_MINUTES', '15')`
- Line 15: `os.getenv('API_REQUEST_MAX_RETRIES', '3')`
- Line 16: `os.getenv('API_REQUEST_RETRY_DELAY', '5.0')`

### src\db\__init__.py
- Line 120: `os.environ.get(name, '')`
- Line 120: `os.environ.get(name, '')`
- Line 144: `os.environ.get('ARANGO_HOST', ARANGO_DEFAULT_URL)`
- Line 144: `os.environ.get('ARANGO_HOST', ARANGO_DEFAULT_URL)`
- Line 145: `os.environ.get('REDIS_HOST', REDIS_DEFAULT_HOST)`
- Line 145: `os.environ.get('REDIS_HOST', REDIS_DEFAULT_HOST)`
- Line 68: `os.environ.get('ARANGO_HOST', ARANGO_DEFAULT_URL)`
- Line 68: `os.environ.get('ARANGO_HOST', ARANGO_DEFAULT_URL)`
- Line 69: `os.environ.get('REDIS_HOST', REDIS_DEFAULT_HOST)`
- Line 69: `os.environ.get('REDIS_HOST', REDIS_DEFAULT_HOST)`
- Line 76: `os.environ.get('ARANGO_DATABASE', 'misthelper')`
- Line 76: `os.environ.get('ARANGO_DATABASE', 'misthelper')`
- Line 77: `os.environ.get('ARANGO_USERNAME', 'root')`
- Line 77: `os.environ.get('ARANGO_USERNAME', 'root')`
- Line 78: `os.environ.get('ARANGO_ROOT_PASSWORD', 'misthelper')`
- Line 78: `os.environ.get('ARANGO_ROOT_PASSWORD', 'misthelper')`
- Line 81: `os.environ.get('REDIS_PASSWORD', 'misthelper')`
- Line 81: `os.environ.get('REDIS_PASSWORD', 'misthelper')`
- Line 84: `os.environ.get('WEBHOOK_SECRET', '')`
- Line 84: `os.environ.get('WEBHOOK_SECRET', '')`
- Additional records: 4

### src\db\arango_writer.py
- Line 4023: `result.get('errors', 0)`
- Line 4029: `strategy.get('type', 'natural_pk')`
- Line 4030: `strategy.get('primary_key', ['id'])`
- Line 4042: `doc.get(primary_keys[0], str(uuid.uuid4()))`
- Line 4067: `mapping.get('edges', [])`
- Line 4099: `edge_config.get('to_col', '')`
- Line 4117: `edge_config.get('to_field', key_field)`
- Line 4122: `edge_config.get('to_col', '')`
- Line 4193: `mapping.get('ensure_target_vertices', [])`
- Line 4022: `result.get('created', 0)`
- Line 4022: `result.get('updated', 0)`
- Line 4100: `edge_config.get('to_key_lookup', '')`
- Line 4124: `to_key_lookup.get(str(v), str(v))`

### src\db\database_schema_utils.py
- Line 190: `builders.get(strategy['type'], DatabaseSchemaUtils._build_autoincrement_sql)`
- Line 202: `strategy.get('indexes', [])`

### src\db\redis_writer.py
- Line 29: `os.environ.get('REDIS_RAW_RETENTION_DAYS', '7')`
- Line 29: `os.environ.get('REDIS_RAW_RETENTION_DAYS', '7')`
- Line 33: `os.environ.get('REDIS_JSON_TTL_DAYS', '7')`
- Line 33: `os.environ.get('REDIS_JSON_TTL_DAYS', '7')`
- Line 145: `strategy.get('primary_key', [])`
- Line 410: `_TOPIC_KEY_PREFIX.get(topic, topic)`
- Line 566: `strategy.get('primary_key', [])`
- Line 80: `m.get('name', b'')`
- Line 626: `record.get(field, 'unknown')`

### src\db\retention.py
- Line 64: `os.environ.get(name, str(default))`
- Line 64: `os.environ.get(name, str(default))`
- Line 110: `stats.get('dataSize', 0)`

### src\db\router.py
- Line 173: `flags.get(backend, False)`
- Line 229: `strategy.get('type', DEFAULT_STRATEGY_TYPE)`
- Line 357: `self._strategies.get('default', DEFAULT_STRATEGY)`
- Line 379: `payload.get('after', payload)`
- Line 266: `strategy.get('primary_key', DEFAULT_PK_FIELDS)`
- Line 277: `record.get(pk_field, '')`
- Line 376: `payload.get('object_id', '')`
- Line 420: `config_record.get('device_id', config_record.get('mac', ''))`
- Line 381: `payload.get('object_type', UNKNOWN_ENTITY_TYPE)`
- Line 420: `config_record.get('mac', '')`

### src\device\_utility_commands_action.py
- Line 344: `data.get('password', str(response.data))`
- Line 230: `vc_data.get('is_virtual_chassis', False)`

### src\device\_utility_commands_selection.py
- Line 53: `self._uc.DEVICE_TYPE_COMPATIBILITY_MAP.get(command_name, [])`
- Line 107: `device_info.get('status', 'unknown')`
- Line 134: `stats.get('ports', [])`
- Line 138: `stats.get('if_stat', {})`
- Line 268: `stats.get('ports', [])`
- Line 336: `stats.get('if_stat', {})`
- Line 337: `stats.get('ip_stat', {})`
- Line 338: `stats.get('ports', [])`
- Line 177: `port.get('port_id', port.get('name', f'port_{index}'))`
- Line 178: `port.get('up', 'unknown')`
- Line 180: `port.get('speed', '')`
- Line 226: `if_stat.get(name, {})`
- Line 271: `stats.get('if_stat', {})`
- Line 280: `port.get('port_id', port.get('name', f'port_{idx}'))`
- Line 309: `if_stat.get(name, {})`
- Line 366: `p.get('port_id', p.get('name', ''))`
- Line 528: `net_cfg.get('ip', '')`
- Line 177: `port.get('name', f'port_{index}')`
- Line 280: `port.get('name', f'port_{idx}')`
- Line 366: `p.get('name', '')`
- Additional records: 2

### src\device\_utility_commands_websocket.py
- Line 305: `result.get('raw', '')`
- Line 319: `result.get('raw', '')`
- Line 323: `result.get('Output', '')`

### src\device\ap_profile_migration_manager.py
- Line 1471: `payload.get('outcome', 'unknown')`
- Line 297: `_pacing.get('delay_count', 0)`
- Line 298: `_pacing.get('delay_sum', 0.0)`
- Line 300: `_pacing.get('delay_max', 0.0)`
- Line 410: `payload.get('aps_planned', [])`
- Line 1219: `payload.get('migration_timestamp_utc', '')`
- Line 1221: `payload.get('source_profile_id', '')`
- Line 1222: `payload.get('target_profile_id', '')`
- Line 1469: `payload.get('aps_planned', [])`
- Line 1470: `payload.get('aps_reassigned', [])`
- Line 1494: `pacing_stats.get('delay_count', 0)`
- Line 1495: `pacing_stats.get('delay_sum', 0.0)`
- Line 1497: `pacing_stats.get('delay_max', 0.0)`
- Line 1612: `payload.get('aps_reassigned', [])`
- Line 311: `final_payload.get('outcome', 'unknown')`
- Line 442: `payload.get('aps_reassigned', [])`
- Line 453: `payload.get('aps_planned', [])`
- Line 455: `payload.get('aps_reassigned', [])`
- Line 1054: `site.get('id', '')`
- Line 1057: `site.get('name', '')`
- Additional records: 17

### src\device\arp_command_manager.py
- Line 190: `msg.get('data', '{}')`
- Line 192: `data_obj.get('data', {})`
- Line 223: `inner_data.get('raw', '')`

### src\device\device_reboot_manager.py
- Line 407: `response.data.get('status', f'SUCCESS - {response.data}')`
- Line 211: `row.get('id', '')`
- Line 212: `row.get('name', '')`
- Line 213: `row.get('site_id', '')`
- Line 153: `row.get('name', '')`
- Line 154: `row.get('id', '')`
- Line 277: `id_to_name.get(gateway_template_id, 'Unknown')`
- Line 230: `row.get('site_id', '')`
- Line 271: `row.get('gatewaytemplate_id', '')`
- Line 275: `row.get('id', '')`
- Line 276: `row.get('name', '')`
- Line 231: `row.get('type', '')`

### src\device\device_utils.py
- Line 106: `device.get(key, '')`

### src\device\prompt_utils.py
- Line 255: `device.get('name', 'Unknown')`
- Line 405: `response.data.get('results', [])`
- Line 456: `device_config_response.data.get('port_config', {})`
- Line 530: `port_cfg.get('usage', '')`
- Line 531: `port_cfg.get('duplex', 'N/A')`
- Line 654: `port_to_config.get(port_name, {})`
- Line 655: `port_cfg.get('port_profile', 'N/A')`
- Line 656: `port_cfg.get('description', '')`
- Line 323: `device.get('name', 'Unknown')`
- Line 373: `dev.get('mac', '')`
- Line 436: `stats_data.get('port_stat', {})`
- Line 534: `port_cfg.get('speed', 'N/A')`
- Line 649: `port_info.get('up', False)`
- Line 650: `port_info.get('speed', 'N/A')`
- Line 652: `port_info.get('duplex', '')`
- Line 652: `port_info.get('full_duplex', False)`
- Line 692: `mapping.get(duplex_value.lower(), str(duplex_value).capitalize())`
- Line 377: `dev.get('name', 'Unknown')`
- Line 551: `port_info.get('up', False)`
- Line 581: `port_info.get('_fallback', False)`
- Additional records: 6

### src\device\utility_commands.py
- Line 164: `self.__dict__.get('_clusters', ())`
- Line 70: `data.get('detail', '')`

### src\device\virtual_chassis.py
- Line 567: `switch.get('name', '')`
- Line 568: `switch.get('site_name', '')`
- Line 577: `switch.get('site_id', '')`
- Line 578: `switch.get('id', '')`
- Line 579: `switch.get('name', '')`
- Line 580: `switch.get('site_name', '')`
- Line 804: `switch.get('type', '')`
- Line 897: `switch.get('vc_mac', '')`
- Line 898: `switch.get('site_id', '')`
- Line 900: `site_id_to_name.get(site_id, 'Unknown Site')`
- Line 314: `target.selected.get('name', '')`
- Line 817: `switch.get('name', '')`
- Line 798: `switch.get('name', '')`
- Line 809: `switch.get('id', '')`
- Line 827: `switch.get('vc_mac', '')`
- Line 914: `row.get('site_id', '')`
- Line 998: `switch.get('vc_mac', '')`
- Line 447: `site_data.get('name', site_id)`
- Line 693: `row.get('name', '')`
- Line 693: `row.get('id', '')`
- Additional records: 23

### src\export\const_definitions_exporter.py
- Line 414: `model_item.get('model', model_item.get('name', ''))`
- Line 414: `model_item.get('name', '')`
- Line 712: `metric_details.get('description', '')`
- Line 713: `metric_details.get('type', '')`
- Line 714: `metric_details.get('unit', '')`
- Line 529: `item.get('name', '')`
- Line 715: `metric_details.get('scopes', [])`
- Line 716: `metric_details.get('report_scopes', [])`
- Line 717: `metric_details.get('intervals', {})`
- Line 718: `metric_details.get('report_intervals', {})`
- Line 731: `interval_data.get('interval', 'N/A')`
- Line 731: `interval_data.get('max_age', 'N/A')`
- Line 743: `interval_data.get('interval', 'N/A')`
- Line 402: `model_details.get('type', '')`
- Line 417: `model_item.get('type', '')`

### src\export\data_exporter.py
- Line 333: `cls._last_snapshot_times.get(api_function_name, 0.0)`
- Line 201: `os.getenv('MISTHELPER_STANDALONE', '')`
- Line 427: `row.get(field_name, '')`
- Line 507: `entry.get(sort_key, '')`

### src\export\device_events_52w_exporter.py
- Line 339: `row.get(key, '')`

### src\export\endpoint_catalog.py
- Line 56: `SAFETY_LABELS.get(self.safety, self.safety)`

### src\export\msp_inventory_exporter.py
- Line 178: `msp_info.get('msp_name', 'Unknown MSP')`
- Line 298: `org.get('name', 'Unknown Org')`
- Line 273: `site_lookup.get(site_id, 'Unknown Site')`
- Line 279: `device.get('type', 'unknown')`
- Line 280: `type_counts.get(device_type, 0)`
- Line 334: `s.get('name', 'Unknown')`
- Line 366: `device.get(field, '')`
- Line 372: `x.get('type', '')`
- Line 369: `x.get('_msp_name', '')`
- Line 370: `x.get('_org_name', '')`
- Line 371: `x.get('_site_name', '')`
- Line 373: `x.get('name', '')`

### src\export\org_client_security_exporter.py
- Line 189: `site.get('name', 'Unknown Site')`

### src\export\org_config_exporter.py
- Line 202: `org.get('name', 'Unknown')`
- Line 203: `org.get('id', 'N/A')`

### src\export\org_device_stats_exporter.py
- Line 130: `site.get('name', 'Unknown')`
- Line 161: `row.get('name', 'Unknown')`
- Line 323: `row.get('mac', '')`

### src\export\org_inventory_exporter.py
- Line 586: `site_lookup.get(site_id, {'name': 'Unknown', 'address': 'Unknown'})`
- Line 218: `d.get('vc_mac', '')`
- Line 288: `device.get('site_name', '')`
- Line 289: `device.get('serial', '')`
- Line 290: `device.get('mac', '')`
- Line 291: `device.get('model', '')`
- Line 293: `device.get('street', '')`
- Line 295: `device.get('city', '')`
- Line 296: `device.get('state', '')`
- Line 297: `device.get('country', 'US')`
- Line 298: `device.get('zip_code', '')`
- Line 388: `device.get('serial', '')`
- Line 389: `device.get('mac', '')`
- Line 390: `device.get('model', '')`
- Line 391: `device.get('street', '')`
- Line 392: `device.get('city', '')`
- Line 393: `device.get('state', '')`
- Line 394: `device.get('zip_code', '')`
- Line 567: `device.get('mac', '')`
- Line 730: `site_lookup.get(site_id, {'name': 'Unknown', 'address': 'Unknown'})`
- Additional records: 18

### src\export\org_sec_intel_profile_exporter.py
- Line 95: `profile.get('id', 'unknown')`
- Line 206: `chosen.get('id', '')`

### src\export\org_webhook_deliveries_exporter.py
- Line 33: `webhook.get('id', '')`
- Line 50: `webhook.get('name', '(unnamed)')`
- Line 50: `webhook.get('id', '?')`

### src\export\site_anomaly_exporter.py
- Line 260: `site_data.get('name', site_id)`
- Line 288: `client.get('hostname', client.get('name', 'Unknown'))`
- Line 288: `client.get('name', 'Unknown')`

### src\export\site_config_exporter.py
- Line 81: `row.get('ssid', '')`

### src\export\site_device_exporter.py
- Line 64: `x.get('model', '')`
- Line 97: `item.get(field, '')`
- Line 78: `d.get('type', '')`

### src\export\site_export_utils.py
- Line 167: `item.get(field, '')`
- Line 334: `payload.get('enabled', [])`
- Line 335: `payload.get('supported', [])`
- Line 156: `x.get(sort_key, '')`

### src\export\site_insights\device_metric_operation.py
- Line 107: `device_info.get('model', '')`
- Line 145: `site_data.get('name', site_id)`
- Line 180: `device.get('model', '')`

### src\export\site_insights\site_metric_operation.py
- Line 119: `site_data.get('name', site_id)`

### src\export\site_webhook_deliveries_exporter.py
- Line 107: `chosen.get('id', '')`
- Line 107: `chosen.get('name', chosen.get('id', 'webhook'))`
- Line 74: `wh.get('name', '(unnamed)')`
- Line 74: `wh.get('id', '?')`
- Line 107: `chosen.get('id', 'webhook')`

### src\export\sites_by_ap_model_exporter.py
- Line 111: `site_map.get(site_id, {})`
- Line 112: `site.get('address', '')`
- Line 115: `site.get('name', '')`
- Line 36: `d.get('model', '')`
- Line 123: `d.get('mac', '')`
- Line 97: `site_map.get(x[0], {})`

### src\export\wan_client_events_exporter.py
- Line 236: `row.get('name', _UNKNOWN_SITE)`

### src\export\wifi_clients_exporter.py
- Line 134: `row.get('name', _UNKNOWN_SITE)`
- Line 262: `row.get('start_time', 0)`

### src\firmware\aggregate_upgrade_service.py
- Line 607: `result.data.get('site_upgrades', result.data.get('upgrades', []))`
- Line 874: `record.get('children', [])`
- Line 916: `record.get('children', [])`
- Line 139: `record.get('operation_id', '')`
- Line 161: `record.get('operation_id', '')`
- Line 163: `record.get('operation_id', '')`
- Line 180: `record.get('operation_id', '')`
- Line 185: `record.get('operation_id', '')`
- Line 201: `record.get('operation_id', '')`
- Line 214: `record.get('operation_id', '')`
- Line 216: `record.get('operation_id', '')`
- Line 444: `outcome.get('route', '')`
- Line 450: `outcome.get('status', 'unknown')`
- Line 505: `candidate.get('children', [])`
- Line 570: `child.get('child_id', '')`
- Line 570: `child.get('route', '')`
- Line 577: `outcome.get('status', 'unknown')`
- Line 607: `result.data.get('upgrades', [])`
- Line 642: `status.get('raw_status', 0)`
- Line 644: `status.get('status_known', True)`
- Additional records: 20

### src\firmware\bulk_ap_upgrader.py
- Line 703: `version_info.get('version', 'Unknown')`
- Line 711: `version_info.get('models', [])`
- Line 837: `entry.get('version', 'Unknown')`
- Line 1667: `device.get('id', 'Unknown')`
- Line 1758: `model_info.get('model', '')`
- Line 1761: `model_info.get('ap_type', 'unknown')`
- Line 2001: `version_info.get('version', '')`
- Line 628: `ap.get('model', 'Unknown')`
- Line 805: `entry.get('models', [])`
- Line 815: `entry.get('version', 'Unknown')`
- Line 920: `self.ap_versions.get(device_id, 'Unknown')`
- Line 1022: `download_strategies.get(download_choice, download_strategies['3'])`
- Line 1043: `reboot_strategies.get(reboot_choice, reboot_strategies['4'])`
- Line 1672: `device.get('name', 'Unnamed')`
- Line 1673: `device.get('mac', 'Unknown')`
- Line 1674: `device.get('model', 'Unknown')`
- Line 1675: `self.ap_versions.get(device_id, 'Unknown')`
- Line 2004: `version_info.get('models', [])`
- Line 259: `s.get('name', '?')`
- Line 391: `s.get('name', '?')`
- Additional records: 24

### src\firmware\bulk_switch_upgrader.py
- Line 148: `org_info.data.get('name', 'Unknown')`
- Line 865: `site_info.get('id', '')`
- Line 866: `site_info.get('name', 'Unknown Site')`
- Line 232: `site.get('name', 'Unnamed')`
- Line 233: `site.get('id', 'Unknown')`
- Line 531: `row.get('record_md5', '')`
- Line 532: `row.get('_short', '')`
- Line 596: `entry.get('version', '')`
- Line 597: `entry.get('model', '')`
- Line 598: `entry.get('record_id', '')`
- Line 599: `entry.get('record_size', '')`
- Line 600: `entry.get('record_md5', '')`
- Line 601: `entry.get('_short', '')`
- Line 736: `self.compatible_versions.get(version, [])`
- Line 1119: `result.get('error', 'Unknown error')`

### src\firmware\firmware_manager.py
- Line 583: `details.get('enable_p2p', False)`
- Line 602: `details.get('targets', {})`
- Line 612: `details.get('upgrades', [])`
- Line 693: `fwupdate.get('status', 'unknown')`
- Line 694: `fwupdate.get('progress', 0)`
- Line 695: `fwupdate.get('timestamp', 0)`
- Line 821: `template_sites_mapping.get(template_id, [])`
- Line 2470: `gw.get('model', '')`
- Line 2711: `gw.get('type', '')`
- Line 2712: `gw.get('model', '')`
- Line 2737: `site.get('name', 'Unknown')`
- Line 2795: `device.get('model', '')`
- Line 2843: `info.get('version', '')`
- Line 2865: `info.get('version', 'unknown')`
- Line 2866: `info.get('model', 'unknown')`
- Line 3034: `site.get('name', 'Unknown')`
- Line 3154: `upgrade_config.get('ssr_models', ['SSR', '128T'])`
- Line 3382: `template_sites_mapping.get(selected_template_id, [])`
- Line 3573: `device_stats.get('site_id', 'Unknown')`
- Line 3588: `device_stats.get('fwupdate', {})`
- Additional records: 111

### src\firmware\org_ap_upgrader.py
- Line 598: `msp.get('msp_name', 'Unknown')`
- Line 1673: `version_entry.get('models', [])`
- Line 1819: `strategies.get(choice, 'big_bang')`
- Line 1836: `strategies.get(choice, 'big_bang')`
- Line 1896: `self.upgrade_config.get('use_site_local_time', False)`
- Line 2393: `self.upgrade_config.get('use_site_local_time', False)`
- Line 2553: `self.upgrade_config.get('use_site_local_time', False)`
- Line 120: `cfg.get('dry_run', False)`
- Line 1242: `ap.get('model', 'Unknown')`
- Line 1335: `d.get('name', d.get('mac', 'unnamed'))`
- Line 1585: `version_info.get('version', 'Unknown')`
- Line 1705: `version_entry.get('version', '')`
- Line 2144: `self.upgrade_config.get('use_site_local_time', False)`
- Line 2721: `self.upgrade_config.get('p2p_cluster_size', 5)`
- Line 2722: `self.upgrade_config.get('p2p_parallelism', 100)`
- Line 1193: `site.get('name', 'Unknown')`
- Line 1335: `d.get('mac', 'unnamed')`
- Line 1382: `version_counts.get(version, 0)`
- Line 1513: `self.ap_versions.get(d.get('mac'), 'Unknown')`
- Line 1555: `d.get('name', d.get('mac', 'unnamed')[:8])`
- Additional records: 18

### src\firmware\org_upgrade_body.py
- Line 76: `request.get('strategy', STRATEGY_DEFAULT)`
- Line 112: `request.get('all_sites', False)`
- Line 114: `request.get('device_type', DEVICE_TYPE_AP)`
- Line 116: `request.get('strategy', STRATEGY_DEFAULT)`

### src\firmware\org_upgrade_service.py
- Line 174: `headers.get('Content-Type', headers.get('content-type'))`

### src\firmware\running_version.py
- Line 166: `device_row.get('id', 'unknown')`

### src\firmware\site_auto_upgrade.py
- Line 1227: `day_map.get(choice, 'any')`
- Line 1362: `site.get('name', 'Unknown')`
- Line 1530: `_MSP_DAY_MAP.get(day_input, 'any')`
- Line 1566: `reference_org.get('name', 'Unknown')`
- Line 1772: `shared_schedule.get('time_of_day', '02:00')`
- Line 425: `settings.get('auto_upgrade', {})`
- Line 441: `auto_upgrade.get('custom_versions', {})`
- Line 626: `self.schedule.get('day_of_week', 'daily')`
- Line 629: `self.schedule.get('time_of_day', 'any time')`
- Line 1070: `model_version_map.get(model, [])`
- Line 1328: `schedule.get('day_of_week', 'any')`
- Line 1329: `schedule.get('time_of_day', 'any')`
- Line 1622: `entry.get('tag', '')`
- Line 1654: `model_version_map.get(model, [])`
- Line 277: `self.schedule.get('day_of_week', 'any')`
- Line 278: `self.schedule.get('time_of_day', '02:00')`
- Line 1135: `ctx.model_version_map.get(model, [])`
- Line 1201: `first.get('version', '')`
- Line 177: `cfg.get('dry_run', False)`
- Line 1191: `entry.get('version', '')`
- Additional records: 5

### src\firmware\upgrade_service.py
- Line 630: `device.get('type', '')`
- Line 631: `device.get('model', '')`
- Line 1611: `payload.get('status', '')`
- Line 1694: `row.get('model', '')`
- Line 1695: `row.get('version', '')`
- Line 1719: `device.get('model', '')`
- Line 1709: `device.get('model', '')`
- Line 1744: `row.get('version', '')`
- Line 1708: `device.get('device_type', device.get('type', ''))`
- Line 1708: `device.get('type', '')`

### src\gateway\_wan2_variable_device.py
- Line 167: `config.get('port_config', {})`
- Line 254: `config.get('port_config', {})`
- Line 98: `site.get('name', '')`
- Line 102: `site.get('id', '')`
- Line 103: `site.get('gatewaytemplate_id', '')`
- Line 162: `device.get('id', '')`
- Line 163: `device.get('name', '')`

### src\gateway\_wan2_variable_io.py
- Line 116: `site.get('gatewaytemplate_id', '')`
- Line 118: `counts.get(tid, 0)`
- Line 88: `s.get('name', '')`

### src\gateway\_wan2_variable_selection.py
- Line 42: `tmpl.get('id', '')`
- Line 43: `tmpl.get('name', 'Unnamed Template')`
- Line 44: `site_counts.get(tid, 0)`
- Line 28: `t.get('name', 'Unnamed Template')`

### src\gateway\_wan2_variable_template.py
- Line 60: `config.get('port_config', {})`

### src\gateway\device_template_cloner.py
- Line 483: `gateway.get('model', 'SRX300')`
- Line 183: `device.get('model', 'Unknown')`
- Line 184: `device.get('name', device.get('mac', 'Unknown'))`
- Line 238: `t.get('name', '')`
- Line 426: `template.get('id', 'unknown')`
- Line 438: `new_template.get('id', '')`
- Line 439: `new_template.get('name', '')`
- Line 440: `new_template.get('type', '')`
- Line 441: `device_info.get('id', '')`
- Line 442: `device_info.get('name', device_info.get('mac', ''))`
- Line 443: `device_info.get('model', '')`
- Line 444: `device_info.get('site_id', '')`
- Line 155: `site.get('name', 'Unknown')`
- Line 155: `site.get('id', '')`
- Line 184: `device.get('mac', 'Unknown')`
- Line 186: `device.get('id', '')`
- Line 442: `device_info.get('mac', '')`

### src\gateway\gateway_export_utils.py
- Line 179: `template_lookup.get(template_id, NO_TEMPLATE_LABEL)`
- Line 184: `device.get('name', UNKNOWN_GATEWAY)`
- Line 185: `device.get('site_id', '')`
- Line 186: `device.get('site_name', UNKNOWN_SITE)`
- Line 190: `site_info.get('gatewaytemplate_id', '')`
- Line 188: `device.get('connected', '')`
- Line 211: `row.get(col, '')`
- Line 271: `site.get('name', UNKNOWN_SITE)`
- Line 248: `row.get('name', UNKNOWN_SITE)`
- Line 258: `device.get('site_id', '')`
- Line 259: `device.get('id', '')`
- Line 260: `device.get('name', '')`
- Line 261: `site_name_lookup.get(device.get('site_id', ''), UNKNOWN_SITE)`
- Line 281: `device.get('site_id', '')`
- Line 282: `device.get('id', '')`
- Line 283: `device.get('name', '')`
- Line 284: `site_name_lookup.get(device.get('site_id', ''), UNKNOWN_SITE)`
- Line 366: `template.get('name', 'Unknown Template')`
- Line 369: `config.get('gateway_mgmt_overlay_ip_ip', '')`
- Line 261: `device.get('site_id', '')`
- Additional records: 1

### src\gateway\gateway_ha_exporter.py
- Line 132: `gateway.get('id', '')`
- Line 116: `ha_data.get('nodes', [])`
- Line 163: `row.get('node_name', '')`
- Line 164: `row.get('status', '')`
- Line 162: `row.get('name', '')`

### src\gateway\gateway_stats_exporter.py
- Line 387: `row.get('device_name', row.get('name', f'Device_{index}'))`
- Line 388: `row.get('site_name', UNKNOWN_SITE_NAME)`
- Line 387: `row.get('name', f'Device_{index}')`
- Line 461: `row.get('device_name', UNKNOWN_LABEL)`
- Line 483: `record.get('device_name', UNKNOWN_LABEL)`
- Line 484: `record.get('site_name', UNKNOWN_SITE_NAME)`
- Line 489: `record.get('port_name', UNKNOWN_LABEL)`
- Line 490: `record.get('port_ip', UNKNOWN_LABEL)`
- Line 493: `record.get('conflict_with_ports', UNKNOWN_LABEL)`
- Line 457: `x.get('device_name', '')`
- Line 457: `x.get('port_name', '')`

### src\gateway\overrides\device_data_fetcher.py
- Line 108: `device_config_data.get('port_config', {})`
- Line 127: `stats_data.get('if_stat', {})`

### src\gateway\overrides\override_classifier.py
- Line 59: `port_config.get('ip_config', {})`
- Line 60: `ip_config.get('type', '')`
- Line 62: `port_config.get('disabled', False)`
- Line 90: `port_config.get('description', '')`
- Line 93: `ip_config.get('gateway', '')`
- Line 94: `ip_config.get('ip', '')`
- Line 95: `ip_config.get('netmask', '')`
- Line 97: `port_config.get('usage', '')`
- Line 116: `device_info.get('device_id', '')`
- Line 61: `interface_stat.get('up', False)`

### src\gateway\overrides\wan_override_walker.py
- Line 175: `site_to_template.get(site_id, '')`
- Line 118: `site.get('id', '')`
- Line 118: `site.get('name', 'Unknown Site')`
- Line 120: `site.get('id', '')`
- Line 120: `site.get('gatewaytemplate_id', '')`
- Line 123: `template.get('id', '')`
- Line 123: `template.get('name', 'Unknown Template')`
- Line 176: `template_lookup.get(template_id, 'No Template')`
- Line 222: `site_lookup.get(site_id, 'Unknown Site')`
- Line 238: `cache.get(device_id, ({}, {}))`
- Line 160: `row.get('name', '')`
- Line 161: `row.get('site_id', '')`
- Line 162: `row.get('id', '')`
- Line 243: `port_configs.get(port_name, {})`
- Line 244: `interface_stats.get(port_name, {})`

### src\gateway\template_config.py
- Line 775: `template_config.get('path_preferences', {})`
- Line 845: `extraction_data.get('configurations', {})`
- Line 1052: `template_config.get('service_policies', [])`
- Line 226: `template.get('name', 'Unnamed Template')`
- Line 253: `template.get('name', 'Unnamed')`
- Line 267: `template.get('name', 'Unnamed')`
- Line 414: `template.get('id', '')`
- Line 415: `template.get('name', 'Unnamed')`
- Line 533: `source.get('name', 'Unnamed')`
- Line 546: `source.get('name', 'Unnamed')`
- Line 654: `template_map.get(target_name, '')`
- Line 754: `template.get('name', 'Unnamed Template')`
- Line 755: `template.get('type', 'standalone')`
- Line 792: `template.get('name', 'Unnamed')`
- Line 860: `dia_pico.get('strategy', 'Unknown')`
- Line 861: `dia_pico.get('paths', [])`
- Line 846: `configs.get('traffic_steering', {})`
- Line 847: `configs.get('application_policies', {})`
- Line 1281: `site.get('address', '')`
- Line 1282: `site.get('country_code', '')`
- Additional records: 8

### src\gateway\wan2_migration_manager.py
- Line 412: `context.device_ip.get('ip_type', '')`
- Line 482: `self.site_to_template_id.get(site_id, '')`
- Line 483: `self.template_port_configs.get(template_id, {})`
- Line 484: `template_config.get('ip_type', 'unknown')`
- Line 502: `IP_TYPE_SEVERITY.get((template_ip_type, device_ip_type), 'UNKNOWN')`
- Line 516: `site.get('id', '')`
- Line 517: `site.get('name', 'Unnamed Site')`
- Line 578: `detail.get('port_identifier', BASE_PORT_IDENTIFIER)`
- Line 607: `current_settings.get('vars', {})`
- Line 115: `payload.get('type', '')`
- Line 119: `payload.get('ip', '')`
- Line 120: `payload.get('netmask', '')`
- Line 121: `payload.get('gateway', '')`
- Line 252: `site.get('name', 'Unnamed Site')`
- Line 253: `site.get('id', '')`
- Line 399: `device_ip_info.get('port_identifier', '')`
- Line 417: `context.device_ip.get('port_identifier', BASE_PORT_IDENTIFIER)`
- Line 420: `context.device_ip.get('ip', '')`
- Line 421: `context.device_ip.get('netmask', '')`
- Line 422: `context.device_ip.get('gateway', '')`
- Additional records: 29

### src\gateway\wan2_variable.py
- Line 120: `self.__dict__.get('_clusters', ())`

### src\gateway\wan_probe_device_override_manager.py
- Line 25: `os.getenv('MIST_WAN_PROBE_IPS', '192.151.29.254,18.154.184.32')`
- Line 27: `os.getenv('MIST_WAN_PROBE_PROFILE', 'lte')`
- Line 374: `device.get('port_config', {})`
- Line 534: `device_config.get('port_config', {})`
- Line 381: `device.get('id', '')`
- Line 382: `device.get('name', 'Unknown Device')`
- Line 395: `port_settings.get('wan_probe_override', {})`
- Line 218: `template.get('id', '')`
- Line 219: `template.get('name', 'Unnamed Template')`
- Line 220: `counts.get(template.get('id', ''), 0)`
- Line 288: `site.get('id', '')`
- Line 288: `site.get('name', 'Unknown Site')`
- Line 220: `template.get('id', '')`
- Line 231: `site.get('gatewaytemplate_id', '')`
- Line 233: `counts.get(template_id, 0)`
- Line 240: `site.get('name', '')`
- Line 305: `site.get('gatewaytemplate_id', '')`
- Line 401: `current_probe.get('ips', [])`
- Line 402: `current_probe.get('probe_profile', '')`
- Line 214: `t.get('name', '')`

### src\input\prompt_client_utils.py
- Line 165: `client.get('hostname', client.get('username', 'Unknown'))`
- Line 166: `client.get('connection_type', 'Unknown')`
- Line 91: `data.get('results', [])`
- Line 110: `client.get('mac', 'Unknown')`
- Line 111: `client.get('ip', 'Unknown')`
- Line 112: `client.get('connection_type', 'Unknown')`
- Line 165: `client.get('username', 'Unknown')`
- Line 109: `client.get('hostname', client.get('username', 'Unknown'))`
- Line 113: `client.get('ssid', 'N/A')`
- Line 109: `client.get('username', 'Unknown')`
- Line 113: `client.get('vlan_id', 'N/A')`
- Line 45: `x.get('hostname', '')`
- Line 45: `x.get('username', '')`

### src\inventory\csv_comparator.py
- Line 323: `os.getenv('END_CUSTOMER_NAME', '')`
- Line 324: `os.getenv('END_CUSTOMER_ACCOUNT_ID', '')`
- Line 645: `device.get('site_name', '')`
- Line 899: `self.comparison_address_lookup.get(device_serial, {})`
- Line 1225: `recommendation_icon.get(result['recommendation'], result['recommendation'])`
- Line 1255: `result.get('recommendation_reason', 'No reason provided')`
- Line 325: `os.getenv('ADDRESS_MATCH_THRESHOLD', '75')`
- Line 607: `device.get('site_name', '')`
- Line 930: `device.get('site_id', '')`
- Line 931: `device.get('site_name', '')`
- Line 932: `device.get('id', '')`
- Line 952: `device.get('site_id', '')`
- Line 953: `device.get('site_name', '')`
- Line 954: `device.get('id', '')`
- Line 1164: `os.getenv('ADDRESS_VALIDATION_TIMEOUT', '10')`
- Line 1328: `device.get('created_time', 0)`
- Line 1378: `config.device.get('site_name', '')`
- Line 1380: `config.device.get('model', '')`
- Line 572: `row.get(self.address_field, '')`
- Line 573: `row.get(self.city_field, '')`
- Additional records: 37

### src\inventory\inventory_summary\pivot_renderer.py
- Line 47: `row.get('count', 0)`
- Line 119: `model_type.get(model, '')`

### src\inventory\inventory_summary\version_per_model_fetcher.py
- Line 191: `model_row.get('device_type', '')`
- Line 192: `model_row.get('model', '')`
- Line 36: `row.get('device_type', '')`
- Line 37: `row.get('model', '')`
- Line 98: `counts.get(key, 0)`
- Line 116: `counts.get(key, 0)`
- Line 215: `version_counts.get(version, 0)`
- Line 239: `version_counts.get(version, 0)`
- Line 38: `row.get('count', 0)`

### src\inventory\org_device_inventory_msp.py
- Line 271: `chosen.get('id', '')`
- Line 475: `org_record.get('id', '')`
- Line 476: `org_record.get('name', child_org_id)`
- Line 302: `row.get('count', 0)`
- Line 317: `ver_counts.get('device_type', '')`
- Line 320: `ver_counts.get(version, 0)`
- Line 333: `ver_counts.get(version, 0)`
- Line 338: `ver_counts.get('device_type', '')`
- Line 516: `active_msp.get('msp_name', 'MSP')`
- Line 99: `org.get('name', org.get('id', 'Unknown'))`
- Line 158: `row.get('model', '')`
- Line 159: `row.get('count', 0)`
- Line 174: `row.get('version', '')`
- Line 175: `row.get('count', 0)`
- Line 301: `row.get('device_type', '')`
- Line 99: `org.get('id', 'Unknown')`

### src\inventory\org_device_inventory_summary.py
- Line 77: `page_data.get('results', [])`
- Line 99: `counts.get(value, 0)`
- Line 133: `counts.get(value, 0)`
- Line 172: `counts.get(value, 0)`
- Line 213: `counts.get((device_type, value), 0)`
- Line 230: `row.get('device_type', '')`
- Line 230: `row.get(distinct, '')`
- Line 340: `row.get(distinct, '')`
- Line 234: `row.get('count', 0)`
- Line 337: `row.get('device_type', '')`
- Line 337: `row.get(distinct, '')`
- Line 337: `row.get('count', 0)`
- Line 296: `row.get('device_type', '')`
- Line 103: `row.get('count', 0)`
- Line 137: `row.get('count', 0)`
- Line 176: `row.get('count', 0)`
- Line 296: `row.get('count', 0)`

### src\maps\_container_detection.py
- Line 51: `os.environ.get(explicit_var, '')`
- Line 51: `os.environ.get(explicit_var, '')`

### src\maps\_flask_viewer.py
- Line 148: `map_response.data.get('url', '')`
- Line 169: `image_response.headers.get(_CONTENT_TYPE_HEADER, _DEFAULT_IMAGE_MIMETYPE)`
- Line 93: `r.get('name', _UNNAMED)`
- Line 116: `x.get('name', '')`

### src\maps\_maps_backup.py
- Line 231: `geometry.get(path_key, {})`
- Line 237: `backup.get(key, [])`

### src\maps\_maps_clone.py
- Line 133: `source_map.get('type', 'image')`
- Line 120: `source_map.get('name', 'Map')`
- Line 260: `zone.get('name', 'Unnamed Zone')`
- Line 262: `zone.get('vertices', [])`
- Line 108: `source_map.get('name', 'Unnamed')`
- Line 109: `source_map.get('type', 'N/A')`
- Line 110: `source_map.get('width', 'N/A')`
- Line 110: `source_map.get('height', 'N/A')`
- Line 111: `source_map.get('ppm', 'N/A')`
- Line 325: `clone_payload.get('width', 'N/A')`
- Line 325: `clone_payload.get('height', 'N/A')`
- Line 326: `clone_payload.get('ppm', 'N/A')`

### src\maps\_maps_coverage.py
- Line 482: `map_data.get('url', '')`
- Line 82: `device.get('name', device.get('mac', 'Unknown'))`
- Line 83: `device.get('type', 'ap')`
- Line 84: `device.get('status', 'unknown')`
- Line 85: `device.get('mac', '')`
- Line 86: `device.get('orientation', 0)`
- Line 92: `zone.get('name', 'Zone')`
- Line 92: `zone.get('vertices', [])`
- Line 100: `client.get('mac', 'Unknown')`
- Line 101: `client.get('ssid', '-')`
- Line 111: `client.get('mac', 'Unknown')`
- Line 112: `client.get('manufacture', '-')`
- Line 121: `device.get('mac', 'Unknown')`
- Line 130: `asset.get('name', 'Asset')`
- Line 131: `asset.get('mac', '-')`
- Line 140: `client.get('name', '')`
- Line 141: `client.get('uuid', '-')`
- Line 315: `coverage_data.get('results', [])`
- Line 316: `coverage_data.get('result_def', [])`
- Line 367: `map_data.get('ppm', _DEFAULT_PPM)`
- Additional records: 7

### src\maps\_maps_matplotlib.py
- Line 302: `device.get('type', _UNKNOWN_TYPE)`
- Line 370: `site.get('id', '')`
- Line 371: `site.get('name', _UNKNOWN_NAME)`
- Line 247: `target_map.get('name', _DEFAULT_MAP_NAME)`
- Line 272: `map_data.get('width', _DEFAULT_MAP_WIDTH)`
- Line 273: `map_data.get('height', _DEFAULT_MAP_HEIGHT)`
- Line 306: `device.get('name', device.get('mac', _UNKNOWN_NAME))`
- Line 307: `_DEVICE_COLORS.get(device_type, _FALLBACK_COLOR)`
- Line 309: `device.get('orientation', 0)`
- Line 162: `first.get('id', '')`
- Line 306: `device.get('mac', _UNKNOWN_NAME)`
- Line 377: `site.get('name', '')`
- Line 274: `map_data.get('name', _DEFAULT_MAP_NAME)`
- Line 365: `s.get('name', '')`

### src\maps\_maps_testing.py
- Line 176: `site.get('name', 'Unknown')`

### src\maps\_maps_wizard.py
- Line 433: `record.get('vertices', [])`
- Line 532: `current_map.get('name', 'Unnamed')`
- Line 729: `context.current_map.get('width', 0)`
- Line 730: `context.current_map.get('height', 0)`
- Line 731: `context.current_map.get('ppm', 0)`
- Line 739: `device.get('name', device.get('mac', 'Unknown'))`
- Line 390: `current_map.get(path_key, {})`
- Line 738: `device.get('x', 0)`
- Line 738: `device.get('y', 0)`
- Line 739: `device.get('mac', 'Unknown')`
- Line 437: `v.get('x', 0)`
- Line 437: `v.get('y', 0)`
- Line 545: `current_map.get('width', 0)`
- Line 546: `current_map.get('height', 0)`
- Line 547: `current_map.get('ppm', DEFAULT_PPM_FALLBACK)`
- Line 548: `current_map.get('width_m', 0)`
- Line 655: `current_map.get('width', 'N/A')`
- Line 655: `current_map.get('height', 'N/A')`
- Line 656: `current_map.get('ppm', 'N/A')`
- Line 658: `current_map.get('wall_path', {})`
- Additional records: 9

### src\maps\_plotly_viewer.py
- Line 116: `device.get('status', 'disconnected')`
- Line 731: `origin.get('x', 0)`
- Line 732: `origin.get('y', 0)`
- Line 809: `map_data.get('origin_x', 0)`
- Line 810: `map_data.get('origin_y', 0)`
- Line 1006: `map_data.get('width', 1000)`
- Line 1007: `map_data.get('height', 1000)`
- Line 272: `beacon.get('name', 'Unnamed Beacon')`
- Line 359: `beacon.get('power', 0)`
- Line 396: `beacon.get('name', beacon.get('mac', 'Unnamed'))`
- Line 487: `coverage_data.get('results', [])`
- Line 574: `device.get('type', 'unknown')`
- Line 624: `device.get('name', 'Unnamed')`
- Line 625: `device.get('orientation', 0)`
- Line 123: `device.get('name', 'Unnamed')`
- Line 124: `device.get('type', 'N/A')`
- Line 125: `device.get('model', 'N/A')`
- Line 126: `device.get('mac', 'N/A')`
- Line 131: `device.get('x', 'N/A')`
- Line 131: `device.get('y', 'N/A')`
- Additional records: 26

### src\maps\_viewer_launch.py
- Line 1426: `map_data.get('width', 1000)`
- Line 1427: `map_data.get('height', 1000)`
- Line 298: `data.map_data.get('width', 1000)`
- Line 299: `data.map_data.get('height', 1000)`
- Line 300: `data.map_data.get('ppm', 10)`
- Line 374: `data.map_data.get('width', 1000)`
- Line 375: `data.map_data.get('height', 1000)`
- Line 504: `data.map_data.get('origin_x', 0)`
- Line 505: `data.map_data.get('origin_y', 0)`
- Line 340: `data.map_data.get('width', 1000)`
- Line 340: `data.map_data.get('height', 1000)`
- Line 751: `map_data.get('name', 'Map')`
- Line 1503: `data.map_data.get('name', 'Unknown')`
- Line 1505: `data.map_data.get('width', 1000)`
- Line 1506: `data.map_data.get('height', 1000)`
- Line 486: `data.map_data.get('name', 'Unnamed')`
- Line 971: `spec.get('margin_top', '0')`
- Line 927: `map_data.get('name', 'export')`
- Line 1447: `map_data.get('ppm', 'N/A')`
- Line 1448: `map_data.get('orientation', 0)`
- Additional records: 6

### src\maps\launcher\_viewer_clone.py
- Line 186: `config.get('map_name', 'Unknown')`
- Line 121: `cache_bust_data.get('trigger', 0)`
- Line 238: `source_map.get('type', 'image')`
- Line 359: `zone.get('name', 'Unnamed Zone')`
- Line 361: `zone.get('vertices', [])`

### src\maps\launcher\_viewer_drawing.py
- Line 282: `last_shape.get('x0', 0)`
- Line 283: `last_shape.get('y0', 0)`
- Line 284: `last_shape.get('x1', 0)`
- Line 285: `last_shape.get('y1', 0)`
- Line 303: `existing_wall_path.get('nodes', [])`
- Line 322: `last_shape.get('type', 'unknown')`
- Line 123: `cfg.get('ppm', self._state.ppm)`
- Line 204: `last_shape.get('type', 'unknown')`
- Line 234: `last_shape.get('x0', 0)`
- Line 235: `last_shape.get('y0', 0)`
- Line 236: `last_shape.get('x1', 0)`
- Line 237: `last_shape.get('y1', 0)`
- Line 250: `last_shape.get('type', 'unknown')`
- Line 315: `existing_wall_path.get('coordinate', 'actual')`
- Line 365: `last_shape.get('x0', 0)`
- Line 366: `last_shape.get('y0', 0)`
- Line 367: `last_shape.get('x1', 0)`
- Line 368: `last_shape.get('y1', 0)`
- Line 560: `zone.get('name', 'Unknown')`
- Line 164: `request.current_fig.get('layout', {})`
- Additional records: 2

### src\maps\launcher\_viewer_refresh.py
- Line 309: `client.get('hostname', '')`
- Line 310: `client.get('mac', 'Unknown')`
- Line 489: `payload.get('wall_path', {})`
- Line 490: `wall_path.get('nodes', [])`
- Line 554: `source.get('ppm', _DEFAULT_PPM)`
- Line 631: `payload.get('result_def', [])`
- Line 632: `payload.get('results', [])`
- Line 159: `anchors.get(key, now)`
- Line 314: `client.get('ip', 'N/A')`
- Line 315: `client.get('ssid', 'N/A')`
- Line 315: `client.get('rssi', 'N/A')`
- Line 399: `t.get('name', 'unnamed')`
- Line 708: `grid_data.get((x_m, y_m), None)`
- Line 323: `client.get('wired', False)`
- Line 348: `trace.get('name', '')`
- Line 499: `trace.get('name', '')`
- Line 741: `trace.get('name', '')`

### src\maps\launcher\_viewer_site_switch.py
- Line 471: `first_map.get('id', '')`
- Line 472: `first_map.get('name', _DEFAULT_MAP_NAME)`
- Line 492: `first_map.get('name', _DEFAULT_MAP_NAME)`
- Line 493: `first_map.get('ppm', _DEFAULT_PPM)`
- Line 494: `first_map.get('width', _DEFAULT_MAP_WIDTH)`
- Line 495: `first_map.get('height', _DEFAULT_MAP_HEIGHT)`
- Line 510: `map_data.get('width', _DEFAULT_MAP_WIDTH)`
- Line 511: `map_data.get('height', _DEFAULT_MAP_HEIGHT)`
- Line 608: `device.get('name', 'Unknown')`
- Line 609: `device.get('type', 'ap')`
- Line 610: `device.get('status', 'unknown')`
- Line 110: `line_shape.get('x0', 0)`
- Line 110: `line_shape.get('y0', 0)`
- Line 111: `line_shape.get('x1', 0)`
- Line 111: `line_shape.get('y1', 0)`
- Line 313: `params.get(name, [None])`
- Line 77: `current_fig.get('layout', {})`
- Line 136: `annotation.get('text', '')`
- Line 151: `shape.get('x0', 0)`
- Line 151: `shape.get('y0', 0)`
- Additional records: 7

### src\maps\launcher\_viewer_ui.py
- Line 257: `point.get('hovertext', '')`
- Line 160: `trace.get('name', '')`
- Line 191: `shape.get('x0', 0)`
- Line 191: `shape.get('y0', 0)`
- Line 192: `shape.get('x1', 0)`
- Line 192: `shape.get('y1', 0)`
- Line 246: `trace.get('hovertext', '')`
- Line 475: `meta.get('origin_x', 0)`
- Line 476: `meta.get('origin_y', 0)`
- Line 636: `current_zone.get('zone_name', 'Unknown')`
- Line 366: `config.get('map_name', 'Unknown')`
- Line 514: `cache_bust_data.get('trigger', 0)`
- Line 526: `config.get('map_name', 'Unknown')`
- Line 151: `zone.get('id', f'zone_{idx}')`
- Line 442: `current_fig.get('layout', {})`
- Line 474: `current_fig.get('layout', {})`
- Line 625: `current_zone.get('zone_name', 'Unknown')`
- Line 449: `current_fig.get('layout', {})`

### src\maps\launcher\_viewer_url_switch.py
- Line 240: `device.get('status', 'disconnected')`
- Line 247: `client.get('hostname', '')`
- Line 248: `client.get('mac', 'unknown')`
- Line 474: `map_data.get('width', _DEFAULT_MAP_WIDTH)`
- Line 475: `map_data.get('height', _DEFAULT_MAP_HEIGHT)`
- Line 818: `coverage_data.get('results', [])`
- Line 819: `coverage_data.get('result_def', [])`
- Line 931: `new_map_data.get('name', _DEFAULT_MAP_NAME)`
- Line 933: `new_map_data.get('width', _DEFAULT_MAP_WIDTH)`
- Line 934: `new_map_data.get('height', _DEFAULT_MAP_HEIGHT)`
- Line 215: `client.get('mac', 'N/A')`
- Line 216: `client.get('hostname', 'N/A')`
- Line 217: `client.get('ssid', 'N/A')`
- Line 218: `client.get('ap_name', 'N/A')`
- Line 219: `client.get('band', 'N/A')`
- Line 220: `client.get('rssi', 'N/A')`
- Line 228: `device.get('name', 'Unnamed')`
- Line 229: `device.get('type', 'N/A')`
- Line 230: `device.get('model', 'N/A')`
- Line 231: `device.get('mac', 'N/A')`
- Additional records: 15

### src\maps\maps_manager.py
- Line 212: `selected_site.get('name', 'Unknown')`
- Line 524: `map_item.get('width', 0)`
- Line 525: `map_item.get('height', 0)`
- Line 676: `site.get('name', 'Unknown')`
- Line 789: `map_item.get('name', 'unnamed')`
- Line 790: `map_item.get('id', 'unknown')`
- Line 806: `map_item.get('name', 'unnamed')`
- Line 1013: `type_map.get(type_choice, 'image')`
- Line 1705: `site.get('name', 'Unknown')`
- Line 1885: `map_data.get('name', 'Unnamed')`
- Line 1908: `map_data.get('ppm', 0)`
- Line 1911: `map_data.get('name', 'Unnamed')`
- Line 2171: `data.map_data.get('name', 'Unnamed')`
- Line 2348: `path.get('name', f'Path {path_idx + 1}')`
- Line 2349: `path.get('coordinate', [])`
- Line 2390: `client.get('mac', 'unknown')`
- Line 2401: `client.get('hostname', '')`
- Line 2508: `graph_data.get('nodes', [])`
- Line 2534: `node.get('position', {})`
- Line 2535: `node.get('edges', {})`
- Additional records: 76

### src\maps\plotly_heatmap_renderer.py
- Line 125: `coverage_data.get('results', [])`
- Line 139: `coverage_data.get('result_def', [])`
- Line 140: `coverage_data.get('gridsize', 1)`
- Line 163: `coverage_data.get('gridsize', 1)`

### src\maps\plotly_map_callback_manager.py
- Line 143: `fig.get('data', [])`
- Line 151: `fig.get('layout', {})`
- Line 144: `trace.get('name', '')`
- Line 153: `annotation.get('name', '')`

### src\maps\plotly_map_figure_builder.py
- Line 144: `path.get('nodes', [])`
- Line 168: `node.get('name', '')`
- Line 169: `node.get('position', {})`
- Line 201: `node.get('position', {})`
- Line 202: `node.get('edges', {})`
- Line 221: `zone.get('name', f'Zone {index + 1}')`
- Line 222: `zone.get('vertices', [])`
- Line 179: `node.get('edges', {})`
- Line 238: `vertex.get('x', 0)`
- Line 239: `vertex.get('y', 0)`
- Line 255: `src.get('x', 0)`
- Line 255: `dst.get('x', 0)`
- Line 256: `src.get('y', 0)`
- Line 256: `dst.get('y', 0)`

### src\maps\plotly_map_serializer.py
- Line 105: `data.get(_KEY_TRIGGER, _DEFAULT_TRIGGER)`
- Line 67: `item.get(_KEY_NAME, default_name)`
- Line 77: `item.get(_KEY_NAME, default_name)`

### src\metrics_gateway\collector.py
- Line 379: `row.get('name', '')`
- Line 328: `entry.get('path', '')`
- Line 363: `row.get('id', '')`
- Line 366: `row.get('name', '')`
- Line 402: `row.get('mac', '')`
- Line 403: `row.get('site_id', '')`
- Line 406: `site_names.get(site_id, '')`
- Line 306: `org.get('name', '')`
- Line 424: `row.get('name', '')`
- Line 425: `row.get('site_id', '')`
- Line 427: `row.get('type', '')`
- Line 465: `row.get('model', '')`
- Line 466: `row.get('serial', '')`
- Line 467: `row.get('version', '')`
- Line 311: `org.get('name', '')`
- Line 362: `item.get('id', '')`
- Line 401: `item.get('mac', '')`
- Line 442: `row.get('name', '')`
- Line 383: `row.get('country_code', '')`

### src\mib_generator\document.py
- Line 90: `self._document.get('openapi', '')`

### src\mib_generator\mib.py
- Line 384: `SCALE_SENTENCE.get(definition.snmp_scale, '')`

### src\network\_routing_utils_display.py
- Line 180: `entry.get('service', '')`
- Line 401: `entry.get('destination', _MISSING)`
- Line 402: `entry.get('next_hop', _MISSING)`
- Line 403: `entry.get('interface', _MISSING)`
- Line 404: `entry.get('protocol', _MISSING)`
- Line 405: `entry.get('admin_distance', _MISSING)`
- Line 449: `entry.get('protocol', 'Unknown')`
- Line 451: `entry.get('vrf', 'default')`
- Line 453: `entry.get('next_hop', '')`
- Line 507: `entry.get('destination', _MISSING)`
- Line 508: `entry.get('next_hop', _MISSING)`
- Line 509: `entry.get('protocol', _MISSING)`
- Line 510: `entry.get('name', _MISSING)`
- Line 511: `entry.get('status', _MISSING)`
- Line 512: `entry.get('selection_reason', _MISSING)`
- Line 513: `entry.get('weight', _MISSING)`
- Line 514: `entry.get('metric', _MISSING)`
- Line 515: `entry.get('local_preference', _MISSING)`
- Line 516: `entry.get('as_path', _MISSING)`
- Line 517: `entry.get('vrf', 'default')`
- Additional records: 23

### src\network\_routing_utils_forwarding.py
- Line 168: `device_info.get('type', 'unknown')`
- Line 169: `device_info.get('model', 'unknown')`
- Line 356: `result.get('raw', '')`
- Line 358: `result.get('Output', '')`
- Line 466: `item.get('prefix', item.get('destination', ''))`
- Line 467: `item.get('nextHop', item.get('next_hop', ''))`
- Line 468: `item.get('interface', item.get('dev', ''))`
- Line 469: `item.get('service', item.get('serviceName', ''))`
- Line 470: `item.get('table', '')`
- Line 471: `item.get('type', '')`
- Line 389: `device_info.get('type', 'unknown')`
- Line 390: `device_info.get('model', 'unknown')`
- Line 466: `item.get('destination', '')`
- Line 467: `item.get('next_hop', '')`
- Line 468: `item.get('dev', '')`
- Line 469: `item.get('serviceName', '')`

### src\network\_routing_utils_parsing.py
- Line 283: `payload.get('rows', [])`
- Line 286: `payload.get('message', '')`
- Line 313: `row.get('prefix', '')`
- Line 314: `row.get('nextHops', '')`
- Line 319: `row.get('status', '')`
- Line 320: `row.get('vrfName', 'default')`
- Line 321: `row.get('name', '')`
- Line 323: `row.get('path', '')`
- Line 325: `row.get('selectionReason', '')`
- Line 436: `item.get('prefix', item.get('destination', item.get('route', '')))`
- Line 437: `item.get('nextHop', item.get('next_hop', item.get('gateway', '')))`
- Line 438: `item.get('interface', item.get('dev', item.get('iface', '')))`
- Line 439: `item.get('protocol', item.get('proto', item.get('type', '')))`
- Line 442: `item.get('active', False)`
- Line 443: `item.get('selected', False)`
- Line 318: `row.get('metric', '')`
- Line 322: `row.get('weight', '')`
- Line 324: `row.get('localPreference', '')`
- Line 436: `item.get('destination', item.get('route', ''))`
- Line 437: `item.get('next_hop', item.get('gateway', ''))`
- Additional records: 9

### src\network\_routing_utils_routing.py
- Line 104: `device_info.get('type', 'unknown')`
- Line 105: `device_info.get('model', 'unknown')`
- Line 176: `device_info.get('type', 'unknown')`
- Line 177: `device_info.get('model', 'unknown')`
- Line 330: `result.get('raw', '')`
- Line 332: `result.get('Output', '')`

### src\network\_routing_utils_ssr.py
- Line 304: `result.get('raw', '')`
- Line 307: `result.get('Output', '')`

### src\network\routing_utils.py
- Line 305: `result.get('raw', '')`
- Line 306: `result.get('Output', '')`
- Line 322: `device_info.get('type', 'unknown')`
- Line 322: `device_info.get('name', device_id[:8])`

### src\org\org_config_migration_manager.py
- Line 323: `metadata.get('object_counts', {})`
- Line 371: `self._existing.get(type_key, [])`
- Line 451: `new_obj.get('addresses', [])`
- Line 475: `existing.get('addresses', [])`
- Line 510: `obj.get('networks', {})`
- Line 523: `obj.get('networks', {})`
- Line 538: `obj.get('services', [])`
- Line 594: `obj.get('name', 'unnamed')`
- Line 595: `obj.get('id', '')`
- Line 175: `config_type.get('list_kwargs', {})`
- Line 319: `metadata.get('source_org_name', 'Unknown')`
- Line 320: `metadata.get('export_timestamp', 'Unknown')`
- Line 562: `bundle.get(config_type['key'], [])`
- Line 652: `response.data.get('id', '')`
- Line 706: `item.get('reason', '')`
- Line 154: `response.data.get('name', 'Unknown')`
- Line 232: `counts.get(key, 0)`
- Line 321: `metadata.get('source_org_id', 'Unknown')`
- Line 517: `self._remap_table.get(old_id, old_id)`
- Line 544: `self._remap_table.get(old_id, old_id)`
- Additional records: 1

### src\org\org_synthetic_probes_manager.py
- Line 1040: `probes_source.get('roles', [])`
- Line 1645: `probes_source.get('roles', [])`
- Line 1704: `probes_source.get('roles', [])`
- Line 2140: `new_probes.get(name, probe)`
- Line 2940: `site.get('id', '')`
- Line 1523: `cenr.get('proxy_hostnames', [])`
- Line 1524: `cenr.get('vpn_hostnames', [])`

### src\org\org_ticket_manager.py
- Line 182: `ticket_data.get('id', 'unknown')`
- Line 189: `ticket_data.get('status', 'open')`
- Line 418: `ticket.get('status', 'unknown')`
- Line 419: `ticket.get('type', 'unknown')`
- Line 420: `ticket.get('subject', '(no subject)')`
- Line 485: `ticket.get('id', '')`
- Line 512: `ticket_data.get('comments', [])`
- Line 522: `comment.get('author', 'unknown')`
- Line 523: `comment.get('created_at', 'unknown')`
- Line 524: `comment.get('comment', '(no text)')`
- Line 526: `comment.get('attachments', [])`
- Line 529: `att.get('name', att.get('content_url', 'file'))`
- Line 508: `ticket_data.get(key, default)`
- Line 529: `att.get('content_url', 'file')`

### src\org_data_collector.py
- Line 538: `tally.get(result, 0)`

### src\refactors\anomaly_metrics_discovery.py
- Line 101: `row.get('name', '')`
- Line 100: `row.get('key', '')`
- Line 102: `row.get('scope', '')`
- Line 124: `x.get('priority', False)`

### src\refactors\fast_mode_backoff_multiplier.py
- Line 27: `os.getenv('FAST_MODE_BACKOFF_MULTIPLIER', '1.5')`

### src\refactors\fast_mode_constants.py
- Line 22: `os.getenv('FAST_MODE_MAX_CONCURRENT_CONNECTIONS', '8')`
- Line 34: `os.getenv('FAST_MODE_MAX_RETRIES', '3')`
- Line 35: `os.getenv('FAST_MODE_RETRY_DELAY', '0.5')`
- Line 36: `os.getenv('FAST_MODE_RETRY_THREADS', '4')`
- Line 37: `os.getenv('FAST_MODE_RETRY_MAX_RETRIES', '2')`
- Line 38: `os.getenv('FAST_MODE_FALLBACK_THREADS', '8')`
- Line 31: `os.getenv('FAST_MODE_USE_CONNECTION_AWARE_THREADING', 'true')`

### src\refactors\fast_mode_devices_per_thread.py
- Line 27: `os.getenv('FAST_MODE_DEVICES_PER_THREAD', '10')`

### src\refactors\fast_mode_sequential_max_retries.py
- Line 30: `os.getenv('FAST_MODE_SEQUENTIAL_MAX_RETRIES', '1')`

### src\refactors\main_entrypoint.py
- Line 82: `state.get('msp_privileges', self.msp_privileges)`
- Line 83: `state.get('selected_msp', self.selected_msp)`
- Line 84: `state.get('org_id', self.org_id)`
- Line 320: `os.getenv('MIST_SITE_EXCLUDE_PREFIX', '')`
- Line 191: `os.environ.get('CONSOLE_LOG_LEVEL', logging.INFO)`
- Line 191: `os.environ.get('CONSOLE_LOG_LEVEL', logging.INFO)`
- Line 192: `os.environ.get('LOGGING_LOG_LEVEL', logging.INFO)`
- Line 192: `os.environ.get('LOGGING_LOG_LEVEL', logging.INFO)`
- Line 271: `os.getenv('API_REQUEST_TIMEOUT', '120')`
- Line 272: `os.getenv('API_REQUEST_MAX_RETRIES', '3')`
- Line 273: `os.getenv('API_REQUEST_RETRY_DELAY', '5.0')`
- Line 278: `os.getenv('FAST_MODE_MAX_RETRIES', '3')`
- Line 279: `os.getenv('FAST_MODE_RETRY_DELAY', '0.5')`
- Line 280: `os.getenv('FAST_MODE_RETRY_THREADS', '4')`
- Line 281: `os.getenv('FAST_MODE_RETRY_MAX_RETRIES', '2')`
- Line 282: `os.getenv('FAST_MODE_FALLBACK_THREADS', '8')`
- Line 306: `os.environ.get('MIST_PAGE_LIMIT', '1000')`
- Line 306: `os.environ.get('MIST_PAGE_LIMIT', '1000')`

### src\refactors\mist_wan_target_ports.py
- Line 37: `os.getenv('MIST_WAN_TARGET_PORTS', '')`

### src\refactors\msp_privilege_detection.py
- Line 113: `user_data.get('privileges', [])`
- Line 96: `priv.get('role', 'unknown')`
- Line 97: `priv.get('scope', 'unknown')`

### src\refactors\serial_cc\global_assignments_builder.py
- Line 65: `_ATTRIBUTE_EXPORTS.get(module_name, ())`

### src\refactors\serial_cc\security_events.py
- Line 264: `site.get('name', 'Unknown Site')`

### src\refactors\serial_cc\site_client_insights.py
- Line 109: `client.get(_KEY_MAC, _UNKNOWN)`
- Line 110: `client.get(_KEY_HOSTNAME, _UNKNOWN)`
- Line 111: `client.get(_KEY_LAST_SEEN, _UNKNOWN)`
- Line 150: `site_data.get(_KEY_NAME, site_id)`

### src\refactors\serial_cc\start_site_scan_capture.py
- Line 188: `_BAND_MAP.get(band_choice, '5')`
- Line 217: `_BANDWIDTH_EXTRA_ROWS.get(band, ())`
- Line 228: `_BANDWIDTH_MAP.get(bw_choice, '20')`
- Line 346: `cap.get('ap_mac', '')`

### src\refactors\serial_cc\switch_vc_stats.py
- Line 64: `switch.get('name', '')`
- Line 65: `switch.get('mac', '')`
- Line 72: `switch.get('model', '')`
- Line 73: `switch.get('serial', '')`
- Line 149: `row.get(field, '')`
- Line 55: `row.get('vc_mac', '')`

### src\refactors\serial_cc\test_results_by_site.py
- Line 77: `response.data.get('results', [])`

### src\refactors\sqlite_database_writer.py
- Line 367: `row.get(field_name, '')`

### src\refactors\wanprobe_config_manager.py
- Line 62: `os.getenv('MIST_WAN_PROBE_PROFILE', 'lte')`
- Line 310: `port_settings.get('wan_probe_override', {})`
- Line 183: `template.get('id', '')`
- Line 184: `template.get('name', 'Unnamed Template')`
- Line 185: `self.template_site_counts.get(template_id, 0)`
- Line 311: `current_probe.get('ips', [])`
- Line 313: `current_probe.get('probe_profile', '')`
- Line 384: `config.get('port_config', {})`
- Line 60: `os.getenv('MIST_WAN_PROBE_IPS', '192.151.29.254,18.154.184.32')`
- Line 155: `site.get('gatewaytemplate_id', '')`
- Line 157: `self.template_site_counts.get(template_id, 0)`
- Line 153: `site.get('name', '')`
- Line 217: `t.get('name', '')`

### src\refactors\wlanradius_timer_manager.py
- Line 197: `template_data.get('name', 'Unknown Template')`
- Line 269: `wlan_template.get('applies', {})`
- Line 275: `self.site_info.get('sitegroup_ids', [])`
- Line 276: `self.site_info.get('wxtag_ids', [])`
- Line 323: `wlan.get('radsec', {})`
- Line 327: `wlan.get('auth', {})`
- Line 394: `wlan.get('radsec', {})`
- Line 487: `wlan.get('auth_servers_timeout', 5)`
- Line 499: `wlan.get('auth_servers_retries', 2)`
- Line 511: `wlan.get('auth_server_selection', 'ordered')`
- Line 528: `wlan.get('fast_dot1x_timers', False)`
- Line 548: `wlan.get('auth_servers', [])`
- Line 147: `self.site_info.get('name', 'Unknown Site')`
- Line 254: `applies.get('site_ids', [])`
- Line 315: `template_info.get('name', 'Unknown Template')`
- Line 325: `radsec_config.get('enabled', False)`
- Line 396: `wlan.get('ssid', 'Unknown SSID')`
- Line 397: `wlan.get('id', 'Unknown ID')`
- Line 398: `wlan.get('enabled', False)`
- Line 399: `wlan.get('_inheritance_level', 'unknown')`
- Additional records: 22

### src\reports\e911_bssid.py
- Line 277: `response.data.get('wlans', {})`
- Line 509: `template.get('applies', {})`
- Line 542: `wlan.get('ssid', '')`
- Line 667: `ap_entry.get('mac', '')`
- Line 680: `ap_entry.get('radio_mac', [])`
- Line 698: `band_info.get('band', 'Unknown')`
- Line 711: `band_info.get('band_key', '')`
- Line 755: `site_info.get('address', '')`
- Line 1016: `checkpoint.get('total_sites', '?')`
- Line 290: `ap_entry.get('radio_mac', [])`
- Line 294: `band_orders.get(len(broadcast_radios), [])`
- Line 514: `applies.get('site_ids', [])`
- Line 540: `wlan.get('enabled', False)`
- Line 601: `ap_entry.get('mac', '')`
- Line 1015: `checkpoint.get('completed_sites', [])`
- Line 1025: `checkpoint.get('map_lookup', {})`
- Line 1026: `checkpoint.get('wlan_band_lookup', {})`
- Line 403: `site_map.get('name', '')`
- Line 1027: `checkpoint.get('completed_sites', [])`
- Line 216: `site.get('name', '')`
- Additional records: 3

### src\reports\global_wired_client_report_generator.py
- Line 147: `criteria.get('mac_operator', '')`
- Line 156: `criteria.get('mfg_operator', '')`
- Line 151: `criteria.get('mac_value', '')`
- Line 158: `criteria.get('mfg_value', '')`
- Line 210: `criteria.get('mac_value', '')`
- Line 218: `criteria.get('mfg_value', '')`
- Line 245: `criteria.get('mac_value', '')`
- Line 248: `criteria.get('mfg_value', '')`

### src\reports\offline_device_reporter.py
- Line 130: `device.get('type', 'unknown')`
- Line 134: `site_lookup.get(device.get('site_id', ''), 'Unknown Site')`
- Line 134: `device.get('site_id', '')`
- Line 140: `device.get('mac', '')`
- Line 141: `device.get('serial', '')`
- Line 142: `device.get('model', '')`
- Line 145: `device.get('status', 'disconnected')`
- Line 197: `type_counts.get(device_type, 0)`
- Line 100: `site.get('name', 'Unknown Site')`
- Line 219: `type_counts.get(record['Device Type'], 0)`
- Line 220: `site_counts.get(record['Site Name'], 0)`
- Line 240: `record.get(f, '')`
- Line 259: `record.get(f, '')`

### src\reports\sfp_transceiver_data_processor.py
- Line 97: `row.get('port_id', '')`
- Line 98: `row.get('xcvr_part_number', '')`
- Line 100: `row.get('xcvr_serial', '')`
- Line 88: `row.get('xcvr_model', '')`
- Line 73: `row.get('site_name', '')`
- Line 74: `row.get('site_address', '')`
- Line 75: `row.get('name', '')`

### src\reports\ssid_broadcast_gap_report.py
- Line 43: `site.get('id', '')`
- Line 67: `wlan.get('enabled', True)`
- Line 56: `site.get('name', '')`

### src\reports\wired_client_manufacturer_report_generator.py
- Line 76: `manufacturer_counts.get(manufacturer, 0)`
- Line 75: `record.get('manufacture', 'Unknown')`
- Line 134: `record.get('manufacture', '')`

### src\site\address_audit\address_resolver.py
- Line 152: `candidates.mist_address.get('address', '')`
- Line 201: `csv_street.get('address', query)`
- Line 205: `outcome.get('comparison_validation', {})`
- Line 464: `cleaned.get('address', '')`
- Line 185: `mist_address.get('city', '')`
- Line 191: `mist_address.get('zipcode', '')`
- Line 192: `mist_address.get('state', '')`
- Line 209: `comparison.get('confidence', 0.0)`
- Line 302: `candidates.mist_address.get('address', '')`
- Line 449: `address.get('address', '')`
- Line 450: `address.get('city', '')`
- Line 451: `address.get('state', '')`
- Line 166: `source.get('address', '')`
- Line 181: `mist_address.get('address', '')`
- Line 314: `address.get('address', '')`
- Line 452: `address.get('zip', address.get('zipcode', ''))`
- Line 429: `counts.get(number, 0)`
- Line 452: `address.get('zipcode', '')`
- Line 515: `raw.get('_street_validated', False)`
- Line 438: `rank.get(hint[0], 9)`

### src\site\address_audit\audit_engine.py
- Line 701: `mist_addr.get('address', '')`
- Line 733: `mist_addr.get('address', '')`
- Line 816: `_DIRECTIONALS.get(tokens[index].lower(), '')`
- Line 885: `labels.get(resolver_result.source, '-')`
- Line 372: `d.get('serial', '')`
- Line 373: `s.get('id', '')`
- Line 753: `csv_addr.get('address', '')`
- Line 968: `address.get('address', '')`
- Line 969: `address.get('city', '')`
- Line 970: `address.get('state', '')`
- Line 357: `os.environ.get('BUSINESS_NAME', '')`
- Line 357: `os.environ.get('BUSINESS_NAME', '')`
- Line 489: `os.environ.get('MIST_DASHBOARD_URL', config.dashboard_url)`
- Line 489: `os.environ.get('MIST_DASHBOARD_URL', config.dashboard_url)`
- Line 516: `os.environ.get(name, '')`
- Line 516: `os.environ.get(name, '')`
- Line 971: `address.get('zip', '')`
- Line 439: `os.environ.get('ADDRESS_AUDIT_GEOCODE', 'auto')`
- Line 439: `os.environ.get('ADDRESS_AUDIT_GEOCODE', 'auto')`

### src\site\address_audit\audit_reporter.py
- Line 87: `address.get('address', '')`
- Line 88: `address.get('city', '')`
- Line 89: `address.get('state', '')`
- Line 90: `address.get('zip', '')`

### src\site\address_audit\business_authority_ingester.py
- Line 80: `index.get('by_name', {})`
- Line 81: `index.get('by_full', {})`
- Line 82: `index.get('by_no_suite', {})`
- Line 83: `by_name.get(self._norm_key(site.site_name or ''), [])`
- Line 89: `by_full.get(csv_full, [])`
- Line 95: `by_no_suite.get(csv_no_suite, [])`
- Line 107: `by_no_suite.get(mist_no_suite, [])`
- Line 103: `mist.get('city', '')`
- Line 104: `mist.get('state', '')`
- Line 105: `mist.get('zip', mist.get('zipcode', ''))`
- Line 102: `mist.get('address', '')`
- Line 105: `mist.get('zipcode', '')`

### src\site\address_audit\comparison_display.py
- Line 113: `address.get('address', '')`
- Line 114: `address.get('city', '')`
- Line 115: `address.get('state', '')`
- Line 98: `counts.get(result.issue_type, 0)`
- Line 116: `address.get('zip', '')`

### src\site\address_audit\perf.py
- Line 45: `self._phases.get(label, [0.0, 0.0])`

### src\site\address_audit\site_matcher.py
- Line 93: `self._sites_by_id.get(site_id, {})`
- Line 107: `site.get('address', '')`
- Line 108: `site.get('city', '')`
- Line 109: `site.get('state', '')`
- Line 110: `site.get('zipcode', site.get('zip', ''))`
- Line 87: `site.get('address', '')`
- Line 87: `site.get('city', '')`
- Line 87: `site.get('state', '')`
- Line 110: `site.get('zip', '')`

### src\site\address_audit\snmp_enricher.py
- Line 39: `site_record.get('id', 'unknown')`

### src\site\address_audit\ui_geocoder.py
- Line 704: `os.environ.get('ProgramFiles(x86)', '')`
- Line 704: `os.environ.get('ProgramFiles(x86)', '')`
- Line 705: `os.environ.get('ProgramFiles', '')`
- Line 705: `os.environ.get('ProgramFiles', '')`

### src\site\bulk_radius_wlan_config_manager.py
- Line 158: `wlan.get('radsec', {})`
- Line 160: `wlan.get('auth', {})`
- Line 166: `wlan.get('auth_servers_timeout', 5)`
- Line 167: `wlan.get('auth_servers_retries', 2)`
- Line 168: `wlan.get('fast_dot1x_timers', False)`
- Line 245: `wlan.get('ssid', 'Unknown')`
- Line 250: `wlan.get('auth_servers_timeout', 5)`
- Line 251: `wlan.get('auth_servers_retries', 2)`
- Line 389: `wlan.get('ssid', 'Unknown')`
- Line 418: `wlan.get('ssid', 'Unknown')`
- Line 429: `wlan.get('ssid', 'Unknown')`
- Line 94: `os.getenv('RADIUS_AUTH_TIMEOUT', '3')`
- Line 95: `os.getenv('RADIUS_AUTH_RETRIES', '2')`
- Line 159: `radsec_config.get('enabled', False)`
- Line 185: `wlan.get('auth_servers_timeout', 5)`
- Line 186: `wlan.get('auth_servers_retries', 2)`
- Line 187: `wlan.get('fast_dot1x_timers', False)`
- Line 249: `wlan.get('_inheritance_level', 'unknown')`
- Line 252: `wlan.get('fast_dot1x_timers', False)`
- Line 354: `wlan.get('ssid', 'Unknown')`
- Additional records: 26

### src\site\site_config_manager.py
- Line 979: `access_point.get('mac', 'unknown')`
- Line 980: `access_point.get('name', ap_mac)`
- Line 148: `site_data.get('lat', '')`
- Line 149: `site_data.get('lng', '')`
- Line 160: `site_data.get('name', '')`
- Line 185: `response.data.get('id', 'unknown')`
- Line 361: `site.get('name', 'Unknown')`
- Line 727: `device.get('name', device.get('mac', 'unknown'))`
- Line 727: `device.get('mac', 'unknown')`
- Line 360: `site.get('country_code', '')`

### src\ssh\batch\multi_host_runner.py
- Line 308: `future_to_host.get(future, 'unknown')`

### src\ssh\cli_shell_manager.py
- Line 160: `CLIShellManager._SHELL_KEYMAP.get(key, key)`

### src\ssh\config\env_loader.py
- Line 80: `config.get('hosts', [])`
- Line 82: `config.get('commands', [])`

### src\ssh\runtime\app_runner.py
- Line 253: `env_config.get('commands', [])`
- Line 158: `env_config.get('hosts', [])`
- Line 160: `env_config.get('commands', [])`

### src\ssh\ssh_runner_manager.py
- Line 568: `results.get('successful', 0)`
- Line 90: `env_config.get('hosts', [])`
- Line 93: `env_config.get('commands', [])`
- Line 469: `gateway.get('Gateway Name', _UNKNOWN_TEMPLATE)`
- Line 471: `gateway.get('Site Name', _UNKNOWN_TEMPLATE)`
- Line 528: `ssh_config.get('commands', [])`
- Line 572: `results.get('failed', 0)`
- Line 577: `results.get('total', len(management_ips))`
- Line 401: `gateway.get(_TEMPLATE_KEY, _UNKNOWN_TEMPLATE)`
- Line 331: `result.get('success', False)`

### src\ssid_consolidation\_ssid_template_cache.py
- Line 134: `cached.get('collected_at', '')`
- Line 199: `existing.get('results', [])`
- Line 201: `existing.get('total', 0)`

### src\ssid_consolidation\_ssid_template_phase1.py
- Line 111: `template.get('applies', {})`
- Line 169: `matched_wlan.get('mxtunnel_ids', [])`
- Line 299: `matched_wlan.get('mxtunnel_ids', [])`
- Line 357: `lookups.mxtunnel_lookup.get(first_tunnel_id, '')`
- Line 88: `tunnel.get('id', '')`
- Line 88: `tunnel.get('name', '')`
- Line 96: `tmpl.get('id', '')`
- Line 103: `group.get('id', '')`
- Line 133: `template.get('wlans', [])`
- Line 237: `matched.get(key, default)`
- Line 252: `matched.get('vlan_id', '')`
- Line 261: `inputs.get('site_name', '')`
- Line 262: `inputs.get('site_id', '')`
- Line 263: `inputs.get('template_name', '')`
- Line 264: `inputs.get('template_id', '')`
- Line 269: `inputs.get('first_tunnel_id', '')`
- Line 270: `inputs.get('cluster_name', '')`
- Line 271: `inputs.get('psk_detected', False)`
- Line 272: `inputs.get('anomaly', False)`
- Line 273: `inputs.get('anomaly_reason', '')`
- Additional records: 17

### src\ssid_consolidation\_ssid_template_phase2.py
- Line 50: `cache.get('deviations', [])`
- Line 51: `cache.get('matrix', [])`
- Line 69: `row.get('site_id', '')`
- Line 88: `row.get('site_name', '')`
- Line 89: `row.get('site_id', '')`
- Line 124: `row.get(param, row.get('vlan_id', ''))`
- Line 125: `site_vars.get(var_name, '')`
- Line 128: `row.get('site_name', '')`
- Line 129: `row.get('site_id', '')`
- Line 148: `entry.get('status', '')`
- Line 101: `cache.get('data', {})`
- Line 124: `row.get('vlan_id', '')`
- Line 78: `deviation.get('parameter', '')`
- Line 85: `row.get('anomaly_reason', '')`
- Line 103: `site.get('vars', {})`

### src\ssid_consolidation\_ssid_template_phase3.py
- Line 80: `cache.get('matrix', [])`
- Line 81: `cache.get('data', {})`
- Line 82: `data.get('mxtunnels', [])`
- Line 83: `data.get('sitegroups', [])`
- Line 179: `plan.get('groups', [])`
- Line 84: `group.get('name', '')`
- Line 154: `row.get('site_id', '')`
- Line 154: `row.get('site_name', '')`
- Line 246: `ctx.group.get('cluster_name', '')`
- Line 310: `plan.get('groups', [])`
- Line 326: `plan.get('groups', [])`
- Line 95: `tunnel.get('name', '')`
- Line 119: `existing.get('id', '')`
- Line 165: `row.get('target_group', '')`
- Line 255: `cache.get('data', {})`
- Line 135: `pilot_existing.get('id', '')`
- Line 257: `group.get('site_ids', [])`
- Line 362: `row.get('site_id', '')`
- Line 362: `row.get('group_id', '')`

### src\ssid_consolidation\_ssid_template_phase45.py
- Line 137: `cache.get('deviations', [])`
- Line 152: `deviation.get('cluster_name', '')`
- Line 153: `deviation.get('parameter', '')`
- Line 241: `phase3_results.get('results', [])`
- Line 291: `cache.get('deviations', [])`
- Line 304: `cache.get('matrix', [])`
- Line 337: `representative.get('mxtunnel_id', '')`
- Line 359: `group_info.get('group_id', 'new')`
- Line 376: `cache.get('matrix', [])`
- Line 154: `deviation.get('unique_values', '[]')`
- Line 242: `result.get('group_name', '')`
- Line 260: `group_info.get('cluster_name', '')`
- Line 335: `representative.get('vlan_id', '')`
- Line 336: `representative.get('auth_type', '')`
- Line 349: `group_plan.get(group_name, {})`
- Line 361: `config.get('ssid', '')`
- Line 402: `row.get('ssid_enabled', True)`
- Line 412: `row.get('site_name', '')`
- Line 413: `row.get('site_id', '')`
- Line 414: `row.get('template_name', '')`
- Additional records: 15

### src\ssid_consolidation\ssid_template_consolidation.py
- Line 726: `existing.get('id', '')`
- Line 771: `params.group_info.get('group_id', '')`
- Line 781: `created.get('id', '')`
- Line 825: `entry.get('old_template_id', '')`
- Line 826: `entry.get('ssid_id', '')`
- Line 292: `self.__dict__.get('_clusters', ())`
- Line 349: `os.getenv('MIST_TARGET_SSID', '')`
- Line 568: `created.get('id', '')`
- Line 728: `template_data.get('wlans', [])`
- Line 801: `params.group_info.get('group_id', '')`
- Line 802: `params.group_info.get('group_id', '')`
- Line 847: `template_data.get('wlans', [])`
- Line 764: `wlan.get('ssid', '')`

### src\troubleshooting\interactive_test_runner.py
- Line 181: `matching_site.get('name', 'Unknown')`
- Line 216: `os.getenv('MIST_INTERACTIVE_TEST_SITE', '')`
- Line 130: `site.get('name', '')`

### src\troubleshooting\marvis_troubleshoot_utils.py
- Line 463: `result.get('description', 'Analysis result')`
- Line 685: `device_response.data.get('name', _UNKNOWN_DEVICE)`
- Line 954: `insight.get('description', insight.get('type', insight.get('name', str(insight))))`
- Line 556: `_MARVIS_ERROR_GUIDANCE.get(kind, ())`
- Line 753: `org_info.get('name', 'Unknown')`
- Line 754: `org_info.get('features', [])`
- Line 954: `insight.get('type', insight.get('name', str(insight)))`
- Line 502: `insight.get('description', insight)`
- Line 954: `insight.get('name', str(insight))`

### src\ui\display_utils.py
- Line 40: `item.get(field, '')`

### src\ui\execution\function_executor.py
- Line 208: `parsed_data.get('results', [])`
- Line 163: `parsed_data.get('results', [])`
- Line 142: `parsed_data.get('results', [])`

### src\ui\layout\layout_builder.py
- Line 114: `item.get('type', 'unknown')`
- Line 115: `item.get('name', 'unknown')`
- Line 177: `selected.get('name', 'unknown')`
- Line 178: `selected.get('signature', '(...)')`
- Line 179: `selected.get('full_doc', 'No documentation available')`
- Line 311: `_HELP_TEXT_TABLE.get(state, _HELP_TEXT_TABLE['navigation'])`
- Line 294: `tui.function_params.get(param_name, '')`
- Line 74: `item.get('name', '')`
- Line 172: `selected.get('description', 'Unknown error')`
- Line 260: `tui.current_function.get('name', 'unknown')`
- Line 167: `selected.get('name', 'unknown')`

### src\ui\layout\results_grid_builder.py
- Line 227: `parsed.get('results', [])`
- Line 277: `parsed.get('total', total_results)`
- Line 278: `self._tui.function_params.get('limit', 1000)`
- Line 279: `parsed.get('distinct', 'N/A')`

### src\ui\prompt_utils.py
- Line 418: `client.get('site_id', '')`
- Line 426: `client.get('connected', True)`
- Line 442: `client.get('ip', '')`
- Line 450: `client.get('ssid', client.get('vlan', ''))`
- Line 488: `client.get('mac', '')`
- Line 489: `client.get('client_type', 'unknown')`
- Line 491: `client.get('hostname', client.get('name', 'Unknown'))`
- Line 407: `client.get('mac', 'Unknown')`
- Line 432: `client.get('last_seen', 0)`
- Line 450: `client.get('vlan', '')`
- Line 490: `client.get('site_id', default_site_id)`
- Line 491: `client.get('name', 'Unknown')`
- Line 106: `item.get('name', '')`
- Line 138: `row.get('name', 'Unnamed')`
- Line 400: `client.get('hostname', client.get('name', 'Unknown'))`
- Line 408: `client.get('client_type', 'unknown')`
- Line 92: `x.get('model', '')`
- Line 103: `item.get('name', '')`
- Line 103: `item.get('mac', '')`
- Line 103: `item.get('model', '')`
- Additional records: 5

### src\upgrade_portal\api\mist_client.py
- Line 75: `site.get('id', '')`
- Line 76: `site.get('name', '')`
- Line 77: `site.get('country_code', '')`
- Line 134: `device.get('id', '')`
- Line 135: `device.get('name', '')`
- Line 136: `device.get('model', '')`
- Line 137: `device.get('serial', '')`
- Line 138: `device.get('fw_version', '')`
- Line 139: `device.get('mac', '')`
- Line 140: `device.get('status', 'unknown')`

### src\upgrade_portal\api\run_controls\routes.py
- Line 218: `source.get('tier', 2)`
- Line 293: `request.headers.get(IDEMPOTENCY_HEADER, '')`
- Line 620: `request.headers.get(IDEMPOTENCY_HEADER, '')`
- Line 519: `indexed.get(target_id, {})`
- Line 481: `record.get('targets', ())`
- Line 568: `request.headers.get(IDEMPOTENCY_HEADER, '')`
- Line 82: `record.get('targets', ())`
- Line 93: `running.get(reading.mac, reading.version)`

### src\upgrade_portal\api\run_controls\services\bulk.py
- Line 75: `self._expected_tokens.get(site_id, '')`

### src\upgrade_portal\api\run_controls\services\preview.py
- Line 87: `site_counts.get(site_id, 0)`

### src\upgrade_portal\api\run_controls\services\reconciliation.py
- Line 574: `record.get('targets', ())`
- Line 598: `record.get('phases', ())`
- Line 679: `record.get('targets', ())`
- Line 645: `record.get('targets', ())`
- Line 124: `value.get('sources', ())`
- Line 601: `copied.get('total', 0)`

### src\upgrade_portal\app\config.py
- Line 473: `os.environ.get(THEMES_VARIABLE, '')`
- Line 473: `os.environ.get(THEMES_VARIABLE, '')`
- Line 504: `os.environ.get(ALLOWED_ADDRESSES_VARIABLE, '')`
- Line 504: `os.environ.get(ALLOWED_ADDRESSES_VARIABLE, '')`
- Line 250: `os.environ.get(ARANGO_HOST_VARIABLE, DEFAULT_ARANGO_HOST)`
- Line 250: `os.environ.get(ARANGO_HOST_VARIABLE, DEFAULT_ARANGO_HOST)`
- Line 251: `os.environ.get(ARANGO_DATABASE_VARIABLE, DEFAULT_ARANGO_DATABASE)`
- Line 251: `os.environ.get(ARANGO_DATABASE_VARIABLE, DEFAULT_ARANGO_DATABASE)`
- Line 252: `os.environ.get(ARANGO_USERNAME_VARIABLE, DEFAULT_ARANGO_USERNAME)`
- Line 252: `os.environ.get(ARANGO_USERNAME_VARIABLE, DEFAULT_ARANGO_USERNAME)`
- Line 264: `os.environ.get(REDIS_HOST_VARIABLE, DEFAULT_REDIS_HOST)`
- Line 264: `os.environ.get(REDIS_HOST_VARIABLE, DEFAULT_REDIS_HOST)`
- Line 298: `os.environ.get(PROXY_HOPS_VARIABLE, '')`
- Line 298: `os.environ.get(PROXY_HOPS_VARIABLE, '')`
- Line 335: `os.environ.get(variable, '')`
- Line 335: `os.environ.get(variable, '')`
- Line 389: `os.environ.get(SECRET_KEY_VARIABLE, '')`
- Line 389: `os.environ.get(SECRET_KEY_VARIABLE, '')`
- Line 410: `os.environ.get(POLL_VARIABLE, '')`
- Line 410: `os.environ.get(POLL_VARIABLE, '')`
- Additional records: 4

### src\upgrade_portal\app\factory.py
- Line 836: `request.args.get(THEME_ARGUMENT, '')`
- Line 256: `ERROR_CODES.get(status, ERROR_CODES[500])`
- Line 257: `ERROR_MESSAGES.get(status, ERROR_MESSAGES[500])`
- Line 527: `current_app.config.get('E2E_OVERRIDES_ACTIVE', False)`

### src\upgrade_portal\app\routes\audit.py
- Line 55: `request.args.get('limit', 100)`
- Line 56: `request.args.get('offset', 0)`

### src\upgrade_portal\app\routes\auth.py
- Line 625: `request.headers.get(SCRIPT_HEADER, '')`
- Line 1061: `current_app.config.get('BROWSER_TOKEN_SIGNIN_ALLOWED', False)`
- Line 288: `os.environ.get(name, '')`
- Line 288: `os.environ.get(name, '')`
- Line 576: `request.form.get(name, '')`
- Line 755: `current_app.config.get('BROWSER_TOKEN_SIGNIN_ALLOWED', False)`
- Line 422: `error.get(MESSAGE_FIELD, '')`

### src\upgrade_portal\app\routes\capture.py
- Line 1121: `body.get('device_ids', [])`
- Line 1122: `body.get('org_id', '')`
- Line 1123: `body.get('site_id', '')`
- Line 1124: `body.get('tier', TIER_STANDARD)`
- Line 326: `record.get(RUN_FIELD, '')`
- Line 495: `job.get('capture_id', '')`
- Line 603: `body.get(TIER_FIELD, TIER_STANDARD)`
- Line 624: `site.get('id', '')`
- Line 928: `document.get(TIER_FIELD, TIER_STANDARD)`
- Line 1007: `document.get(TIER_FIELD, TIER_STANDARD)`
- Line 1318: `request.args.get(FORMAT_ARGUMENT, '')`
- Line 1382: `request.args.get('site_id', '')`
- Line 1383: `request.args.get(RUN_FIELD, '')`
- Line 1384: `request.args.get(ROLE_FIELD, DEFAULT_ROLE)`
- Line 1388: `status.get(TIER_FIELD, TIER_STANDARD)`
- Line 1400: `status.get('stored_size_bytes', 0)`
- Line 324: `record.get(ROLE_FIELD, '')`
- Line 629: `site.get('name', site_id)`
- Line 659: `site.get('id', '')`
- Line 915: `entry.get('section', '')`
- Additional records: 5

### src\upgrade_portal\app\routes\comparison.py
- Line 197: `data.get('approved_items', [])`
- Line 198: `data.get('rejected_items', [])`
- Line 199: `data.get('engineer_notes', '')`
- Line 200: `data.get('approve_all', False)`
- Line 255: `request.headers.get('X-User-ID', 'anonymous')`
- Line 107: `comparison_doc.get('run_id', '')`
- Line 109: `comparison_doc.get('deltas', [])`
- Line 111: `comparison_doc.get('summary', {})`
- Line 113: `comparison_doc.get('flagged_for_review', [])`
- Line 115: `comparison_doc.get('timestamp', '')`
- Line 117: `comparison_doc.get('approved', False)`
- Line 119: `comparison_doc.get('approved_by', '')`
- Line 121: `comparison_doc.get('approved_at', '')`

### src\upgrade_portal\app\routes\jwt_auth.py
- Line 64: `data.get('username', '')`
- Line 65: `data.get('password', '')`
- Line 177: `data.get('token', '')`
- Line 141: `data.get('username', 'unknown')`

### src\upgrade_portal\app\routes\mist.py
- Line 98: `request.args.get('type', 'all')`

### src\upgrade_portal\app\routes\org_upgrade.py
- Line 143: `current_app.config.get(SERVICE_CONFIG_KEY, OrgUpgradeService)`
- Line 156: `current_app.config.get(OPTIONS_VIEW_CONFIG_KEY, build_options_view)`
- Line 167: `current_app.config.get(OPTIONS_BUILDER_CONFIG_KEY, build_options_record)`
- Line 467: `targets.get('total', 0)`
- Line 513: `data.get('site_upgrades', data.get('upgrades', []))`
- Line 1034: `record.get('children', [])`
- Line 1083: `data.get('site_upgrades', data.get('upgrades', []))`
- Line 1162: `session.get(LAST_JOB_SESSION_KEY, {})`
- Line 246: `source.get('reboot', 'yes')`
- Line 247: `source.get('junos_file_action', 'yes')`
- Line 261: `options.get('strategy', 'big_bang')`
- Line 262: `options.get('reboot', True)`
- Line 263: `options.get('junos_file_action', True)`
- Line 264: `options.get('force', False)`
- Line 356: `options.get('version_ap', first.get('version', ''))`
- Line 360: `options.get('strategy', 'canary')`
- Line 362: `options.get('max_failure_percentage', 5)`
- Line 435: `record.get('operation_id', '')`
- Line 438: `record.get('operation_id', '')`
- Line 480: `entry.get('site_id', nested.get('site_id', ''))`
- Additional records: 74

### src\upgrade_portal\app\routes\review.py
- Line 544: `_REFUSALS.get(reason, _DEFAULT_REFUSAL)`
- Line 1203: `row.get(DEVICE_COUNT_FIELD, stored.get(DEVICE_TOTAL_KEY))`
- Line 1805: `request.args.get(FORMAT_FIELD, '')`
- Line 1806: `request.args.get(SCOPE_FIELD, compare_download.SCOPE_DIFFERENCES)`
- Line 545: `record.get(SCHEMA_VERSION_FIELD, UNKNOWN_VERSION)`
- Line 965: `request.args.get(OUTCOME_FIELD, '')`
- Line 1054: `request.args.get(LIMIT_FIELD, '')`
- Line 1057: `request.args.get(OFFSET_FIELD, '')`
- Line 1686: `view.get(name, fallback)`
- Line 1726: `row.get(CAPTURE_ID_FIELD, '')`
- Line 1778: `request.args.get(BEFORE_FIELD, '')`
- Line 1778: `request.args.get(AFTER_FIELD, '')`
- Line 1800: `request.args.get(BEFORE_FIELD, '')`
- Line 1800: `request.args.get(AFTER_FIELD, '')`
- Line 1730: `copied.get(CAPTURE_ID_FIELD, '')`
- Line 1731: `counts_by_id.get(capture_id, copied)`
- Line 1810: `_EXPORT_MESSAGES.get(result.error, BAD_FORMAT_MESSAGE)`
- Line 1827: `request.args.get(BEFORE_FIELD, '')`
- Line 1828: `request.args.get(AFTER_FIELD, '')`
- Line 1932: `request.args.get(SITE_ID_FIELD, '')`
- Additional records: 2

### src\upgrade_portal\app\routes\runs.py
- Line 204: `data.get('device_ids', [])`
- Line 165: `data.get('user_id', '')`
- Line 178: `data.get('org_id', '')`
- Line 191: `data.get('site_id', '')`
- Line 234: `data.get('notes', '')`

### src\upgrade_portal\app\routes\select.py
- Line 1848: `LOCK_ERROR_STATUS.get(code, CONFLICT_STATUS)`
- Line 338: `parameters.get(ORG_FIELD, '')`
- Line 624: `payload.get(SITE_IDS_FIELD, [])`
- Line 676: `request.headers.get(SCRIPT_HEADER, '')`
- Line 827: `site.get('id', '')`
- Line 831: `counts.get(site_id, 0)`
- Line 1560: `request.args.get(FILTER_FIELD, '')`
- Line 1616: `site.get('name', site_id)`
- Line 1655: `request.args.get(FILTER_FIELD, '')`
- Line 811: `entry.get('id', '')`
- Line 830: `site.get('name', '')`
- Line 1197: `targets_by_mac.get(normalize_device_mac(device.get(MAC_FIELD)), {})`
- Line 1379: `request.args.get(field, '')`
- Line 1475: `request.args.get(FILTER_FIELD, '')`
- Line 1584: `row.get('site_id', '')`
- Line 553: `request.form.get(ORG_FIELD, '')`
- Line 591: `request.form.get(MODE_FIELD, '')`
- Line 854: `site.get('id', '')`
- Line 1104: `device.get(STATUS_FIELD, '')`
- Line 1244: `site.get('id', '')`
- Additional records: 7

### src\upgrade_portal\app\routes\upgrade.py
- Line 614: `current_app.config.get(SELF_READER_KEY, default_self_reader)`
- Line 1163: `built.get(TARGETS_FIELD, [])`
- Line 1164: `built.get('options', {})`
- Line 1289: `record.get(TARGETS_FIELD, [])`
- Line 1888: `current_app.config.get('POLL_INTERVAL_SECONDS', 30)`
- Line 2035: `body.get('device_ids', [])`
- Line 2036: `body.get('firmware_version', '')`
- Line 2037: `body.get('strategy', 'serial')`
- Line 2038: `body.get('rollback_enabled', False)`
- Line 1165: `built.get('selected_types', ['ap', 'switch', 'gateway'])`
- Line 1166: `built.get(WARNINGS_FIELD, [])`
- Line 1288: `record.get('site_id', '')`
- Line 1428: `record.get('options', {})`
- Line 1430: `record.get('options', {})`
- Line 1510: `record.get('site_id', '')`
- Line 1556: `record.get('site_id', '')`
- Line 1663: `record.get('run_id', '')`
- Line 1664: `record.get('site_id', '')`
- Line 1793: `record.get('site_id', '')`
- Line 1839: `record.get('org_id', '')`
- Additional records: 34

### src\upgrade_portal\app\wiring.py
- Line 135: `run.get('run_id', '')`
- Line 598: `record.get('site_id', '')`
- Line 769: `bindings.get(EMAIL_FIELD, '')`
- Line 860: `record.get('org_id', '')`
- Line 946: `record.get('site_id', '')`
- Line 971: `record.get('run_id', '')`
- Line 1000: `record.get('run_id', '')`
- Line 1021: `record.get('run_id', '')`
- Line 250: `run.get('run_id', '')`
- Line 463: `request.get('run_id', '')`
- Line 464: `request.get('ordinal', POST_CHECK_ORDINAL)`
- Line 525: `record.get('run_id', '')`
- Line 600: `record.get('targets', ())`
- Line 603: `record.get('options', {})`
- Line 765: `record.get('org_id', '')`
- Line 766: `record.get('site_id', '')`
- Line 767: `record.get('tier', DEFAULT_TIER)`
- Line 770: `record.get('org_name', '')`
- Line 771: `record.get('site_name', '')`
- Line 796: `record.get('run_id', '')`
- Additional records: 9

### src\upgrade_portal\auth\session.py
- Line 276: `request.headers.get('Authorization', '')`
- Line 508: `pause_state_dict.get('next_device_index', 0)`
- Line 510: `pause_state_dict.get('device_count', 0)`
- Line 512: `pause_state_dict.get('current_phase', 'resuming')`
- Line 399: `upgrade_run.get('initiated_by', 'unknown')`
- Line 400: `upgrade_run.get('phase', 'idle')`
- Line 406: `upgrade_run.get('next_device_index', 0)`
- Line 407: `upgrade_run.get('failed_devices', [])`
- Line 401: `upgrade_run.get('device_statuses', [])`
- Line 410: `upgrade_run.get('retry_count', 0)`
- Line 403: `upgrade_run.get('device_statuses', [])`

### src\upgrade_portal\capture\assembly.py
- Line 959: `names.get(_address(row.get('device_mac')), '')`
- Line 555: `sections.clients.get('wired', ())`
- Line 556: `sections.clients.get('wireless', ())`
- Line 557: `sections.clients.get('guest', ())`
- Line 660: `sections.clients.get(group, ())`
- Line 1108: `sections.clients.get(name, ())`

### src\upgrade_portal\capture\clients.py
- Line 327: `os.environ.get(PAGE_LIMIT_VARIABLE, '')`
- Line 327: `os.environ.get(PAGE_LIMIT_VARIABLE, '')`

### src\upgrade_portal\capture\collector.py
- Line 922: `REASON_ROWS.get(section, (section,))`
- Line 921: `reason.get('section', '')`
- Line 969: `job.get('ordinal', assembly.FIRST_ORDINAL)`
- Line 970: `job.get('actor_email', '')`
- Line 1053: `job.get('capture_id', '')`
- Line 1054: `job.get('tier', TIER_STANDARD)`
- Line 1169: `job.get('capture_id', '')`
- Line 676: `job.get('tier', TIER_STANDARD)`
- Line 1147: `document.get('capture_id', '')`
- Line 673: `job.get('org_id', '')`
- Line 673: `job.get('site_id', '')`
- Line 968: `job.get('run_id', '')`
- Line 973: `job.get('capture_id', '')`
- Line 1001: `job.get('org_id', '')`
- Line 1002: `job.get('org_name', '')`
- Line 1003: `job.get('site_id', '')`
- Line 1004: `job.get('site_name', '')`
- Line 275: `self._groups.get(name, '')`

### src\upgrade_portal\capture\export.py
- Line 310: `self.values.get(name, '')`
- Line 392: `heading.get(name, '')`
- Line 485: `row.get('mac', '')`

### src\upgrade_portal\capture\extras.py
- Line 192: `_MESSAGES.get(self.reason, _MESSAGES[REASON_CALL_FAILED])`
- Line 251: `payload.get('results', [])`

### src\upgrade_portal\capture\service.py
- Line 285: `capture_doc.get('user_id', '')`

### src\upgrade_portal\capture\store.py
- Line 1006: `digests.get('whole', '')`
- Line 1240: `payload.get(target.key_field, '')`
- Line 1278: `payload.get(_CAPTURE_TARGET.key_field, '')`
- Line 1447: `capture.get('capture_id', '')`
- Line 1448: `capture.get('run_id', '')`
- Line 1597: `capture.get('capture_id', '')`
- Line 1634: `edge.get('_from', '')`
- Line 1698: `edge.get('_key', '')`
- Line 419: `record.get('capture_id', '')`
- Line 1221: `_MESSAGES.get(verification.reason, _MESSAGES[REASON_ABSENT])`
- Line 1453: `capture.get('role', '')`
- Line 1598: `capture.get('run_id', '')`
- Line 1506: `edge.get('_key', '')`
- Line 1535: `edge.get('_key', '')`
- Line 1557: `capture.get('capture_id', '')`
- Line 1557: `capture.get('run_id', '')`
- Line 473: `record.get(CAPTURE_STATE_FIELD, '')`

### src\upgrade_portal\capture\tables.py
- Line 363: `_UNAVAILABLE_MESSAGES.get(reason_code, _DEFAULT_UNAVAILABLE_MESSAGE)`

### src\upgrade_portal\compare\download.py
- Line 550: `capture.get(_CAPTURE_ID_KEY, '')`
- Line 551: `capture.get(_ROLE_KEY, '')`
- Line 552: `capture.get(compare_statistics.STARTED_AT_KEY, '')`
- Line 555: `capture.get(compare_statistics.FINISHED_AT_KEY, '')`
- Line 576: `named.get(_SITE_NAME_KEY, '')`
- Line 577: `named.get(_SITE_ID_KEY, '')`
- Line 578: `named.get(_ORG_NAME_KEY, '')`

### src\upgrade_portal\compare\lock_audit.py
- Line 89: `earlier.get('actor_email', '')`
- Line 92: `earlier.get('org_id', '')`
- Line 93: `earlier.get('site_id', '')`
- Line 157: `record.get('inferred', False)`

### src\upgrade_portal\compare\render.py
- Line 582: `_STATISTIC_LABELS.get(name, name)`
- Line 583: `flat.get(name, 0)`

### src\upgrade_portal\compare\service.py
- Line 875: `pre_capture.get('devices', [])`
- Line 876: `post_capture.get('devices', [])`
- Line 1058: `pre_capture.get('devices', [])`
- Line 1059: `post_capture.get('devices', [])`
- Line 327: `settle_results.get('failed_checks', [])`
- Line 791: `delta.get('severity', 'low')`
- Line 173: `settle_results.get('passed', False)`
- Line 928: `pre_dev.get('name', device_id)`
- Line 930: `self.SEVERITY_LEVELS.get('device_removed', 'high')`
- Line 971: `post_dev.get('name', device_id)`
- Line 972: `self.SEVERITY_LEVELS.get('device_added', 'medium')`
- Line 1077: `self.SEVERITY_LEVELS.get('firmware_upgrade', 'high')`
- Line 1082: `self.SEVERITY_LEVELS.get('firmware_downgrade', 'critical')`

### src\upgrade_portal\persistence\actions\models.py
- Line 151: `summary.get('decision_basis_digest', '')`
- Line 1099: `document.get('items', ())`
- Line 1103: `document.get('site_blocks', {})`
- Line 625: `document.get('site_id', '')`
- Line 643: `document.get('prior_state', '')`
- Line 644: `document.get('final_state', '')`
- Line 645: `document.get('checked_at', '')`
- Line 646: `document.get('completed_at', '')`
- Line 651: `document.get('message', '')`
- Line 652: `document.get('result_run_id', '')`
- Line 654: `document.get('live_run_id', '')`

### src\upgrade_portal\persistence\actions\repository.py
- Line 384: `stored.get('_rev', '')`
- Line 309: `_ACTION_STRATEGY.get('indexes', ())`
- Line 311: `_ACTION_STRATEGY.get('unique_constraints', ())`
- Line 295: `item.get('fields', ())`

### src\upgrade_portal\persistence\actions\transactions.py
- Line 62: `self.document.get('run_id', self.run_id)`

### src\upgrade_portal\runtime\dependencies.py
- Line 150: `os.environ.get(AUTOSTART_VARIABLE, '')`
- Line 150: `os.environ.get(AUTOSTART_VARIABLE, '')`

### src\upgrade_portal\runtime\identity.py
- Line 285: `os.environ.get(name, '')`
- Line 285: `os.environ.get(name, '')`
- Line 250: `os.environ.get(name, '')`
- Line 250: `os.environ.get(name, '')`
- Line 954: `entry.get(ORG_PRIVILEGE_FIELD, '')`
- Line 974: `entry.get('name', '')`

### src\upgrade_portal\runtime\lock.py
- Line 155: `os.environ.get(LOCK_RENEWAL_MAX_SECONDS_VARIABLE, '')`
- Line 155: `os.environ.get(LOCK_RENEWAL_MAX_SECONDS_VARIABLE, '')`
- Line 787: `stored.get('lock_token', '')`
- Line 788: `stored.get('run_id', '')`
- Line 789: `stored.get('acquired_at', '')`
- Line 790: `stored.get('refreshed_at', '')`
- Line 779: `stored.get('actor_email', '')`
- Line 780: `stored.get('browser_id', '')`
- Line 781: `stored.get('identity_kind', 'email')`

### src\upgrade_portal\runtime\runs.py
- Line 590: `record.get('state', RunState.CREATED.value)`
- Line 735: `cls.PHASE_NOUNS.get(str(phase.get('name', '')), ('device', 'devices'))`
- Line 793: `cls.STATE_MESSAGES.get(state, 'The run is in progress.')`
- Line 430: `record.get('run_id', '')`
- Line 453: `record.get('run_id', '')`
- Line 499: `record.get('state', '')`
- Line 699: `entry.get('name', '')`
- Line 699: `record.get('phases', [])`
- Line 712: `record.get('targets', [])`
- Line 734: `phase.get('total', 0)`
- Line 734: `phase.get('settled', 0)`
- Line 735: `phase.get('name', '')`
- Line 762: `cls.PHASE_NOUNS.get(family, ('device', 'devices'))`
- Line 808: `record.get('run_id', '')`
- Line 840: `record.get('targets', [])`
- Line 900: `source.get('state', PhaseState.PENDING.value)`
- Line 901: `source.get('settled', 0)`
- Line 902: `source.get('total', 0)`

### src\upgrade_portal\runtime\signals.py
- Line 346: `run.get('run_id', '')`
- Line 135: `record.get('message', '')`
- Line 194: `record.get('requested_by', '')`
- Line 195: `record.get('requested_at', '')`
- Line 196: `record.get('confirmation_text', STOP_CONFIRMATION_TEXT)`
- Line 197: `record.get('scope', STOP_SCOPE_RUN)`

### src\upgrade_portal\upgrade\driver.py
- Line 900: `record.get('targets', [])`
- Line 1029: `record.get('targets', [])`
- Line 1049: `record.get('options', {})`
- Line 1147: `record.get('targets', [])`
- Line 1212: `record.get('tier', TIER_STANDARD)`
- Line 1643: `record.get('targets', [])`
- Line 1673: `record.get('targets', [])`
- Line 1825: `record.get('run_id', '')`
- Line 1862: `record.get('run_id', '')`
- Line 752: `record.get('org_id', '')`
- Line 752: `record.get('site_id', '')`
- Line 903: `record.get('run_id', '')`
- Line 904: `record.get('org_id', '')`
- Line 905: `record.get('site_id', '')`
- Line 1082: `entry.get(key, 0)`
- Line 1125: `entry.get('state', '')`
- Line 1358: `record.get('run_id', '')`
- Line 1382: `record.get('run_id', '')`
- Line 1477: `record.get('run_id', '')`
- Line 1534: `record.get('run_id', '')`
- Additional records: 18

### src\upgrade_portal\upgrade\events.py
- Line 602: `event.get('type', '')`
- Line 208: `row.get('key', '')`

### src\upgrade_portal\upgrade\options.py
- Line 231: `OPTION_HELP.get(field, ('', UNKNOWN_OPTION_RULE))`
- Line 317: `versions_by_model.get(str(device['model']).strip(), ())`
- Line 1291: `os.environ.get(variable, '')`
- Line 1291: `os.environ.get(variable, '')`
- Line 1505: `choice.get('version_target', '')`
- Line 1538: `versions_by_model.get(model, ())`
- Line 513: `device.get('model', '')`
- Line 569: `device.get('model', '')`
- Line 572: `by_model.get(model, ())`
- Line 583: `device.get('version', '')`
- Line 1426: `device.get('name', '')`
- Line 1428: `device.get('model', '')`
- Line 1429: `device.get('version', '')`
- Line 1537: `device.get('model', '')`
- Line 576: `selections.get(device_type, {})`
- Line 1622: `entry.get('name', '')`
- Line 1624: `entry.get('model', '')`
- Line 1625: `entry.get('version_before', '')`
- Line 305: `device.get('model', '')`
- Line 570: `device.get('type', '')`
- Additional records: 4

### src\upgrade_portal\upgrade\phase_gate.py
- Line 536: `entry.get('version_before', '')`
- Line 538: `entry.get('version_target', '')`
- Line 535: `entry.get('device_type', '')`

### src\upgrade_portal\upgrade\service.py
- Line 409: `upgrade_run.get('device_status', {})`
- Line 724: `upgrade_run.get('device_status', {})`
- Line 623: `upgrade_run.get('rollback_enabled', False)`

### src\utils\address_utils.py
- Line 108: `raw.get('Reason', 'Address in skip list')`
- Line 499: `comparison_result.get('place_type', '')`
- Line 1003: `result.get('address', {})`
- Line 1022: `result.get('display_name', '')`
- Line 302: `_STATE_MAPPING.get(state, state)`
- Line 390: `parsed.get('address_line_1', '')`
- Line 391: `parsed.get('city', '')`
- Line 392: `parsed.get('state', '')`
- Line 393: `parsed.get('postal_code', '')`
- Line 498: `mist_result.get('place_type', '')`
- Line 893: `address_dict.get(k, '')`
- Line 1019: `result.get('importance', 0.0)`
- Line 1045: `result.get('display_name', '')`
- Line 1046: `result.get('type', '')`
- Line 1047: `result.get('class', '')`
- Line 1048: `result.get('address', {})`
- Line 400: `parsed.get('address_line_1', '')`
- Line 400: `parsed.get('address_line_2', '')`
- Line 990: `result.get('type', '')`
- Line 991: `result.get('class', '')`
- Additional records: 20

### src\utils\environment_utils.py
- Line 39: `os.environ.get(explicit_var, '')`
- Line 39: `os.environ.get(explicit_var, '')`

### src\utils\performance\recorder.py
- Line 162: `source.get('MISTHELPER_PERF_SAMPLE_RATE', '1.0')`
- Line 172: `source.get('MISTHELPER_PERF_CAPACITY', '2048')`
- Line 182: `source.get('MISTHELPER_PERF_MAX_BYTES', str(DEFAULT_MAX_BYTES))`
- Line 137: `source.get('MISTHELPER_PERF_CPU', '1')`
- Line 152: `source.get('MISTHELPER_PERF_LEVEL', 'off')`

### src\utils\rate_limiting.py
- Line 289: `usage.get('requests', 0)`
- Line 290: `usage.get('request_limit', _DEFAULT_REQUEST_LIMIT)`
- Line 508: `api_usage_cache.get('previous_elapsed', elapsed)`
- Line 541: `tuning_data.get('error', [])`
- Line 467: `tuning_data.get('integral', 0.0)`

### src\utils\tls_policy.py
- Line 39: `os.environ.get(SKIP_VERIFY_ENV_VAR, '')`
- Line 39: `os.environ.get(SKIP_VERIFY_ENV_VAR, '')`

### src\utils\zscaler_catalogue.py
- Line 908: `slot.get('seen_in_clouds', [])`
- Line 1191: `merged.get('proxy_hostnames', [])`
- Line 1192: `merged.get('vpn_hostnames', [])`
- Line 1193: `merged.get('by_city', {})`
- Line 843: `slot.get('proxy_hostnames', [])`
- Line 846: `slot.get('vpn_hostnames', [])`

### src\utils\zscaler_probe.py
- Line 781: `probes.get('roles', [])`
- Line 425: `cert.get('subject', ())`
- Line 426: `cert.get('issuer', ())`
- Line 784: `role.get('fqdns', [])`
- Line 813: `cenr.get(key, [])`
- Line 678: `role.get('role', '')`
- Line 679: `role.get('description', '')`
- Line 681: `role.get('critical', False)`

### src\wan_hub_group_manager.py
- Line 312: `profile.get('name', '')`
- Line 313: `vpn_data.get(name, [])`
- Line 409: `profile.get('name', '')`
- Line 410: `vpn_data.get(name, [])`
- Line 423: `profile.get('name', '')`
- Line 424: `vpn_data.get(name, [])`
- Line 514: `vpn_copy.get('paths', {})`
- Line 212: `vpn.get('id', '')`
- Line 213: `vpn.get('name', '')`
- Line 214: `vpn.get('paths', {})`
- Line 229: `profile.get('name', '')`
- Line 245: `profile.get('name', '')`
- Line 246: `vpn_data.get(name, [])`
- Line 303: `selected.get('name', '')`
- Line 185: `vpn.get('type', _UNKNOWN_TYPE)`
- Line 186: `type_counts.get(vpn_type, 0)`
- Line 217: `path_value.get('pod', self.POD_DEFAULT)`
- Line 149: `profile.get('name', '')`

### src\wan_vpn_builder.py
- Line 161: `created_vpn.get('id', '')`
- Line 315: `profile.get('name', '')`
- Line 316: `profile.get('port_config', {})`
- Line 426: `vpn_body.get('paths', {})`
- Line 520: `profile.get('name', '')`
- Line 136: `vpn.get('name', '')`
- Line 196: `config.get('usage', '')`
- Line 392: `vpn.get('name', '')`
- Line 393: `vpn.get('type', 'unknown')`
- Line 413: `profile.get('name', '')`
- Line 414: `profile.get('port_config', {})`
- Line 442: `vpn_body.get('type', '')`
- Line 443: `vpn_body.get('path_selection', {})`
- Line 652: `fresh_profile.get('port_config', {})`
- Line 758: `profile.get('name', '')`
- Line 759: `profile.get('id', '')`
- Line 361: `created.get('id', '')`
- Line 394: `vpn.get('paths', {})`
- Line 334: `profile.get('name', '')`

### src\websocket\commands.py
- Line 247: `mac_table_result.get('raw', '')`
- Line 248: `mac_table_result.get('Output', '')`

### src\websocket\diagnostics\arp_executor.py
- Line 133: `device_info.get('type', 'unknown')`
- Line 134: `device_info.get('model', 'unknown')`
- Line 135: `device_info.get('name', f'Device {device_id[:8]}')`
- Line 148: `device_info.get('type', 'unknown')`
- Line 149: `device_info.get('model', 'unknown')`
- Line 312: `device_info.get('type', 'unknown')`
- Line 330: `arp_result.get('raw', '')`
- Line 331: `arp_result.get('Output', '')`
- Line 385: `device_info.get('type', 'unknown')`
- Line 386: `device_info.get('model', 'unknown')`
- Line 387: `device_info.get('name', 'Unknown Device')`
- Line 453: `gateway_data.get('columns', [])`
- Line 458: `gateway_data.get('rows', [])`
- Line 533: `device_info.get('type', 'unknown')`
- Line 534: `device_info.get('model', 'unknown')`
- Line 559: `device_info.get('type', 'unknown')`
- Line 560: `device_info.get('name', device_id[:8])`
- Line 460: `col.get('display_name', col.get('id', 'Unknown'))`
- Line 460: `col.get('id', 'Unknown')`
- Line 515: `column.get('id', '')`
- Additional records: 2

### src\websocket\diagnostics\ping_executor.py
- Line 300: `ping_result.get('raw', '')`
- Line 301: `ping_result.get('Output', '')`

### src\websocket\manager.py
- Line 148: `os.getenv('MIST_HOST', 'api.mist.com')`
- Line 46: `os.getenv('DEBUG', '')`

### src\websocket\polling\completion_detector.py
- Line 361: `msg.get('raw', '')`

### src\websocket\polling\message_router.py
- Line 239: `message_data.get(_CHANNEL_KEY, '')`
- Line 300: `data_payload.get(_DATA_KEY, {})`
- Line 240: `message_data.get(_DATA_KEY, {})`
- Line 204: `message_data.get(_EVENT_KEY, 'unknown')`
- Line 205: `message_data.get(_CHANNEL_KEY, 'unknown')`

### src\websocket\polling\result_collector.py
- Line 276: `self._deps.results.get(ctx.session_id, [])`
- Line 249: `r.get('raw', '')`

### src\websocket\polling\result_combiner.py
- Line 109: `result.get('raw', '')`

### src\websocket\service_ping_discovery.py
- Line 172: `config.get('service_policies', [])`
- Line 187: `config.get('routing_instances', [])`
- Line 199: `policy.get('services', [])`
- Line 275: `stats_data.get('service_stat', [])`
- Line 579: `details.get('type', 'custom')`
- Line 580: `details.get('description', '')`
- Line 154: `config.get('router', {})`
- Line 226: `router.get('tenants', [])`
- Line 229: `router.get('services', [])`

### src\websocket\service_ping_manager.py
- Line 176: `self.device_info.get('type', 'unknown')`
- Line 177: `self.device_info.get('model', 'unknown')`
- Line 183: `_DEVICE_TYPE_LABELS.get(device_type, 'Unknown device type')`
- Line 246: `response.data.get('session', '')`
- Line 328: `result.get('raw', '')`
- Line 329: `result.get('Output', '')`
- Line 340: `self.device_info.get('type', 'unknown')`
- Line 341: `self.device_info.get('model', 'unknown')`
- Line 342: `self.device_info.get('name', 'Unknown Device')`
- Line 396: `self.device_info.get('type', 'unknown')`
- Line 397: `self.device_info.get('name', 'Unknown Device')`
- Line 399: `_TROUBLESHOOTING_TIPS.get(device_type, _DEFAULT_TIPS)`
- Line 361: `self.device_info.get('name', 'Unknown Device')`
- Line 362: `self.device_info.get('type', 'unknown')`

### starlink_dashboard.py
- Line 49: `os.environ.get(GPS_EXACT_ENV_VAR, '')`
- Line 49: `os.environ.get(GPS_EXACT_ENV_VAR, '')`
- Line 1291: `cls._HARDWARE_TEST_RESULTS.get(diag.hardware_self_test, 'NO RESULT')`
- Line 1667: `stats.get('connected', False)`
- Line 1671: `stats.get('service_status', 'UNKNOWN')`
- Line 1675: `stats.get('hardware_test', 'UNKNOWN')`
- Line 1679: `stats.get('obstruction_status', 'UNKNOWN')`
- Line 1686: `stats.get('software_version', 'N/A')`
- Line 1691: `stats.get('hardware_version', 'N/A')`
- Line 1694: `stats.get('utc_offset_hours', 0)`
- Line 1698: `stats.get('azimuth_current', 0.0)`
- Line 1701: `stats.get('elevation_current', 0.0)`
- Line 1704: `stats.get('azimuth_target', 0.0)`
- Line 1707: `stats.get('elevation_target', 0.0)`
- Line 1719: `stats.get('status_message', 'No status available')`
- Line 1684: `stats.get('terminal_id', 'N/A')`

### tests\bootstrap\test_dependency_check_venv_guard.py
- Line 34: `env.get(key, default)`

### tests\contract\packaging\test_ops_portal_job.py
- Line 93: `step.get('timeout-minutes', 0)`

### tests\contract\packaging\test_wheel_layout.py
- Line 60: `wheel_target.get('packages', [])`
- Line 71: `wheel_target.get('packages', [])`
- Line 80: `wheel_target.get('packages', [])`
- Line 93: `wheel_target.get('force-include', {})`
- Line 109: `target.get('packages', [])`
- Line 109: `target.get('force-include', {})`

### tests\contract\test_exclusion_drift.py
- Line 41: `step.get('run', '')`

### tests\contract\upgrade_portal\conftest.py
- Line 92: `self.payloads.get(name, [])`

### tests\contract\upgrade_portal\test_capture_attach.py
- Line 151: `record.get('run_id', '')`

### tests\contract\upgrade_portal\test_comparison.py
- Line 427: `row.get('outcome', '')`

### tests\contract\upgrade_portal\test_comparison_export.py
- Line 348: `response.headers.get(DISPOSITION_HEADER, '')`
- Line 448: `response.headers.get(DISPOSITION_HEADER, '')`

### tests\contract\upgrade_portal\test_container_naming_policy.py
- Line 109: `body.get('ports', [])`
- Line 119: `body.get('ports', [])`
- Line 102: `body.get('name', '')`
- Line 101: `document.get('networks', {})`
- Line 101: `document.get('volumes', {})`
- Line 94: `body.get('container_name', '')`
- Line 102: `body.get('name', '')`

### tests\contract\upgrade_portal\test_errors.py
- Line 106: `response.headers.get(CONTENT_TYPE_HEADER, '')`
- Line 122: `response.headers.get(ALLOW_HEADER, '')`

### tests\contract\upgrade_portal\test_lock.py
- Line 411: `body.get('error', {})`
- Line 398: `body.get('error', {})`

### tests\contract\upgrade_portal\test_no_credential_leak.py
- Line 460: `answer.headers.get(LOCATION_HEADER, '')`

### tests\contract\upgrade_portal\test_org_upgrade_routes.py
- Line 863: `body.get('error', {})`

### tests\contract\upgrade_portal\test_run_status.py
- Line 289: `body.get('error', {})`

### tests\contract\upgrade_portal\test_upgrade_options.py
- Line 281: `body.get('targets', [])`
- Line 484: `body.get('error', {})`

### tests\contract\upgrade_portal\test_upgrade_routes\test_bulk_actions.py
- Line 163: `record.get('run_id', '')`
- Line 374: `body.get('error', {})`
- Line 361: `body.get('error', {})`

### tests\contract\upgrade_portal\test_upgrade_start.py
- Line 155: `record.get('run_id', '')`
- Line 373: `body.get('error', {})`

### tests\contract\upgrade_portal\test_upgrade_stop.py
- Line 339: `body.get('error', {})`
- Line 321: `body.get('error', {})`

### tests\e2e\upgrade_portal\conftest.py
- Line 82: `os.environ.get('UPGRADE_PORTAL_E2E_RUN_ID', '')`
- Line 82: `os.environ.get('UPGRADE_PORTAL_E2E_RUN_ID', '')`
- Line 1110: `record.get('run_id', '')`
- Line 1085: `job.get('tier', capture.TIER_STANDARD)`

### tests\e2e\upgrade_portal\test_assets.py
- Line 356: `answer.headers.get(CSP_HEADER, '')`
- Line 373: `answer.headers.get(CSP_HEADER, '')`

### tests\e2e\upgrade_portal\test_comparison.py
- Line 536: `answer.headers.get('content-disposition', '')`

### tests\e2e\upgrade_portal\test_history_layout.py
- Line 98: `values.get('filename', '')`

### tests\e2e\upgrade_portal\test_run_controls\test_existing.py
- Line 194: `body.get('code', '')`
- Line 197: `body.get('details', {})`

### tests\e2e\upgrade_portal\test_stop.py
- Line 245: `body.get('code', '')`
- Line 248: `body.get('details', {})`

### tests\e2e\upgrade_portal\test_two_operators.py
- Line 302: `body.get(ERROR_FIELD, {})`
- Line 362: `body.get(ERROR_FIELD, {})`

### tests\e2e\upgrade_portal\test_upgrade.py
- Line 269: `body.get('code', '')`
- Line 272: `body.get('details', {})`

### tests\guardrails\test_auto_merge_issue_close.py
- Line 206: `step.get('run', '')`

### tests\guardrails\test_changelog_fragment_policy.py
- Line 102: `os.environ.get('GITHUB_BASE_REF', '')`
- Line 102: `os.environ.get('GITHUB_BASE_REF', '')`
- Line 257: `os.environ.get('GITHUB_HEAD_REF', '')`
- Line 257: `os.environ.get('GITHUB_HEAD_REF', '')`

### tests\guardrails\test_ci_gate_triggers.py
- Line 110: `trigger.get('branches', [])`

### tests\guardrails\test_codeql_register_gate.py
- Line 45: `job.get('continue-on-error', False)`
- Line 57: `workflow.get('env', {})`
- Line 58: `job.get('env', {})`
- Line 49: `step.get('continue-on-error', False)`
- Line 91: `step.get('run', '')`
- Line 61: `step.get('env', {})`
- Line 66: `step.get('uses', '')`

### tests\guardrails\test_compose_naming_policy.py
- Line 60: `service.get('ports', [])`
- Line 74: `service.get('container_name', '')`
- Line 165: `service.get('networks', [])`
- Line 87: `volume.get('name', '')`

### tests\guardrails\test_container_policy_docs.py
- Line 79: `service.get('ports', [])`

### tests\guardrails\test_container_tls_verification.py
- Line 163: `settings.get(name, 'unset')`

### tests\guardrails\test_performance_hook_catalog.py
- Line 222: `symbol_index.get(row['file_path'], [])`
- Line 232: `counts.get(row[column], 0)`

### tests\integration\conftest.py
- Line 92: `os.getenv('MIST_HOST', 'api.mist.com')`

### tests\integration\test_compose_deploy.py
- Line 16: `os.environ.get('COMPOSE_TEST', '0')`
- Line 16: `os.environ.get('COMPOSE_TEST', '0')`
- Line 34: `os.environ.get('ARANGO_ROOT_PASSWORD', 'misthelper')`
- Line 34: `os.environ.get('ARANGO_ROOT_PASSWORD', 'misthelper')`
- Line 45: `os.environ.get('REDIS_PASSWORD', 'misthelper')`
- Line 45: `os.environ.get('REDIS_PASSWORD', 'misthelper')`

### tests\integration\test_runtime_coupling.py
- Line 35: `os.getenv('RUNTIME_COUPLING_PROFILES', '')`

### tests\integration\test_wan_vpn_builder_live.py
- Line 141: `created.get('id', '')`
- Line 180: `created.get('id', '')`
- Line 57: `vpn.get('id', '')`
- Line 56: `vpn.get('name', '')`
- Line 261: `created_vpn.get('id', '')`

### tests\integration\upgrade_portal\test_two_operators.py
- Line 479: `body.get('error', {})`
- Line 492: `body.get('error', {})`

### tests\maps\test_viewer_callbacks_wave_e2.py
- Line 87: `it.get('name', default_name)`
- Line 90: `it.get('name', default_name)`

### tests\support\lock_store_double.py
- Line 170: `record.get(EMAIL_FIELD, '')`

### tests\support\rehearsal\cloud.py
- Line 167: `self._counts.get(name, 0)`
- Line 315: `RECONNECT_TYPES.get(device_type, 'AP_CONNECTED')`
- Line 196: `self._counts.get(name, 0)`
- Line 259: `body.get('results', [])`

### tests\support\rehearsal\harness.py
- Line 175: `request.get('run_id', '')`
- Line 147: `run.get('run_id', '')`
- Line 148: `run.get('state', '')`
- Line 421: `entry.get('name', '')`

### tests\support\upgrade_portal_e2e\__init__.py
- Line 100: `seams.get('captures', ())`
- Line 102: `seams.get('cloud_scripts', {})`

### tests\support\upgrade_portal_e2e\records\actions.py
- Line 204: `prior.get('_rev', '0')`

### tests\support\upgrade_portal_e2e\records\cloud.py
- Line 36: `record.get('value', [])`

### tests\support\upgrade_portal_e2e\records\portal.py
- Line 209: `decoded.get('lock_token', '')`
- Line 56: `prior.get('_rev', '0')`

### tests\test_clear_bpdu_error.py
- Line 40: `captured.get('body', {})`
- Line 40: `captured.get('body', {})`

### tests\test_clear_learned_macs.py
- Line 36: `captured.get('body', {})`

### tests\test_clear_policy_hit_count.py
- Line 39: `captured.get('body', {})`

### tests\test_issue_429_log_parity.py
- Line 87: `site_def.get('source', 'MistHelper.py')`

### tests\test_ticket_manager.py
- Line 663: `sample_details.get(ticket_id, {})`

### tests\tools\test_quality_analyzer\test_cli.py
- Line 167: `report.get('stale_baseline_entries', [])`

### tests\tools\test_quality_analyzer\test_cli_aggregate.py
- Line 88: `report.get('findings', [])`
- Line 115: `report.get('findings', [])`
- Line 137: `report.get('parse_errors', [])`

### tests\tools\test_quality_analyzer\test_golden_repo.py
- Line 134: `report.get('findings', [])`
- Line 110: `report.get('skipped_files', [])`

### tests\unit\_test_arango_writer_helpers.py
- Line 449: `mapping.get('ensure_target_vertices', [])`
- Line 518: `COLLECTION_VERTEX_MAP.get(op, {})`
- Line 502: `COLLECTION_VERTEX_MAP.get(op, {})`

### tests\unit\bootstrap\test_dependency_check_paths.py
- Line 93: `installed_versions.get(name, '')`
- Line 94: `version_satisfies.get((installed, spec), True)`
- Line 97: `latest_versions.get(name, '')`

### tests\unit\container\test_write_session_env_script.py
- Line 62: `os.environ.get('PATH', '/usr/bin:/bin')`
- Line 62: `os.environ.get('PATH', '/usr/bin:/bin')`

### tests\unit\device\test_ap_profile_migration_manager.py
- Line 716: `payload.get('source_profile_id', 'src')`
- Line 717: `payload.get('target_profile_id', 'tgt')`

### tests\unit\export\test_data_exporter.py
- Line 399: `DataExporter._last_snapshot_times.get('listStuff', 0.0)`

### tests\unit\metrics_gateway\test_snmp_and_service.py
- Line 347: `os.environ.get('METRICS_SITE_IDS', '')`
- Line 347: `os.environ.get('METRICS_SITE_IDS', '')`

### tests\unit\org\test_org_synthetic_probes_manager.py
- Line 166: `cenr_source.get('vpn_hostnames', [])`
- Line 1288: `row.get('probes', [])`
- Line 2557: `v.get('target', '')`

### tests\unit\test_arango_writer.py
- Line 1614: `mapping.get('ensure_target_vertices', [])`
- Line 1773: `mapping.get('ensure_target_vertices', [])`

### tests\unit\test_csv_comparator.py
- Line 108: `d.get('name', d.get('serial', 'unknown'))`
- Line 108: `d.get('serial', 'unknown')`

### tests\unit\test_e911_bssid.py
- Line 612: `call_kwargs.kwargs.get('filename_or_table', call_kwargs[1].get('filename_or_table', ''))`

### tests\unit\test_offline_device_reporter.py
- Line 53: `device.get('type', 'unknown')`
- Line 57: `site_lookup.get(device.get('site_id', ''), 'Unknown Site')`
- Line 99: `type_counts.get(device_type, 0)`
- Line 57: `device.get('site_id', '')`
- Line 93: `type_counts.get(device_type, 0)`
- Line 95: `site_counts.get(site_name, 0)`
- Line 64: `device.get('mac', '')`
- Line 65: `device.get('serial', '')`
- Line 66: `device.get('model', '')`
- Line 69: `device.get('status', 'disconnected')`

### tests\unit\test_org_data_collector.py
- Line 187: `kwargs.get('data_type', '?')`

### tests\unit\test_ssid_template_consolidation.py
- Line 1036: `config.get('band', '')`

### tests\unit\test_wan_hub_group_manager.py
- Line 269: `body.get('paths', {})`

### tests\unit\upgrade_portal\test_capture_lock_holder.py
- Line 281: `error.get('code', '')`

### tests\unit\upgrade_portal\test_capture_start_lock_grant.py
- Line 312: `error.get('code', '')`

### tests\unit\upgrade_portal\test_compare_client_present_counts.py
- Line 89: `sizes.get(kind, 0)`

### tests\unit\upgrade_portal\test_config.py
- Line 157: `self.values.get(key, default)`

### tests\unit\upgrade_portal\test_confirm_warning.py
- Line 112: `values.get('filename', '')`

### tests\unit\upgrade_portal\test_guardrails.py
- Line 446: `COMMENT_PATTERNS.get(suffix, ())`
- Line 209: `IDENTIFIER_FIELDS.get(type(node), ())`
- Line 464: `entry.get('category', '')`
- Line 488: `entry.get('type', '')`
- Line 467: `entry.get('skip_reason', '')`

### tests\unit\upgrade_portal\test_history_device_type.py
- Line 96: `values.get('filename', '')`
- Line 132: `window.get('total', len(rows))`

### tests\unit\upgrade_portal\test_history_layout.py
- Line 113: `values.get('filename', '')`

### tests\unit\upgrade_portal\test_history_view.py
- Line 167: `values.get('filename', '')`

### tests\unit\upgrade_portal\test_org_picker.py
- Line 132: `values.get('filename', '')`

### tests\unit\upgrade_portal\test_run_adopts_precheck.py
- Line 60: `row.get('started_at', '')`

### tests\unit\upgrade_portal\test_upgrade_driver.py
- Line 177: `self.state_for.get(phase, PhaseState.SETTLED.value)`
- Line 228: `record.get('targets', [])`
- Line 1141: `self.outcomes.get(phase, driver.PhaseOutcome(phase, settled=total, total=total))`
- Line 116: `run.get('state', '')`
- Line 126: `record.get('phases', [])`

### tests\unit\upgrade_portal\test_upgrade_site_name.py
- Line 99: `values.get('filename', '')`

### tests\unit\utils\test_zscaler_catalogue.py
- Line 670: `role_body.get('fqdns', [])`
- Line 619: `city_slot.get(bag_key, [])`

### tests\unit\utils\test_zscaler_probe.py
- Line 333: `role.get('role', '')`
- Line 334: `role.get('description', '')`
- Line 336: `role.get('critical', False)`

### tests\unit\utils\test_zscaler_probe_transport.py
- Line 108: `kwargs.get('shell', False)`

### tools\capture_log_baseline.py
- Line 144: `lookup_index.get(target_line, [])`

### tools\check_citations.py
- Line 188: `index.get(os.path.basename(target), ())`

### tools\compliance_analyzer\reporting.py
- Line 285: `totals.get(violation.rule_id, 0)`
- Line 137: `metrics.get('lines_of_code', 0)`
- Line 138: `metrics.get('code_lines', 0)`
- Line 139: `metrics.get('function_count', 0)`
- Line 140: `metrics.get('class_count', 0)`
- Line 141: `metrics.get('avg_complexity', 0)`
- Line 142: `metrics.get('max_complexity', 0)`
- Line 143: `metrics.get('inline_comment_coverage', 0)`

### tools\compliance_analyzer\scoring.py
- Line 38: `penalties.get(violation.category, 0)`

### tools\guard_proof_audit.py
- Line 102: `payload.get('detector_metrics', {})`
- Line 309: `payload.get('project', {})`

### tools\openapi_endpoint_catalog.py
- Line 170: `op.get('parameters', [])`
- Line 156: `doc.get('paths', {})`

### tools\refactor_analyzer\__main__.py
- Line 124: `counts.get(candidate.category, 0)`

### tools\refactor_analyzer\analysis.py
- Line 197: `refs_by_name.get(defn.name, [])`

### tools\refactor_analyzer\reporting.py
- Line 60: `counts.get(candidate.category, 0)`

### tools\ste_linter\analysis\spacy_backend.py
- Line 61: `_POS_MAP.get(word.pos_, OTHER)`

### tools\ste_linter\config.py
- Line 69: `self.weights.get(rule_id, default)`
- Line 73: `self.section_weights.get(section, 1.0)`
- Line 105: `data.get('tool', {})`
- Line 106: `tool.get('ste_linter', {})`
- Line 81: `self.weights.get(rule_id, 1.0)`
- Line 112: `table.get('procedural_limit', config.procedural_limit)`
- Line 113: `table.get('descriptive_limit', config.descriptive_limit)`
- Line 114: `table.get('noun_cluster_limit', config.noun_cluster_limit)`
- Line 115: `table.get('paragraph_limit', config.paragraph_limit)`
- Line 118: `table.get('dictionary', config.dictionary_path)`
- Line 119: `table.get('prefer_spacy', config.prefer_spacy)`
- Line 126: `table.get('grade_logging_strings', config.grade_logging_strings)`
- Line 129: `table.get('grade_user_facing_strings', config.grade_user_facing_strings)`
- Line 124: `table.get('allowlist', [])`
- Line 132: `table.get('logging_call_names', config.logging_call_names)`
- Line 135: `table.get('user_facing_call_names', config.user_facing_call_names)`
- Line 120: `table.get('weights', {})`
- Line 122: `table.get('section_weights', {})`

### tools\ste_linter\dictionary\extract.py
- Line 238: `columns.get(0, [])`
- Line 239: `columns.get(1, [])`

### tools\ste_linter\dictionary\loader.py
- Line 45: `self._entries.get(word.lower(), [])`
- Line 68: `data.get('entries', [])`
- Line 71: `record.get('part_of_speech', '')`
- Line 72: `record.get('approved', True)`
- Line 74: `record.get('approved_meaning', '')`
- Line 73: `record.get('alternatives', [])`

### tools\ste_linter\dictionary\quality.py
- Line 116: `data.get('entries', data)`
- Line 102: `golden.get('alternatives', [])`
- Line 103: `record.get('alternatives', [])`
- Line 65: `record.get('keyword', '')`
- Line 65: `record.get('part_of_speech', '')`

### tools\ste_linter\scoring.py
- Line 91: `units.get(rule.scope, 1)`
- Line 41: `counts.get(rule.rule_id, 0)`
- Line 92: `counts.get(rule.rule_id, 0)`

### tools\test_quality_analyzer\__main__.py
- Line 623: `severity_overrides.get(finding.rule_id, finding.severity)`
- Line 707: `metrics.get(key, 0)`

### tools\test_quality_analyzer\baseline.py
- Line 202: `obj.get('heuristic', False)`

### tools\test_quality_analyzer\config.py
- Line 88: `raw.get('exclusions', {})`
- Line 150: `exclusions.get('banned_imports', ['mistapi'])`
- Line 151: `exclusions.get('excluded_src_prefixes', ['src/api/'])`
- Line 163: `exclusions.get('path_globs', [])`
- Line 86: `raw.get('rules', {})`
- Line 87: `raw.get('severity', {})`

### tools\test_quality_analyzer\reporting.py
- Line 222: `subschema.get('required', [])`
- Line 228: `subschema.get('properties', {})`

### web_portal\app.py
- Line 127: `os.environ.get(WEBHOOK_ENABLED_CONFIG_KEY, 'true')`
- Line 127: `os.environ.get(WEBHOOK_ENABLED_CONFIG_KEY, 'true')`
- Line 155: `os.environ.get('DATA_DIR', 'data')`
- Line 155: `os.environ.get('DATA_DIR', 'data')`
- Line 167: `config.get('theme', 'dark')`
- Line 175: `config.get('allowed_ips', [])`
- Line 208: `app.config.get(WEBHOOK_ENABLED_CONFIG_KEY, False)`
- Line 231: `app.config.get('PORTAL', {})`
- Line 130: `os.environ.get(WEBHOOK_SECRET_CONFIG_KEY, '')`
- Line 130: `os.environ.get(WEBHOOK_SECRET_CONFIG_KEY, '')`
- Line 234: `portal.get('title', 'MistHelper')`
- Line 235: `portal.get('logo_url', '/static/img/logo-default.svg')`
- Line 236: `portal.get('accent_color', '#0d6efd')`
- Line 237: `portal.get('theme', 'dark')`

### web_portal\routes\dashboard.py
- Line 40: `current_app.config.get('DATA_DIR', 'data')`
- Line 74: `current_app.config.get('DATA_DIR', 'data')`
- Line 118: `os.environ.get('ARANGO_HOST', f'http://{DEFAULT_ARANGO_HOST}:{DEFAULT_ARANGO_PORT}')`
- Line 118: `os.environ.get('ARANGO_HOST', f'http://{DEFAULT_ARANGO_HOST}:{DEFAULT_ARANGO_PORT}')`
- Line 127: `os.environ.get('REDIS_HOST', DEFAULT_REDIS_HOST)`
- Line 127: `os.environ.get('REDIS_HOST', DEFAULT_REDIS_HOST)`
- Line 128: `os.environ.get('REDIS_PORT', str(DEFAULT_REDIS_PORT))`
- Line 128: `os.environ.get('REDIS_PORT', str(DEFAULT_REDIS_PORT))`
- Line 111: `os.environ.get('OUTPUT_FORMAT', 'sqlite')`
- Line 111: `os.environ.get('OUTPUT_FORMAT', 'sqlite')`

### web_portal\routes\data.py
- Line 15: `request.args.get('sort', 'modified')`
- Line 16: `request.args.get('order', 'desc')`
- Line 29: `current_app.config.get('DATA_DIR', 'data')`
- Line 40: `current_app.config.get('DATA_DIR', 'data')`
- Line 42: `request.args.get('page', 1, type=int)`
- Line 43: `request.args.get('per_page', 50, type=int)`
- Line 44: `request.args.get('search', '')`
- Line 57: `current_app.config.get('DATA_DIR', 'data')`
- Line 59: `request.args.get('page', 1, type=int)`
- Line 60: `request.args.get('per_page', 50, type=int)`
- Line 61: `request.args.get('search', '')`
- Line 74: `current_app.config.get('DATA_DIR', 'data')`

### web_portal\routes\maps.py
- Line 64: `image_data.get('content_type', 'image/png')`
- Line 111: `map_info.get('name', '')`
- Line 113: `map_info.get('width', 0)`
- Line 114: `map_info.get('height', 0)`
- Line 75: `site.get('id', '')`
- Line 75: `site.get('name', '')`
- Line 89: `m.get('id', '')`
- Line 90: `m.get('name', '')`
- Line 91: `m.get('width', 0)`
- Line 92: `m.get('height', 0)`
- Line 130: `d.get('id', '')`
- Line 131: `d.get('name', '')`
- Line 132: `d.get('type', 'ap')`
- Line 133: `d.get('x', 0)`
- Line 134: `d.get('y', 0)`
- Line 135: `d.get('mac', '')`

### web_portal\routes\operations.py
- Line 34: `current_app.config.get('MENU_ACTIONS', {})`
- Line 46: `data.get('parameters', {})`
- Line 47: `parameters.get('input_answers', [])`
- Line 160: `request.args.get('type', 'all')`
- Line 45: `data.get('menu_number', '')`
- Line 215: `entry.get('message', entry)`
- Line 216: `entry.get('level', 'info')`
- Line 228: `entry.get('message', entry)`
- Line 229: `entry.get('level', 'debug')`
- Line 365: `raw.get('results', [])`
- Line 393: `raw.get('results', [])`
- Line 193: `current_app.config.get('MENU_ACTIONS', {})`
- Line 294: `site.get('id', '')`
- Line 295: `site.get('name', '')`
- Line 296: `site.get('address', '')`
- Line 297: `site.get('country_code', '')`
- Line 298: `site.get('timezone', '')`
- Line 327: `device.get('id', '')`
- Line 328: `device.get('mac', '')`
- Line 329: `device.get('name', '')`
- Additional records: 14

### web_portal\routes\webhooks.py
- Line 67: `current_app.config.get(WEBHOOK_SECRET_CONFIG_KEY, '')`
- Line 108: `payload.get('topic', '')`
- Line 124: `payload.get('events', [payload])`
- Line 136: `payload.get('topic', '')`
- Line 137: `payload.get('events', [])`
- Line 85: `request.headers.get(SIGNATURE_HEADER, '')`

### web_portal\services\config.py
- Line 236: `os.environ.get('PORTAL_TRUSTED_PROXIES', '')`
- Line 236: `os.environ.get('PORTAL_TRUSTED_PROXIES', '')`
- Line 292: `request.headers.get('X-Forwarded-For', '')`
- Line 87: `os.environ.get(key, default)`
- Line 87: `os.environ.get(key, default)`
- Line 355: `self.DISPLAY_LABELS.get(name, name.replace('-', ' ').title())`
- Line 205: `os.environ.get(PUBLIC_ACCESS_SETTING, '')`
- Line 205: `os.environ.get(PUBLIC_ACCESS_SETTING, '')`

### web_portal\services\data_browser.py
- Line 318: `item.get(col, '')`
- Line 264: `item.get(column, '')`
- Line 352: `item.get(col, '')`
- Line 387: `item.get(col, '')`

### web_portal\services\operation.py
- Line 663: `parameters.get('input_answers', [])`
- Line 651: `run.get('sequence', 0)`
- Line 770: `run.get('dropped_log_count', 0)`
- Line 772: `run.get('dropped_output_file_count', 0)`
- Line 784: `run.get('dropped_log_count', 0)`
- Line 786: `run.get('dropped_output_file_count', 0)`
- Line 524: `entry.get('category', 'interactive')`
- Line 525: `entry.get('parameters', [])`
- Line 765: `run.get('output_files', [])`
- Line 767: `run.get('log_messages', [])`
- Line 768: `run.get('debug_messages', [])`
- Line 894: `self._run.get('dropped_log_count', 0)`
- Line 936: `self._run.get('dropped_output_file_count', 0)`

### wsgi.py
- Line 49: `os.environ.get('MIST_ORG_ID', '')`
- Line 49: `os.environ.get('MIST_ORG_ID', '')`
- Line 65: `data.get('privileges', [])`
