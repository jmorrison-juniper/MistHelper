# Tasks: Implementation Work Items (Do NOT implement in this audit ticket)

1) Add PK strategy entries
   - File: MistHelper.py
   - Section: ENDPOINT_PRIMARY_KEY_STRATEGIES (~line 3260)
   - Add entries for:
     - "searchSiteWirelessClients": composite_pk, primary_key: ["mac","timestamp"], indexes: ["site_id","device_id","ssid","mac","timestamp"]
     - "searchSiteWirelessClientSessions": composite_pk, primary_key: ["mac","timestamp"], indexes: ["site_id","device_id","start_time","mac"]
   - Include descriptive "description" fields.

2) Update exporter
   - File: MistHelper.py
   - Function: SiteClientExporter.wifi_clients
   - Change DataExporter.save_data_to_output(sanitized, "SiteWiFiClients.CSV") to:
     DataExporter.write_with_format_selection(sanitized, "SiteWiFiClients.CSV", api_function_name="searchSiteWirelessClients")
   - Add a short comment explaining rationale for chosen api_function_name.

3) Tests
   - File: tests/unit/test_pk_strategies.py (or new test file)
   - Add assertions that new ENDPOINT_PRIMARY_KEY_STRATEGIES keys exist and have valid structure.
   - File: tests/test_exports.py (new or extend)
   - Mock DataExporter.write_with_format_selection and assert wifi_clients calls it with correct api_function_name.
   - Integration: create a test that runs SQLiteDatabaseWriter on sample data using the new strategy and verifies PK columns present in the created table in data/mist_data.db (use a temporary DB path or in-memory DB if supported).

4) Documentation
   - Update README.md to mention dual-output behavior for Menu #34 and list endpoint key added to ENDPOINT_PRIMARY_KEY_STRATEGIES.

5) QA
   - Run full test suite: pytest -q
   - Verify no regressions.

Owner: QA/Developer
Priority: High (data integrity for SQLite exports)
