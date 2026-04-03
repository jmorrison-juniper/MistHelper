# Audit: Menu #68 — Export insight metrics for a site (SiteExportUtils.insight_metrics)

Target: SiteExportUtils.insight_metrics in MistHelper.py
Location: Approx. MistHelper.py lines 15220-15294

Summary:
- Iterates site-scoped insight metrics and calls mistapi.api.v1.sites.insights.getSiteInsightMetrics.
- Aggregates and writes to a filename like SiteInsightMetrics_[SiteName].csv using DataExporter.save_data_to_output.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No explicit strategy key for getSiteInsightMetrics found.
- DataExporter: Uses save_data_to_output; no api_function_name provided.
- Tests: No tests found targeting site insight metrics export.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
