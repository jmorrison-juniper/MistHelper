Tasks for Menu #66 audit

- T66-1: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entries
  - Add entries for getOrgSle and getOrgSitesSle with recommended primary keys and indexes.
- T66-2: Update OrgExportUtils.sle_metrics
  - Replace DataExporter.save_data_to_output(...) with DataExporter.write_with_format_selection(..., api_function_name="getOrgSle") where appropriate.
- T66-3: Add unit tests
  - tests/unit/test_sle_metrics.py: Mock apisession and DataExporter to assert write_with_format_selection called when SQL selected.
- T66-4: Run checks
  - python -m py_compile MistHelper.py
  - pytest tests/unit -q
- T66-5: Documentation
  - Update README and changelog mentioning PK strategy entries and tests added.
