Plan — Audit remediation for Menu 19 (Gateway test results)

Goals
- Ensure SQL-compliant dual-output by routing exports through DataExporter.write_with_format_selection with api_function_name set.
- Define a primary key strategy for site-level synthetic tests in ENDPOINT_PRIMARY_KEY_STRATEGIES.
- Add unit tests for both fast (cached+concurrent) and sequential paths.

Steps
1. Add PK strategy
   - Edit MistHelper.py ENDPOINT_PRIMARY_KEY_STRATEGIES to add:
     "searchSiteSyntheticTest": {
         "type": "composite_pk",
         "primary_key": ["id", "site_id", "timestamp"],
         "indexes": ["site_id", "timestamp", "type"],
         "description": "Site synthetic test search results"
     }
   - Rationale: searchSiteSyntheticTest returns multiple records per site; timestamp present allows composite uniqueness.

2. Route export through write_with_format_selection
   - In GatewayTestExporter.test_results_by_site, replace:
       DataExporter.save_data_to_output(sanitized, filename)
     with:
       DataExporter.write_with_format_selection(sanitized, filename, api_function_name="searchSiteSyntheticTest")
   - Rationale: ensures CSV + SQLite exports use endpoint PK strategy and upsert semantics.

3. Tests
   - Add tests/unit/test_gateway_test_results.py with two tests:
     - test_results_by_site_sequential_calls_writer
     - test_results_by_site_fast_mode_calls_writer
   - Use monkeypatch to stub mistapi responses and to capture calls to DataExporter.write_with_format_selection.

4. Validation
   - Run python -m py_compile MistHelper.py
   - Run pytest -q; ensure new tests pass and existing tests unaffected.

5. Documentation
   - Note change in README changelog.

Assumptions
- No API contract changes. If timestamp not present in returned records, fallback to auto_increment_with_unique will be considered during implementation.
