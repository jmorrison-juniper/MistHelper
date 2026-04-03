# Audit: Menu Option #22 - Export all devices with site and address info

Location: MistHelper.py (class OrgInventoryExporter, method devices_with_site_info)
Category: data_export

Scope:
- Verify completeness of OrgInventoryExporter.devices_with_site_info
- Ensure SQL export compliance via ENDPOINT_PRIMARY_KEY_STRATEGIES
- Confirm usage of DataExporter.write_with_format_selection with api_function_name
- Review test coverage in tests/ for this feature

Assumptions:
- No code changes will be made in this audit; this is an analysis-only spec.
- The primary key strategies are authoritative and located in MistHelper.py around line ~3260.

Deliverables:
- Findings report summarizing gaps in implementation, tests, and export compliance.
- Recommended actions for missing SQL export hooks or test coverage.
