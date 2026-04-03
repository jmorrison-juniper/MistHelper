Plan to verify and harden Menu #41 (wired_clients):

1. Add unit test to assert DataExporter.write_with_format_selection is called with api_function_name="searchOrgWiredClients" when OrgClientSecurityExporter.wired_clients() runs (mock API + capture write).
2. Integration test to write sample records to SQLite and verify composite_pk (mac,timestamp) used.
3. Run test suite; ensure no regressions.

Assumptions: Uses pytest, monkeypatch, and a temporary sqlite DB in data/ or tmp project folder.