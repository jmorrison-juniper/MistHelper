Plan
----
1. Locate MSPInventoryExporter.execute implementation
2. Enumerate API endpoints used and map to ENDPOINT_PRIMARY_KEY_STRATEGIES
3. Scan for DataExporter.write_with_format_selection calls with api_function_name
4. Evaluate tests/ for MSP inventory coverage (unit/e2e)
5. Create remediation tasks for missing PKs, missing DataExporter usage, or tests