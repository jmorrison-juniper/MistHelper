Title: Audit — Menu #48: Export WLAN configuration (org)

Summary:
- Menu impl: OrgConfigExporter.wlans uses mistapi.api.v1.orgs.wlans.listOrgWlans via OrgExportUtils.export_data
- PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES does NOT contain an explicit entry for listOrgWlans (missing)
- Export path: OrgExportUtils → APIDataFetcher → DataExporter; api_function_name is not set, so SQLite uses default strategy
- Tests: No unit tests found for org-level WLAN export; pk_strategies test lacks listOrgWlans entry

Risks:
- Missing strategy entry means SQLite exports will use fallback auto-increment strategy instead of natural_pk on 'id', harming queryability and deduplication.

Recommendations:
1) Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "listOrgWlans" with type "natural_pk" and primary_key ["id"].
2) Ensure the exporter passes api_function_name="listOrgWlans" to DataExporter for SQLite exports.
3) Add unit tests for strategy and exporter behavior.
