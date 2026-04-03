# Audit: Menu #69 — Export client insights for a site (SiteClientExporter.client_insights)

Target: SiteClientExporter.client_insights in MistHelper.py
Location: Approx. MistHelper.py lines 14425-14553

Summary:
- Discovers client (by MAC or index) and iterates client-scoped metrics calling mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient.
- Writes consolidated client metric records to SiteClientInsights_[Site]_[MAC].csv via DataExporter.save_data_to_output.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No entry for getSiteInsightMetricsForClient found in strategies.
- DataExporter: Uses save_data_to_output; no api_function_name set.
- Tests: No unit tests found covering client_insights.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
