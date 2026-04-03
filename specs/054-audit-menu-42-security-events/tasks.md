Tasks for Menu #42 (security_events):

- task-054-1: Create unit tests that run security_events in fast mode with mocked API responses and assert DataExporter.save_data_to_output/write_with_format_selection receives explicit api_function_name values for each file. (If code change approved, tests should fail until updated.)
- task-054-2: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entries for "listOrgSecIntelProfiles" and for any synthetic aggregated key used for OrgRogueData; specify appropriate PK/indexes.
- task-054-3: Add integration test to write OrgSecurityPolicies and OrgSecIntelProfiles to a temp sqlite and validate schema (natural_pk for policies, chosen strategy for secintel).
- task-054-4: Document changes in README and changelog.

Estimated effort: 3-6 hours (includes code changes, tests, and QA). Note: Implementation deferred until user approves code modifications.