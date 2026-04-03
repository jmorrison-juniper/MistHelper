Tasks for Menu #67 audit

- T67-1: Create PK strategy entry for getOrgSitesSle in ENDPOINT_PRIMARY_KEY_STRATEGIES.
- T67-2: Update OrgExportUtils.sites_sle_summary to call write_with_format_selection with api_function_name.
- T67-3: Add unit test tests/unit/test_sites_sle_summary.py to mock DataExporter and API calls.
- T67-4: Run python -m py_compile MistHelper.py and pytest.
