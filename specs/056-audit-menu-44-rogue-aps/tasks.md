Tasks for Menu #44 (rogue_aps):

- task-056-1: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry 'orgAggregatedRogueAps' (composite_pk: mac, site_id, timestamp).
- task-056-2: Modify rogue_aps exporter to pass api_function_name when saving (deferred).
- task-056-3: Unit test 'test_rogue_aps_sql_mapping' verifying SQLite schema uses composite_pk when api_function_name provided.
- task-056-4: Integration test to insert sample rogue AP rows and validate primary key/index presence and upsert correctness.

Estimated effort: 3-5 hours.