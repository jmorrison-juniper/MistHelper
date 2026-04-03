Audit: Menu #41 
Export wired client statistics

Location: MistHelper.py 
Class: OrgClientSecurityExporter.wired_clients (around line ~13089)

Summary findings:
- Method delegates to OrgExportUtils.export_data(api_call=mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients).
- Flow identical to wireless_clients: APIDataFetcher propagates api_function_name to DataExporter.
- ENDPOINT_PRIMARY_KEY_STRATEGIES includes "searchOrgWiredClients" with composite_pk (primary_key: ["mac","timestamp"]).

Conclusion: SQL export compliance: PASS.
Test coverage: No direct unit tests found. Add tests mirroring wireless plan.