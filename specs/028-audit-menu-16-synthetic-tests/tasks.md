Tasks — Menu 16 audit remediation (actionable)

T001 - Add PK strategies
- File: MistHelper.py
- Edit ENDPOINT_PRIMARY_KEY_STRATEGIES to add entries:
  - "searchSiteSyntheticTest": { type: "composite_pk", primary_key: ["id","site_id","timestamp"], indexes: ["site_id","timestamp","type"], description: "Site synthetic test search results" }
  - "getSiteDeviceSyntheticTest": { type: "auto_increment_with_unique", primary_key: ["misthelper_internal_id"], unique_constraints: [["device_id","site_id","timestamp"]], indexes: ["device_id","site_id","site_name"], description: "Per-device synthetic test summary (no stable API id)" }
- Acceptance: New keys present and commented.

T002 - Route export through DataExporter
- File: MistHelper.py
- Replace DataExporter.save_data_to_output(sanitized, filename) with:
    DataExporter.write_with_format_selection(sanitized, filename, api_function_name="getSiteDeviceSyntheticTest")
- For site-level exporter (test_results_by_site), ensure use of api_function_name="searchSiteSyntheticTest".
- Acceptance: write_with_format_selection is called with correct api_function_name.

T003 - Unit tests
- File: tests/unit/test_gateway_synthetic_tests.py (new)
- Tests:
  - test_synthetic_tests_calls_write_with_format_selection_sequential
  - test_synthetic_tests_calls_write_with_format_selection_fast
- Use monkeypatch to stub API calls and DataExporter.write_with_format_selection capturing arguments.
- Acceptance: Both tests assert correct filename, record count, and api_function_name passed.

T004 - Run CI checks locally
- Commands:
  - python -m py_compile MistHelper.py
  - pytest -q
- Acceptance: No syntax errors; all tests pass.

T005 - Documentation
- Update README.md changelog with version timestamp and note dual-output fix for menu 16.
- Acceptance: README updated.

Dependencies and notes
- Determine exact response fields (timestamp/id) when implementing PKs. If uncertain, prefer auto_increment_with_unique to avoid accidental duplicate collisions.
- Ensure DataProcessingUtils.flatten_nested_fields produces list[dict].
