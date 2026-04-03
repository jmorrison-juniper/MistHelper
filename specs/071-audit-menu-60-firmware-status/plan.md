Plan:
1. Verify the exact mistapi functions used by FirmwareManager.check_firmware_upgrade_status (grep for mistapi.api.v1.* firmware-related calls).
2. Add/confirm ENDPOINT_PRIMARY_KEY_STRATEGIES entry for the firmware endpoint(s). Define primary_key strategy (natural_pk with 'id' or composite_pk with device_id+timestamp as appropriate) and indexes.
3. Update FirmwareManager.check_firmware_upgrade_status to call DataExporter.write_with_format_selection(processed_rows, "OrgFirmwareUpgradeStatus", api_function_name="<exact_mistapi_function_name>") when data exists; preserve existing CSV fallback.
4. Add unit tests in tests/test_firmware_status.py to assert write_with_format_selection called with correct args and to validate behavior with empty results.
5. Run python -m py_compile and existing test suite.

Deliverables:
- PK strategy patch to ENDPOINT_PRIMARY_KEY_STRATEGIES
- Code change to FirmwareManager.check_firmware_upgrade_status
- Tests covering both non-empty and empty responses
- Spec and task artifacts (this directory)