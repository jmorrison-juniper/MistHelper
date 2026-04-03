Objective:
Verify Menu #47 webhook export flows to CSV/SQLite correctly and that SQL exports use correct PK strategy.

Plan:
1. Inspect OrgConfigExporter.webhooks source and trace to DataExporter invocation.
2. Add unit tests mocking mistapi to simulate webhook list and assert DataExporter called with api_function_name.
3. If missing, plan a code change to pass api_function_name through APIDataFetcher to DataExporter.
4. Run test suite.
