Audit: Menu #40 
Export wireless client statistics

Location: MistHelper.py 
Class: OrgClientSecurityExporter.wireless_clients (around line ~13082)

Summary findings:
- Method delegates to OrgExportUtils.export_data(api_call=mistapi.api.v1.orgs.clients.searchOrgWirelessClients).
- API flow: OrgExportUtils -> APIDataFetcher -> DataExporter.export_with_processing -> DataExporter.save_data_to_output -> DataExporter.write_with_format_selection.
- API function name propagates via APIDataFetcher (api_function_name is passed), so SQLite writer receives api_function_name and will select the endpoint strategy from ENDPOINT_PRIMARY_KEY_STRATEGIES.
- ENDPOINT_PRIMARY_KEY_STRATEGIES includes "searchOrgWirelessClients" with composite_pk (primary_key: ["mac","timestamp"]).

Conclusion: SQL export compliance: PASS.
Test coverage: No unit tests found referencing wireless_clients; add tests to ensure end-to-end behavior and sqlite write with correct strategy.