# Plan: Remediation for Menu 18 (Site Configuration Settings Export)

Objective

Ensure Menu 18 exports are SQL-compliant with explicit primary key strategy and have unit test coverage.

Approach

1. Add endpoint strategy in ENDPOINT_PRIMARY_KEY_STRATEGIES for the canonical API name used by all_site_settings (recommendation: "getSiteSetting"). Define:
   - type: natural_pk
   - primary_key: ["site_id"]
   - indexes: ["site_name", "org_id"]

2. Refactor SiteConfigExporter.settings to call DataExporter.write_with_format_selection(data, filename, api_function_name="getSiteSetting") instead of DataExporter.save_data_to_output.

3. Add unit tests:
   - Mock ConfigUtils.get_cached_or_prompted_org_id to return a test org id.
   - Mock APIFetchUtils.all_site_settings to return sample site configs.
   - Assert DataExporter.write_with_format_selection called with expected args and data length.

4. Run existing test suite and linting. Fix issues as needed.

5. Update README changelog with version tag and brief description of change.

Assumptions

- The canonical api_function_name used by DataExporter should be the string key matching the endpoints in ENDPOINT_PRIMARY_KEY_STRATEGIES (e.g., "getSiteSetting").
- No schema migration required beyond adding indexes/PK definitions to the export pipeline.

Validation

- All tests pass.
- Manual inspection: run Menu 18 in a sandbox environment and confirm the SQLite export has the expected primary key column and indexes applied.
