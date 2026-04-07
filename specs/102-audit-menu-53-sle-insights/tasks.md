# Tasks (actionable)

1. Add spec files
   - Create folder specs/102-audit-menu-53-sle-insights and add this spec_md, plan_md, tasks_md. (depends: none)

2. Implement API wrapper
   - File: src/site_export_utils_wrappers.py (or existing SiteExportUtils integration point)
   - Task: implement a function call_site_insights(org_id, site_id, metric, start, end, interval) with pagination, retries, and normalized output. (depends: task 1)

3. Implement flattening
   - File: src/export/flatteners.py
   - Task: implement flatten_sle_insight(record) -> list of rows matching schema. Include assertions for timestamp and numeric value. (depends: task 2)

4. Implement export logic
   - File: src/export/exporter.py
   - Task: add write_csv(rows, path) and write_sqlite(rows, db_path, table_name='sle_insights') using CREATE TABLE + INSERT OR REPLACE, and create indexes. (depends: task 3)

5. Wire menu operation
   - File: MistHelper.py or menu registration place
   - Task: add menu entry "Export SLE Insights" (menu_id: 53) calling wrapper -> flatten -> exporter. Support CLI args for org/site/metric/start/end/interval and format flag (csv/sqlite). (depends: tasks 2,3,4)

6. Tests
   - Files: tests/test_flatten_sle.py, tests/test_export_sqlite_sle.py, tests/test_integration_sle_mock.py
   - Task: unit tests for flattening and sqlite upsert; integration test mocking SiteExportUtils.insights. (depends: tasks 2,3,4)

7. Documentation and spec commit
   - Task: update README/CHANGELOG and place spec files under specs/102-audit-menu-53-sle-insights; include usage example. (depends: tasks 1–6)

8. Validation and verification
   - Run unit tests and integration tests; run sqlite queries to confirm indexes and upsert behavior. Fix issues found. (depends: tasks 6,7)

Dependency summary: 1 -> 2 -> 3 -> 4 -> 5; tests (6) depend on 2,3,4; docs (7) after implementation; verification (8) final.
