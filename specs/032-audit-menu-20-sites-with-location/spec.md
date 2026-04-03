# Spec: Audit - Menu 20: Sites with Location and Timezone

Summary:
- Audit menu option #20 (OrgSiteExporter.sites_with_location) for completeness, SQL export compliance, and test coverage.

Scope:
- Review implementation in MistHelper.py
- Verify ENDPOINT_PRIMARY_KEY_STRATEGIES contains applicable strategy
- Confirm use of DataExporter.write_with_format_selection(api_function_name=...)
- Check existing tests
- Produce plan and tasks for remediation (no code changes in this ticket)

Assumptions:
- sites_with_location should map to the 'listOrgSites' API endpoint
- Exports should use DataExporter.write_with_format_selection so SQL PK strategies are applied

Acceptance Criteria:
- Spec, plan, and tasks created in specs/032-audit-menu-20-sites-with-location/
- Findings recorded, including whether write_with_format_selection is used
