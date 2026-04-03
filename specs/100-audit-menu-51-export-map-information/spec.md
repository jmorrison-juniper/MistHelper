# Feature Specification: Audit - Export map information (Menu #51)

**Feature Branch**: `100-export-map-information`  
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "MistHelper Menu #51: \"Export map information\"\n\nFunction: SiteConfigExporter.maps\nCategory: data_export\nSQL export relevant: Yes\n\nThis is an AUDIT spec — analyze the existing implementation in MistHelper.py, document current state, identify issues, and define acceptance criteria for fixes.\n\nFocus on: how SiteConfigExporter.maps works, API call flow, data flattening, dual output (CSV/SQLite), primary key strategy, test coverage gaps, any issues found."

---

## Summary

This audit documents the current implementation of the "Export map information" feature (Menu #51), implemented by SiteConfigExporter.maps (delegates to SiteExportUtils / APIDataFetcher and DataExporter in MistHelper.py). The audit covers:

- API call flow used to fetch site maps (mistapi.api.v1.sites.maps.listSiteMaps)
- Data flattening and sanitization for nested map structures (geometry/coverage, zones, device placements)
- Dual output support (CSV and SQLite) and how the code selects the format
- SQLite primary-key / schema strategy and insert/upsert behavior for map rows
- Current test coverage and gaps
- Concrete issues found and acceptance criteria for fixes

Primary recommendation: add targeted unit/integration tests for the maps export pipeline, clarify handling of binary/image fields, and stabilize flattening and primary-key behavior for reliable CSV and SQLite exports.


## User Scenarios & Testing (mandatory)

### User Story 1 - Export site maps to CSV (Priority: P1)

Operators want to export map metadata for a selected site into a CSV file for documentation, inventory, and audit purposes.

Why this priority: Map metadata (map name, id, site, dimensions, zones, device coordinates) is essential for site audits and migration activities.

Independent Test:
- Invoke SiteConfigExporter.maps (or the SiteExportUtils/_export_data wrapper with api_call=mistapi.api.v1.sites.maps.listSiteMaps) for a site with representative maps.
- Verify a CSV file is created under data/ with header columns and rows representing maps and flattened nested fields.

Acceptance Scenarios:
1. Given a site with 2 maps containing nested coverage/geometry and device placement lists, when the user runs "Export map information", then a CSV file is written containing one row per map with flattened columns for stable top-level fields and deterministic columns for nested content.
2. Given no maps returned from the API, when the exporter runs, then a CSV is created per the configured empty-output policy (see Clarifications) and the user is notified.

---

### User Story 2 - Export site maps to SQLite (Priority: P2)

Operators want to persist map metadata into the local SQLite datastore to allow querying and historical snapshots.

Why this priority: Queryable map metadata enables downstream automation (search, joins with devices/zones) and historical comparisons.

Independent Test:
- Run the exporter with OUTPUT_FORMAT="sqlite" (or call write_with_format_selection with explicit override) and verify a database table (SiteMaps or sanitized name) exists with expected columns and rows.
- Verify primary-key behavior (upsert vs rebuild) per strategy.

Acceptance Scenarios:
1. Given maps returned from API and OUTPUT_FORMAT=sqlite, when the exporter runs, then a SQLite table named "SiteMaps" (or sanitized) exists and contains exported rows with a stable primary key strategy.
2. Given re-running the exporter with the same map IDs, when strategy indicates natural primary key, then rows are upserted (no duplicates) using INSERT OR REPLACE or equivalent.

---

### Edge Cases

- API returns a dict containing a "results" list instead of a list: exporter must normalize response shapes.
- Map objects contain nested arrays with inconsistent keys across rows; exported CSV should be readable and not crash.
- Map objects include image metadata or binary references: exporter should not attempt to embed binary data in CSV but may optionally store image metadata or image filenames in SQLite per configuration.
- Very large coverage/geometry JSON blobs must be sanitized/escaped for CSV and stored as text in SQLite.


## Requirements (mandatory)

### Functional Requirements

- FR-001: The exporter MUST call the Mist API endpoint for maps (mistapi.api.v1.sites.maps.listSiteMaps) with the correct site_id and handle pagination.
- FR-002: The exporter MUST handle response shapes: list of dicts, or dict containing a "results" list; if structure differs, attempt recovery and save recovered data.
- FR-003: The exporter MUST flatten nested dicts and lists consistently so CSV columns are stable for consumers. Non-dict lists MUST be converted to comma-separated strings. Lists-of-dicts MUST be flattened using a deterministic and bounded strategy.
- FR-004: The exporter MUST escape multiline strings for CSV compatibility (replace newlines with \n) and preserve content for SQLite.
- FR-005: The exporter MUST support two output formats: CSV (default) and SQLite (hybrid strategy). The format is chosen by OUTPUT_FORMAT or by an explicit override parameter.
- FR-006: When using SQLite output, the exporter MUST select table schema and primary-key strategy using DatabaseSchemaUtils.get_endpoint_strategy or explicit api_function_name and then create/verify table and indexes accordingly.
- FR-007: For endpoints with a natural primary key (e.g., 'id'), the SQLite writer MUST upsert rows (INSERT OR REPLACE); when no natural key is present, it MUST either use a composite natural key (site_id + id) or clear-and-insert using an auto-increment fallback.
- FR-008: The exporter MUST not embed binary image payloads into CSV/SQLite rows. It MAY include image metadata (url, filename, width, height) and optionally download images to a configurable images/ directory when explicitly requested.
- FR-009: The exporter MUST write emergency/partial saves when API rate-limit or exceptions occur so partial data is not lost.
- FR-010: The implementation SHOULD log debug information about API calls, recovered data, and write operations.

### Key Entities

- Entity: Map
  - Representative attributes: id, name, site_id, image_url, image_filename, width, height, coverage (JSON), zones (list/dict), device_positions (list of dicts), created_time, updated_time, any export metadata (site_name)
  - Behavior: Map objects must be flattenable; nested lists-of-dicts must be handled deterministically.

- Entity: Export Output
  - Two flavors: CSV file (data/SiteMaps.csv) or SQLite table (SiteMaps)
  - Metadata persisted for SQLite: misthelper_created_time, misthelper_updated_time


## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: Given a site with N maps, 100% of map objects returned by Mist API are persisted to the selected output (CSV or SQLite). Verified by a unit test that mocks API to return N known objects.
- SC-002: For CSV output, exporter produces a file with header row and N data rows in data/SiteMaps.CSV for N > 0.
- SC-003: For SQLite output and natural primary keys, re-running the exporter against the same dataset results in no duplicate rows (upsert behavior) verified via SELECT COUNT(*) and SELECT COUNT(DISTINCT primary_key).
- SC-004: Exporter does not embed binary images into CSV and only includes image metadata unless explicitly requested; optional image-download feature stores files under data/images/ and records filenames in SQLite.
- SC-005: Automated unit tests added for the exporter — see Test Coverage section.


## Current Implementation (observed in MistHelper.py)

- SiteConfigExporter.maps delegates to SiteExportUtils._export_data / APIDataFetcher with api_call=mistapi.api.v1.sites.maps.listSiteMaps and data_type="maps" (sort_key="name" in some callers).
- Multiple call sites call mistapi.api.v1.sites.maps.listSiteMaps(...) directly when building viewer state or refreshing maps; higher-level exporter calls DataExporter.write_with_format_selection(maps_data, filename, api_function_name="listSiteMaps").
- The common data pipeline observed elsewhere in MistHelper is used: APIDataFetcher -> DataProcessingUtils.flatten_nested_fields -> DataProcessingUtils.escape_multiline -> DataExporter.write_with_format_selection.
- DataProcessingUtils.flatten_nested_fields:
  - Attempts to parse stringified JSON/dict values with ast.literal_eval / json.loads when value starts with '{' or '[' (heuristic observed in other exporter code paths).
  - Flattens nested dicts by joining keys with '_' and flattens lists-of-dicts by indexed suffixes (e.g., devices_0_x, devices_0_y).
  - Non-dict lists are joined into comma-separated strings.
- DataExporter.write_with_format_selection is commonly invoked with api_function_name="listSiteMaps" for maps export paths (evidence: calls explicitly pass api_function_name in several places).
- SQLite writer (SQLiteDatabaseWriter) behavior across exporters:
  - Uses DataProcessingUtils.get_unique_keys to determine columns.
  - Uses DatabaseSchemaUtils.get_endpoint_strategy(api_function_name, fields) to determine primary-key strategy (natural_pk/composite_pk/auto_increment)
  - For natural/composite PK strategies, it performs upsert semantics (INSERT OR REPLACE). For auto-increment fallback it may clear or recreate table before insert.
  - Default behavior observed in other exporters is to coerce values to strings for SQLite insert.


## Issues Found (audit)

1. Empty-output behavior: exporter callers sometimes expect an empty CSV to be created for downstream automation, but DataExporter may skip writes when given empty lists, resulting in missing placeholder files and downstream failures.
   - Impact: Missing CSV files and inconsistent outputs across exporters.

2. Flattening strategy for lists-of-dicts can cause column explosion and inconsistent headers when different map rows contain different numbers of nested items (e.g., device_positions with variable length).
   - Impact: Very wide, sparse CSVs that are hard to consume programmatically.

3. Conservative parsing vs aggressive parsing: current heuristics that attempt ast.literal_eval/json.loads on strings starting with '{' or '[' risk mutating legitimate strings that begin with those characters.
   - Impact: Unexpected data transformations in exported fields like notes/comments.

4. Image handling ambiguity: maps include image references (URLs, base64, or binary). Current pipeline includes calls that create different map subsets (maps_with_images, maps_without_images) but there is no clear policy whether images should be stored, downloaded, or represented as metadata only.
   - Impact: Potential accidental attempts to serialize binary data into CSV/SQLite or unpredictable behavior when image fields are large.

5. SQLite typing and NULLs: the SQLite writer commonly coerces all values to strings and uses empty-string substitution for None. This loses type information and prevents storing NULL semantics for missing values.
   - Impact: Loss of fidelity for numeric/boolean/NULL fields; impedes meaningful SQL queries.

6. Test coverage gaps: there are no dedicated unit tests in the repository targeting SiteConfigExporter.maps and the maps export pipeline (no tests found referencing listSiteMaps or SiteConfigExporter.maps).
   - Impact: Regressions can go undetected and core fixes lack automated verification.


## Acceptance Criteria for Fixes

1. Empty-output behavior
   - AC-1.1: When callers call DataExporter.save_data_to_output([] , "SomeFile.csv"), a CSV file is created at data/SomeFile.csv containing a header row if fields are provided or a single informational header-only CSV when no fields can be derived. Unit tests must assert file creation.
   - AC-1.2: DataExporter.write_with_format_selection returns False for invalid inputs (non-list) but returns True and creates file for an empty list input.

2. Flattening / column stability
   - AC-2.1: Implement a deterministic list-of-dicts flattening strategy with a configurable max_items parameter (default e.g., 5) to bound columns. Document behavior in code comments.
   - AC-2.2: Add unit tests that validate flattening output for representative map objects including nested device_positions and zones; tests must assert consistent columns across rows.

3. Conservative parsing
   - AC-3.1: Update parsing heuristics to avoid automatic ast.literal_eval/json.loads unless the field is explicitly known to be stringified JSON or a config flag enables aggressive parsing. Add tests verifying plain strings starting with '{' remain unchanged.

4. Image handling policy
   - AC-4.1: Define and implement a clear policy: by default do NOT embed or download map images; include only metadata fields (image_url, image_filename, width, height) in CSV/SQLite. Add an explicit optional flag (e.g., --download-images) that when enabled downloads images into data/images/ and records filenames in the SQLite table.
   - AC-4.2: Add unit/integration tests demonstrating that default export does not include binary image data and that the optional download-images path correctly saves files and records filenames.

5. SQLite typing and NULLs
   - AC-5.1: Preserve Python None as SQL NULL in SQLite inserts (preferred) or, if a consistent string-only strategy is chosen, document it and implement tests. Add tests verifying numeric and boolean fields stored as appropriate SQLite types or documented string equivalents.

6. Tests: Add coverage for maps exporter pipeline
   - AC-6.1: Add unit tests that mock mistapi responses for: normal list of map dicts, dict-with-results, empty response, and rate-limited response -> partial save.
   - AC-6.2: Add tests for DataProcessingUtils.flatten_nested_fields and escape_multiline for map-specific fixtures (coverage JSON, device_positions).
   - AC-6.3: Add tests for DataExporter.write_with_format_selection exercising both CSV and SQLite (SQLite tests may use temp DB file).


## Test Plan (high level)

- Unit tests (fast):
  - flatten_nested_fields: fixtures for maps with coverage JSON, device_positions list-of-dicts, and strings starting with '{' to validate conservative parsing behavior.
  - escape_multiline: verify newline escapes and list->CSV conversion for fields like coverage JSON or zone descriptions.
  - DataExporter._write_csv_format: use tmpdir to assert CSV file created, header columns, and rows.
  - SQLiteDatabaseWriter: temp SQLite DB to validate table creation, PKs, indexes, upsert behavior, and NULL preservation.
  - APIDataFetcher / SiteExportUtils._export_data: mock mistapi.listSiteMaps to return varied shapes to validate normalization and partial saves.

- Integration test (slow):
  - Full pipeline test that calls SiteConfigExporter.maps (or SiteExportUtils._export_data) with a mocked apisession returning representative map objects and validates both CSV and SQLite outputs and optional image-download behavior.


## Assumptions

- Map objects returned by Mist API include an "id" field. When absent, exporter may use composite key (site_id + name) or auto-increment fallback.
- Default output format is CSV unless OUTPUT_FORMAT is set to "sqlite" or write_with_format_selection is called with format_override.
- Tests are allowed to create temporary files under test-only data directory or use in-memory SQLite DB for isolation.


## Files & Call Sites Reviewed

- MistHelper.py (SiteConfigExporter.maps, SiteExportUtils, DataProcessingUtils, DataExporter, DatabaseSchemaUtils, SQLiteDatabaseWriter)
- Existing exporter audit specs (menus #18, #52) for consistent patterns


## Recommendations (next steps)

1. Implement small fix to DataExporter._validate_write_inputs so that an explicit empty-list input results in a created empty CSV (or controlled empty SQLite table) rather than silently skipping writes. Add unit tests.
2. Implement deterministic flattening for lists-of-dicts with a configurable max_items to avoid column explosion. Add tests and document behavior.
3. Update parsing heuristics to be conservative by default and add tests to prevent mutation of plain strings beginning with '{' or '['.
4. Define and implement image handling policy (metadata-only by default, optional download). Update export UI/flags and add tests.
5. Preserve NULLs in SQLite or document and test the chosen conversion strategy.
6. Add unit and integration tests described in the Test Plan and include them in CI.

---

### Audit outcome

Status: SUCCESS — spec ready for planning and implementation of fixes. The spec includes concrete, testable acceptance criteria for each identified issue and a prioritized test plan.


Generated by: speckit.specify (audit)



Notes:
- [NEEDS CLARIFICATION: image handling policy - see Clarification Questions]
- [NEEDS CLARIFICATION: preferred SQLite primary-key strategy for maps (id vs composite site_id+id) - see Clarification Questions]
- [NEEDS CLARIFICATION: empty-output CSV policy (header-only vs informational row) - see Clarification Questions]
