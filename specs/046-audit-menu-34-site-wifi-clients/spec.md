# Audit: Menu #34 — Site WiFi Clients (SiteClientExporter.wifi_clients)

Summary:
- Function: SiteClientExporter.wifi_clients (MistHelper.py, ~lines 14401-14546).
- Calls Mist API endpoints: searchSiteWirelessClients and searchSiteWirelessClientSessions.
- Merges client and session records and writes output via DataExporter.save_data_to_output("SiteWiFiClients.CSV").

Findings:
1) DataExporter.write_with_format_selection accepts api_function_name to select ENDPOINT_PRIMARY_KEY_STRATEGIES for SQLite upserts, but wifi_clients calls save_data_to_output without api_function_name, causing SQLite writes to use the "default" fallback (auto-increment PK) if SQLite output is used.
2) ENDPOINT_PRIMARY_KEY_STRATEGIES (starts ~line 3260) contains "searchOrgWirelessClients" but DOES NOT contain keys for the site-scoped endpoints "searchSiteWirelessClients" or "searchSiteWirelessClientSessions". This prevents correct composite PK mapping when using sqlite output for this exporter.

Impact:
- SQLite exports of SiteWiFiClients will not have meaningful primary keys/indexes and may not upsert correctly, causing duplicates and inefficient queries.

AC:
- Endpoints used by wifi_clients have matching entries in ENDPOINT_PRIMARY_KEY_STRATEGIES with appropriate composite_pk keys.
- The exporter calls DataExporter.write_with_format_selection(..., api_function_name="searchSiteWirelessClients") (or a chosen api key) so SQLite writes use the correct strategy.
- Unit tests validate strategy presence and exporter usage of api_function_name.
