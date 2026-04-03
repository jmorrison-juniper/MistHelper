Tasks for Menu #43 (rogue_clients):

- task-055-1: Create ENDPOINT_PRIMARY_KEY_STRATEGIES entry 'orgAggregatedRogueClients' with composite_pk (mac, site_id, timestamp).
- task-055-2: Modify rogue_clients exporter to pass api_function_name when saving (deferred until code change approved).
- task-055-3: Unit test 'test_rogue_clients_sql_mapping' to assert schema uses composite_pk when api_function_name provided.
- task-055-4: Integration test writing sample rogue client rows and verifying upsert semantics.

Estimated effort: 3-5 hours.