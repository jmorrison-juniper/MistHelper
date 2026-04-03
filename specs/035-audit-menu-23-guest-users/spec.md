Audit: Menu 23 — Guest Users Export

Summary of findings
- Menu item #23 maps to OrgSiteExporter.current_guests() and OrgSiteExporter.historical_guests() (located in MistHelper.py around lines 11637-11748).
- Both methods call mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization and use mistapi.get_all to collect results.
- Both methods write output using DataExporter.save_data_to_output(...), not DataExporter.write_with_format_selection(). They do not pass api_function_name to the exporter.
- ENDPOINT_PRIMARY_KEY_STRATEGIES (starts at line 3260) does not contain an entry for the guest authorization endpoint (searchOrgGuestAuthorization). The dict falls back to the 'default' strategy.
- tests/ contains test_exports.py but no tests that cover guest export methods; a search for "guest" in tests/ returned no matches.

Impact
- Without api_function_name passed to the exporter, the SQL export pathway cannot map the API endpoint to a primary key/index strategy; guests will fall back to default auto-increment behavior, defeating deterministic upserts and index creation.
- No unit tests cover guest exports; risk of regressions.

Recommendation (high level)
1. Update OrgSiteExporter.current_guests() and historical_guests() to call DataExporter.write_with_format_selection(data, filename, api_function_name="searchOrgGuestAuthorization") to ensure SQL exports use endpoint-specific strategies.
2. Add an appropriate ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "searchOrgGuestAuthorization" (suggested: composite_pk, primary_key including id and timestamp or org_id — see plan for details).
3. Add unit tests that mock mistapi.get_all and assert DataExporter.write_with_format_selection is called with the correct api_function_name and that file naming is preserved.

Acceptance criteria
- Both guest export methods call DataExporter.write_with_format_selection with api_function_name.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for searchOrgGuestAuthorization with a documented primary key strategy.
- Automated tests exist and pass locally (py_compile and pytest).