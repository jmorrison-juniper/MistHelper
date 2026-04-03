Plan

1. Locate SiteDeviceExporter.port_stats in MistHelper.py and read implementation
2. Identify which Mist API endpoint is called (searchSiteSwOrGwPorts) and parameters passed
3. Inspect ENDPOINT_PRIMARY_KEY_STRATEGIES for searchSiteSwOrGwPorts: primary key type, fields, indexes
4. Trace DataExporter.write_with_format_selection invocation and validate api_function_name usage and upsert logic
5. Search tests/ for any unit/integration tests referencing port stats or endpoint; list missing tests
6. Produce findings and recommended test cases and fixes

Assumptions
- No code changes will be made in this task
- specs directory exists
