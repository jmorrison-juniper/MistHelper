# Tasks for Menu 18 Audit Remediation

- add-endpoint-strategy
  - title: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for site settings
  - description: Insert a mapping for "getSiteSetting" with type "natural_pk", primary_key ["site_id"], and indexes ["site_name", "org_id"].
  - estimate: 0.5d
  - depends_on: []

- refactor-site-settings-export
  - title: Refactor SiteConfigExporter.settings to use write_with_format_selection
  - description: Replace DataExporter.save_data_to_output call with DataExporter.write_with_format_selection(data, filename, api_function_name="getSiteSetting"). Ensure data is flattened and escaped before writing.
  - estimate: 0.5d
  - depends_on: [add-endpoint-strategy]

- add-unit-tests
  - title: Add unit tests for SiteConfigExporter.settings
  - description: Create tests that mock APIFetchUtils.all_site_settings and assert DataExporter.write_with_format_selection is called with api_function_name="getSiteSetting" and correct record count. Place tests in tests/unit or tests/.
  - estimate: 0.5d
  - depends_on: [refactor-site-settings-export]

- run-tests-and-validate
  - title: Run full test suite and validate exports
  - description: Execute pytest, ensure no regressions, and perform a manual export run to verify SQLite primary key behavior.
  - estimate: 0.5d
  - depends_on: [add-unit-tests]

- update-readme
  - title: Update README changelog
  - description: Add version entry describing the audit fix.
  - estimate: 0.25d
  - depends_on: [run-tests-and-validate]

Notes:
- Do NOT implement changes in this task branch without PR review.
- Use mocks to isolate API calls in unit tests. Ensure tests clean up any created files in data/.
