# Feature Specification: Export beacon information

**Feature Branch**: `001-export-beacons`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Create a feature specification for MistHelper Menu #50: \"Export beacon information\"\n\nFunction: SiteClientExporter.beacons\nCategory: data_export\nSQL export relevant: Yes\n\nThis is an AUDIT spec — analyze the existing implementation in MistHelper.py, document current state, identify issues, and define acceptance criteria for fixes. Focus on: how SiteClientExporter.beacons works, API call flow, data flattening, dual output (CSV/SQLite), primary key strategy, test coverage gaps, any issues found."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export site beacons to CSV (Priority: P1)

Operators need a simple, reliable way to export all beacon records for a selected site to a CSV file for audit, troubleshooting, or archival purposes.

Why this priority: Beacon exports are used for audits and physical inventory reconciliation; CSV is the baseline customer format for downstream tools and spreadsheets.

Independent Test:
- Select a site with known beacons and run the Menu #50 export.
- Verify a CSV file is created under data/, named like `SiteBeacons_<SiteName>.csv` and that it contains one row per beacon with expected columns.

Acceptance Scenarios:
1. Given a site with N beacons, When the operator runs the export, Then the system writes exactly N rows to the CSV and reports "! N records exported".
2. Given a site where the API returns nested structures (e.g., "location": {..}), When exported, Then nested fields are flattened into distinct columns with deterministic keys (e.g., location_lat, location_lon).
3. Given the API returns no beacons, When exported, Then an empty CSV (header only) is created and a log/warn message is emitted.

---

### User Story 2 - Export site beacons to SQLite (Priority: P2)

Operators or analytic processes need beacons available in a local SQLite database for queries and joining with other tables produced by MistHelper.

Why this priority: SQLite is the canonical downstream format for aggregated exports in this project; SQL export is relevant for audit-grade storage and indexing.

Independent Test:
- Run the export with OUTPUT_FORMAT set to "sqlite" and verify table exists in the configured database.
- Verify the table contains expected columns and that primary key strategy preserves uniqueness across repeated exports.

Acceptance Scenarios:
1. Given OUTPUT_FORMAT=sqlite and site with N beacons, When export runs, Then the SQLite database contains table `SiteBeacons_<SiteName>` with N rows and the chosen primary key strategy applied.
2. Given repeated exports for the same site, When strategy is natural/composite PK then duplicate rows are upserted (not duplicated); when using auto-increment fallback, the table is cleared and re-populated (behavior documented).

---

### User Story 3 - Reliable handling of API pagination and rate-limiting (Priority: P1)

Operators must be confident exports are complete even for sites with large numbers of beacons and when the API paginates or rate-limits.

Independent Test:
- Simulate or mock paginated API responses and verify all pages are requested and processed.
- Simulate 429 responses and verify retry/backoff is used (or note behavior if not currently implemented).

Acceptance Scenarios:
1. Given API paginates results, When export runs, Then the exporter collects all pages and reports total count equal to sum of pages.
2. Given API returns HTTP 429 briefly, When export runs, Then exporter either retries (with backoff) or fails gracefully with a clear error message.

---

### Edge Cases

- Very large site export (10k+ beacons): ensure memory and write strategy tolerates the volume (streaming where possible).
- Missing or unexpected fields (e.g., missing "id" vs. "uuid"): exporter should neither crash nor produce ambiguous primary key behavior.
- Partial API failures (some pages fail): exporter should perform an emergency save of partial data and report which pages failed.

## Analysis of Current Implementation (current-state audit)

Summary
- The public Menu handler is SiteClientExporter.beacons(), implemented as a thin wrapper calling SiteExportUtils._export_data(api_call=mistapi.api.v1.sites.beacons.listSiteBeacons, data_type="beacons", sort_key="name").
- SiteExportUtils._export_data handles site selection, fetches site name, invokes the provided API call (with limit=1000 where supported), collects all pages via mistapi.get_all(response=...), flattens nested fields using DataProcessingUtils.flatten_nested_fields(), escapes multiline strings with DataProcessingUtils.escape_multiline(), and writes output via DataExporter.save_data_to_output(data, filename).

API call flow
- User triggers Menu #50 → SiteClientExporter.beacons() → SiteExportUtils._export_data() with api_call mistapi.api.v1.sites.beacons.listSiteBeacons.
- SiteExportUtils inspects the api_call signature to decide whether to pass limit=1000.
- The call is executed as api_call(apisession, site_id, limit=1000) (when supported).
- mistapi.get_all(response=..., mist_session=apisession) is used to collect paginated results into a single list (rawdata).
- Post-processing: optional sort by provided key, flattening, escaping multiline, then DataExporter.save_data_to_output() is called.

Data flattening behavior
- DataProcessingUtils.flatten_nested_fields:
  - For each dict entry it attempts to parse stringified dicts/lists using ast.literal_eval then json.loads fallback.
  - Nested dicts are flattened using flatten_dict which concatenates keys with underscore separator. Lists of dicts are flattened by indexing items (key_0_field, key_1_field, ...). Non-dict lists are joined into comma-separated strings.
  - This approach produces predictable flat column names but can lead to a variable schema depending on list lengths (list indexing creates per-index columns).

Dual output (CSV / SQLite) behavior
- DataExporter.write_with_format_selection chooses between CSV and SQLite based on global OUTPUT_FORMAT (or explicit override).
- CSV: DataExporter.write_to_csv writes CSV into data/ directory, determining all unique fields across records as CSV headers.
- SQLite: DataExporter._write_sqlite_format delegates to SQLiteDatabaseWriter(data, table_name, api_function_name).write().

Primary key strategy (SQLite)
- SQLiteDatabaseWriter determines fields and queries DatabaseSchemaUtils.get_endpoint_strategy(api_func_name, fields) to choose a strategy.
- api_func_name is inferred via DatabaseSchemaUtils.determine_api_function_name_from_context() when not passed explicitly; it scans the Python call stack for function names containing patterns like listSite, getSite, etc., and returns the first match.
- DatabaseSchemaUtils.get_endpoint_strategy:
  - Uses an ENDPOINT_PRIMARY_KEY_STRATEGIES mapping for many API names; if the detected api_function_name is present, that explicit strategy is used.
  - Otherwise falls back to the "default" strategy: type=auto_increment_with_unique, with enhancement: if 'id' exists in data_fields, it appends 'id' to unique_constraints and indexes. Common index fields (org_id, site_id, device_id, timestamp, mac, serial) are also added if present.
- The SQLite writer then builds CREATE TABLE SQL according to strategy:
  - natural_pk and composite_pk use PRIMARY KEY constraints on specified fields and write using INSERT OR REPLACE for upsert semantics.
  - auto_increment_with_unique uses an auto-increment internal id primary key and applies UNIQUE(...) constraints where specified; it uses plain INSERT after clearing the table (DELETE FROM) to ensure fresh data.

Test coverage and code paths exercised
- The codebase contains many utilities, but there are no unit tests discovered in the repository that specifically target:
  - SiteExportUtils._export_data behavior for site-scoped API calls
  - DataProcessingUtils.flatten_nested_fields edge cases (stringified JSON, lists of dicts, deeply nested dicts)
  - SQLiteDatabaseWriter strategy selection and upsert/insert behaviors for the beacons endpoint
  - DatabaseSchemaUtils.determine_api_function_name_from_context behavior (stack-inspection brittle in different calling contexts)
- Integration tests for dual-output modes (csv vs sqlite) are not present.

Issues and risks found
1. Implicit API function detection (stack inspection)
   - SQLiteDatabaseWriter relies on DatabaseSchemaUtils.determine_api_function_name_from_context to infer the API function name when the api_function_name is not provided. Stack inspection is brittle, may fail in refactors or when code is invoked differently (e.g., via task agents or external wrappers), leading to wrong strategy selection and therefore incorrect primary key/index behavior.

2. Missing explicit propagation of api_function_name
   - SiteExportUtils._export_data calls DataExporter.save_data_to_output(data, filename) without passing api_function_name or api_call.__name__. This misses an opportunity to deterministically inform the SQLite writer which endpoint is being processed.

3. Variable schema from list-of-dicts flattening
   - DataProcessingUtils.flatten_nested_fields flattens lists of dicts by expanding indexed keys (e.g., tags_0_name, tags_1_name). For endpoints where list lengths vary across records, the CSV header and SQLite table schema may balloon unpredictably and differ between runs, causing downstream schema instability.

4. Primary key ambiguity for beacons
   - If beacon records do not include a stable 'id' field (or if the field is named differently, e.g., 'uuid' or 'beacon_id'), DatabaseSchemaUtils may not detect a natural key and will fall back to auto-increment with no unique constraints. That means repeated exports can create table re-population behavior instead of idempotent upserts. SiteExportUtils._export_data does not pass api_function_name to DataExporter to allow DatabaseSchemaUtils to match endpoint-specific strategy if one existed.

5. No explicit handling of API rate-limits in SiteExportUtils._export_data
   - The code relies on mistapi.get_all to handle pagination; although APIDataFetcher has rate-limit handling, SiteExportUtils._export_data does not implement explicit retry/backoff logic for 429 responses in this wrapper. This may lead to incomplete exports on rate-limited calls.

6. Test coverage gaps
   - No unit tests for flattening, sqlite write strategies, or for the SiteExportUtils._export_data flow. This increases risk that refactors or bug fixes introduce regressions.

7. Lack of logging/metrics for schema evolution
   - When flattening results introduce new fields (columns), there's no summary log pointing out newly added columns or schema drift; debugging schema issues requires manual inspection of data/ or SQLite schema.

## Functional Requirements (testable)

- FR-001: SiteClientExporter.beacons MUST export all beacons from the selected site by calling the correct Mist API (listSiteBeacons) and collecting paginated results. (Test: mock paginated API and assert all pages requested)

- FR-002: The exporter MUST flatten nested fields deterministically using underscore separators, and lists of dicts MUST be flattened with indexed suffixes (e.g., sensors_0_type). (Test: given nested sample input, assert flattened keys match expected output)

- FR-003: The exporter MUST write output to CSV when OUTPUT_FORMAT is "csv" and to SQLite when OUTPUT_FORMAT is "sqlite". (Test: set OUTPUT_FORMAT and assert presence of CSV file or SQLite table)

- FR-004: When writing to SQLite, the exporter MUST use an explicit api_function_name (derived from api_call.__name__) to determine schema strategy, falling back to stack inspection only if this explicit value is absent. (Test: spy on SQLiteDatabaseWriter.determine strategy when api_function_name passed vs not passed)

- FR-005: The SQLite write strategy for beacons SHOULD prefer a natural primary key when the API exposes a stable identifier (id or uuid). If such a stable identifier exists, the table MUST be created with PRIMARY KEY on that field and writes MUST use upsert/REPLACE semantics. (Test: sample data containing 'id' should produce a natural_pk strategy and REPLACE behavior)

- FR-006: The exporter MUST handle API rate limiting and transient errors gracefully (retry with exponential backoff at least once for 429). If full retrieval cannot be completed, the exporter MUST save partial results and report which page(s) failed. (Test: simulate 429 responses and validate retry/backoff)

- FR-007: The exporter MUST log schema differences when a new export run introduces new fields (at INFO level, listing added column names). (Test: run two exports with incremental fields and assert INFO log listing new fields)

- FR-008: Documentation: The code MUST include a short docstring or comment in SiteExportUtils._export_data to explain that api_function_name should be forwarded to DataExporter.save_data_to_output when available. (Test: code review or static check)

## Success Criteria *(mandatory, measurable)*

- SC-001: 100% of beacons returned by mistapi.get_all for listSiteBeacons are present in the final exported dataset (CSV or SQLite) for test sites up to 25k items. (Verification: integration test against mocked API)

- SC-002: CSV export completes and writes a file under data/ within 5 minutes for sites with <= 10,000 beacons on a typical developer workstation. (Verification: timed export run)

- SC-003: SQLite exports for endpoints where 'id' exists use natural_pk or composite_pk strategy and perform idempotent upserts (verified by re-running export twice and asserting row count does not increase after second run). (Verification: run export twice and query row count)

- SC-004: On simulated 429 responses, the exporter retries with backoff at least 2 times before failing; if it ultimately fails, partial data is saved and error report indicates the failed pages. (Verification: mock 429 responses)

- SC-005: Unit test coverage for DataProcessingUtils.flatten_nested_fields and SQLiteDatabaseWriter strategy selection increases to >= 80% for their public behaviors related to beacons export. (Verification: coverage report)

## Key Entities

- Beacon
  - Typical attributes: id (uuid), uuid, mac, name, type, power, major, minor, x, y, map_id, site_id, created_at
  - Notes: Some beacons are virtual (vbeacons) and may be returned by a different API (listSiteVBeacons) with overlapping but not identical fields.

- Site
  - Attributes: id, name

- ExportFile / DB Table
  - Attributes: filename/table_name, columns determined by flattened field set, row_count

## Assumptions

- Assumes the Mist API returns a stable identifier in the field 'id' for beacons; if the actual field is 'uuid' or another name, DatabaseSchemaUtils will only pick it up if that field appears in the flattened data_fields.
- Assumes mistapi.get_all handles pagination correctly and returns a list or empty list when no results.
- Assumes OUTPUT_FORMAT global exists and is either 'csv' or 'sqlite'.
- Reasonable default for retries/backoff is at least 2 retries with exponential backoff; exact policy to be implemented per FR-006.

## Proposed Fixes / Improvements (actionable)

1. Pass api_function_name explicitly when calling DataExporter.save_data_to_output from SiteExportUtils._export_data: e.g., DataExporter.save_data_to_output(data, filename, api_function_name=api_call.__name__). This removes reliance on stack inspection and ensures correct strategy selection.

2. Enhance DataProcessingUtils.flatten_nested_fields to optionally limit list expansion (configurable max_list_items) and to provide a stable "list aggregation" mode (e.g., join or JSON-encode) to avoid schema explosion from variable-length lists. Default behavior should remain unchanged but make this configurable via global or optional parameter.

3. Add explicit retry/backoff around site-scoped API calls in SiteExportUtils._export_data (or ensure mistapi.get_all is configured to retry 429s). Add logging that notes retries and pages fetched.

4. Improve logging to record schema diffs between previous CSV/SQLite schema and current run (INFO log). Implement a lightweight schema fingerprint (sorted column list) stored in data/ as a small JSON to detect drift.

5. Add unit tests covering:
   - flatten_nested_fields with nested dicts, lists of dicts, stringified JSON, and edge cases
   - DatabaseSchemaUtils.get_endpoint_strategy for endpoints with and without explicit mapping
   - SQLiteDatabaseWriter behavior for natural_pk, composite_pk, and auto_increment_with_unique strategies (including INSERT OR REPLACE vs DELETE-and-INSERT modes)

6. Update documentation: add a short comment in SiteExportUtils._export_data explaining why api_function_name should be forwarded and how SQLite schema mapping works.

## Acceptance Criteria for fixes (testable)

- AC-1: Code change adds passing of api_function_name to DataExporter.save_data_to_output in all site-scoped export helpers. Unit test verifies that SQLiteDatabaseWriter receives the explicit api_function_name and DatabaseSchemaUtils chooses the expected strategy for listSiteBeacons.

- AC-2: Add a configuration option (or parameter) to flatten_nested_fields to control list expansion. Unit tests demonstrate that when max_list_items=0 (or mode="aggregate") the exporter uses JSON-encoded list fields rather than creating indexed columns.

- AC-3: Implement retry/backoff for site-scoped API calls, with unit/integration tests simulating 429 responses showing retries and eventual success or partial save on repeated failures.

- AC-4: Add logging of schema diffs to INFO level. Acceptance verified by running two controlled exports with incremental fields and confirming INFO log contains a concise list of new columns.

- AC-5: Add unit tests for SQLiteDatabaseWriter demonstrating correct upsert behavior for natural_pk and composite_pk strategies; coverage for these classes meets the target in SC-005.


## Implementation Notes (non-normative)

- Prefer explicit api_call.__name__ propagation to DataExporter to make strategy resolution deterministic.
- When changing flattening behavior, make the new behavior opt-in behind a parameter to avoid breaking existing users who depend on indexed list flattening.
- For large exports, consider streaming CSV writes rather than building full in-memory lists; APIDataFetcher already provides a model suitable for streaming in future work.




---

**Spec status**: SUCCESS (spec ready for planning)
