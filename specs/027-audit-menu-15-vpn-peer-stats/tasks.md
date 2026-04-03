Tasks for Menu #15 audit (vpn_peer_stats)

T001 - Create unit test for vpn_peer_stats (owner: dev)
- File: tests/unit/test_menu_15_vpn_peer_stats.py
- Steps:
  1. Patch mistapi.api.v1.orgs.stats.searchOrgPeerPathStats to be a callable mock.
  2. Patch mistapi.get_all to return sample list of peer path stat dicts (3-5 records).
  3. Patch DataExporter.write_with_format_selection to a mock and assert called with api_function_name="searchOrgPeerPathStats" and filename contains "OrgVPNPeerStats".
  4. Run pytest tests/unit/test_menu_15_vpn_peer_stats.py and fix failures.
- Estimate: 2-3 hours
- Acceptance: Test asserts API and DataExporter invocation and passes locally.

T002 - Create integration-style test for CSV and SQLite outputs (owner: dev)
- File: tests/integration/test_vpn_peer_stats_export.py
- Steps:
  1. Monkeypatch data directory to a tmp path.
  2. Mock API call returning representative payload.
  3. Run APIDataFetcher(...) .execute() and assert CSV file exists and has >=1 data row.
  4. Optionally: Open data/mist_data.db and assert table OrgVPNPeerStats (or OrgVPNPeerStats without .csv) exists and primary keys/columns per ENDPOINT_PRIMARY_KEY_STRATEGIES are present.
- Estimate: 3-4 hours
- Acceptance: CSV created; DataExporter called with correct api_function_name; DB inspection optional but recommended.

T003 - CI integration & documentation (owner: devops)
- Steps:
  1. Ensure new tests run in CI (pytest discovery).
  2. If SQLite DB checks are added, ensure CI has sqlite3 available (should be present).
  3. Update specs index (if maintained) to include this audit.
- Estimate: 1 hour
- Acceptance: CI run passes including new tests.

T004 - Review & merge (owner: reviewer)
- Steps:
  1. Peer review test code for robustness and mocking hygiene.
  2. Merge into main branch after passing CI.
- Estimate: 1 hour

Notes
- Keep tests isolated (no network, use tmpfs-like temp dirs). Use pytest tmp_path fixture and monkeypatch for environment variables.
