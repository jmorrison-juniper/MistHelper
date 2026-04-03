# Audit: Menu #67 — Export SLE summary for all sites (OrgExportUtils.sites_sle_summary)

Target: OrgExportUtils.sites_sle_summary in MistHelper.py
Location: Approx. MistHelper.py lines 13648-13701

Summary:
- Calls mistapi.api.v1.orgs.insights.getOrgSitesSle for sle types and aggregates site-level entries.
- Writes output via DataExporter.save_data_to_output("OrgSitesSLESummary.csv").

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No entry detected for getOrgSitesSle (strategy missing).
- DataExporter: Uses save_data_to_output; no api_function_name provided to enable PK selection.
- Tests: No tests found covering this function.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
