Plan: How to perform the audit for Menu #30 (SiteClientExporter.clients)

Assumptions
- MistHelper.py is the source of truth.
- Tests run via pytest in tests/ directory.
- No code changes will be made in this task; produce findings and recommended fixes.

Steps
1. Static code review
   - Inspect SiteClientExporter.clients implementation for API calls, parameters, pagination, error handling, logging, and output path.
   - Confirm the exact API function name used: listSiteWirelessClientsStats.
2. Verify PK strategy mapping
   - Inspect ENDPOINT_PRIMARY_KEY_STRATEGIES for an entry matching listSiteWirelessClientsStats.
   - Confirm primary_key, indexes, and type (composite_pk).
3. Trace DataExporter behavior
   - Read DataExporter.write_with_format_selection implementation to understand how api_function_name influences SQLite table schema, upsert behavior, and indexes.
   - Compare that behavior to DataExporter.save_data_to_output used in clients().
4. Test coverage check
   - Search tests/ for any tests referencing SiteClientExporter, SiteClients, or listSiteWirelessClientsStats.
   - Run pytest -k to run relevant tests locally (note: do not modify code). Capture failures unrelated to this audit.
5. Produce audit report
   - Summarize risks, gaps, and recommendations: e.g., switch to write_with_format_selection to enable DB exports, add unit tests for empty/error cases, ensure composite PK fields exist in flattened output.

Acceptance criteria
- A clear report stating what was found and a prioritized list of recommended changes.
- tasks.md with actionable items for implementation (separate file).