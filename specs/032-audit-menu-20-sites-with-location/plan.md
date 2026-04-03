# Plan: Audit Menu #20 - Sites with Location and Timezone

Objectives:
1. Static review of OrgSiteExporter.sites_with_location to confirm data flow and output call
2. Verify ENDPOINT_PRIMARY_KEY_STRATEGIES contains a strategy covering the API used (listOrgSites)
3. Confirm whether DataExporter.write_with_format_selection(api_function_name=...) is used; if not, recommend change
4. Identify missing unit/integration tests and propose test coverage
5. Produce tasks to implement fixes and tests

Steps (high level):
- Read method body and note data transformations
- Search codebase for DataExporter usage patterns and current testing approach
- Draft unit test cases mocking APICoreFetchUtils and DataExporter
- Draft integration test plan to validate SQLite export when OUTPUT_FORMAT=sqlite
- Summarize recommendations and next steps

Constraints/Notes:
- Do NOT implement code changes in this ticket; produce artifacts only
