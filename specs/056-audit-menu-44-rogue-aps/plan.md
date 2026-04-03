Plan to remediate and test Menu #44 (rogue_aps):

1. Define synthetic api_function_name (e.g., "orgAggregatedRogueAps") and add ENDPOINT_PRIMARY_KEY_STRATEGIES entry with composite_pk ["mac","site_id","timestamp"].
2. Update rogue_aps to call DataExporter.save_data_to_output(sanitized, "OrgRogueAPs", api_function_name="orgAggregatedRogueAps").
3. Add unit tests to verify write_with_format_selection receives api_function_name and integration tests that validate SQLite schema and upsert semantics.
4. Run test suite.

Note: Implementation deferred until user approves code edits.