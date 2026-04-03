Plan
----
1. Locate GatewayStatsExporter.device_stats_with_freshness in MistHelper.py
2. Confirm ENDPOINT_PRIMARY_KEY_STRATEGIES entry for related endpoint(s) (gateway stats)
3. Search for DataExporter.write_with_format_selection calls inside the method with api_function_name set
4. Search tests/ for unit/integration tests covering this method
5. Produce tasks for missing coverage, missing PK strategy, or missing SQL export compliance

Deliverable: tasks.md with actionable remediation items.