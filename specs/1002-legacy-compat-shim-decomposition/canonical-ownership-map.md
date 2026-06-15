# Canonical Ownership Map

| Legacy Surface | Canonical Owner |
| - | - |
| `get_csv_file_path_legacy` | `MistHelper.get_csv_file_path` |
| `export_gateway_templates_to_csv_legacy` | `MistHelper.export_gateway_templates_to_csv` |
| `InsightMetricsUtils.export_legacy` refresh | `src.export.site_insights_exporter.SiteInsightsExporter.refresh_insight_metrics_cache` |
| Site insights metric scope filtering | `MistHelper.get_insight_metrics_by_scope` (interim), target dedicated `src/export/site_insights` catalog module |
| Site capture alias `run()` | `SitePcapWaitDownloadWorkflow.execute` |
| Org capture alias `run()` | `OrgPcapWaitDownloadWorkflow.execute` |
| Top-level facade `__getattr__` branches | Direct imports from respective `src` ownership modules (phased) |
| Menu fallback `_noop_menu_action` | explicit menu action registrations in canonical menu dispatcher |
| Menu fallback `_ensure_menu_coverage` | explicit registry completeness + parity tests |
