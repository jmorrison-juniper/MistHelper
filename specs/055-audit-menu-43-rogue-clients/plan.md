Plan to remediate and test Menu #43 (rogue_clients):

1. Define a synthetic api_function_name for the aggregated output (e.g., "orgAggregatedRogueClients") and add ENDPOINT_PRIMARY_KEY_STRATEGIES entry with type="composite_pk", primary_key=["mac","site_id","timestamp"], indexes including site_id and timestamp.
2. Update code to call DataExporter.save_data_to_output(sanitized, "OrgRogueClients", api_function_name="orgAggregatedRogueClients"). (User requested no code changes now.)
3. Add unit and integration tests to validate sqlite schema and upsert behavior.
4. Run full test suite.

Assumptions: Timestamps are present in rogue client data; if not, use ingestion time as a timestamp field to enable composite PK.