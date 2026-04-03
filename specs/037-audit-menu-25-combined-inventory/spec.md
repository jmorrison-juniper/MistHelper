# Audit Spec: Menu Option #25 - Export combined inventory with site and address info by calendar week

Objective: Audit OrgInventoryExporter.combined_inventory_with_site_info for completeness, test coverage, and SQL export compliance.

Scope:
- Verify method implementation and behavior
- Verify ENDPOINT_PRIMARY_KEY_STRATEGIES entry relevant to this export
- Verify DataExporter.write_with_format_selection is used with api_function_name set
- Review existing tests and coverage for this operation

Acceptance criteria:
- Documented findings and gaps
- Actionable task list for any missing items
