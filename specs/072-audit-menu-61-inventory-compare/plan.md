Plan:
1. Identify core responsibilities exercised by InventoryCSVComparator.execute: CSV loading, normalization, device matching, conflict reporting, and any API calls to fetch org inventory.
2. Create focused unit tests for key behaviors: CSV parsing, address normalization, exact and fuzzy matching, duplicate detection, and report generation. Use small, deterministic fixtures.
3. For any exported outputs intended for SQL storage, add DataExporter.write_with_format_selection calls and define corresponding entries in ENDPOINT_PRIMARY_KEY_STRATEGIES (likely auto_increment_with_unique or composite_pk depending on report content).
4. Refactor only if necessary to extract small helper methods to make unit-testing feasible; follow 5-Item Rule when refactoring.
5. Run test suite and iterate until all tests pass.

Deliverables:
- tests/test_inventory_compare.py with comprehensive unit tests
- Small PK strategy additions if API endpoints used for exports
- Minimal code adjustments (if needed) to call DataExporter.write_with_format_selection