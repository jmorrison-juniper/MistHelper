Tasks — Menu 19 audit remediation (actionable)

T001 - Add PK strategy for site synthetic tests
- File: MistHelper.py
- Add entry to ENDPOINT_PRIMARY_KEY_STRATEGIES:
  - "searchSiteSyntheticTest": {
      "type": "composite_pk",
      "primary_key": ["id","site_id","timestamp"],
      "indexes": ["site_id","timestamp","type"],
      "description": "Site synthetic test search results"
    }
- Acceptance: New key present and documented.

T002 - Route export through DataExporter.write_with_format_selection
- File: MistHelper.py
- Replace DataExporter.save_data_to_output(sanitized, filename) with:
    DataExporter.write_with_format_selection(sanitized, filename, api_function_name="searchSiteSyntheticTest")
- Acceptance: write_with_format_selection is called with correct api_function_name.

T003 - Unit tests
- File: tests/unit/test_gateway_test_results.py (new)
- Tests to add:
  - test_results_by_site_sequential_calls_writer: mocks single-site path, ensures DataExporter.write_with_format_selection called with filename "AllGatewayTestResults.csv", correct record count, and api_function_name.
  - test_results_by_site_fast_mode_calls_writer: mocks cached CSV and concurrent path; asserts same behavior.
- Use monkeypatch/fixtures to stub mistapi and DataExporter.
- Acceptance: Both tests pass locally.

T004 - CI checks
- Commands:
  - python -m py_compile MistHelper.py
  - pytest -q
- Acceptance: No syntax errors; tests pass.

T005 - Documentation
- Update README changelog with timestamped entry noting dual-output compliance fix for menu 19.
- Acceptance: README updated.

Notes
- Implementation details (threading, rate limiting) should remain unchanged except for export routing.
- If returned records lack "timestamp" field, choose auto_increment_with_unique with an appropriate unique constraint.
