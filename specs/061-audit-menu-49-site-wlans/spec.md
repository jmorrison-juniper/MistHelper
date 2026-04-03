Title: Audit — Menu #49: Export WLAN configuration (site)

Summary:
- Menu impl: SiteConfigExporter.wlans uses mistapi.api.v1.sites.wlans.listSiteWlans (Site scope)
- PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES does NOT contain listSiteWlans (missing)
- Export path: SiteExportUtils/OrgExportUtils → APIDataFetcher → DataExporter; api_function_name not provided
- Tests: No unit tests for site-level WLAN export; pk_strategies test lacks listSiteWlans entry

Risks & Recommendations:
1) Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry "listSiteWlans" with natural_pk on "id" and indexes ["site_id","ssid","template_id"].
2) Pass api_function_name="listSiteWlans" when calling DataExporter to ensure correct SQLite strategy.
3) Add unit and integration tests for site WLAN exporter and SQL schema.
