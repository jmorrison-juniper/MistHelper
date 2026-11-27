# Implementation Plan: Blind Except Handler Audit (issue 1794)

**Branch**: `docs/1794-blind-except-audit` (this record) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `spec.md`. Numeric route `specs/numbered/0/0/0/2/4/1/3/4/`, which is the base-5 form of 1794 (RC-019, RC-020).

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The repository holds about 827 broad `except` clauses (Local evidence). Ruff does not select `BLE001`, so no gate reports them. A growth guard blocks new blind handlers (RC-032). This plan audits every in-scope site in 23 slices of at most 40 sites each. Each slice applies one outcome per site (`delete`, `narrow`, or `keep`), adds a log call where the code continues, and adds tests. The final pull request selects `BLE001` and removes the pylint `W0718` disable in one change.

## Technical Context

**Language/Version**: Python 3.15 (`requires-python >=3.15`, RC-005). The ruff target is `py315` (RC-006).

**Primary Dependencies**: Pinned in `requirements-dev.txt`: ruff 0.17.6 (RC-008), pylint 4.1.4 (RC-007), mypy 2.4.1, black 26.10.1, radon 6.0.1, vulture 2.16, interrogate 1.7.0, pydocstyle 6.3.0, bandit 1.9.4, and pytest 9.2.0. The Mist SDK is mistapi 0.64.1 (RC-018). No new dependency is added.

**Storage**: Not applicable. The work changes handler blocks, log calls, tests, comments, one configuration block, and the growth baseline.

**Testing**: pytest unit tests and the guards under `tests/guardrails`. Test files are chosen by a search rule at slice start (see the test rule below). The CI shards run all tests (RC-017).

**Target Platform**: Windows 11 development hosts, macOS, and Linux. CI runs on Linux.

**Project Type**: Python CLI and portal repository.

**Performance Goals**: No runtime change. A log call adds one line of output on a handled failure. The CI lint job keeps its current runtime.

**Constraints**:
- Ruff reads the repository with the `extend-exclude` list in `pyproject.toml` line 206 (RC-004).
- Pylint reads `src/` only in CI (RC-014). Its score floor is 9.5 (RC-128), and CI records a 9.53 score before the change (RC-129).
- Each slice holds at most 40 sites (FR-017).
- Each changed function stays inside the constitution limits: five parameters, five blocks, five operations per block, and 25 lines.

**Test rule**: For each changed module, the slice owner searches `tests/unit` for `test_<module>.py`. If one exists, the slice adds its cases there. If none exists, the slice adds a new file under the matching `tests/unit/` path. The moved paths in research.md (RC-065, RC-067, RC-070, RC-074, RC-083) are the current paths.

**Scale/Scope**: 261 candidate files and 678 text sites in ruff scope (Local evidence). Four excluded trees hold 149 more sites, and they are not in this audit (D-8). Twenty-three slices and one final gate pull request.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes with one stated exception (D-13).*

| Principle or rule | Result | Reason |
| - | - | - |
| I. Five-item rule | PASS | This record folder holds five children at the root and five under `design/` (FR-031). Each changed function stays inside its limits. A helper is extracted when a log call pushes a function past 25 lines. |
| II. Class-based architecture | PASS | The work adds no class and no wrapper function. Each change stays inside an existing class or function. |
| III. Safety first | PASS | No input path changes. A narrowed type keeps operational failures visible (FR-010). Each changed log call has a redaction test (FR-016). |
| IV. Full deployment pipeline | PASS | Each slice follows branch, commit, rebase, push, pull request, CI, and merge. The final pull request includes the issue closure (D-12). The container build runs after code slices merge. |
| V. Observability and logging | PASS | Log output stays ASCII. Levels follow the standard: info before an action, debug after it, error with context on failure (FR-013). |
| VI. Inline comments | PASS | FR-036 requires a comment on each changed line. |
| VII. Action logging | PASS | FR-013 adds an error log at each continued handler. Existing logs stay in place. |
| Technology: mistapi only | PASS | No REST call is added or changed. FR-011 forbids a new transport exception type. |
| Technology: owned WebSocket transport | PASS (not used) | No transport changes. |
| Technology: test containers | PASS (not used) | The gates run on the host. No container is started (RC-029). |
| Technology: file paths | PASS | Changes use existing path code only. |
| Technology: output backends | PASS | Export output contracts stay as they are. |
| Technology: operational store | PASS (not used) | No new store. |
| Technology: data directory | PASS | No new product output. Tests use `tmp_path`. |
| Technology: container security and Zscaler | PASS (not used) | No container or push change. |
| Development workflow: menu operations | PASS (not applicable) | No menu is added or changed. |
| Testing: skip list | PASS | The test categories stay as they are. |
| Security findings: fix over suppress | PASS with exception | No ruff suppression is added (FR-015). Kept sites that pylint flags carry one inline disable and a reason (D-13). This exception follows the existing pattern of 57 inline disables (Local evidence). |
| Documentation: README | PASS (not applicable) | No operation count changes. |
| Documentation: release notes | PASS | One fragment per slice (FR-035). |
| Audience standard | PASS | Log messages stay plain and do not change in meaning. |
| SpecKit escalation | PASS | This record is the required escalation for 23 slices. |
| Multi-agent git workflow | PASS | Issue first (D-7). One area per slice. Serial publication. A reference keyword in slice pull requests (FR-029). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/0/2/4/1/3/4/1794-blind-except-audit/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      outcome-table.md
      log-record.md
      gate-configuration.md
    checklists/
      requirements.md
      gates.md
      evidence.md
```

### Source code (repository root)

The map below names each candidate file. Counts are text matches of `except Exception` or `except BaseException` at the verified commit (Local evidence). Ruff decides the final set at T001. A re-raise handler is not counted by ruff, so a text count can be higher than the ruff count. Every row is a modify action. Test paths follow the test rule. Each slice also modifies `.github/blind-exception-handler-baseline.json` to lower its counts, and each slice adds one changelog fragment (`changelog.d/issue-<child>-<slug>.md`). No file is deleted, and no file is added except tests and fragments.

### Slice map

**S01 (10 sites, 2 files)**: `MistHelper.py` (7), `wsgi.py` (3). The safe sweep gate applies (`python MistHelper.py --test`). The hot file rule applies to `MistHelper.py`: one open pull request at a time.

**S02 (34 sites, 20 files)**: `src/mist/access/api/api_data_fetcher.py` (4), `src/mist/access/audit/audit_analysis_ops.py` (1), `src/mist/access/auth/interactive/login_orchestrator.py` (1), `src/mist/access/auth/interactive/msp_org_selector.py` (1), `src/mist/intelligence/analytics/data_collection_manager.py` (2), `src/mist/intelligence/analytics/site/zone_analyzer.py` (2, and coordinate with the owner named in issue comment 7), `src/mist/intelligence/juniper_docs/classify/content_sampler.py` (1), `src/mist/intelligence/marvis/marvis_utils.py` (1), `src/mist/intelligence/marvis/troubleshooting/marvis_troubleshoot_utils.py` (6), `src/mist/intelligence/reports/certificate_expiry/client.py` (3), `src/mist/intelligence/reports/certificate_expiry/model.py` (1), `src/mist/intelligence/reports/e911_bssid.py` (2), `src/mist/intelligence/reports/global_wired_client_report_generator.py` (1), `src/mist/intelligence/reports/offline_device_reporter.py` (1), `src/mist/intelligence/reports/psk_hygiene/operation.py` (2), `src/mist/intelligence/reports/site_variable_audit/client.py` (1), `src/mist/intelligence/reports/subscription_expiry/client.py` (1), `src/mist/intelligence/reports/wired_client_manufacturer_report_generator.py` (1), `src/mist/intelligence/troubleshooting/rf_diagnostics/recording.py` (1), `src/mist/intelligence/troubleshooting/rf_diagnostics/spectrum.py` (1).

**S03 (38 sites, 17 files)**: `src/mist/networking/network/_routing_utils_display.py` (3), `src/mist/networking/network/_routing_utils_forwarding.py` (1), `src/mist/networking/network/_routing_utils_payload.py` (1), `src/mist/networking/network/_routing_utils_routing.py` (1), `src/mist/networking/network/_routing_utils_ssr.py` (1), `src/mist/networking/network/routing_utils.py` (2), `src/mist/resources/inventory/csv_comparator.py` (3), `src/mist/resources/inventory/device_replace/operation.py` (1), `src/mist/resources/inventory/inventory_summary/version_per_model_fetcher.py` (2), `src/mist/resources/inventory/org_device_inventory_msp.py` (2), `src/mist/resources/org/mxedge_lifecycle/operation.py` (2), `src/mist/resources/org/org_config_migration_manager.py` (2), `src/mist/resources/org/org_synthetic_probes_manager.py` (3), `src/mist/resources/org/org_ticket_manager.py` (6), `src/operations/wan/org_data_collector.py` (1), `src/operations/wan/wan_hub_group_manager.py` (3), `src/operations/wan/wan_vpn_builder.py` (4).

**S04 (30 sites, 16 files)**: `src/interfaces/monitoring/metrics_gateway/collector.py` (1), `src/mist/realtime/websocket_streams/intake/pickers/devices.py` (2), `src/mist/realtime/websocket_streams/intake/pickers/records.py` (1), `src/mist/realtime/websocket_streams/intake/pickers/resources.py` (5), `src/mist/realtime/websocket_streams/live/runners/channel/runner.py` (1), `src/mist/realtime/websocket_streams/live/runners/shell/lifecycle/opening.py` (1), `src/mist/realtime/websocket_streams/live/runners/shell/lifecycle/reading.py` (1), `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py` (2), `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` (3), `src/mist/realtime/websocket/commands.py` (1), `src/mist/realtime/websocket/diagnostics/arp_executor.py` (2), `src/mist/realtime/websocket/diagnostics/ping_executor.py` (1), `src/mist/realtime/websocket/manager.py` (3), `src/mist/realtime/websocket/polling/message_router.py` (1), `src/mist/realtime/websocket/service_ping_discovery.py` (2), `src/mist/realtime/websocket/service_ping_manager.py` (3, RC-044). The ping test assertion branch (`tests/unit/websocket/diagnostics/test_ping_executor.py`, RC-087) waits for issue #2711.

**S05 (32 sites, 11 files)**: `src/mist/resources/gateway/_wan2_variable_device.py` (2), `src/mist/resources/gateway/_wan2_variable_template.py` (2), `src/mist/resources/gateway/device_template_cloner.py` (1), `src/mist/resources/gateway/gateway_export_utils.py` (1), `src/mist/resources/gateway/gateway_ha_exporter.py` (2), `src/mist/resources/gateway/gateway_stats_exporter.py` (3), `src/mist/resources/gateway/overrides/device_data_fetcher.py` (2), `src/mist/resources/gateway/template_config.py` (10), `src/mist/resources/gateway/wan_probe_device_override_manager.py` (2), `src/mist/resources/gateway/wan2_migration_manager.py` (1), `src/operations/execution/ssid_consolidation/ssid_template_consolidation.py` (6).

**S06 (27 sites, 9 files)**: `src/foundation/persistence/cache/cache_utils.py` (1, held cache slice target, RC-064), `src/foundation/persistence/db/database_schema_utils.py` (1, and issue #4712 owns the schema fallback), `src/foundation/persistence/db/retention.py` (1), `src/foundation/persistence/db/writers/arango_writer.py` (4), `src/mist/resources/site/address_audit/address_corrector.py` (1), `src/mist/resources/site/address_audit/address_resolver.py` (1), `src/mist/resources/site/address_audit/audit_engine.py` (3), `src/mist/resources/site/address_audit/ui_geocoder.py` (12), `src/mist/resources/site/bulk_radius_wlan_config_manager.py` (3).

**S07 (40 sites, 9 files)**: `src/mist/resources/device/_utility_commands_clear.py` (9), `src/mist/resources/device/_utility_commands_websocket.py` (2), `src/mist/resources/device/ap_profile_migration_manager.py` (9), `src/mist/resources/device/arp_command_manager.py` (1), `src/mist/resources/device/client_session_control/handler.py` (1), `src/mist/resources/device/device_reboot_manager.py` (6, destructive reboot path, RC-043), `src/mist/resources/device/device_utils.py` (1), `src/mist/resources/device/utility_commands.py` (1), `src/mist/resources/device/virtual_chassis.py` (10, RC-055). This slice changes a destructive path. Its merge needs a human review and no auto-merge label (AGENTS.md, T-MERGE).

**S08 (39 sites, 13 files)**: `src/operations/execution/ssh/batch/batch_executor.py` (3), `src/operations/execution/ssh/batch/host_runner.py` (1), `src/operations/execution/ssh/batch/interactive_batch_executor.py` (7), `src/operations/execution/ssh/batch/multi_host_runner.py` (2), `src/operations/execution/ssh/cli_shell_manager.py` (3), `src/operations/execution/ssh/command/command_runner.py` (3), `src/operations/execution/ssh/config/csv_loader.py` (1, held SSH CSV target, RC-072), `src/operations/execution/ssh/config/env_loader.py` (2), `src/operations/execution/ssh/connection/connector.py` (3), `src/operations/execution/ssh/runtime/app_runner.py` (4), `src/operations/execution/ssh/runtime/shell_execution/shell_executor.py` (3), `src/operations/execution/ssh/ssh_runner_manager.py` (2), `src/operations/execution/ssh/ssh_runner.py` (5).

**S09 (25 sites, 8 files)**: `src/operations/execution/capture/_packet_capture_exec.py` (6), `src/operations/execution/capture/_packet_capture_org.py` (5), `src/operations/execution/capture/_packet_capture_prompts.py` (1), `src/operations/execution/capture/client_pcap_downloader.py` (3), `src/operations/execution/capture/multi_ap_scan_workflow.py` (2), `src/operations/execution/capture/packet_capture_download.py` (4), `src/operations/execution/capture/packet_capture.py` (2), `src/operations/protection/security/rogue_dhcp/scanner.py` (2).

**S10 (29 sites, 1 file)**: `src/operations/execution/firmware/firmware_manager.py` (29, RC-059). This file belongs to the destructive firmware path. The merge needs a human review and no auto-merge label.

**S11 (24 sites, 5 files)**: `src/operations/execution/firmware/aggregate_upgrade_service.py` (4), `src/operations/execution/firmware/bulk_ap_upgrader.py` (11, RC-056), `src/operations/execution/firmware/bulk_switch_upgrader.py` (1, one broad handler remains at line 664, RC-041), `src/operations/execution/firmware/org_ap_upgrader.py` (8), and `src/operations/execution/firmware/running_version.py` (0 text matches). The last file has no candidate site, but its `RuntimeError` catch at line 138 is unreachable on the REST path (RC-036, RC-037, RC-093, RC-094). Its fix replaces the catch with a response check under D-4, and its test file `tests/unit/firmware/test_running_version.py` (RC-038) adds the matching case. This slice changes a destructive path.

**S12 (38 sites, 17 files)**: `src/operations/exporting/export/count_exporter.py` (1), `src/operations/exporting/export/data_exporter.py` (4), `src/operations/exporting/export/device_events_52w_exporter.py` (3), `src/operations/exporting/export/endpoint_family_exporter.py` (1), `src/operations/exporting/export/gateway_test_exporter.py` (2), `src/operations/exporting/export/msp_inventory_exporter.py` (3), `src/operations/exporting/export/msp_license_exporter.py` (1), `src/operations/exporting/export/org_admin_exporter.py` (1), `src/operations/exporting/export/org_alarm_event_exporter.py` (1), `src/operations/exporting/export/org_client_security_exporter.py` (3), `src/operations/exporting/export/org_config_exporter.py` (1), `src/operations/exporting/export/org_cradlepoint_connection_exporter.py` (1), `src/operations/exporting/export/org_device_stats_exporter.py` (7, held device-stats target, RC-075), `src/operations/exporting/export/org_inventory_exporter.py` (6, held inventory target, RC-076), `src/operations/exporting/export/org_inventory_search_exporter.py` (1), `src/operations/exporting/export/org_search_exporter.py` (1), `src/operations/exporting/export/org_sec_intel_profile_exporter.py` (1).

**S13 (40 sites, 13 files)**: `src/operations/exporting/export/org_template_exporter.py` (5), `src/operations/exporting/export/org_webhook_deliveries_exporter.py` (1), `src/operations/exporting/export/self_account_exporter.py` (1), `src/operations/exporting/export/self_export_utils.py` (1), `src/operations/exporting/export/simple_endpoint_exporter.py` (1), `src/operations/exporting/export/site_anomaly_exporter.py` (7), `src/operations/exporting/export/site_application_list_exporter.py` (1), `src/operations/exporting/export/site_asset_exporter.py` (3), `src/operations/exporting/export/site_client_exporter.py` (2, RC-046), `src/operations/exporting/export/site_device_exporter.py` (4), `src/operations/exporting/export/site_export_utils.py` (9), `src/operations/exporting/export/site_guest_authorization_exporter.py` (1), `src/operations/exporting/export/site_insights/device_metric_operation.py` (4).

**S14 (16 sites, 11 files)**: `src/operations/exporting/export/site_insights/site_metric_operation.py` (3), `src/operations/exporting/export/site_mist_edge_events_exporter.py` (1), `src/operations/exporting/export/site_nac_client_events_exporter.py` (1), `src/operations/exporting/export/site_other_device_events_exporter.py` (1, held other-device target, RC-078, and issue #4709 coordinates), `src/operations/exporting/export/site_search_exporter.py` (2), `src/operations/exporting/export/site_system_events_exporter.py` (1), `src/operations/exporting/export/site_wan_usage_exporter.py` (1), `src/operations/exporting/export/site_webhook_deliveries_exporter.py` (1), `src/operations/exporting/export/sites_by_ap_model_exporter.py` (1, held AP-address target, RC-077), `src/operations/exporting/export/wan_client_events_exporter.py` (2), `src/operations/exporting/export/wifi_clients_exporter.py` (2).

**S15 (39 sites, 17 files)**: `src/foundation/support/refactors/anomaly_metrics_discovery.py` (1, held anomaly target, RC-069), `src/foundation/support/refactors/connection_pool_executor.py` (4), `src/foundation/support/refactors/device_data_fetcher.py` (1, held device-fetch target, RC-071), `src/foundation/support/refactors/main_entrypoint.py` (1, holds the handler chain used by the redaction tests, RC-061), `src/foundation/support/refactors/maps_manager_launcher.py` (2), `src/foundation/support/refactors/msp_privilege_detection.py` (2, and issue #4713 owns the refused-profile defect), `src/foundation/support/refactors/serial_cc/security_events.py` (4), `src/foundation/support/refactors/serial_cc/site_client_insights.py` (4), `src/foundation/support/refactors/serial_cc/sle_metrics.py` (4), `src/foundation/support/refactors/serial_cc/start_site_scan_capture.py` (1), `src/foundation/support/refactors/serial_cc/switch_vc_stats.py` (2), `src/foundation/support/refactors/serial_cc/test_results_by_site.py` (2), `src/foundation/support/refactors/service_ping_launcher.py` (1), `src/foundation/support/refactors/sqlite_database_writer.py` (6), `src/foundation/support/refactors/tui_launcher.py` (1, RC-085, and issue #4711 is closed but its fix is not verified), `src/foundation/support/refactors/wan2_migration_launcher.py` (1), `src/foundation/support/refactors/wanprobe_config_manager.py` (2).

**S16 (20 sites, 10 files)**: `src/foundation/support/refactors/wlanradius_timer_manager.py` (5), `src/foundation/runtime/input/prompt_client_utils.py` (2), `src/foundation/runtime/time/time_utils.py` (1, held time target, RC-066), `src/foundation/support/menu_testing/interactive_test_runner.py` (2), `src/foundation/support/utils/environment_utils.py` (1, held container-detection target, RC-068), `src/foundation/support/utils/file_path_utils.py` (1, held CSV-template target, RC-082, uncommitted changes per comment 61), `src/foundation/support/utils/logger_utils.py` (1, the redaction filter itself, keep with a recursion note), `src/foundation/support/utils/rate_limiting.py` (2), `src/foundation/support/utils/zscaler_catalogue.py` (2, held catalog target, RC-084, and issue #3824 needs a file-scoped handoff), `src/foundation/support/utils/zscaler_probe.py` (3). The address-normalization commit (`30edc280`, RC-123) joins this slice for `src/foundation/support/utils/address_utils.py`, which holds no text match on main (RC-073). Rebase it onto PR #4503 and recheck.

**S17 (6 sites, 5 files)**: `src/interfaces/portals/licensing_comparison/api.py` (1), `src/interfaces/visualization/ui/execution/debug_saver.py` (2, RC-062, and PR #4499 already changed the handler at line 106), `src/interfaces/visualization/ui/execution/function_executor.py` (1), `src/interfaces/visualization/ui/execution/item_executor.py` (1), `src/interfaces/visualization/ui/runtime/tui_runner.py` (1). The held debug-saver commit is superseded by PR #4499 (RC-103).

**S18 (38 sites, 11 files)**: `src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py` (2), `src/interfaces/portals/upgrade_portal/app/factory.py` (3), `src/interfaces/portals/upgrade_portal/app/routes/auth.py` (5), `src/interfaces/portals/upgrade_portal/app/routes/capture.py` (2), `src/interfaces/portals/upgrade_portal/app/routes/comparison.py` (3), `src/interfaces/portals/upgrade_portal/app/routes/mist.py` (2), `src/interfaces/portals/upgrade_portal/app/routes/org_controls.py` (1), `src/interfaces/portals/upgrade_portal/app/routes/org_postcheck.py` (1), `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` (9), `src/interfaces/portals/upgrade_portal/app/routes/runs.py` (3), `src/interfaces/portals/upgrade_portal/app/routes/select.py` (7). Issue #2926 closed with 131 sites in this portal on main. D-7 applies.

**S19 (40 sites, 2 files)**: `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` (14, destructive upgrade path), `src/interfaces/portals/upgrade_portal/app/wiring.py` (26). This slice changes a destructive path.

**S20 (40 sites, 19 files)**: `src/interfaces/portals/upgrade_portal/audit/logger.py` (2), `src/interfaces/portals/upgrade_portal/auth/session.py` (2), `src/interfaces/portals/upgrade_portal/capture/assembly.py` (1), `src/interfaces/portals/upgrade_portal/capture/collector.py` (1), `src/interfaces/portals/upgrade_portal/capture/devices.py` (1), `src/interfaces/portals/upgrade_portal/capture/extras.py` (2), `src/interfaces/portals/upgrade_portal/capture/service.py` (4), `src/interfaces/portals/upgrade_portal/compare/service.py` (2), `src/interfaces/portals/upgrade_portal/persistence/actions/transactions.py` (2), `src/interfaces/portals/upgrade_portal/persistence/runs.py` (3), `src/interfaces/portals/upgrade_portal/runtime/lock.py` (2), `src/interfaces/portals/upgrade_portal/runtime/pools.py` (2), `src/interfaces/portals/upgrade_portal/settle/service.py` (6), `src/interfaces/portals/upgrade_portal/upgrade/driver.py` (3), `src/interfaces/portals/upgrade_portal/upgrade/events.py` (2), `src/interfaces/portals/upgrade_portal/upgrade/gate.py` (1), `src/interfaces/portals/upgrade_portal/upgrade/options.py` (1), `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/close.py` (1), `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/locks.py` (2).

**S21 (13 sites, 7 files)**: `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/readers.py` (1), `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` (2), `src/interfaces/portals/upgrade_portal/upgrade/org_precheck.py` (1), `src/interfaces/portals/upgrade_portal/upgrade/org_versions.py` (1), `src/interfaces/portals/upgrade_portal/upgrade/phase_gate.py` (2), `src/interfaces/portals/upgrade_portal/upgrade/service.py` (4), `src/interfaces/portals/upgrade_portal/upgrade/stop.py` (2).

**S22 (39 sites, 25 files)**: `tests/contract/upgrade_portal/test_page_links_resolve.py` (1), `tests/e2e/upgrade_portal/conftest.py` (1), `tests/e2e/upgrade_portal/journeys/test_parity_pages.py` (1), `tests/e2e/upgrade_portal/test_assets.py` (1), `tests/e2e/upgrade_portal/test_capture.py` (2), `tests/e2e/upgrade_portal/test_comparison.py` (1), `tests/e2e/upgrade_portal/test_history_layout.py` (1), `tests/e2e/upgrade_portal/test_history.py` (2), `tests/e2e/upgrade_portal/test_narrow_action_cells.py` (1), `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` (2), `tests/e2e/upgrade_portal/test_signin.py` (1), `tests/e2e/upgrade_portal/test_site_selection.py` (1), `tests/e2e/upgrade_portal/test_stop.py` (2), `tests/e2e/upgrade_portal/test_two_operators.py` (2), `tests/e2e/upgrade_portal/test_upgrade.py` (2), `tests/e2e/web_portal/firmware_restore/test_restore_portal.py` (1), `tests/e2e/web_portal/licensing_comparison/test_session_state.py` (1), `tests/e2e/web_portal/test_firmware_policy.py` (1), `tests/e2e/web_portal/test_operations_counts.py` (1), `tests/e2e/websockets_tab/dialog_audit/support/journeys.py` (1), `tests/e2e/websockets_tab/dialog_audit/support/policy.py` (2), `tests/e2e/websockets_tab/dialog_audit/test_live.py` (3), `tests/guardrails/test_blind_exception_handler_ratchet.py` (5, most matches sit in string literals, U-13, and the guard logic must not weaken), `tests/guardrails/test_source_modules_import.py` (1), `tests/integration/test_wan_vpn_builder_live.py` (2).

**S23 (21 sites, 14 files)**: `tests/portal_sweep.py` (2), `tests/support/upgrade_portal_e2e/lock_holds.py` (1), `tests/support/upgrade_portal_e2e/org_operations.py` (4), `tests/unit/config/standalone/foundation/support/utilities/system/test_logger_utils.py` (2), `tests/unit/firmware/test_aggregate_upgrade_service.py` (2), `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py` (1), `tests/unit/marvis/mist/resources/inventory/support/versioning/test_version_per_model_fetcher_wave3.py` (2), `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py` (1), `tests/unit/ssh/config/test_env_loader_wave9.py` (1), `tests/unit/test_prompt_network_device_utils.py` (1), `tests/unit/upgrade_portal/test_dispatch_gate.py` (1), `tests/unit/utils/test_zscaler_catalogue.py` (1), `tests/unit/web_portal/test_operations_silent_failure.py` (1), `tests/unit/websocket/test_manager_thread_join.py` (1).

**S24 (final gate, no site change)**: `pyproject.toml` (modify lines 209 and 588 to 594, FR-022, FR-023), `documentation/quality-gates.md` (modify the ruff row at line 50 and add the BLE001 gate, AGENTS.md documentation rule), `tests/guardrails/test_blind_exception_handler_ratchet.py` (modify the stored-baseline test at lines 445 to 450 and add one test case, FR-026), `.github/blind-exception-handler-baseline.json` (remove entries at zero), and one changelog fragment (add). The final pull request closes #1794 (D-12, constitution IV step 7).

**Excluded trees (no change in this audit)**: `mist-ops-platform/` (23 sites in 13 files), `web_portal/` (26 sites in 9 files), `scripts/` (32 sites in 12 files), and `src/interfaces/visualization/maps/` (68 sites in 15 files, with 16 inert `noqa` lines). Each tree receives a follow-up issue (FR-032, T033).

### Held commits and their owning slices

| Held commit (not on main) | Owning slice | Note |
| - | - | - |
| `ecdf3fef` cache correction, `88e8bd4f` prior commit | S06 | Test path moved (RC-065). |
| `f35a5103` time correction | S16 | Test path moved (RC-067). |
| `a2641739` container detection | S16 | Test path follows the test rule. |
| `acdbcb0c` anomaly metrics | S15 | Test renamed (RC-070). |
| `0055f708` device-fetch privacy | S15 | Test path follows the test rule. |
| `0157ec13` SSH command CSV | S08 | Test path follows the test rule. |
| `57fd57c8` catalog validation | S16 | Issue #3824 handoff first. |
| `54fc78c4` device statistics cache | S12 | Issue #4746 coordinates. |
| `f9b33748` AP address | S14 | New test file (RC-089) added by the slice. |
| `45ca06d2` inventory address | S12 | New test file (RC-090) added by the slice. |
| `30edc280` address normalization | S16 | Base changed by PR #4503 (RC-073, RC-074). |
| `63dd076f` other-device events | S14 | Issue #4709 coordinates. |
| `49c665d9` ping assertion | S04 | Issue #2711 handoff first. |
| `c3d0f769` and `8a700b2b` PR heads | None | Superseded by squash commits RC-103 and RC-105. |

## Architecture

The audit adds no module and no class. It changes existing handler blocks and adds one log call per continued handler. The three gates work in sequence:

1. **Growth guard now**: `tests/guardrails/test_blind_exception_handler_ratchet.py` reads `.github/blind-exception-handler-baseline.json` and fails when a changed file gains a blind handler (RC-032, RC-033).
2. **Slice gates per pull request**: ruff, black, mypy, pytest for the changed tests, radon, bandit, pylint, vulture, pydocstyle, interrogate, symbol-diff, and STE for changed Markdown (quickstart.md).
3. **Final lint gate**: ruff selects `BLE001` and keeps `RUF100` (RC-035 shows that RUF100 is selected), and pylint no longer disables `W0718`.

## Dependencies

- Toolchain: Python 3.15.2 through uv (copilot-instructions lines 25 and 28), and the pinned packages in `requirements-dev.txt` (RC-007, RC-008, RC-018). The `misthelper-devtools` package supplies `complexity-gate`, `symbol-diff`, `test-quality-analyzer`, and `ste-linter`.
- Repository state: the verified commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (research.md). T001 confirms it before measuring.
- Coordination: the owners named in spec.md, Dependencies. Each slice owner holds the file reservation for its files.
- GitHub access for remote CI and issue creation through `gh`.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The count moves between the baseline and a slice | The scope changes | T001 records the count. Each slice rechecks the count for its files. |
| A narrowed type turns a caught error into a crash | An operator sees a new failure | FR-010 and FR-021 require a propagation test and a caller read. |
| Mistapi changes its REST wrapper | A narrowed call receives a new exception | The pin stays at 0.64.1 (RC-018). A wrapper change needs a new analysis. |
| A log call leaks a credential | A secret reaches the log | FR-016 requires a redaction test through the real handler chain (RC-061). |
| Suppressions grow with each kept site | The gate loses meaning | D-13 limits the inline disables. The final pull request counts them. |
| The pylint score falls below 9.5 | CI fails | The final pull request runs the pylint gate before merge. CI records a 9.53 score before the change (RC-128, RC-129). |
| Held commits conflict with newer code | Rework | D-6 requires a rebase and a fresh check. |
| A destructive path changes | An unsafe merge | S07, S10, S11, S19 need a human review and no auto-merge label (AGENTS.md, T-MERGE). |
| The closing keyword closes #1794 early | Tracking loses the umbrella | FR-029 and D-12. The record pull request is the only closing reference, and the orchestrator reopens #1794 if needed (analysis A-13). |
| The growth guard and ruff disagree on tests and excluded trees | A gap in coverage | D-8 and FR-033. The follow-up issues close the gap. |

## Rollback

- **Slice**: revert the slice merge commit on main through a new pull request. Do not force-push main. The revert restores the baseline counts in the same change.
- **Final gate**: revert the final pull request. The revert restores the `W0718` disable and removes the `BLE001` selection. The growth guard stays in place.
- **Held commits**: no rollback is needed. They stay unpublished until their slice merges.
- **Failed CI after a merge**: follow the AGENTS.md rollback path. Do not delete the failing commit from history.

## Complexity Tracking

| Item | Kind | Why it stays | Remediation |
| - | - | - | - |
| 23 slices and one final gate | Required by the scope | 678 text sites cannot land in one reviewable change (FR-017). | Each slice is one pull request. |
| Inline pylint disables on kept sites | New suppression pattern | D-13 limits it to kept sites with a reason. | The final pull request counts them. |
| Root-level legacy records | Grandfathered debt | They are baseline entries (RC-022). | D-11 supersedes them. T036 adds the note. |
| Excluded trees | Out of gate scope | The gate configuration keeps `extend-exclude` (FR-025). | T033 opens follow-up issues. |
