# Spec

## Summary of current state
- Feature: Export VPN peer path statistics (menu_id: 15).
- Implementation reference: OrgDeviceStatsExporter.vpn_peer_stats.
- SQL relevance: Yes — SQL compliant via APIDataFetcher.
- Known gap: missing unit tests.
- Spec dir: specs/027-audit-menu-15-vpn-peer-stats

## Purpose
Provide a menu-driven operation that fetches VPN peer path statistics from the Mist API, normalizes/flatens results, and exports them to CSV and/or SQLite with correct upsert behavior for ingestion into analytics and reporting pipelines.

## Stakeholders
- NOC / Network Operations (consumers of exported metrics)
- Platform engineers (maintain exporter and DB schemas)
- QA/testing team
- Documentation maintainers

## Acceptance Criteria
1. Data retrieval: OrgDeviceStatsExporter.vpn_peer_stats is invoked and returns expected fields for known peers in API fixtures.
2. Export formats: Supports CSV and SQLite (via existing DataExporter/write_with_format_selection API).
3. SQL upsert behavior: Records must be upserted such that repeated runs do not create duplicates and updates to existing records overwrite older values. Implementations must use a deterministic upsert (INSERT OR REPLACE or equivalent UPSERT) respecting the chosen primary-key strategy.
4. Indices: Ensure indexes exist on commonly queried columns (device_id, peer_id, timestamp) for query performance.
5. Idempotency: Running the exporter repeatedly with identical input yields no duplicate rows and leaves data consistent.
6. Tests: Unit tests that mock API responses and assert correct flattening and call into write_with_format_selection; integration tests that verify SQL upsert semantics using a temporary SQLite DB.

## Required API function name
- OrgDeviceStatsExporter.vpn_peer_stats (as provided in metadata).

## Recommended primary-key strategy
- composite_pk
  - Suggested primary key fields: ["device_id", "peer_id", "path_id", "timestamp"] (or ["device_id","peer_id","timestamp"] if path_id not provided).
  - Reasoning: VPN peer path statistics are time-series/observational records tied to a device and peer (and optionally per-path). Composite keys avoid collisions across devices and peers, allow time-based uniqueness, and support upsert semantics for repeated ingestion of the same observation.

## Test plan outline
- Unit tests
  - Mock OrgDeviceStatsExporter.vpn_peer_stats responses (happy path, missing fields, empty set).
  - Assert flattening/normalization outputs expected dict structure and types.
  - Assert exporter calls DataExporter.write_with_format_selection with correct filename, api_function_name, and payload shape.
- Integration tests
  - Use a temporary SQLite DB to run the exporter end-to-end against fixture responses.
  - Verify INSERT/UPSERT behavior: run twice with the same fixture, assert row count remains stable; run with an updated fixture and assert row values update.
- SQL verification steps
  - Verify that primary-key constraints prevent duplicates.
  - Run sample SELECT queries to assert indexes are present and return expected rows.
  - Validate that exported CSV matches SQL contents for a sample timeframe.

## Notes
- The spec documents the PK recommendation; do not modify runtime ENDPOINT_PRIMARY_KEY_STRATEGIES until implement phase. Unit tests are currently missing and must be added before merging code changes.
