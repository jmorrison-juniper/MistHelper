# Tasks: Maps Manager sub-menu (Menu 112)

1. Code discovery task
- id: audit-112-code-discovery
- description: Locate Maps Manager command handlers in MistHelper.py and maps_manager.py, list functions called, and capture their signatures.
- output: discovery.json saved under specs/112-audit-menu-112-maps-manager-sub-menu/

2. Export strategy task
- id: audit-112-export-strategy
- description: For each handler that returns list/table data, add an entry to ENDPOINT_PRIMARY_KEY_STRATEGIES and implement a call to DataExporter.write_with_format_selection if missing.
- acceptance: write_with_format_selection used with filename param and api_function_name recorded

3. Test skeletons task
- id: audit-112-test-skeletons
- description: Create pytest skeletons under tests/test_maps_manager.py with mocks for Mist API, sample payloads, and JSON fixtures.
- acceptance: pytest runs the skeleton and imports modules with no syntax errors

4. Integration task (follow-on)
- id: audit-112-integration
- description: Wire up full tests using recorded fixtures to validate DataExporter outputs (CSV/SQLite) in tmp directories.

Estimated effort: 2-4 days for a single developer to implement everything end-to-end.

