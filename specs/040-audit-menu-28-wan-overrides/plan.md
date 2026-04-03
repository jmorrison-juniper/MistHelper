Plan: Audit Menu 28 - with_wan_overrides

Objective
- Produce a clear implementation plan for addressing issues discovered during static review. No code changes in this task.

Steps
1. Static review (done): Inspect with_wan_overrides, DataExporter, SQLiteDatabaseWriter, and ENDPOINT_PRIMARY_KEY_STRATEGIES mapping. Record findings.
2. Design change: Decide canonical api_function_name for this export (suggest: "getGatewayOverriddenPorts" or "gatewayOverriddenPorts").
3. PK Strategy: Review ENDPOINT_PRIMARY_KEY_STRATEGIES and add an entry for the chosen api_function_name with appropriate type (likely 'natural_pk' or 'auto_increment_with_unique' depending on available keys). Recommend composite primary key: ["device_id","port_name"] if no stable id present.
4. Implementation (separate task): Update GatewayExportUtils.with_wan_overrides to call DataExporter.write_with_format_selection(processed_data, "GatewayOverriddenPorts.csv", api_function_name="<chosen>") and ensure CSV fallback still works.
5. Tests: Add unit tests mocking CacheUtils, mistapi calls, and DataExporter.write_with_format_selection to assert api_function_name forwarded and correct behavior for: no env var, zero overrides, several overrides (fast and non-fast modes), API permission errors (403).
6. CI: Run python -m py_compile MistHelper.py and tests. Update README/changelog with version entry.

Notes
- For database strategy, prefer composite PK (device_id + port_name) to avoid auto-increment when a business key exists.
- Ensure DataExporter.validate_write_inputs will accept empty datasets: currently it warns and returns False; code currently creates empty CSV when no overrides and returns early — keep this behavior.

Deliverables
- Implementation changes (separate PR)
- Unit tests covering branches
- Updated ENDPOINT_PRIMARY_KEY_STRATEGIES entry
- CHANGELOG/README update
