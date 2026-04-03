# Feature Specification: Audit - Export zone information (Menu #52)

**Feature Branch**: `101-export-zone-information`  
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "MistHelper Menu #52: \"Export zone information\"\n\nFunction: SiteConfigExporter.zones\nCategory: data_export\nSQL export relevant: Yes\n\nThis is an AUDIT spec — analyze the existing implementation in MistHelper.py, document current state, identify issues, and define acceptance criteria for fixes. The spec should be saved to: specs/101-audit-menu-52-export-zone-information/spec.md\n\nFocus on: how SiteConfigExporter.zones works, API call flow, data flattening, dual output (CSV/SQLite), primary key strategy, test coverage gaps, any issues found."

---

## Summary

This audit documents the current implementation of the "Export zone information" feature (Menu #52), implemented by SiteConfigExporter.zones (delegates to SiteExportUtils and DataExporter in MistHelper.py). The audit covers:

- API call flow used to fetch zones
- Data flattening and sanitization
- Dual output support (CSV and SQLite) and how the code selects format
- SQLite primary-key / schema strategy and insert/upsert behavior
- Current test coverage and gaps
- Concrete issues found and acceptance criteria for fixes

Primary recommendation: add targeted unit/integration tests and fix a few mismatches between callers' expectations and DataExporter behavior (see Issues & Acceptance Criteria).


## User Scenarios & Testing (mandatory)

### User Story 1 - Export site zones to CSV (Priority: P1)

Operators want to export zone objects for a selected site into a CSV file so they can review and share site zoning configuration.

**Why this priority**: Basic export capability is core user value of Menu #52 and used by operators for configuration review and audits.

**Independent Test**:
- Invoke the menu action (or call SiteExportUtils._export_data with api_call=mistapi.api.v1.sites.zones.listSiteZones) for a site with known zones.
- Verify SiteZones.CSV (or specified filename) is created under data/ with expected header columns and rows representing zones.

**Acceptance Scenarios**:
1. Given a site with 3 zones and standard zone objects, when user runs "Export zone information", then a CSV file is written containing 3 rows and columns for top-level zone attributes and flattened nested fields (e.g., geometry entries flattened as expected).
2. Given no zones returned from the API, when user runs export, then a CSV file with a header and a single informational row or an empty CSV (as agreed) is created and the user is notified.

---

### User Story 2 - Export site zones to SQLite (Priority: P2)

Operators want to populate the local SQLite datastore with zone rows for faster querying and historical snapshots.

**Why this priority**: Important for workflows that expect queryable results (search, joins) rather than simple CSVs.

**Independent Test**:
- Run the exporter with OUTPUT_FORMAT="sqlite" (or pass format override) and verify a database table (SiteZones) exists in the configured DATABASE_PATH with expected columns and rows.
- Verify primary-key behavior (upsert vs rebuild) per strategy.

**Acceptance Scenarios**:
1. Given zones returned from API and OUTPUT_FORMAT=sqlite, when exporter runs, then a SQLite table named "SiteZones" (or sanitized table name) exists and contains the exported rows.
2. Given re-running the exporter with the same zone IDs, when strategy indicates natural primary key, then rows are upserted (no duplicates) using INSERT OR REPLACE.

---

### Edge Cases

- API returns unexpected structure (dict with results vs list): exporter should recover data and still save partial/whole results.
- Zone objects contain nested arrays of dicts with inconsistent keys across rows; exported CSV should be readable and safe (no crashes) and SQLite schema consistent.
- Long multiline fields (e.g., comments or geometry JSON) must be sanitized/escaped for CSV, and stored as text in SQLite.


## Requirements (mandatory)

### Functional Requirements

- FR-001: The exporter MUST call the Mist API endpoint for zones (mistapi.api.v1.sites.zones.listSiteZones) with the correct site_id and handle pagination.
- FR-002: The exporter MUST handle these response shapes: list of dicts, or dict containing a "results" list; if structure differs, attempt recovery and save recovered data.
- FR-003: The exporter MUST flatten nested dicts and lists consistently so CSV columns are stable for consumers. Arrays of non-dict values MUST be converted to comma-separated strings.
- FR-004: The exporter MUST escape multiline strings for CSV compatibility (replace newlines) and preserve content for SQLite.
- FR-005: The exporter MUST support two output formats: CSV (default) and SQLite (hybrid strategy). The format is chosen by the global OUTPUT_FORMAT or by an explicit override parameter.
- FR-006: When using SQLite output, the exporter MUST select table schema and primary-key strategy using DatabaseSchemaUtils.get_endpoint_strategy and then create/verify table and indexes accordingly.
- FR-007: For endpoints with a natural/explicit primary key (e.g., 'id'), the SQLite writer MUST use INSERT OR REPLACE to upsert rows; for auto-increment fallback the writer MUST clear table then insert.
- FR-008: The exporter MUST write emergency/partial saves when rate-limited or when API exceptions occur (so partial data is not lost).
- FR-009: The implementation SHOULD log detailed debug information about API calls, recovered data, and write operations.

### Key Entities

- Entity: Zone
  - Representative attributes: id, name, site_id, geometry (nested), created_time, updated_time, any site metadata added by export (site_name)
  - Behavior: Can be flattened; lists of nested dicts indexed (zone_rules_0_...), non-dict lists joined as CSV values

- Entity: Export Output
  - Two flavors: CSV file (data/SiteZones.csv) or SQLite table (SiteZones)
  - Metadata persisted for SQLite: misthelper_created_time, misthelper_updated_time


## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: Given a site with N zones, 100% of zone objects returned by Mist API are persisted to the selected output (CSV or SQLite). Verified by a test that mocks API to return N known objects.
- SC-002: For CSV output, exporter produces a file with header row and N data rows in data/SiteZones.CSV (or configured filename) for N > 0.
- SC-003: For SQLite output and natural primary keys, re-running the exporter against the same dataset results in no duplicate rows (upsert behavior) and verification via SELECT COUNT(*) and SELECT COUNT(DISTINCT primary_key).
- SC-004: Exporter recovers and saves data from malformed API responses at least once (emergency save) and logs the recovery event.
- SC-005: Automated unit tests added for the exporter (see Test Coverage section) — see Acceptance Criteria for a minimal passing test set.


## Current Implementation (observed in MistHelper.py)

- SiteConfigExporter.zones delegates to SiteExportUtils._export_data / APIDataFetcher with api_call=mistapi.api.v1.sites.zones.listSiteZones and data_type="zones" (sort_key="name").
- APIDataFetcher handles calling the Mist API with retry on timeout, rate-limit handling, and uses mistapi.get_all(...) to obtain paginated data.
- On retrieval, standard pipeline applies: DataProcessingUtils.flatten_nested_fields -> DataProcessingUtils.escape_multiline -> DataExporter.save_data_to_output(...).
- DataProcessingUtils.flatten_nested_fields:
  - Parses stringified JSON/dict values with ast.literal_eval / json.loads when value starts with '{' or '['
  - Flattens nested dicts using flatten_dict (keys joined with '_')
  - For lists of dicts, flattens each element adding an indexed suffix (e.g., key_0_field)
  - For non-dict lists, joins values with commas
- DataProcessingUtils.escape_multiline converts lists to comma-strings and replaces newlines in strings with "\\n" and strips CRs.
- DataExporter.save_data_to_output delegates to DataExporter.write_with_format_selection which selects CSV or SQLite depending on OUTPUT_FORMAT (global) or explicit override.
- CSV writer uses DataProcessingUtils.get_unique_keys to compute header columns and writes rows under data/ directory.
- SQLite writer uses SQLiteDatabaseWriter:
  - Determines fields via DataProcessingUtils.get_unique_keys
  - Determines strategy using DatabaseSchemaUtils.get_endpoint_strategy(api_function_name, fields)
  - DatabaseSchemaUtils maps endpoint names (ENDPOINT_PRIMARY_KEY_STRATEGIES) to schema strategies (natural_pk / composite_pk / auto_increment_with_unique).
  - If strategy.type is "natural_pk" or "composite_pk", SQLiteDatabaseWriter uses "INSERT OR REPLACE" (upsert); otherwise it deletes existing table rows and uses plain INSERT (auto-increment id column present).
  - Creates indexes based on strategy.indexes
  - Adds metadata columns misthelper_created_time and misthelper_updated_time


## Issues Found (audit)

1. Mismatch: callers expect empty CSV creation but DataExporter._validate_write_inputs returns False when data is empty
   - Evidence: multiple call sites call DataExporter.save_data_to_output([], filename) to create empty placeholder CSVs (e.g., in early exits). DataExporter._validate_write_inputs immediately returns False for empty data and prevents any file creation. This is a behavioral regression vs callers' expectations.
   - Impact: Empty CSV placeholders are not created; callers may rely on presence of these files. User-visible effect: missing CSV files and confusing warnings.

2. Flattening produces variable columns across rows for lists-of-dicts
   - Evidence: flatten_nested_fields flattens lists-of-dicts using indexed keys (key_0_field, key_1_field). For collections where elements might have varying keys or different length across rows, CSV header set (get_unique_keys) becomes union across rows; this can produce many sparse columns and inconsistent ordering for downstream consumers.
   - Impact: Harder to consume CSVs programmatically; potential column explosion and layout confusion.

3. String parsing heuristics may mutate intended string values
   - Evidence: flatten_nested_fields attempts ast.literal_eval / json.loads on strings starting with '{' or '['. If a legitimate string begins with these characters, it will be attempted parsed and possibly converted, changing the original content.
   - Impact: Risk of incorrect transformations of fields containing user text that starts with those characters.

4. SQLite primary-key strategy detection depends on call-stack heuristics
   - Evidence: DatabaseSchemaUtils.determine_api_function_name_from_context walks call stack looking for patterns to infer API function name if api_function_name not provided. This is fragile in refactors or when called from wrappers.
   - Impact: Wrong strategy chosen -> table schema or primary-key choice may be incorrect leading to duplicate rows or bad upserts.

5. SQLite writer coercion to strings loses typing and null vs empty-string distinctions
   - Evidence: SQLiteDatabaseWriter._prepare_row_values converts all values to str(value) or "" when None. This flattens True/False/numeric semantics and removes ability to distinguish NULL vs empty string.
   - Impact: Downstream queries expecting typed fields may be suboptimal; inability to store NULL explicitly.

6. Missing unit/integration tests for SiteConfigExporter.zones and the write pipeline
   - Evidence: repository appears to contain no dedicated tests for this exporter path. (No tests found referencing listSiteZones or SiteConfigExporter.zones.)
   - Impact: Regressions (e.g., issue #1) can pass unnoticed until runtime.


## Acceptance Criteria for Fixes

For each issue above, acceptance criteria that are testable and verifiable:

1. Fix: Empty-output behavior (create empty CSVs when callers expect them)
   - AC-1.1: When callers call DataExporter.save_data_to_output([] , "SomeFile.csv"), a CSV file is created at data/SomeFile.csv containing header row only (derived from fields if provided) or a single informational row if no fields available. Unit tests must assert the file exists after call.
   - AC-1.2: DataExporter.write_with_format_selection still returns False when input is invalid (non-list) but returns True and creates file when input is an empty list.

2. Fix: Flattening / column stability
   - AC-2.1: Add a deterministic strategy for list-of-dicts flattening where a stable prefix is used and a configurable limit (e.g., max indexed items) to avoid column explosion. Document behavior in code comments.
   - AC-2.2: Add unit tests that validate flattening output for representative zone objects including nested dicts and lists-of-dicts. Tests must assert consistent columns across rows from same endpoint.

3. Fix: Conservative string parsing
   - AC-3.1: Modify parsing heuristics: only attempt JSON/AST parsing when the field is explicitly typed as stringified JSON from API (or when a heuristic config flag is enabled). Default behavior must not mutate plain strings starting with '{' or '['.
   - AC-3.2: Add unit tests demonstrating that a literal string starting with '{' (not JSON) remains unchanged.

4. Fix: Make API function / strategy explicit or more robust
   - AC-4.1: Ensure callers (SiteExportUtils._export_data / APIDataFetcher) pass the API function name (api_call.__name__) explicitly into DataExporter.save_data_to_output / SQLiteDatabaseWriter so strategy selection does not rely on call stack inspection. Unit tests should assert DatabaseSchemaUtils.get_endpoint_strategy selects the expected strategy for the "listSiteZones" endpoint.
   - AC-4.2: Add integration test that writes to SQLite for a known zone dataset and verifies primary-key fields derived from strategy match expected natural key (id) and that subsequent runs perform upserts.

5. Fix: Preserve NULLs and types or document conversion
   - AC-5.1: Decide and document a consistent mapping: either preserve Python None as SQL NULL (preferred) or consistently encode as empty string. Implement and add tests to verify behavior for numeric and boolean fields.

6. Tests: Add coverage for the exporter pipeline
   - AC-6.1: Add unit tests that mock mistapi responses for these cases: normal list of zone dicts, dict with results key, empty response, rate-limited response -> partial save.
   - AC-6.2: Add tests for DataProcessingUtils.flatten_nested_fields showing expected flattened output for typical zone objects (geometry, rules list, metadata).
   - AC-6.3: Add tests for DataExporter.write_with_format_selection that exercise both CSV and SQLite paths (SQLite test can use a temporary DATABASE_PATH in test env).


## Test Plan (high level)

- Unit tests (fast):
  - flatten_nested_fields: multiple fixtures (nested dict, list-of-dicts, stringified-json, strings starting with '{')
  - escape_multiline: verify newline escapes and list->CSV conversion
  - DataExporter._write_csv_format: use temp directory to assert CSV created, header columns, and rows
  - SQLiteDatabaseWriter: small in-memory SQLite DB or temp file to validate table creation, PKs, indexes, and insert/upsert behavior
  - APIDataFetcher: mock mistapi responses to simulate list response, dict-with-results, timeout/429, and validate saved outputs and logs

- Integration test (slow):
  - Full pipeline test that calls SiteExportUtils._export_data(api_call=listSiteZones) with a mocked apisession that returns representative zone objects and validates both CSV and SQLite outputs.


## Assumptions

- Zone objects returned by Mist API include an "id" field (typical). When absent, exporter will fall back to auto-increment strategy.
- Default output format is CSV unless OUTPUT_FORMAT is set to "sqlite" or write_with_format_selection is called with format_override.
- Tests will be allowed to create temporary files under a test-only data directory or use an in-memory SQLite DB for isolation.


## Files & Call Sites Reviewed

- MistHelper.py (site export utilities, DataProcessingUtils, DataExporter, DatabaseSchemaUtils, SQLiteDatabaseWriter)
- maps_manager.py (standalone map manager - contains additional uses of listSiteZones for map-related flows)


## Recommendations (next steps)

1. Implement small fix to DataExporter._validate_write_inputs so that an explicit empty-list input results in a created empty CSV (or controlled empty SQLite table) rather than skipping writes. Add unit tests.
2. Make api_function_name explicit when calling save_data_to_output so DatabaseSchemaUtils does not need call-stack heuristics. Update callers in APIDataFetcher and SiteExportUtils._export_data.
3. Harden flattening heuristics per Acceptance Criteria #2 and #3. Add tests to prevent regressions.
4. Add unit and integration tests described in Test Plan and include them in CI.
5. Consider changing SQLiteDatabaseWriter to preserve NULL/typed values where appropriate.


---

### Audit outcome

Status: SUCCESS — spec ready for planning and implementation of fixes. The spec includes concrete, testable acceptance criteria for each identified issue and a prioritized test plan.


Generated by: speckit.specify (audit)


