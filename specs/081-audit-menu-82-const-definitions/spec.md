# Audit: Menu #82 — Export all const definitions (ConstDefinitionsExporter.export_all)

Target: ConstDefinitionsExporter.export_all in MistHelper.py
Location: Approx. MistHelper.py lines 20398-20411 (class defined ~20368)

Summary:
- Dynamically discovers const endpoints under mistapi.api.v1.const and exports each to Const{Endpoint}.csv using DataExporter.save_data_to_output.
- Uses introspection to select list*/get* functions and handles special cases.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: Const endpoints are dynamic; exporter currently uses DataExporter.save_data_to_output and does not pass api_function_name.
- DataExporter: No write_with_format_selection usage per endpoint; PK mapping would need dynamic selection.
- Tests: No tests found specifically covering the dynamic discovery or export_all logic.

Conclusion: SQL export compliance: PARTIAL — dynamic endpoints require mapping; current code does not use write_with_format_selection, so SQL exports will not leverage PK strategies. Test coverage: MISSING.
