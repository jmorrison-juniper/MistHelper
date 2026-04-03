# Audit: Menu #83 — Export Organization Insight Metrics (OrgExportUtils.insight_metrics)

Target: OrgExportUtils.insight_metrics in MistHelper.py
Location: Approx. MistHelper.py lines 13703-13892

Summary:
- Iterates organization-scoped insight metrics, handles special cases (sites-sle), normalizes into summary/time-series/results/sites files.
- Writes multiple CSVs using DataExporter.save_data_to_output; legacy combined file OrgInsightMetrics_Legacy.csv also written.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No explicit entries for getOrgSle/getOrgSitesSle or generic insight endpoints found.
- DataExporter: Uses save_data_to_output across multiple output files; no write_with_format_selection calls with api_function_name.
- Tests: No unit tests found for this function.

Conclusion: SQL export compliance: FAIL (no api_function_name usage). Test coverage: MISSING.
