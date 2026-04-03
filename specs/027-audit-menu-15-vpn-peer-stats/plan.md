Implementation Plan: Audit coverage & tests for Menu #15 (vpn_peer_stats)

Overview
- Goal: Provide test coverage and verification that org VPN peer path statistics export (menu 15) is SQL-export-compliant and uses DataExporter with correct api_function_name.
- Scope: Add unit and integration tests; document test run steps and update CI docs if required. No production code changes.

Steps
1. Add unit test: tests/unit/test_menu_15_vpn_peer_stats.py
   - Mock mistapi.api.v1.orgs.stats.searchOrgPeerPathStats to return a deterministic response object.
   - Mock mistapi.get_all to return a list of dicts representing peer path stats.
   - Patch APIDataFetcher.execute or call OrgDeviceStatsExporter.vpn_peer_stats with mocks for APIDataFetcher to avoid real network.
   - Spy/mock DataExporter.write_with_format_selection to assert it was called with api_function_name="searchOrgPeerPathStats" and expected filename pattern (OrgVPNPeerStats.csv).
2. Add integration-style unit test: tests/integration/test_vpn_peer_stats_export.py
   - Use temporary directory (monkeypatch data dir) to capture CSV output.
   - Invoke APIDataFetcher directly with api_call mocked and a sample payload.
   - Assert CSV file exists and contains expected flattened columns.
   - Optionally check SQLite table created in data/mist_data.db (mock or in-memory DB) and validate PK columns presence per ENDPOINT_PRIMARY_KEY_STRATEGIES.
3. Update tests/index or CI docs to include new tests. Ensure tests run on CI.
4. Run pytest locally and iterate until green.

Deliverables
- tests/unit/test_menu_15_vpn_peer_stats.py
- tests/integration/test_vpn_peer_stats_export.py
- specs/027-audit-menu-15-vpn-peer-stats/* (spec.md, plan.md, tasks.md)

Risk/Assumptions
- Tests must mock mistapi and avoid network calls.
- SQLite validation may require small helper to introspect schema; prefer verifying that DataExporter.write_with_format_selection was invoked with correct api_function_name if DB inspection is costly.
