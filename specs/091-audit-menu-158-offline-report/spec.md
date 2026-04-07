# Offline Device Report (menu_id: 158)

## Summary of current state
- Menu item: Offline Device Report
- Implementation entrypoint: OfflineDeviceReporter.execute
- Notes: Has tests (tests/test_offline_device_reporter.py). Uses DataExporter.write_with_format_selection for dual output (CSV / SQLite). SQL export is relevant (sql_export_relevant = 1) and report appears compliant with project patterns.

## Purpose
Provide a repeatable report of devices that are offline for customers/NOC use. Output must support CSV for quick consumption and SQLite for downstream queries and historical storage.

## Stakeholders
- NOC engineers (primary users)
- QA / Test Engineers
- Release/DevOps (exports, schema management)
- Product Owner / Support

## Acceptance Criteria
1. Functional
   - OfflineDeviceReporter.execute collects offline devices (per business rules) and returns a list/dict of records.
   - Outputs are written via DataExporter.write_with_format_selection supporting CSV and SQLite.
2. SQL behaviour
   - When SQL export is selected, records are persisted into a SQLite table with deterministic upsert semantics (no duplicates for the same logical record per run).
   - Upsert semantics MUST be explicit: either INSERT OR REPLACE or INSERT ... ON CONFLICT DO UPDATE depending on the schema strategy.
   - Table must include appropriate indexes for query performance (at minimum: org_id, device_id, site_id).
3. Observability & tests
   - Unit tests must validate behavior of the reporter logic and the write_with_format_selection invocation (mocked writer). Existing tests/test_offline_device_reporter.py must pass unchanged.
   - Integration tests must validate actual SQLite writes using a test DB file and assert upsert behaviour.

## Recommended Primary-Key Strategy
Recommended: composite_pk
- Primary key: ["device_id", "report_timestamp"] (report_timestamp = run timestamp or snapshot_ts)
- Reasoning:
  - Offline device reporting is a time-series snapshot: we want to keep a historical record of "which devices were offline at this snapshot" while avoiding duplicate rows for the same device within the same run.
  - Composite key with device_id + report_timestamp allows efficient historical queries and deterministic upserts for a single run (use report_timestamp truncated to run ID or exact UTC timestamp used by the exporter).
  - Add indexes on org_id and site_id for operational queries.

Alternative (if only current state is desired): natural_pk on device_id with last_seen/offline_since fields — but this loses historical snapshots.

## Schema notes (high-level)
- Table name suggestion: offline_devices
- Columns (minimum): device_id (TEXT), org_id (TEXT), site_id (TEXT), last_seen (INTEGER/ISO), offline_reason (TEXT), report_timestamp (INTEGER/ISO), metadata JSON (TEXT)
- Primary key: (device_id, report_timestamp)
- Indexes: org_id, site_id

## Test plan outline
1. Unit tests (fast, mocked):
   - Verify OfflineDeviceReporter.execute returns expected record shape for mocked API responses.
   - Verify DataExporter.write_with_format_selection is called with correct filename, format selection and api_function_name metadata.
   - Edge cases: no offline devices, API pagination or partial failures, malformed device records.
2. Integration tests (disk-based SQLite):
   - Use a temp test SQLite DB under repo (specs/091-audit-menu-158-offline-report/test_schema.db or pytest tmp_path). Run reporter with SQL export enabled.
   - Assert table created as expected, rows inserted.
   - Run reporter twice with same report_timestamp (or run id) and assert duplicate rows are not created (upsert), and with different timestamps historical rows accumulate.
   - Assert indexes exist and simple queries (COUNT, WHERE org_id=...) return expected results.
3. SQL verification steps:
   - Verify schema DDL matches recommended schema.
   - Validate primary key constraint exists and upsert uses it (INSERT OR REPLACE or ON CONFLICT clause).
   - Confirm performance for moderate sample sizes (1000s rows) by timing simple SELECT with index.

## Deliverables for implement phase
- Schema DDL (SQLite) and documentation in specs/091-audit-menu-158-offline-report/
- Updated ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "offline_devices" operation
- Integration test suite that performs SQL verification and is runnable via pytest
- Small README in spec_dir describing run/verification steps
