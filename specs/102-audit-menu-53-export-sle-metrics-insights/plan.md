# Implementation Plan: Export SLE metrics insights (Menu #53)

Branch: 102-audit-menu-53-export-sle-metrics-insights
Spec: specs/102-audit-menu-53-export-sle-metrics-insights/spec.md
Date: 2026-04-03

## Executive summary (developer-ready)

Goal: Ensure SiteExportUtils.insights (Menu #53) exports complete, deterministic SLE metrics to CSV and optional SQLite with correct flattening, pagination handling, idempotent writes and indexes for fast queries.

Acceptance criteria (mapping to spec.md):
- AC-001: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for `listSiteSlesMetrics` with composite key [site_id, metric, duration, timestamp].
- AC-002/FR-002/FR-003: Stabilize and document flattening strategy; arrays will be JSON-encoded in a single cell.
- AC-003/FR-005: DataExporter.save_data_to_output to create endpoint-aware SQLite schema and perform upserts (idempotent).
- AC-004/FR-007: Implement and test pagination handling to fetch all pages.
- AC-005/FR-008: Wrap SQLite writes in transactions with rollback on failure.

This plan provides exact file edits, minimal function/class signatures, SQL DDL and test plan so a developer can implement the change with small, atomic commits.

## Concrete code changes (files, signatures, minimal patches)

High-level: introduce endpoint strategy entry, extend DataExporter to accept api_function_name and strategy, add helper class SleMetricsExporter to encapsulate logic (follow Five-Item Rule and class-based architecture).

Files to edit/create (surgical):
- MistHelper.py (modify): add ENDPOINT_PRIMARY_KEY_STRATEGIES entry and register menu mapping (if missing). Search for ENDPOINT_PRIMARY_KEY_STRATEGIES in repo and add the snippet below.
- src/exporters/sle_metrics.py (new): class SleMetricsExporter with method export(site_id, duration, csv_filename, sqlite_enabled=False, page_size=50)
- src/data_processing.py (modify if exists) or DataProcessingUtils (ensure flatten_nested_fields behaviour documented) -- add JSON-encode arrays option
- src/data_exporter.py (modify): DataExporter.write_with_format_selection(data_iterable, filename, api_function_name=None, sqlite_db_path='data/mist_data.db')
- tests/unit/test_flatten_sle_metrics.py (new)
- tests/integration/test_insights_export_integration.py (new)
- tests/fixtures/sle_metrics_sample.json (new)

Minimal class/function signatures (to add):

# in src/exporters/sle_metrics.py
class SleMetricsExporter:
    def __init__(self, api_client, data_exporter, page_size: int = 50):
        self.api = api_client
        self.data_exporter = data_exporter
        self.page_size = page_size

    def export(self, site_id: str, duration: str, csv_filename: str, sqlite_enabled: bool = False, limit: int | None = None) -> int:
        """Fetch all pages from listSiteSlesMetrics, flatten rows, and call data_exporter to persist.
        Returns number of rows exported."""
        ...

# in src/data_exporter.py (modification)
class DataExporter:
    def write_with_format_selection(self, rows_iter, filename_base: str, api_function_name: str | None = None, sqlite_db_path: str = 'data/mist_data.db') -> None:
        """rows_iter: iterator of dicts (flattened). If api_function_name provided, use ENDPOINT_PRIMARY_KEY_STRATEGIES to create table and upsert."""
        ...

Implementation notes & pseudopatch snippets:

1) ENDPOINT_PRIMARY_KEY_STRATEGIES entry (add to MistHelper.py or config module):

"listSiteSlesMetrics": {
  "type": "composite_pk",
  "primary_key": ["site_id", "metric", "duration", "timestamp"],
  "indexes": [["site_id", "metric", "duration"], ["timestamp"]],
  "description": "Site SLE metrics with composite key to ensure deduplication by site/metric/duration/timestamp"
},

2) DataExporter upsert pseudocode (sqlite):

# create table if not exists
CREATE TABLE IF NOT EXISTS sle_metrics (
  site_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  duration TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  value_json TEXT,
  raw_payload TEXT,
  PRIMARY KEY (site_id, metric, duration, timestamp)
);

# upsert per-row
INSERT INTO sle_metrics (site_id, metric, duration, timestamp, value_json, raw_payload)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(site_id, metric, duration, timestamp) DO UPDATE SET
  value_json = excluded.value_json,
  raw_payload = excluded.raw_payload;

Note: Use parameterized queries via sqlite3 module. For complex JSON fields, store as TEXT (JSON string). Use executemany for batching.

3) Page-collecting in SleMetricsExporter.export pseudocode:

rows_out = []
page = 1
while True:
    resp = self.api.v1.sites.sle.listSiteSlesMetrics(site_id=site_id, duration=duration, limit=self.page_size, page=page)
    items = resp.get('data', [])
    if not items:
        break
    for item in items:
        flat = DataProcessingUtils.flatten_nested_fields(item, json_encode_arrays=True)
        rows_out.append(flat)
    if not resp.get('next'):
        break
    page += 1
self.data_exporter.write_with_format_selection(iter(rows_out), filename_base=csv_filename, api_function_name='listSiteSlesMetrics')

For large exports avoid collecting all rows in memory: implement rows as generator streaming through writer and SQLite upserts using batch transactions of configurable batch_size (e.g., 1000).

## DB / schema changes

Add this snippet to centralized ENDPOINT_PRIMARY_KEY_STRATEGIES (exact text to add in MistHelper.py or config module):

"listSiteSlesMetrics": {
  "type": "composite_pk",
  "primary_key": ["site_id", "metric", "duration", "timestamp"],
  "indexes": [["site_id", "metric", "duration"], ["timestamp"]],
  "description": "Site SLE metrics with composite key to ensure deduplication by site/metric/duration/timestamp"
},

SQL DDL for SQLite table (example file: src/data_exporter.py will execute this):

CREATE TABLE IF NOT EXISTS sle_metrics (
  site_id TEXT NOT NULL,
  site_name TEXT,
  metric TEXT NOT NULL,
  duration TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  value_json TEXT,
  details_json TEXT,
  raw_payload TEXT,
  PRIMARY KEY (site_id, metric, duration, timestamp)
);
CREATE INDEX IF NOT EXISTS idx_sle_metrics_site_metric_duration ON sle_metrics(site_id, metric, duration);
CREATE INDEX IF NOT EXISTS idx_sle_metrics_timestamp ON sle_metrics(timestamp);

Upsert/dedup strategy:
- Use INSERT ... ON CONFLICT(primary_key) DO UPDATE to replace/merge values.
- If merging quantiles or arrays is needed, implement a small merge function before upsert (e.g., prefer latest timestamp or merge JSON fields). For simplicity prefer the latest write to overwrite.

SQL example (parameterized):

INSERT INTO sle_metrics (site_id, site_name, metric, duration, timestamp, value_json, details_json, raw_payload)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(site_id, metric, duration, timestamp) DO UPDATE SET
  site_name = excluded.site_name,
  value_json = excluded.value_json,
  details_json = excluded.details_json,
  raw_payload = excluded.raw_payload;

Note: SQLite supports ON CONFLICT DO UPDATE since 3.24.0; ensure CI environment uses modern sqlite3 (commonly available).

## Test plan

Unit tests (fast):
- tests/unit/test_flatten_sle_metrics.py
  - fixture: tests/fixtures/sle_metrics_sample.json (contains nested dicts and arrays)
  - assertions: flattened keys deterministic, arrays JSON-encoded, multiline strings escaped.
- tests/unit/test_endpoint_strategy_lookup.py
  - assert ENDPOINT_PRIMARY_KEY_STRATEGIES contains listSiteSlesMetrics and correct keys.

Integration tests (requires network stubbing):
- tests/integration/test_insights_export_integration.py
  - stub mistapi.api.v1.sites.sle.listSiteSlesMetrics to return paginated responses (3 pages). Use pytest monkeypatch or requests-mock on the mistapi client.
  - run SleMetricsExporter.export in test mode with sqlite_db_path pointing to a tmp file in tmp_path fixture.
  - assert CSV file exists, table sle_metrics exists, and row count equals sum of pages.
  - idempotency: run export twice and assert row count unchanged.

Edge cases:
- Flatten nested arrays (array of dimensions) — ensure JSON string preserved; test that array element order preserved.
- Dedup across paginated responses: include duplicated rows across pages to ensure ON CONFLICT prevents duplicates.
- Malformed responses: simulate missing fields, ensure exporter logs and skips but does not crash; verify transaction rollback if partial failure occurs.

Sample fixtures:
- tests/fixtures/sle_metrics_sample.json (2 sample items, one with nested arrays)
- tests/fixtures/sle_metrics_page_1.json, page_2.json, page_3.json for integration

Test file templates (minimal):
- tests/unit/test_flatten_sle_metrics.py
- tests/unit/test_data_exporter_upsert.py
- tests/integration/test_insights_export_integration.py

## Performance considerations

- Streaming: implement DataExporter.write_with_format_selection to accept an iterator/generator of rows so CSV and SQLite writes are streamed and do not require building the full dataset in memory.
- Batch upserts: use executemany with a batch_size (default 500-1000) wrapped in a single transaction for each batch to reduce disk I/O overhead.
- Memory guidance: on a typical dev machine, set batch_size such that peak memory < 200MB. For time-series exports with millions of rows use batch_size=1000 and enable WAL mode in SQLite (PRAGMA journal_mode=WAL) and PRAGMA synchronous=NORMAL.
- CSV streaming: use csv.DictWriter on file object opened with newline='' and buffering=1MB to avoid large RAM spikes.

Perf test harness (simple script):
- scripts/perf/run_sle_export_perf.py (new): generate N synthetic metric rows, feed to DataExporter.write_with_format_selection and measure throughput and peak memory using psutil; parameters: num_rows, batch_size, page_size.

## Migration & verification steps (deploy)

1. Create a feature branch: git checkout -b ci/102-audit-menu-53-export-sle-metrics-insights
2. Implement changes and run syntax check: python -m py_compile MistHelper.py
3. Run unit tests: pytest tests/unit -q
4. Run integration tests (may require setting env var TEST_MODE=1): pytest tests/integration -q
5. Run perf test (optional): python scripts/perf/run_sle_export_perf.py --num-rows 100000
6. Commit with message: "version 26.04.03.12.00 - implement menu 53 SLE metrics" (UTC) and include Co-authored-by trailer if pairing.

CI checklist (pre-merge):
- [ ] python -m py_compile MistHelper.py passes
- [ ] All unit tests pass
- [ ] Integration tests pass (or are marked flaky with justification)
- [ ] New fixtures added under tests/fixtures
- [ ] ENDPOINT_PRIMARY_KEY_STRATEGIES updated and tested
- [ ] Observability: logs at DEBUG/INFO as appropriate and no secrets logged

Recommended commit format:
version YY.MM.DD.HH.MM - implement menu 53 SLE metrics

Co-authored-by: Name <name@example.com>

## Tasks summary (see tasks.md for full entries)

T1 (S): add ENDPOINT_PRIMARY_KEY_STRATEGIES entry
T2 (M): implement SleMetricsExporter class and unit tests
T3 (M): update DataExporter to support endpoint-aware upserts and streaming
T4 (M): add pagination handling and integration tests
T5 (S): add logging & error handling + transaction rollback test
T6 (S): add quickstart and documentation files

## Assumptions & open clarifications

Assumptions (documented):
- Python 3.13+ (per constitution)
- SQLite3 available and supports ON CONFLICT DO UPDATE (sqlite3 version modern)
- Mist API client (mistapi) provides paginated responses via listSiteSlesMetrics with a standard shape (data, next)
- Default cache TTL and interactive pager page size unaffected by code changes (cache TTL=1 hour; page size default=50)

Remaining clarifications (product review required):
- Confirm composite primary key: [site_id, metric, duration, timestamp] is accepted. (Spec currently recommends this.)
- If merging behavior is required on duplicate keys (e.g., combine quantiles), define merge rules. Current plan overwrites with latest.


---

Plan authored by: speckit.plan agent
