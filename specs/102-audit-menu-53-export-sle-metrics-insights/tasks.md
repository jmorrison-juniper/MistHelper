# Tasks (dependency-ordered)

This tasks.md contains atomic, dependency-ordered todos suitable for insertion into the session DB `todos` table. Each item includes files to edit/create, tests to add, estimated size, and dependencies.

1) add-endpoint-strategy-listSiteSlesMetrics (S)
- Title: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for listSiteSlesMetrics
- Description: Insert the composite PK strategy into MistHelper.py (or central config). Ensure unit test verifies presence.
- Files: MistHelper.py (or src/config.py)
- Tests: tests/unit/test_endpoint_strategy_lookup.py
- Size: S
- Dependencies: none

2) unit-flatten-sle-metrics (S)
- Title: Unit test for flattening SLE metrics payloads
- Description: Add tests exercising DataProcessingUtils.flatten_nested_fields with json_encode_arrays=True. Add fixture sle_metrics_sample.json.
- Files: tests/unit/test_flatten_sle_metrics.py, tests/fixtures/sle_metrics_sample.json
- Tests: TC-001
- Size: S
- Dependencies: add-endpoint-strategy-listSiteSlesMetrics

3) implement-sle-metrics-exporter (M)
- Title: Implement SleMetricsExporter class
- Description: Create src/exporters/sle_metrics.py with SleMetricsExporter class that fetches paginated results, flattens rows, and streams to DataExporter.
- Files: src/exporters/sle_metrics.py
- Tests: tests/integration/test_insights_export_integration.py (integration), unit test for paging logic
- Size: M
- Dependencies: unit-flatten-sle-metrics

4) update-data-exporter-upsert (M)
- Title: Extend DataExporter to support endpoint-aware SQLite schema and upserts
- Description: Modify src/data_exporter.py to accept api_function_name, consult ENDPOINT_PRIMARY_KEY_STRATEGIES, create tables and indexes if missing, and perform batch upserts using ON CONFLICT DO UPDATE. Implement streaming writes and batch transactions.
- Files: src/data_exporter.py
- Tests: tests/unit/test_data_exporter_upsert.py
- Size: M
- Dependencies: implement-sle-metrics-exporter

5) integration-tests-paginate-and-idempotency (M)
- Title: Add integration tests for pagination and idempotency
- Description: Add tests to simulate paginated responses and duplicates across pages; verify CSV output, SQLite table, and idempotency across repeated runs.
- Files: tests/integration/test_insights_export_integration.py, tests/fixtures/sle_metrics_page_*.json
- Tests: TC-002, TC-003
- Size: M
- Dependencies: update-data-exporter-upsert

6) error-handling-rollback (S)
- Title: Implement transaction rollback and error handling tests
- Description: Ensure SQLite writes are wrapped in transactions and rollback on exceptions. Add test to simulate failure during write and assert no partial commits.
- Files: src/data_exporter.py, tests/unit/test_data_exporter_rollback.py
- Tests: TC-004
- Size: S
- Dependencies: update-data-exporter-upsert

7) docs-quickstart-and-data-model (S)
- Title: Add quickstart.md and data-model.md
- Description: Create docs under specs/102-audit-menu-53-export-sle-metrics-insights/
- Files: specs/102-audit-menu-53-export-sle-metrics-insights/quickstart.md, data-model.md
- Tests: n/a (documentation)
- Size: S
- Dependencies: none (can be done in parallel)

8) perf-harness (M)
- Title: Add simple perf harness to simulate large timeseries
- Description: scripts/perf/run_sle_export_perf.py to generate synthetic rows and measure throughput with configurable batch sizes.
- Files: scripts/perf/run_sle_export_perf.py
- Tests: manual perf runs; optional CI job
- Size: M
- Dependencies: update-data-exporter-upsert

SQL-ready INSERT statements (for session DB insertion):

INSERT INTO todos (id, title, description, status) VALUES
('add-endpoint-strategy-listSiteSlesMetrics', 'Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for listSiteSlesMetrics', 'Insert composite PK strategy into MistHelper.py and add unit test', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('unit-flatten-sle-metrics', 'Unit test for flattening SLE metrics payloads', 'Add unit tests and fixture for flattening behavior', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('implement-sle-metrics-exporter', 'Implement SleMetricsExporter class', 'Create exporter that pages, flattens and streams to DataExporter', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('update-data-exporter-upsert', 'Extend DataExporter for endpoint-aware upserts', 'Create tables/indexes and perform batch upserts with ON CONFLICT DO UPDATE', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('integration-tests-paginate-and-idempotency', 'Integration tests for pagination/idempotency', 'Add integration tests simulating pagination and duplicates', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('error-handling-rollback', 'Implement transaction rollback and tests', 'Ensure atomic writes and rollback on failure', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('docs-quickstart-and-data-model', 'Add quickstart.md and data-model.md', 'Create documentation files under specs/102-audit-menu-53-export-sle-metrics-insights/', 'pending');

INSERT INTO todos (id, title, description, status) VALUES
('perf-harness', 'Add perf harness for sle export', 'Add scripts/perf/run_sle_export_perf.py and test with large synthetic workloads', 'pending');


Notes:
- Keep each task small. If any task grows beyond its estimate, break it into sub-tasks respecting the Five-Item Rule.
- When implementing code, follow the Constitution rules: class-based architecture, syntax validation, and logging standards.


