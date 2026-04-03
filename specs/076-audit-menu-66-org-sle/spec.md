# Audit: Menu #66 — Export Organization SLE Metrics (OrgExportUtils.sle_metrics)

Target: OrgExportUtils.sle_metrics in MistHelper.py
Location: Approx. MistHelper.py lines 14029-14195

Summary:
- Function collects org SLE using mistapi.api.v1.orgs.insights.getOrgSle and getOrgSitesSle.
- Processes aggregated results and calls DataExporter.save_data_to_output("OrgSLEMetrics.csv").

Checks performed:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No explicit entries found for getOrgSle or getOrgSitesSle keys in the strategies block.
- DataExporter: Uses save_data_to_output; does NOT call DataExporter.write_with_format_selection with api_function_name, so SQLite export/PK selection is not invoked.
- Tests: No unit tests found in tests/ that exercise sle_metrics or verify SQL export behavior.

Conclusion: SQL export compliance: FAIL (no api_function_name, no PK strategy entry). Test coverage: MISSING.
