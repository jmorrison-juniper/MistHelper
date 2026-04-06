# Spec

## Summary of current state
- Menu item 13: "Export device statistics". Notes: SQL compliant via APIDataFetcher; missing unit tests.

## Purpose
Provide a repeatable operation to export device statistics (time-series metrics) from the Mist API into CSV and SQL backends using the existing exporter plumbing so NOC engineers can analyze device behavior offline.

## Stakeholders
- NOC engineers (primary users)
- Platform engineers (maintainers of exporter and DB schemas)
- QA (test and verification)

## Required API function
- OrgDeviceStatsExporter.device_stats (function_ref)

## Acceptance criteria
1. The exporter calls OrgDeviceStatsExporter.device_stats and passes responses through existing flatten/normalize helpers.
2. Dual-output support: CSV and SQLite (via DataExporter.write_with_format_selection) must be available.
3. SQL behavior: upsert semantics must prevent duplicate rows and preserve latest sample values:
   - For composite_pk endpoints, use INSERT OR REPLACE keyed by (device_id, metric_id, timestamp) to allow time-series granularity.
   - For natural PK endpoints (if any), use INSERT OR REPLACE on the UUID.
   - For aggregated summaries, use auto_increment_with_unique with a generated misthelper_internal_id and a uniqueness constraint if needed.
4. Indexes exists to support typical queries (device_id, timestamp).  
5. No regressions in existing exporters; exporter remains idempotent and rate-limited per APIDataFetcher.
6. Unit tests present and passing for all new logic; integration test validates end-to-end export to SQLite with upsert verification.

## Recommended primary-key strategy and rationale
- Recommended: composite_pk
  - Reason: device statistics are time-series. Composite key of [device_id, metric_name (or metric_id), timestamp] prevents accidental aggregation collisions and supports efficient upserts of individual samples.
  - Suggested primary_key fields: ["device_id","metric_name","timestamp"]
  - Suggested indexes: (device_id, timestamp), (metric_name, timestamp)

## Test plan outline
1. Unit tests (missing today):
   - Mock OrgDeviceStatsExporter.device_stats to return representative payloads.
   - Validate JSON flattening, field types (timestamps normalized), and CSV rows generated.
   - Verify that DataExporter.write_with_format_selection is called with expected parameters (CSV and SQL paths).
2. Integration tests:
   - Run the exporter against a local test SQLite DB via APIDataFetcher mocks and fixture responses.
   - Verify row counts, sample values and indexes.
3. SQL verification steps:
   - Insert fixture rows twice; confirm row count does not duplicate when keys equal (upsert happened).
   - Insert later-timestamped sample for same device+metric; confirm row replaced or new row inserted according to composite key semantics.
4. Edge cases:
   - Missing metric_name or timestamp fields (assert and normalize or drop depending on contract).
   - Large payloads and rate-limit handling (simulate paginated API responses).

