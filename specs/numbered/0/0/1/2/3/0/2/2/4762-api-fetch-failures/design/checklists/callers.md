# Caller Checklist: API Fetch Failures

**Purpose**: Confirm that each production caller of the two fetch helpers has one class and one behavior after the change.
**Created**: 2026-11-26
**Source**: `design/research.md`, Caller Inventory, and the remote rows cited below.

Class values: Optional means the caller catches `APIFetchError`, logs one warning, and continues. Required means the caller propagates `APIFetchError`. Direct reader means the caller calls `mistapi.get_all` itself and stays unchanged.

## Optional Lookups

- [x] `SiteNameLookup.fetch` at `src/mist/intelligence/reports/switch_scorecard/site_lookup.py` line 23. Class: Optional. Rows R10.
- [x] WAN scorecard at `src/mist/intelligence/reports/wan_edge_scorecard/scorecard.py` line 85. Class: Optional through `SiteNameLookup.fetch`. Row R11.
- [x] Switch scorecard at `src/mist/intelligence/reports/switch_scorecard/operation.py` line 41. Class: Optional through `SiteNameLookup.fetch`. Row R12.
- [x] AP scorecard at `src/mist/intelligence/reports/ap_scorecard/operation.py` line 49. Class: Optional through `SiteNameLookup.fetch`. Row R13.
- [x] Offline device report at `src/mist/intelligence/reports/offline_device_reporter.py` line 107. Class: Optional. Rows R14 and R15.
- [x] Site device statistics at `src/operations/exporting/export/site_device_exporter.py` line 141. Class: Optional. Rows R16 and R17.
- [x] AP model export at `src/operations/exporting/export/sites_by_ap_model_exporter.py` line 173. Class: Optional. Rows R18 and R19.
- [x] Devices site lookup at `src/operations/exporting/export/org_inventory_exporter.py` line 509, reached through lines 530 and 557. Class: Optional. Rows R21, R22, and R23.
- [x] Gateways site lookup at `src/operations/exporting/export/org_inventory_exporter.py` line 688. Class: Optional. Row R24.
- [x] MSP site lookup at `src/operations/exporting/export/msp_inventory_exporter.py` line 358. Class: Optional with the broad catch kept. Rows R27 and R28.
- [x] Prompt site cache at `src/interfaces/visualization/ui/prompt_utils.py` line 394. Class: Optional through the `RuntimeError` catch. Rows R30 and R31.
- [x] Prompt client at `src/foundation/runtime/input/prompt_client_utils.py` line 229. Class: Optional through the prompt cache. Row R32.
- [x] Firmware site lookup at `src/operations/execution/firmware/firmware_manager.py` line 3542. Class: Optional with the existing warning. Row R41.
- [x] CSV generator in the fast path at `src/foundation/persistence/cache/cache_utils.py` line 103. Class: Optional by design. Row R65.

## Required Reads

- [x] AP model inventory at `src/operations/exporting/export/sites_by_ap_model_exporter.py` line 36. Class: Required. Row R33.
- [x] Devices inventory cache fallback at `src/operations/exporting/export/org_inventory_exporter.py` line 544. Class: Required. Row R34.
- [x] Devices inventory at `src/operations/exporting/export/org_inventory_exporter.py` line 558. Class: Required. Row R35.
- [x] Gateways inventory at `src/operations/exporting/export/org_inventory_exporter.py` line 692. Class: Required. Row R36.
- [x] Gateway export inventory at `src/mist/resources/gateway/gateway_export_utils.py` line 561. Class: Required. Row R37.
- [x] Gateway export inventory again at `src/mist/resources/gateway/gateway_export_utils.py` line 572. Class: Required. Row R38.
- [x] Firmware manager site seam at `src/operations/execution/firmware/firmware_manager.py` line 1901. Class: Required. Row R40. The consumer is inferred (U-5).
- [x] Bulk upgrader sites at `src/operations/execution/firmware/bulk_ap_upgrader.py` line 313. Class: Required. Row R42.
- [x] Org AP upgrader sites at `src/operations/execution/firmware/org_ap_upgrader.py` line 1016. Class: Required, with the existing handler at line 1023. Rows R43 and R44.
- [x] Site auto upgrade sites at `src/operations/execution/firmware/site_auto_upgrade.py` line 333. Class: Required, with the existing `RuntimeError` handler at line 340. Rows R45 and R46.
- [x] Organization site list at `src/operations/exporting/export/org_site_exporter.py` line 90. Class: Required. Row R47.
- [x] Site location export at `src/operations/exporting/export/org_site_exporter.py` line 115. Class: Required. Row R48.
- [x] Zone analysis wiring at `src/operations/exporting/export/site_export_utils.py` line 553. Class: Required. Row R49.
- [x] Zone analyzer at `src/mist/intelligence/analytics/site/zone_analyzer.py` line 561. Class: Required. Row R50.
- [x] Zone script at `scripts/replace_zone.py` line 30. Class: Required. Row R51.
- [x] Zone menu wiring at `MistHelper.py` line 5771. Class: Required. Row R64.
- [x] Zone menu wiring at `MistHelper.py` line 5794. Class: Required. Same wiring as row R64.
- [x] Firmware configuration at `MistHelper.py` line 3621. Class: Required. Row R62. The consumer is inferred (U-5).
- [x] Org upgrade configuration at `MistHelper.py` line 5732. Class: Required. Row R63. The consumer is inferred (U-5).
- [x] CLI `--site` resolver at `MistHelper.py` line 7886. Class: Required. Rows R55 to R58.
- [x] API site settings at `src/mist/access/api/api_fetch_utils.py` line 154. Class: Required. Row R52.
- [x] Site settings export at `src/operations/exporting/export/site_config_exporter.py` line 168. Class: Required. Row R53.
- [x] SSID gap report at `src/mist/intelligence/reports/ssid_broadcast_gap_report.py` line 41. Class: Required. Row R54.

## Direct Readers Outside the Change

- [x] MSP organization inventory at `src/operations/exporting/export/msp_inventory_exporter.py` line 275. Class: Direct reader. Unchanged. Row R29.
- [x] Gateway export site lookup at `src/mist/resources/gateway/gateway_export_utils.py` line 282. Class: Direct reader. Unchanged. Row R39.

## Checks Across All Callers

- [x] Each caller in the lists above appears once in `design/contracts/optional-lookups.md` or `design/contracts/operator-output.md`, or it is listed as required.
- [x] Each optional caller has one warning template. The template is in `design/contracts/optional-lookups.md`.
- [x] Each required caller propagates the error. The menu behavior is in `design/contracts/operator-output.md`.
