# Implementation Plan: Split the Juniper RMA and export packages

**Branch**: `chore/4168-split-rma-and-export-packages` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numbered record `specs/numbered/0/0/1/1/3/1/3/3/4168-split-rma-and-export-packages/`, route from `.specify/scripts/powershell/spec-route.ps1`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Split three packages that hold more than five children. Move 59 modules into domain packages, add 16 package markers, and update each live reference. Remove three baseline entries. The guard measure changes from 190 to 206 directories, from 33 to 30 violations, and from 236 to 190 total excess.

## Technical Context

**Language/Version**: Python 3.15 or newer, because `pyproject.toml` requires `>=3.15`.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`. The change adds no dependency.

**Storage**: No storage change. `DataExporter` writes CSV, SQLite, ArangoDB, and Redis as before.

**Testing**: Guard tests in `tests/guardrails/`, the sharded pytest commands in `.github/copilot-instructions.md`, and the local gates table.

**Target Platform**: Windows 11, macOS, and Linux. The move uses absolute imports and `pathlib` paths only.

**Project Type**: Python command-line tool and web portal.

**Performance Goals**: None. The change adds no runtime work.

**Constraints**: Five children maximum for each directory. No compatibility shim. ASCII log output. No Mist REST call change.

**Scale/Scope**: 59 moved modules, 1 moved package marker, 16 new package markers, 187 live files named by the old-path search, and 7 manual edits outside that search.

Measured baseline on remote `main` (see `design/research.md`, section Local measurement): 931 Python files, 190 directories examined, 33 violations, and 236 total excess.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | Each new directory holds five children or fewer. The three touched violations leave the baseline. No new violation appears. The other 30 entries keep remediation issue #3824. |
| II. Class-Based Architecture | Pass | The change moves classes. It adds no function and no wrapper. |
| III. Safety-First | Pass | No input handling changes. |
| IV. Full Deployment Pipeline | Pass with steps | `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` carry each pipeline step. |
| V. Observability and Logging | Pass with change | Logger names change with each module path, as the table below records. Log text stays ASCII. |
| VI. Inline Comments | Pass with condition | Each changed import line keeps its comment. Each new package marker holds a docstring. |
| VII. Action Logging | Pass | The change adds no action. Moved blocks keep their logs. |
| Mist Cloud transport | Not applicable | No REST call and no WebSocket transport changes. |
| Test containers | Not applicable | The change starts no container. |
| File paths | Pass | Paths stay in `pathlib` form and absolute imports. |
| Output backends | Pass | `DataExporter` stays at `src/operations/exporting/export/data_exporter.py`. |
| Database keys | Not applicable | No endpoint or primary key strategy changes. |
| Menu operations | Not applicable | No menu is added. Menu numbers and categories stay unchanged. |
| Move a module table | Pass | The table in `.github/copilot-instructions.md` stays unchanged. `T-LOCAL-GATES` runs each applicable gate. |
| Hot files | Pass with sequencing | No open pull request names `MistHelper.py`. Pull request #4813 changes `data_exporter.py` and two export test files. This change edits `tests/unit/export/test_endpoint_family_exporter.py`, so the change waits for #4813. |
| Documentation | Pass | Live documents and generated references change in the same change. |
| Release notes | Pass | One fragment is added under `changelog.d/`. `CHANGELOG.md` stays unchanged. |

### Logger and class module changes

Each module with `logging.getLogger(__name__)` changes its logger name to its new dotted path. Each class in a moved module changes its `__module__` value to the new dotted path. Tests that assert an old logger name or an old `__module__` value change with the move.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/1/3/3/4168-split-rma-and-export-packages/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      module-move-map.md
      ratchet-guard-output.md
    checklists/
      requirements.md
```

### Source layout after the change

```text
src/operations/exporting/export/
  __init__.py
  data_exporter.py                    (unchanged, content owned by pull request #4813)
  org/
    __init__.py
    org_export_utils.py
    inventory/                        (5 modules)
    events/                           (5 modules)
    config/                           (5 modules)
    account/                          (4 modules)
  site/
    __init__.py
    site_export_utils.py
    events/                           (5 modules)
    devices/                          (5 modules)
    queries/                          (5 modules)
    insights/                         (4 modules)
  wan/
    __init__.py                       (3 modules)
  generic/
    __init__.py
    const_definitions_exporter.py
    count_exporter.py
    http_response_status.py
    endpoints/                        (3 modules)
src/operations/exporting/juniper_rma/model/
  __init__.py
  parsers/                            (asset.py, service_request.py)
  rows/                               (export_rows.py, reference_rows.py, request_rows.py)
  run_record.py                       (unchanged)
src/operations/exporting/juniper_rma/workflows/
  __init__.py
  reads/                              (case_reads.py, reference_reads.py, juniper_menu_support.py)
  lookups/                            (lookup.py, asset_lookup.py)
  access_check.py                     (unchanged)
  correlation.py                      (unchanged)
```

Each directory holds five children or fewer. The guard counts a child module except `__init__.py`, and it counts a child directory that holds tracked Python files.

## File-by-file change map

### A. Moved files (`git mv`)

Each row moves one file. The prefix `src/operations/exporting/export/` appears in every export row, and the prefix `src/operations/exporting/juniper_rma/` appears in every Juniper RMA row.

| # | Old path | New path |
| - | - | - |
| 1 | src/operations/exporting/export/org_export_utils.py | src/operations/exporting/export/org/org_export_utils.py |
| 2 | src/operations/exporting/export/org_inventory_exporter.py | src/operations/exporting/export/org/inventory/org_inventory_exporter.py |
| 3 | src/operations/exporting/export/org_inventory_search_exporter.py | src/operations/exporting/export/org/inventory/org_inventory_search_exporter.py |
| 4 | src/operations/exporting/export/org_search_exporter.py | src/operations/exporting/export/org/inventory/org_search_exporter.py |
| 5 | src/operations/exporting/export/org_device_stats_exporter.py | src/operations/exporting/export/org/inventory/org_device_stats_exporter.py |
| 6 | src/operations/exporting/export/msp_inventory_exporter.py | src/operations/exporting/export/org/inventory/msp_inventory_exporter.py |
| 7 | src/operations/exporting/export/org_alarm_event_exporter.py | src/operations/exporting/export/org/events/org_alarm_event_exporter.py |
| 8 | src/operations/exporting/export/org_webhook_deliveries_exporter.py | src/operations/exporting/export/org/events/org_webhook_deliveries_exporter.py |
| 9 | src/operations/exporting/export/device_events_52w_exporter.py | src/operations/exporting/export/org/events/device_events_52w_exporter.py |
| 10 | src/operations/exporting/export/org_client_security_exporter.py | src/operations/exporting/export/org/events/org_client_security_exporter.py |
| 11 | src/operations/exporting/export/org_sec_intel_profile_exporter.py | src/operations/exporting/export/org/events/org_sec_intel_profile_exporter.py |
| 12 | src/operations/exporting/export/org_admin_exporter.py | src/operations/exporting/export/org/config/org_admin_exporter.py |
| 13 | src/operations/exporting/export/org_config_exporter.py | src/operations/exporting/export/org/config/org_config_exporter.py |
| 14 | src/operations/exporting/export/org_cradlepoint_connection_exporter.py | src/operations/exporting/export/org/config/org_cradlepoint_connection_exporter.py |
| 15 | src/operations/exporting/export/org_site_exporter.py | src/operations/exporting/export/org/config/org_site_exporter.py |
| 16 | src/operations/exporting/export/org_template_exporter.py | src/operations/exporting/export/org/config/org_template_exporter.py |
| 17 | src/operations/exporting/export/self_account_exporter.py | src/operations/exporting/export/org/account/self_account_exporter.py |
| 18 | src/operations/exporting/export/self_export_utils.py | src/operations/exporting/export/org/account/self_export_utils.py |
| 19 | src/operations/exporting/export/license_export_utils.py | src/operations/exporting/export/org/account/license_export_utils.py |
| 20 | src/operations/exporting/export/msp_license_exporter.py | src/operations/exporting/export/org/account/msp_license_exporter.py |
| 21 | src/operations/exporting/export/site_export_utils.py | src/operations/exporting/export/site/site_export_utils.py |
| 22 | src/operations/exporting/export/site_anomaly_exporter.py | src/operations/exporting/export/site/events/site_anomaly_exporter.py |
| 23 | src/operations/exporting/export/site_mist_edge_events_exporter.py | src/operations/exporting/export/site/events/site_mist_edge_events_exporter.py |
| 24 | src/operations/exporting/export/site_nac_client_events_exporter.py | src/operations/exporting/export/site/events/site_nac_client_events_exporter.py |
| 25 | src/operations/exporting/export/site_system_events_exporter.py | src/operations/exporting/export/site/events/site_system_events_exporter.py |
| 26 | src/operations/exporting/export/site_webhook_deliveries_exporter.py | src/operations/exporting/export/site/events/site_webhook_deliveries_exporter.py |
| 27 | src/operations/exporting/export/site_device_exporter.py | src/operations/exporting/export/site/devices/site_device_exporter.py |
| 28 | src/operations/exporting/export/site_asset_exporter.py | src/operations/exporting/export/site/devices/site_asset_exporter.py |
| 29 | src/operations/exporting/export/site_config_exporter.py | src/operations/exporting/export/site/devices/site_config_exporter.py |
| 30 | src/operations/exporting/export/sites_by_ap_model_exporter.py | src/operations/exporting/export/site/devices/sites_by_ap_model_exporter.py |
| 31 | src/operations/exporting/export/site_other_device_events_exporter.py | src/operations/exporting/export/site/devices/site_other_device_events_exporter.py |
| 32 | src/operations/exporting/export/site_client_exporter.py | src/operations/exporting/export/site/queries/site_client_exporter.py |
| 33 | src/operations/exporting/export/wifi_clients_exporter.py | src/operations/exporting/export/site/queries/wifi_clients_exporter.py |
| 34 | src/operations/exporting/export/site_guest_authorization_exporter.py | src/operations/exporting/export/site/queries/site_guest_authorization_exporter.py |
| 35 | src/operations/exporting/export/site_search_exporter.py | src/operations/exporting/export/site/queries/site_search_exporter.py |
| 36 | src/operations/exporting/export/site_application_list_exporter.py | src/operations/exporting/export/site/queries/site_application_list_exporter.py |
| 37 | src/operations/exporting/export/site_insights_exporter.py | src/operations/exporting/export/site/insights/site_insights_exporter.py |
| 38 | src/operations/exporting/export/site_insights/__init__.py | src/operations/exporting/export/site/insights/__init__.py |
| 39 | src/operations/exporting/export/site_insights/device_metric_operation.py | src/operations/exporting/export/site/insights/device_metric_operation.py |
| 40 | src/operations/exporting/export/site_insights/metric_refusals.py | src/operations/exporting/export/site/insights/metric_refusals.py |
| 41 | src/operations/exporting/export/site_insights/site_metric_operation.py | src/operations/exporting/export/site/insights/site_metric_operation.py |
| 42 | src/operations/exporting/export/gateway_test_exporter.py | src/operations/exporting/export/wan/gateway_test_exporter.py |
| 43 | src/operations/exporting/export/site_wan_usage_exporter.py | src/operations/exporting/export/wan/site_wan_usage_exporter.py |
| 44 | src/operations/exporting/export/wan_client_events_exporter.py | src/operations/exporting/export/wan/wan_client_events_exporter.py |
| 45 | src/operations/exporting/export/const_definitions_exporter.py | src/operations/exporting/export/generic/const_definitions_exporter.py |
| 46 | src/operations/exporting/export/count_exporter.py | src/operations/exporting/export/generic/count_exporter.py |
| 47 | src/operations/exporting/export/http_response_status.py | src/operations/exporting/export/generic/http_response_status.py |
| 48 | src/operations/exporting/export/endpoint_catalog.py | src/operations/exporting/export/generic/endpoints/endpoint_catalog.py |
| 49 | src/operations/exporting/export/endpoint_family_exporter.py | src/operations/exporting/export/generic/endpoints/endpoint_family_exporter.py |
| 50 | src/operations/exporting/export/simple_endpoint_exporter.py | src/operations/exporting/export/generic/endpoints/simple_endpoint_exporter.py |
| 51 | src/operations/exporting/juniper_rma/model/asset.py | src/operations/exporting/juniper_rma/model/parsers/asset.py |
| 52 | src/operations/exporting/juniper_rma/model/service_request.py | src/operations/exporting/juniper_rma/model/parsers/service_request.py |
| 53 | src/operations/exporting/juniper_rma/model/export_rows.py | src/operations/exporting/juniper_rma/model/rows/export_rows.py |
| 54 | src/operations/exporting/juniper_rma/model/reference_rows.py | src/operations/exporting/juniper_rma/model/rows/reference_rows.py |
| 55 | src/operations/exporting/juniper_rma/model/request_rows.py | src/operations/exporting/juniper_rma/model/rows/request_rows.py |
| 56 | src/operations/exporting/juniper_rma/workflows/case_reads.py | src/operations/exporting/juniper_rma/workflows/reads/case_reads.py |
| 57 | src/operations/exporting/juniper_rma/workflows/reference_reads.py | src/operations/exporting/juniper_rma/workflows/reads/reference_reads.py |
| 58 | src/operations/exporting/juniper_rma/workflows/juniper_menu_support.py | src/operations/exporting/juniper_rma/workflows/reads/juniper_menu_support.py |
| 59 | src/operations/exporting/juniper_rma/workflows/lookup.py | src/operations/exporting/juniper_rma/workflows/lookups/lookup.py |
| 60 | src/operations/exporting/juniper_rma/workflows/asset_lookup.py | src/operations/exporting/juniper_rma/workflows/lookups/asset_lookup.py |

Row 38 moves a package marker. The other 59 rows move modules. `data_exporter.py`, `run_record.py`, `access_check.py`, and `correlation.py` keep their paths.

Warning: A move that runs outside `git mv` in a dirty worktree can lose a local edit. Run each move in a clean worktree on the feature branch.

### B. New package markers (create, docstring only)

Each marker holds one module docstring and no re-export. The current markers in the source tree also hold only a docstring.

| # | New file | Docstring text |
| - | - | - |
| 1 | src/operations/exporting/export/org/__init__.py | Organization exporters grouped by domain. |
| 2 | src/operations/exporting/export/org/inventory/__init__.py | Organization and MSP inventory exporters. |
| 3 | src/operations/exporting/export/org/events/__init__.py | Organization event, delivery, device event, and security exporters. |
| 4 | src/operations/exporting/export/org/config/__init__.py | Organization configuration, template, and site exporters. |
| 5 | src/operations/exporting/export/org/account/__init__.py | Account, license, and MSP license exporters. |
| 6 | src/operations/exporting/export/site/__init__.py | Site exporters grouped by domain. |
| 7 | src/operations/exporting/export/site/events/__init__.py | Site event, anomaly, and webhook delivery exporters. |
| 8 | src/operations/exporting/export/site/devices/__init__.py | Site device, asset, configuration, and AP model exporters. |
| 9 | src/operations/exporting/export/site/queries/__init__.py | Site client, guest, search, and application list exporters. |
| 10 | src/operations/exporting/export/wan/__init__.py | WAN gateway test, WAN usage, and WAN client event exporters. |
| 11 | src/operations/exporting/export/generic/__init__.py | Endpoint-independent exporters and shared status helpers. |
| 12 | src/operations/exporting/export/generic/endpoints/__init__.py | Endpoint family and simple endpoint exporters. |
| 13 | src/operations/exporting/juniper_rma/model/parsers/__init__.py | Parsers for Juniper asset and service request records. |
| 14 | src/operations/exporting/juniper_rma/model/rows/__init__.py | Row builders and column tables for the Juniper outputs. |
| 15 | src/operations/exporting/juniper_rma/workflows/reads/__init__.py | Juniper read menus 294 to 300. |
| 16 | src/operations/exporting/juniper_rma/workflows/lookups/__init__.py | Juniper lookup menus 303 and 304. |

### C. Removed paths

- `src/operations/exporting/export/site_insights/` is removed after row 38 to row 41 move. The directory holds no file after the moves.
- Each old path in section A is removed by its move. No file remains at an old path.

### D. Manual edits outside the old-path search

| File | Edit |
| - | - |
| tests/guardrails/nested_package_baseline.json | Remove the three objects for `src/operations/exporting/export` (remote lines 156 to 160), `src/operations/exporting/juniper_rma/model` (remote lines 161 to 165), and `src/operations/exporting/juniper_rma/workflows` (remote lines 166 to 170). Remove the trailing comma from the new last object. Keep valid JSON and sorted order. |
| tests/guardrails/test_nested_package_structure.py | Change the expected message on remote line 177 from `33 violations, 236 total excess` to `30 violations, 190 total excess`. Add `test_relocated_modules_reject_old_paths` (FR-016). |
| tests/guardrails/test_performance_hook_catalog.py | Add 46 entries to `_HISTORICAL_PATH_MOVES` (remote lines 28 to 38). Each key is an old path that `hook-catalog.csv` names, and each value is the new path. |
| documentation/architecture.md | Change the path text on remote lines 263 and 284 from `src/operations/exporting/export/` to `src/operations/exporting/export/site/` for the site utilities and site insights rows. |
| scripts/menu_api_map/analysis/source_index.py | Change the four example paths that name `site_exporter` (lines 67, 69, 92, and 102) to `src.operations.exporting.export.site.events.site_anomaly_exporter` and the matching slash form. The old example names a module that the tree never held. |
| scripts/menu_api_map/render/markdown.py | Change the example path in the docstring at line 38 to the new slash form `src/operations/exporting/export/site/events/site_anomaly_exporter.py`. |
| scripts/menu_api_map/render/pages.py | Change the example path in the comment at line 51 to the new slash form `src/operations/exporting/export/site/events/site_anomaly_exporter.py`. |
| changelog.d/issue-4168-split-rma-and-export-packages.md | Add one new fragment. It names issue #4168 and lists the three moved packages. |

The approved move table in `test_performance_hook_catalog.py` uses these 46 old paths. The row for `data_exporter.py` stays out of the table, because that module does not move.

### E. Modified files from the old-path search (187 files)

This list is the output of the search in `design/quickstart.md`, step 3, with `CHANGELOG.md` removed. Each file changes its moved-module import, patch target, module string, or live text. Each file keeps its other lines unchanged.

**Root and process files (2):**

```text
MistHelper.py
```

**Hand-edited documents and data (documentation, junk, and GitHub files):**

```text
.github/copilot-handoff.md
junk/refactor_candidates.md
documentation/diagrams/class-hierarchy/exporters.md
documentation/api/constants: GET_const_marvisclient_events.md
documentation/api/msps: POST_msps_msp_id_ssos_sso_id_delete_admins.md
documentation/api/orgs: DELETE_orgs_org_id_exports_e911_report.md, GET_orgs_org_id_claims_claim_id.md, GET_orgs_org_id_claims.md, GET_orgs_org_id_edgeconnect_register_cmd.md, GET_orgs_org_id_exports_e911_report.md, GET_orgs_org_id_insights_marvisclient_marvisclient_id_marvisclient-metrics.md, GET_orgs_org_id_logs_search.md, GET_orgs_org_id_marvisclients_events_count.md, GET_orgs_org_id_marvisclients_events_search.md, GET_orgs_org_id_stats_marvisclients_count.md, GET_orgs_org_id_stats_marvisclients_search.md, POST_orgs_org_id_claims.md, POST_orgs_org_id_exports_e911_report.md, POST_orgs_org_id_nac_clients_client_mac_coa.md, POST_orgs_org_id_ssos_sso_id_delete_admins.md
documentation/api/sites: DELETE_sites_site_id_auto_map_assignment.md, DELETE_sites_site_id_devices_device_id_zigbee_join.md, DELETE_sites_site_id_marvis_configs_id.md, GET_sites_site_id_auto_map_assignment.md, GET_sites_site_id_insights_ap_device_id_stats.md, GET_sites_site_id_iotendpoints_count.md, GET_sites_site_id_iotendpoints_search.md, GET_sites_site_id_marvis_configs_count.md, GET_sites_site_id_marvis_configs_search.md, GET_sites_site_id_rrm_channel_scores_band_band.md, POST_sites_site_id_apply_auto_map_assignment.md, POST_sites_site_id_auto_map_assignment.md, POST_sites_site_id_clear_auto_map_assignment.md, POST_sites_site_id_devices_device_id_zigbee_event_trail.md, POST_sites_site_id_devices_device_id_zigbee_join.md, POST_sites_site_id_devices_device_id_zigbee_kick.md, POST_sites_site_id_devices_device_id_zigbee_packet_trail.md, POST_sites_site_id_iotendpoints_id_zigbee_rejoin.md, POST_sites_site_id_maps_map_id_apply_autoplacement.md, POST_sites_site_id_marvis_configs_id_feedback.md, POST_sites_site_id_nac_clients_client_mac_coa.md
documentation/api/utilities: GET_sites_site_id_devices_device_id_flow_records_search.md, GET_sites_site_id_mxedges_upgrade_upgrade_id.md, GET_sites_site_id_mxedges_upgrade.md, POST_orgs_org_id_mxedges_upgrade_upgrade_id_cancel.md, POST_sites_site_id_mxedges_upgrade_upgrade_id_cancel.md, POST_sites_site_id_mxedges_upgrade.md, PUT_orgs_org_id_mxedges_upgrade_upgrade_id.md, PUT_sites_site_id_mxedges_upgrade_upgrade_id.md
```

**Generated references (14 files). Run the generators in `T021`. Do not hand-edit these pages:**

```text
documentation/menu_reference.md
documentation/menu-api: continuous-loop.md, destructive.md, interactive-safe.md, interactive.md, resource-intensive.md, safe.md
documentation/wiki: Menu-API-Endpoints-Continuous-Loop.md, Menu-API-Endpoints-Destructive.md, Menu-API-Endpoints-Interactive-Safe.md, Menu-API-Endpoints-Interactive.md, Menu-API-Endpoints-Resource-Intensive.md, Menu-API-Endpoints-Safe.md, Menu-Reference.md
```

**Scripts and web portal (3 files):**

```text
scripts/generate_menu_wiki.py
scripts/menu_api_map/reference/curated.json
web_portal/services/operation.py
```

**Source files outside the moved packages (8 files):**

```text
src/foundation/runtime/config: source_dependency_resolver.py
src/foundation/support/refactors: msp_privilege_detection.py
src/foundation/support/refactors/serial_cc: site_client_insights.py
src/interfaces/visualization/ui: prompt_utils.py
src/mist/intelligence/analytics: data_collection_manager.py
src/mist/intelligence/reports: sfp_transceiver_data_processor.py
src/mist/resources/device: device_reboot_manager.py
src/mist/resources/site/rrm_reset: client.py
```

**Moved source files that import a moved module (21 files, edited at their new paths):**

```text
src/operations/exporting/export (old path): endpoint_family_exporter.py, org_alarm_event_exporter.py, org_inventory_exporter.py, org_site_exporter.py, simple_endpoint_exporter.py, site_client_exporter.py, site_config_exporter.py, site_device_exporter.py, site_export_utils.py
src/operations/exporting/export/site_insights (old path): device_metric_operation.py, site_metric_operation.py
src/operations/exporting/juniper_rma/model (old path): asset.py, export_rows.py, reference_rows.py, request_rows.py
src/operations/exporting/juniper_rma/workflows (old path): asset_lookup.py, case_reads.py, correlation.py, juniper_menu_support.py, lookup.py, reference_reads.py
```

**Tests (91 files, edited at their existing paths):**

```text
tests/e2e/web_portal: juniper_browser_harness.py
tests/fixtures: next5_parity_baseline.py
tests/guardrails: test_endpoint_backlog_safety.py, test_endpoint_catalog.py
tests/integration/export: test_org_webhook_native_refusals.py, test_wifi_clients_native_response_failures.py
tests/unit: test_device_events_52w_exporter_extended.py, test_device_events_52w_exporter.py, test_issue_2971_census_repairs.py, test_org_inventory_exporter_helpers.py
tests/unit/config/standalone/foundation/support/quality/cross_domain: test_issue_2971_status_slice3.py
tests/unit/db/sle_window_summary: test_export_identity.py
tests/unit/export: test_const_definitions_exporter.py, test_count_exporter_workflows.py, test_count_exporter.py, test_count_org_vars_exporter.py, test_endpoint_family_exporter.py, test_export_notice_separator.py, test_gateway_test_exporter_runtime_wiring.py, test_gateway_test_exporter.py, test_http_response_status.py, test_issue_2971_export_status_slice.py, test_issue_3188_webhook_id_selection.py, test_issue_4714_org_licenses_status.py, test_license_export_utils.py, test_msp_inventory_exporter.py, test_msp_license_exporter.py, test_org_admin_exporter.py, test_org_alarm_event_exporter.py, test_org_client_security_exporter.py, test_org_config_exporter.py, test_org_cradlepoint_connection_exporter.py, test_org_device_stats_exporter.py, test_org_export_utils.py, test_org_inventory_search_exporter.py, test_org_search_exporter.py, test_org_sec_intel_profile_exporter.py, test_org_site_exporter.py, test_org_template_exporter.py, test_org_webhook_deliveries_exporter.py, test_org_webhook_response_refusals.py, test_selective_insight_definitions.py, test_self_account_exporter.py, test_self_export_utils.py, test_simple_endpoint_exporter_http_status_4025.py, test_simple_endpoint_exporter.py, test_site_anomaly_exporter.py, test_site_asset_and_events_exporters.py, test_site_client_exporter.py, test_site_config_exporter.py, test_site_device_exporter.py, test_site_export_utils_extended.py, test_site_export_utils.py, test_site_insights_exporter.py, test_site_other_device_events_exporter.py, test_site_search_exporter.py, test_site_webhook_deliveries_exporter.py, test_sites_by_ap_model_exporter.py, test_wan_client_events_exporter_paths.py, test_wan_client_events_exporter.py, test_wifi_clients_exporter.py, test_wifi_clients_response_failures.py
tests/unit/export/site_insights: test_device_metric_operation_wave3.py, test_device_metric_refusals.py, test_metric_refusals.py, test_site_insight_path.py, test_site_metric_operation_wave9.py
tests/unit/juniper_rma/model: test_asset.py, test_export_rows.py, test_service_request.py
tests/unit/juniper_rma/workflows: test_access_check.py, test_lookups.py
tests/unit/maps/interfaces/ui/interaction/dispatch: test_device_prompt_rename_guard.py
tests/unit/marvis/mist/intelligence/troubleshooting/core: test_logged_error_observer_filter.py
tests/unit/marvis/standalone/mist/intelligence/reports: test_issue_2971_status_slice4.py
tests/unit/prod_readiness/operations/exporting/juniper_rma/api/transport: test_fixture_replies.py, test_read_gets.py
tests/unit/prod_readiness/operations/exporting/juniper_rma/model/rows: test_request_rows.py
tests/unit/prod_readiness/operations/exporting/juniper_rma/workflows/menus: test_read_menus_live.py, test_read_menus_offline.py
tests/unit/prod_readiness/standalone/operations/exporting/inventory: test_menu_12_inventory.py, test_menu_13_device_stats.py, test_menu_19_device_port_stats.py
tests/unit/prod_readiness/standalone/operations/exporting/reports: test_exports.py, test_pk_strategies.py
tests/unit/web_portal: test_portal_label_accuracy.py, test_portal_log_routing.py, test_portal_required_answers.py, test_portal_required_controls.py, test_portal_silent_completion.py, test_portal_terminal_state_4025.py
```

Each test file in this list names a moved module by a dotted path or by a package-form import.

### F. Paths that stay unchanged

| Path | Reason |
| - | - |
| src/operations/exporting/export/data_exporter.py | Owned by pull request #4813. Its path stays. |
| src/operations/exporting/juniper_rma/model/run_record.py | Path stays. Its content names no moved module. |
| src/operations/exporting/juniper_rma/workflows/access_check.py | Path stays. Its content changes only through the list in section E. |
| src/operations/exporting/juniper_rma/workflows/correlation.py | Path stays. Its content names no moved module. |
| src/operations/exporting/juniper_rma/api/*.py | Content names no moved module. |
| pyproject.toml | The mypy override `src.operations.exporting.export.*` covers the new subpackages. |
| tests/unit/export/test_data_exporter.py | Imports only `data_exporter`. |
| tests/unit/config/standalone/foundation/support/quality/assertions/test_bare_assert_replacements.py | Imports only `data_exporter`. |
| tests/unit/container/output_defaults/test_contract.py | Imports only `data_exporter`. |
| tests/unit/juniper_rma/api/*.py, tests/unit/juniper_rma/model/test_run_record.py, tests/unit/juniper_rma/workflows/test_correlation.py | Content names no moved module. |
| documentation/CONTRIBUTING-MistHelper.md | Names the folder `src\operations\exporting\export\`, which still exists. |
| documentation/upgrade_capture_portal.md, documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md, documentation/diagrams/core/*.md, documentation/diagrams/class-hierarchy/overview.md | Name only `data_exporter.py`. |
| .github/copilot-instructions.md | The `### Move a module` table stays unchanged (FR-010). |
| tests/unit/test_* not listed in section E | Content names no moved module. |

### G. Dated records (no change)

| Path | Reason |
| - | - |
| specs/ (196 files, including `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` and `python-inventory.csv`) | Dated records. The hook catalog is immutable, and the inventory pins its source revision. |
| changelog.d/ historical fragments | Dated release notes. |
| CHANGELOG.md | Shared release history. AGENTS.md forbids editing it on a feature branch. |
| .specify/bugs/menu-93-inventory-output/assessment.md | Dated bug assessment. |
| The legacy record `specs/numbered/0/0/1/1/3/1/3/3/4168-org-auto-upgrade-policy/` | Belongs to issue #4217 (FR-012, D-16). |

## Sequencing and ownership

1. Wait for pull request #4813 to merge (`T001`). It changes `data_exporter.py`, `tests/unit/export/test_data_exporter.py`, and `tests/unit/export/test_endpoint_family_exporter.py`.
2. Rebase onto `main` after #4813 merges. Confirm that `main` still holds the baseline of 190 directories and 33 violations.
3. Run the moves in section A, then the import updates, then the guard changes, then the documentation changes.
4. Run `T-LOCAL-GATES` after all tasks in `tasks.md` complete.
5. Open one pull request (`T-PR`).

Pull request #4208 owns `tests/guardrails/test_src_public_symbol_preservation.py`. This change does not edit that file, so the two pull requests do not conflict on it.

Issue #4142 owns the split of `tests/unit/`. This change edits imports in `tests/unit/juniper_rma/` and `tests/unit/export/`. If #4142 merges first, rebase this change before editing those files.

## Risks with mitigations

| Risk | Mitigation |
| - | - |
| The change touches about 190 files. | Run the moves first, then the imports, then the guard checks, and run each guard after each phase. |
| A package-form import misses a moved module. | Run the old-path search in `design/quickstart.md` before `T-LOCAL-GATES`. |
| The hook catalog guard reports missing paths. | Add each old path and new path pair to `_HISTORICAL_PATH_MOVES` (section D). |
| Generated menu pages drift. | Run the two generators twice. The second run must change no file. |
| A logger name filter in a document or test stops matching. | Run the old dotted logger name search in `T023` before the pull request. Update each hit that names a moved logger. |
| A circular import appears after the package change. | Import each new module in `T025`. Each import must succeed. |
| The mypy wildcard does not cover nested packages. | Run mypy in `T-LOCAL-GATES`. If mypy reports a missing override, list each new package in `pyproject.toml`. |
| Pull request #4813 changes a file in this change. | Wait for #4813 (`T001`). Rebase after the merge. |

## Rollback

1. Open a revert pull request for the squash commit on `main`.
2. Confirm that `tests/guardrails/nested_package_baseline.json` lists the three entries with counts 48, 6, and 7.
3. Confirm that the guard reports 33 violations and 236 total excess.

Warning: A force push to `main` removes other agents' commits. Use a revert pull request only.

## Dependencies

No new package or tool is required. The change depends on pull request #4813 merging. The change does not close issue #3824 or issue #4142.
