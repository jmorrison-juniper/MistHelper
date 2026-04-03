Audit: Menu #24 - Export all switch virtual chassis (VC/stacking) stats to CSV

Summary of findings

- Location: MistHelper.py — class OrgDeviceStatsExporter.switch_vc_stats (defined around lines 12165–12516).
- Behavior: Reads cached OrgInventory.csv, filters switches with vc_mac, calls mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis per device, flattens and sanitizes results, and calls DataExporter.save_data_to_output(all_vc_stats, "OrgSwitchVCStats.csv").
- DataExporter usage: save_data_to_output delegates to DataExporter.write_with_format_selection, but switch_vc_stats calls save_data_to_output without passing api_function_name.
- ENDPOINT_PRIMARY_KEY_STRATEGIES: Located at MistHelper.py ~line 3260. There is no explicit entry for "getSiteDeviceVirtualChassis" in the mapping.
- Tests: No unit tests directly exercise OrgDeviceStatsExporter.switch_vc_stats. A related test (tests/test_readopt.py) mocks getSiteDeviceVirtualChassis for a different menu (readopt), but does not validate exports.

Implications

- SQL export compliance: Because switch_vc_stats does not pass api_function_name, SQLite export (if enabled) will rely on context-based resolution (DatabaseSchemaUtils.determine_api_function_name_from_context) or the enhanced default strategy. Without an explicit ENDPOINT_PRIMARY_KEY_STRATEGIES entry, the schema may use suboptimal default keys and miss intended business keys (e.g., using misthelper_internal_id rather than a natural/composite key that preserves device identity).

Recommended next steps (high level)

1. Update OrgDeviceStatsExporter.switch_vc_stats to pass api_function_name="getSiteDeviceVirtualChassis" when calling DataExporter.save_data_to_output/write_with_format_selection.
2. Add an explicit ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "getSiteDeviceVirtualChassis" with an appropriate strategy (suggested: natural_pk using primary key ["id"] or composite_pk if API returns time-series-like records). Validate fields returned by the API and choose the correct PK fields.
3. Add unit tests for switch_vc_stats that mock the API responses and verify both CSV output and SQLite schema/insert behavior (when OUTPUT_FORMAT=sqlite). Verify correct table schema (primary key & indexes) and that exported records include expected fields.

