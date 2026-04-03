Specification: Audit of Menu #30 — Export client statistics for a selected site

Scope
- Target: Menu option #30 mapped to SiteClientExporter.clients in MistHelper.py
- Category: data_export
- Goals: Verify correctness, data-export path, DB primary key strategy usage, pagination behavior, and test coverage. Do not change code in this task.

Background findings (code references)
- Function: SiteClientExporter.clients (MistHelper.py) — uses mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(apisession, site_id, limit=1000) and mistapi.get_all to retrieve results.
- Data processing: DataProcessingUtils.flatten_nested_fields -> DataProcessingUtils.escape_multiline
- Current output: DataExporter.save_data_to_output(sanitized_data, filename) — writes CSV only.
- PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES includes "listSiteWirelessClientsStats" configured as composite_pk with primary_key ["client_mac","timestamp"]. See MistHelper.py (ENDPOINT_PRIMARY_KEY_STRATEGIES).

Audit questions
1. Does the function honor pagination correctly (uses get_all) and limits (limit=1000)?
2. Is data flattened and sanitized consistently with other exporters?
3. Should DataExporter.write_with_format_selection(api_function_name=...) be used instead of save_data_to_output to enable SQLite/Redis exports and upserts according to ENDPOINT_PRIMARY_KEY_STRATEGIES?
4. Are there unit/integration tests covering this menu action and edge cases (empty results, API errors, large payloads)?

Deliverables
- Short audit report summarizing findings and recommended non-breaking changes (e.g., using write_with_format_selection, adding tests).
- Actionable task list and implementation plan (separate files).
