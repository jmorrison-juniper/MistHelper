Audit: Menu Option #15 — Export VPN peer path statistics (OrgDeviceStatsExporter.vpn_peer_stats)

Current state analysis
- Function: OrgDeviceStatsExporter.vpn_peer_stats found in MistHelper.py (static method at ~line 12434).
- Behavior: Uses APIDataFetcher(api_call=mistapi.api.v1.orgs.stats.searchOrgPeerPathStats, filename="OrgVPNPeerStats.csv", ...). APIDataFetcher.execute() exports via DataExporter which ultimately calls DataExporter.write_with_format_selection(..., api_function_name=api_name).

Issues found
- No direct unit test exists for OrgDeviceStatsExporter.vpn_peer_stats under tests/ (no matches for OrgVPNPeerStats or vpn_peer_stats).
- While DataExporter/APIDataFetcher pipeline sets api_function_name (derived from api_call.__name__), there is no targeted test asserting DataExporter.write_with_format_selection is invoked with api_function_name="searchOrgPeerPathStats" for this menu.
- No integration/e2e test exercising menu 15 behavior or CSV/SQLite outputs.

SQL export compliance check
- ENDPOINT_PRIMARY_KEY_STRATEGIES includes an entry for "searchOrgPeerPathStats" with type "composite_pk" and primary_key ["from_device","to_device","timestamp"] (lines ~3415-3421). Good.
- DataExporter.write_with_format_selection is invoked via APIDataFetcher with api_function_name derived from api_call.__name__. Given api_call is mistapi.api.v1.orgs.stats.searchOrgPeerPathStats, api_name will be "searchOrgPeerPathStats" — matching the PK strategy. Compliance: PASS, but untested.

Test coverage
- Unit tests present for ENDPOINT_PRIMARY_KEY_STRATEGIES validation (tests/unit/test_pk_strategies.py) include searchOrgPeerPathStats entry.
- No unit or integration tests exist for vpn_peer_stats behavior or that exports use the correct api_function_name for SQLite upserts.

Acceptance criteria
1. Unit test added that calls OrgDeviceStatsExporter.vpn_peer_stats (or the underlying APIDataFetcher) with mocked mistapi and DataExporter to assert:
   - API called: mistapi.api.v1.orgs.stats.searchOrgPeerPathStats
   - DataExporter.write_with_format_selection invoked with api_function_name="searchOrgPeerPathStats" and filename starting with "OrgVPNPeerStats".
2. Integration test that runs APIDataFetcher with a sample payload and asserts both CSV file created (data/OrgVPNPeerStats.csv) and SQLite table populated using SQLiteDatabaseReader (or inspecting data/mist_data.db) per ENDPOINT_PRIMARY_KEY_STRATEGIES mapping.
3. Update test docs and CI if necessary; all tests must pass.

Notes & assumptions
- Assume APIDataFetcher derives api_function_name via api_call.__name__ (confirmed in code).
- Tests should avoid calling real Mist APIs; use mocks for mistapi and file system where appropriate.
- Do NOT modify production code in this audit; only tests and specs are required.
