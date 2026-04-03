Plan to verify and harden Menu #40 (wireless_clients):

1. Add unit test that calls OrgClientSecurityExporter.wireless_clients in test mode (mock API + FILE output) and asserts DataExporter.write_with_format_selection was invoked with api_function_name="searchOrgWirelessClients".
2. Add integration test: simulate API response rows and run APIDataFetcher path to write to SQLite; assert resulting table uses composite_pk strategy (PRIMARY KEY includes mac,timestamp).
3. Add lint rule/check to ensure exporter methods using APIDataFetcher pass api_function_name through to DataExporter (already true here).
4. Run existing unit test suite to confirm no regressions.

Assumptions:
- Tests will mock mistapi and filesystem. Use pytest fixtures for temp DB and monkeypatch for DataExporter.