Plan:
1. Inspect GatewayExportUtils.device_configs to find the exact API calls and exported filename.
2. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for the gateway device config endpoint (e.g., 'getOrgGatewayDeviceConfigs') with an appropriate primary key.
3. Update device_configs to call DataExporter.write_with_format_selection(processed_configs, "AllSiteGatewayConfigs", api_function_name="getOrgGatewayDeviceConfigs") instead of raw CSV writes.
4. Add unit tests (tests/test_gateway_configs.py) to assert the exporter calls DataExporter.write_with_format_selection with correct args and to test empty results.
5. Run py_compile and pytest; fix issues.

Deliverables:
- PK strategy entry
- Code adjustment to use write_with_format_selection
- Unit tests for SQL-export compliance
