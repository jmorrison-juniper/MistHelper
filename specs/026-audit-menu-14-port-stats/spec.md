# Spec

## Summary of current state
- Menu item 14: Export port-level statistics
- Function ref: OrgDeviceStatsExporter.device_port_stats
- Notes: SQL compliant, missing unit tests

## Purpose
Provide a robust, SQL-capable export of per-port statistics for organization devices. Support CSV and SQLite outputs with correct upsert semantics so repeated runs don't create duplicates and time-series data are preserved.

## Stakeholders
- NOC engineers (consumers)
- Backend developers (maintainers)
- QA / Test engineers
- Product owner / Documentation

## Acceptance criteria
1. Calling OrgDeviceStatsExporter.device_port_stats produces port-level records suitable for CSV and SQLite export.
2. When SQL export is selected, records are persisted using an upsert strategy that prevents duplicate rows for the same business key.
3. Upsert path must: INSERT new rows, UPDATE existing rows when the incoming row has a newer/changed payload, and preserve history for unique timestamped samples.
4. Exports include required indexes for query performance (see PK/index section).
5. Automated tests (unit + integration + SQL) present and passing.

## SQL behavior and upsert specifics
- Upsert semantics: Use SQLite `INSERT OR REPLACE` or `UPSERT` (preferred) consistent with existing DataExporter approach.
- Idempotency: Running the same export with identical samples must not create duplicate rows.
- Time-series preservation: Multiple samples for a port at different timestamps must be stored independently.
- Transactionality: Bulk inserts/updates must be wrapped in a transaction to ensure atomicity and performance.

## Required API function
- OrgDeviceStatsExporter.device_port_stats (as provided in metadata)

## Recommended primary-key strategy
- Recommendation: composite_pk
  - primary_key: ["device_id", "port_id", "timestamp"]
  - Reasoning: Port stats are time-series tied to both a device and a logical/physical port. A composite key prevents duplicate samples for the same timestamp while allowing multiple time-series entries over time. This enables efficient upserts and straightforward retention/aggregation queries.
  - Indexes: add secondary indexes on (device_id, timestamp) and (port_id) for filtering/joins.

## Test plan outline
- Unit tests (small scope):
  - Validate JSON flattening/field mapping for single port sample.
  - Validate correct column types and presence of required columns.
  - Validate exporter method calls write_with_format_selection with appropriate args (mocked).
- Integration tests (wider scope):
  - Run device_port_stats end-to-end with a mocked Mist API and in-memory SQLite to assert rows inserted.
  - Verify CSV output format and header correctness.
- SQL verification tests (critical):
  - Upsert idempotency: run exporter twice with same samples; assert rowcount unchanged.
  - Upsert update-path: insert row, then run with modified non-key field; assert row updated.
  - Time-series preservation: insert samples with different timestamps; assert multiple rows exist.
  - Transactionality and rollback: simulate failure mid-batch and assert no partial commits.

