Spec: Menu 61 — Compare inventory with external CSV (InventoryCSVComparator.execute)

Summary of findings:
- InventoryCSVComparator class exists and Menu wiring uses InventoryCSVComparator(...).execute().
- Due to class size (65 methods), tests may exercise some functionality but no focused unit tests were found for inventory-CSV comparison core behaviors.
- SQL export: Inventory comparator outputs reports; ensure any exported result intended for SQLite uses DataExporter.write_with_format_selection with api_function_name set (e.g., 'compareInventoryWithCSV' or a representative value) so the DB schema and PK strategy can be applied.

Key issues to address:
- Lack of targeted unit tests for matching logic, address normalization, and CSV parsing edge cases.
- Confirm ENDPOINT_PRIMARY_KEY_STRATEGIES entries for any API endpoints the comparator calls; most comparisons use local CSV vs fetched inventory, so ensure any API-derived exports have PK strategy.
