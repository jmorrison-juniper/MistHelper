Spec: Menu 60 — Check firmware upgrade status (FirmwareManager.check_firmware_upgrade_status)

Summary of findings:
- Method exists: FirmwareManager.check_firmware_upgrade_status is present in MistHelper.py.
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No explicit entry observed for any firmware upgrade status endpoint; confirm entry for the API endpoint(s) used (e.g., listOrgFirmwareUpgrades / searchOrgFirmwareUpgrades).
- DataExporter usage: Ensure method calls DataExporter.write_with_format_selection(..., api_function_name="<mistapi_function_name>") for SQL export compatibility. Current implementation may use save_data_to_output or direct CSV writes.
- Tests: No unit tests found that assert SQL-export compliance or that DataExporter is invoked with correct api_function_name. Add tests for normal and empty-result cases.

Risks/Assumptions:
- Assume the underlying mistapi call name is e.g. "listOrgFirmwareUpgrades" or similar; verify exact function names before implementing changes.
