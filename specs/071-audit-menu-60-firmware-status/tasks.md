Tasks (ordered):
1. Inspect FirmwareManager.check_firmware_upgrade_status to record the exact mistapi calls (file: MistHelper.py).
2. Add an ENDPOINT_PRIMARY_KEY_STRATEGIES entry for the endpoint(s) used. Example:
   'listOrgFirmwareUpgrades': { 'type': 'natural_pk', 'primary_key': ['id'], 'indexes': ['org_id','device_id','status'] }
3. Modify method to call DataExporter.write_with_format_selection(..., api_function_name="listOrgFirmwareUpgrades").
4. Create tests/test_firmware_status.py:
   - test_firmware_status_writes_sql_compatible_call: mock mistapi call to return sample data and assert DataExporter.write_with_format_selection called with filename 'OrgFirmwareUpgradeStatus' and proper api_function_name.
   - test_firmware_status_handles_empty_result: mock empty return; assert no write or that empty file behavior is consistent with project pattern.
5. Run python -m py_compile MistHelper.py and run pytest. Fix issues until all tests pass.

Notes: Keep changes surgical and limited to firmware status flows. Add logging checkpoints for test instrumentation.