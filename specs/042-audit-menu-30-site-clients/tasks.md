Tasks: Audit Menu #30 — SiteClientExporter.clients

1. Code review (owner: auditor)
   - Read SiteClientExporter.clients and document the exact API call, parameters, and data flow to the output file.
   - Output: one-paragraph summary (done in spec.md).

2. PK strategy verification (owner: auditor)
   - Confirm ENDPOINT_PRIMARY_KEY_STRATEGIES contains listSiteWirelessClientsStats and validate primary_key fields (client_mac,timestamp) are present in flattened output.
   - Outcome: note any mismatches.

3. DataExporter behavior analysis (owner: auditor)
   - Read DataExporter.write_with_format_selection to determine table creation and upsert semantics when api_function_name is provided.
   - Compare to save_data_to_output usage in clients(); note missing DB-export capability.

4. Test inventory and execution (owner: auditor)
   - Search tests/ for existing tests; run pytest focused on pk strategies and export functions. Note absence of tests for this menu item.
   - Outcome: list missing tests.

5. Recommendations and prioritization (owner: auditor)
   - Provide recommended changes: use write_with_format_selection(api_function_name='listSiteWirelessClientsStats'), ensure flattened data contains primary key fields, add unit tests for empty/error cases, add integration test writing to temp SQLite and verifying upserts.

6. Reporting (owner: auditor)
   - Produce final one-page audit report summarizing findings and next steps.

Notes
- Do NOT implement code changes in this task. Provide clear, minimal reproduction steps and exact code locations for proposed edits.