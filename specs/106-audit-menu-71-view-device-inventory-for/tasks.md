Dependency-ordered todos (atomic steps). Each item includes ID, title, description, test to add/update, and CI step.

1) Add ListSiteDevicesPager abstraction
- id: list-site-devices-pager
- Title: Implement paginated device iterator
- Description: New class that accepts (site_id, page_size, api_client) and yields device dicts. Internally iterates API with page tokens.
- Files: src/export/pager.py
- Tests: tests/unit/test_pager.py
  - test_iterates_pages_and_yields_devices
  - test_handles_empty_pages
  - test_retries_on_transient_errors
- CI: run tests/unit

2) Add StreamingCSVWriter
- id: streaming-csv-writer
- Title: Add streaming CSV writer abstraction
- Description: Writes header row then yields rows as devices stream in. Buffered writes (~64KB).
- Files: src/export/streaming_exporter.py
- Tests: tests/unit/test_streaming_writer.py
  - test_writer_streams_rows_without_accumulating
  - test_handles_commas_newlines_and_quotes
- CI: run tests/unit

3) Add SiteCache with TTL and forceRefresh
- id: site-cache
- Title: Per-site cache implementation
- Description: Cache API: get(site_id, force_refresh=False) -> index_info. Use lock per site during refresh.
- Files: src/cache/site_cache.py
- Tests: tests/unit/test_site_cache.py
  - test_ttl_expiry
  - test_force_refresh_bypasses_ttl
  - test_concurrent_refresh_serialized
- CI: run tests/unit

4) Integrate streaming export into SiteDeviceExporter
- id: integrate-exporter
- Title: Wire StreamingCSVWriter + Pager into exporter command
- Description: Modify relevant exporter CLI / handler to call ListSiteDevicesPager and StreamingCSVWriter when export requested.
- Files: src/commands/export_cmd.py (or existing exporter)
- Tests: tests/integration/test_streaming_export.py
  - test_integration_streaming_csv_row_count_and_content
  - test_export_uses_no_more_than_X_mb_memory (see perf harness)
- CI: run integration tests

5) Add InteractivePager UI
- id: interactive-pager
- Title: Implement pager with navigation and truncation
- Description: Add interactive pager to the menu with default page size 50, previous/next/first/last, column toggle and export command.
- Files: src/ui/pager.py
- Tests: tests/unit/test_pager_ui.py
  - test_page_navigation
  - test_truncation_rules
- CI: run tests/unit

6) Performance harness & benchmark job
- id: perf-harness
- Title: Add performance harness for large export
- Description: Standalone script tools/perf_harness.py that can create N synthetic devices or mock API and run streaming export measuring time, peak memory, CSV size.
- Metrics to capture: duration_ms, peak_memory_bytes, rows_exported, csv_size_bytes, writes_count, average_write_size
- Tests: N/A (it's a benchmark), but include script self-check: exit code 0 on success
- CI: add manual workflow or gated job that runs harness with N=10000 on dedicated runner (if available). Otherwise run on dedicated perf machine.

7) Docs & quickstart
- id: docs-quickstart
- Title: Add spec docs and quickstart
- Description: Create specs/106-audit-menu-71-view-device-inventory-for/{plan.md,research.md,data-model.md,quickstart.md,tasks.md}
- Tests: n/a
- CI: n/a

Notes
- Each task should be its own small PR (max 5 files changed per PR).
- Tests must include deterministic mocks to avoid flakiness.

-----------------------------------------------------------------------
