Tasks:
1. Read InventoryCSVComparator.execute in MistHelper.py and list the API calls and outputs it produces.
2. Write unit tests covering:
   - CSV parsing and normalization (various address formats, missing columns)
   - Matching logic (exact hostname, MAC, IP; fuzzy address matching)
   - Duplicate detection and reporting
   - Final report format (CSV/SQLite compatibility)
3. If method writes CSV via save_data_to_output, change to DataExporter.write_with_format_selection(report_rows, "InventoryComparisonResults", api_function_name="inventoryCompare") for SQL export compatibility.
4. Add PK strategy in ENDPOINT_PRIMARY_KEY_STRATEGIES if API-based export introduced.
5. Run pytest and fix failures.

Notes: Prefer tests that mock external network/API calls and rely on small CSV fixtures kept in tests/fixtures/.