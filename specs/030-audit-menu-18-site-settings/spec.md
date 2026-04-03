# Spec: Audit — Menu 18 — Site Configuration Settings Export

Summary

Audit of MistHelper menu option #18 (SiteConfigExporter.settings).

Background

Menu 18 exports configuration settings for all sites to AllSiteConfigs.csv by calling APIFetchUtils.all_site_settings() and writing output.

Findings

- Implementation: SiteConfigExporter.settings calls APIFetchUtils.all_site_settings(), flattens and escapes data, and calls DataExporter.save_data_to_output(data, "AllSiteConfigs.csv").
- SQL/export strategy: No explicit api_function_name is passed to DataExporter (write_with_format_selection), so SQL export pathway cannot apply an endpoint-specific primary key strategy.
- Endpoint mapping: ENDPOINT_PRIMARY_KEY_STRATEGIES (starts at line 3260) does not contain a specific entry for the underlying API used (mistapi.api.v1.sites.setting.getSiteSetting / getSiteSettings). The default fallback will be used for SQL exports.
- Test coverage: No unit tests found for this menu option in tests/ (no references to AllSiteConfigs or SiteConfigExporter).

Impact

- SQLite/SQL exports will lack correct primary key/index definitions for site configuration records if saved via the SQL exporter, leading to potential duplicate rows or poor queryability.
- No automated tests means regressions can occur unnoticed.

Acceptance Criteria

1. SiteConfigExporter.settings must call DataExporter.write_with_format_selection(..., api_function_name="getSiteSetting") or equivalent.
2. Add an ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "getSiteSetting" (or the canonical API name used) defining a suitable primary key (e.g., ["site_id"]) and useful indexes.
3. Add unit tests that mock APIFetchUtils.all_site_settings and assert DataExporter.write_with_format_selection is called with the expected api_function_name and correct row count.
4. Update README/changelog noting the audit and changes.

Notes

- The API call used by APIFetchUtils.all_site_settings is mistapi.api.v1.sites.setting.getSiteSetting (single-site call executed for each site). The canonical name for the strategy should match the api_function_name passed to DataExporter.write_with_format_selection.
- Do NOT implement changes in this spec; this document defines the audit findings and acceptance criteria only.
