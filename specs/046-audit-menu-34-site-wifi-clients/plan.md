# Plan: Audit & Remediation Path for Menu #34

Goal: Ensure SiteWiFiClients export uses correct SQLite primary key strategy and dual-output path.

Steps:
1. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entries (readable, documented) for:
   - "searchSiteWirelessClients": composite_pk, primary_key: ["mac","timestamp"], indexes: ["mac","timestamp","site_id","device_id","ssid"]
   - "searchSiteWirelessClientSessions": composite_pk, primary_key: ["mac","timestamp"], indexes: ["mac","timestamp","site_id","device_id","start_time"]

2. Update SiteClientExporter.wifi_clients to call DataExporter.write_with_format_selection(sanitized, "SiteWiFiClients.CSV", api_function_name="searchSiteWirelessClients") to select the appropriate PK strategy.

3. Add unit tests:
   - Assert ENDPOINT_PRIMARY_KEY_STRATEGIES contains new keys.
   - Mock DataExporter.write_with_format_selection and assert wifi_clients passes api_function_name.
   - Integration test: write sample merged data and assert SQLite table created with expected PK columns (in-memory DB or temp DB under data/).

4. Run existing unit test suite; fix any issues.

Notes/Assumptions:
- Use composite_pk ["mac","timestamp"] for both endpoints for consistency with org-level mappings. If session timestamps use "start_time", adapt PK accordingly and document choice in the strategy description.
