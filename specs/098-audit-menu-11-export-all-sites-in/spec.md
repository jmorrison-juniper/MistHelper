Feature: Audit - Menu #11 "Export all sites in the organization"

Short name: audit-export-sites

Created: 2026-04-03
Status: Draft

Input: Audit of OrgSiteExporter.sites implementation in MistHelper.py (menu #11)

## Summary (purpose)

This is an AUDIT specification for MistHelper menu #11 (OrgSiteExporter.sites). The goal is to analyze the current implementation in MistHelper.py, document the API call flow and data transforms, identify correctness and robustness issues (especially for dual CSV/SQLite output and primary-key/index strategy), and define concrete, testable acceptance criteria for fixes.

Scope: Focus is limited to OrgSiteExporter.sites and its dependent export flow (APIDataFetcher -> DataExporter -> SQLiteDatabaseWriter / CSV writer), data flattening, primary key/index selection for SQL exports, emergency/recovery save paths, and test coverage gaps. This is not a design for a new exporter — it is an audit and remediation spec.

## Current state (observed implementation)

- OrgSiteExporter.sites() implementation (in MistHelper.py) is a thin wrapper that:
  - Logs and emits progress for menu #11
  - Calls APIDataFetcher(..., api_call=mistapi.api.v1.orgs.sites.listOrgSites, filename="SiteList", sort_key="name", limit=1000).execute()
  - APIDataFetcher handles API call, pagination (via mistapi.get_all), error handling and finally calls DataExporter.export_with_processing(...) to write results.

- API call flow:
  - APIDataFetcher._call_api_with_retry invokes the provided API function (listOrgSites) with org_id and limit=1000 and retry/backoff on transient failures.
  - mistapi.get_all(response, mist_session=apisession) is used to collect paginated results into a list of site dicts.
  - The API function name passed through to downstream exporters is listOrgSites (APIDataFetcher passes api_function_name=self.api_call.__name__).

- Data processing & flattening:
  - APIDataFetcher.export_with_processing performs:
    - Keep only dict entries
    - Optional sort by sort_key (name)
    - DataProcessingUtils.flatten_nested_fields(processed_data)
    - DataProcessingUtils.escape_multiline(...) to replace newlines and join lists
  - DataExporter.write_with_format_selection receives processed data and the filename "SiteList" and selects output format based on global OUTPUT_FORMAT ("csv" or "sqlite").

- Dual output paths:
  - CSV path: DataExporter._write_csv_format writes to data/SiteList.csv; it determines all unique keys (after flattening) and writes a header and rows.
  - SQLite path: DataExporter._write_sqlite_format calls SQLiteDatabaseWriter(data, table_name, api_function_name).write()
    - SQLiteDatabaseWriter._process_data currently applies escape_multiline (but NOT flatten_nested_fields) before determining unique keys and schema strategy.
    - DatabaseSchemaUtils.get_endpoint_strategy(api_function_name, fields) attempts to select a strategy from ENDPOINT_PRIMARY_KEY_STRATEGIES (if configured) or enhance the default strategy (adds unique_constraints/indexes when "id" detected in fields).
    - DatabaseSchemaUtils.build_create_table_sql builds CREATE TABLE SQL according to strategy types: natural_pk, composite_pk, or auto_increment_with_unique (internal autoincrement pk + optional UNIQUE constraints).
    - Insert mode: for natural_pk/composite_pk, writer uses "INSERT OR REPLACE" (upsert). For auto_increment fallback, it deletes existing rows and inserts fresh rows.

- Error/emergency save paths:
  - APIDataFetcher has handlers for malformed responses and exceptions. In recovery or emergency save paths (_save_recovered_data, _handle_rate_limit, _emergency_save_and_raise, _save_partial_data_on_error), DataExporter.save_data_to_output(self.rawdata, self.filename, api_function_name=api_name) is invoked using the raw (unprocessed/unflattened) response list.
  - In normal path export, flattening is applied before save; in emergency/recovery paths flattening is not applied before calling DataExporter.save_data_to_output.

## Issues & Risks (findings)

1) Inconsistent processing between normal and emergency save paths
   - Normal export path flattens nested structures (flatten_nested_fields) before saving.
   - Emergency/recovered save paths pass raw API response objects to DataExporter.save_data_to_output without flattening.
   - Risk: SQLiteDatabaseWriter expects list[dict[str,Any]] with scalar values; if nested dicts/lists remain, the SQLite writer's field detection and INSERT logic can produce unexpected table columns (representing dict objects), or may fail when trying to insert non-primitive values. CSV emergency saves may produce cell values like "{'a':1}" which are harder to consume.

2) SQLite writer processing is not symmetric with CSV writer
   - SQLiteDatabaseWriter._process_data currently only calls escape_multiline, not flatten_nested_fields. This leads to different schemas between CSV and SQLite outputs for the same logical data set.
   - Risk: Table columns in SQLite may not match CSV headers; endpoint strategy detection (which relies on presence of "id") may fail if "id" is present inside nested structures rather than top-level keys.

3) Primary key / insert-mode choices can cause silent data loss
   - For auto_increment fallback strategy, _determine_insert_mode deletes all existing rows from the table before inserting new rows. If a more appropriate natural_pk strategy exists (e.g., 'id' present), delete behavior is undesirable.
   - Risk: If endpoint-specific strategy is not configured or not detected, the fallback will wipe and re-insert data causing gaps in historical tracking and making incremental upserts impossible.

4) ENDPOINT strategy mapping coverage and naming
   - The code relies on ENDPOINT_PRIMARY_KEY_STRATEGIES keyed by API function name (e.g., "listOrgSites"). If the mapping does not include the exact function name the default strategy is used. Naming mismatches (e.g., searchOrgSites vs listOrgSites) can cause incorrect strategy selection.
   - Risk: Mis-identified strategy leads to wrong primary key choice; for "SiteList" we expect a natural PK on 'id', but absence in the mapping could cause fallback.

5) Flattening behavior may create many sparse columns and ambiguous column names
   - DataProcessingUtils.flatten_nested_fields flattens nested dicts and lists by index. For complex site objects this generates many columns (e.g., contact_0_name, contact_1_name) and may produce inconsistent column order across runs.
   - Risk: CSV consumers may find columns unstable; SQLite schema proliferation can cause large, sparse tables and performance issues.

6) Missing explicit tests for critical behaviors
   - There are no explicit unit tests (observed) that validate: (a) listOrgSites CSV header includes id,name; (b) SQLite table SiteList uses 'id' as primary key and supports INSERT OR REPLACE upsert; (c) emergency save path yields flattened, consistent output; (d) rate-limit and partial save paths produce valid and queryable SQLite / CSV artifacts.

7) APIDataFetcher._save_recovered_data and emergency saving can leak unprocessed nested data into SQLite
   - When raw API response objects are given to SQLite writer, DatabaseSchemaUtils.get_endpoint_strategy obtains fields by DataProcessingUtils.get_unique_keys; nested dicts are not expanded and keys may be inconsistent.
   - Risk: Database schema generation could omit expected 'id' field if it's nested, or store Python dict/string representations in table columns.

8) Filename/table name conventions
   - OrgSiteExporter.sites calls APIDataFetcher with filename="SiteList" (no extension). DataExporter appends .csv when writing CSV but uses the given name as table name for SQLite. This is acceptable but should be documented.

## User scenarios & testing (P1..P3)

### User Story 1 - Export all sites (Priority: P1)

As an operator, I run menu #11 to export the full organization site list for downstream analysis.

Why: Core operational workflow — site inventories are a common export for audits and enrichments.

Independent test:
- Run OrgSiteExporter.sites() with OUTPUT_FORMAT=csv and verify data/SiteList.csv exists and contains one header row including id,name and one row per site.
- Run with OUTPUT_FORMAT=sqlite and verify database contains table "SiteList" (or sanitized equivalent) and that 'id' is present as a primary key or unique constraint.

Acceptance scenarios (testable):
1. Given an org with N sites, When running menu #11 with OUTPUT_FORMAT=csv, Then data/SiteList.csv exists and has N data rows and headers are flattened with no raw dict objects in cells.
2. Given OUTPUT_FORMAT=sqlite and a previously created SiteList table, When menu #11 runs, Then the table contains the latest N rows and rows for unchanged sites are upserted rather than duplicated if a natural PK strategy exists.

---

### User Story 2 - Partial/Rate-limited export (Priority: P2)

As an operator, I may hit API rate limits or transient errors; partial results must still be saved in a usable format.

Independent test:
- Simulate API raising rate-limit error mid-fetch and verify the partial artifact saved is flattened and consistent with normal output (CSV or SQLite as configured).

Acceptance scenarios:
1. Given partial results due to HTTP 429, When APIDataFetcher handles rate-limit, Then a partial SiteList artifact is saved and is loadable by consumers (CSV has header, SQLite table has columns and rows inserted for partial data).

---

### User Story 3 - Emergency malformed response recovery (Priority: P3)

If the API returns a malformed structure, the tool recovers available records and saves them in the same processed layout as successful exports.

Independent test:
- Provide a response shaped as {"data": [...]} and verify _attempt_data_recovery recovers the inner list and the saved artifact is flattened and matches a normal export.

Acceptance scenarios:
1. Given arbitrarily nested/malformed response, When recovery logic extracts records, Then saved artifact is in the canonical flattened format (not raw nested dict cells) and includes required fields (id,name).

---

### Edge cases

- Org has zero sites: exporter should create an empty CSV with header only or create an empty SQLite table schema and log a warning but not crash.
- Site objects include nested "address" dicts or lists of contacts: flattening should produce stable, documented column names (address_street/address_city or address_line_0).
- Very large orgs: pagination must complete and progress emitters should report counts. APIDataFetcher already uses mistapi.get_all with limit=1000 and internal rate-limiting.

## Functional requirements (testable)

- FR-001: OrgSiteExporter.sites MUST call the Mist API listOrgSites for the configured org_id and collect all pages using mistapi.get_all with limit=1000.
- FR-002: Normal export flow MUST produce flattened, CSV-safe records before writing (use DataProcessingUtils.flatten_nested_fields + escape_multiline).
- FR-003: CSV output MUST produce a deterministic header set containing unique flattened field names and one row per site (missing fields yield empty cells).
- FR-004: SQLite output MUST apply an endpoint-aware primary key strategy (prefer natural PK on site 'id') so subsequent runs use upsert (INSERT OR REPLACE) rather than destructive DELETE when a natural key exists.
- FR-005: Emergency/recovery and partial-save paths MUST save artifacts using the same processing pipeline as normal exports (flatten + escape) so CSV and SQLite artifacts are consistent in schema and type.
- FR-006: Database schema builder MUST create indexes for frequently queried fields (id, org_id, site_id, name) when present.
- FR-007: All exported artifacts MUST be human-loadable (CSV opens in common spreadsheet apps; SQLite schema is queryable with sqlite3).
- FR-008: Export code MUST log the API function name used and which primary key strategy was applied, and include a sample of the first 3 rows in debug logs.

## Acceptance criteria (explicit, verifiable)

AC-001 (CSV export correctness):
- GIVEN OUTPUT_FORMAT=csv and an org with at least 1 site
- WHEN running OrgSiteExporter.sites()
- THEN data/SiteList.csv exists
- AND the CSV header includes at least the columns: id, name
- AND no CSV cell contains a Python dict literal (e.g., "{'key': 'value'}") or raw JSON object — nested fields must be flattened or serialized as CSV-safe strings
- VERIFICATION: A test script reads data/SiteList.csv and asserts header contains 'id' and 'name' and that for first data row, none of the cell values match regex r"^\{.*\}$".

AC-002 (SQLite schema & upsert):
- GIVEN OUTPUT_FORMAT=sqlite and an org with sites
- WHEN running OrgSiteExporter.sites() twice with no API changes
- THEN the SQLite database (DATABASE_PATH) contains a table named SiteList (sanitized) with a primary key or unique constraint that includes 'id'
- AND the second run does not create duplicate records for the same site (i.e., upsert behavior is used)
- VERIFICATION: After run1 record_count == run2 record_count and for a sample site id, values are identical or updated (no duplicates).

AC-003 (Emergency/partial save consistency):
- GIVEN API failure during fetch and partial raw data available
- WHEN APIDataFetcher triggers partial/emergency save
- THEN saved artifact (CSV or SQLite depending on OUTPUT_FORMAT) is flattened and matches the exact column set and escaping rules as a normal successful export
- VERIFICATION: Simulate a partial response and assert DataProcessingUtils.flatten_nested_fields was applied before writing the artifact.

AC-004 (Strategy mapping):
- GIVEN the endpoint listOrgSites
- WHEN DatabaseSchemaUtils.get_endpoint_strategy("listOrgSites", fields) is called with fields including "id"
- THEN the returned strategy must prefer a natural or composite primary key including "id" (or at minimum include UNIQUE constraint on id and index on id)
- VERIFICATION: Unit test against the mapping and fallback strategy verifies "id" is in strategy['unique_constraints'] or strategy['primary_key'].

AC-005 (No destructive deletes for natural PK):
- GIVEN strategy resolves to a natural_pk/composite_pk
- WHEN writing to SQLite
- THEN the _determine_insert_mode() must choose an upsert mode (INSERT OR REPLACE) and must NOT execute an unconditional DELETE FROM <table>
- VERIFICATION: Unit test asserts that for strategy type natural_pk/composite_pk, _determine_insert_mode returns "INSERT OR REPLACE" and does not issue a DELETE.

AC-006 (Logging & telemetry):
- GIVEN a normal or failed export
- WHEN the exporter runs
- THEN logs contain: API function name (listOrgSites), number of records fetched, chosen database strategy, and a debug sample of first 3 rows
- VERIFICATION: Integration test parses logs for these messages after run.

## Key entities

- Site (id, name, address, street, city, state, zip_code, country, timezone, tags, contact list, created_time, updated_time)
- Export artifact (CSV file data/SiteList.csv or SQLite table SiteList in DATABASE_PATH)
- Endpoint function name: listOrgSites

## Test cases to add (unit / integration)

1. Unit: DataProcessingUtils.flatten_nested_fields
   - Input: site objects with nested address dict and list of contacts
   - Assert: output contains flattened keys (address_street, address_city) and contact_0_name etc.

2. Unit: DatabaseSchemaUtils.get_endpoint_strategy
   - Inputs: api_function_name="listOrgSites" and fields contains 'id'
   - Assert: returned strategy includes either natural_pk with primary_key ['id'] or unique_constraints includes 'id'

3. Unit: SQLiteDatabaseWriter.write (happy path)
   - Input: flattened site rows, table_name="SiteList", api_function_name="listOrgSites"
   - Assert: table created, primary key present, indexes created, rows inserted

4. Unit: SQLiteDatabaseWriter emergency handling
   - Input: raw nested dict rows simulated via APIDataFetcher._save_recovered_data
   - Assert: either writer flattens before insert (preferred) or raises a controlled error with useful message. Policy: prefer flattening.

5. Integration: APIDataFetcher + DataExporter end-to-end
   - Simulate mistapi.get_all returning a sample site list
   - Run APIDataFetcher(...).execute()
   - Assert CSV file content and SQLite schema meet AC-001 and AC-002

6. Integration: Partial/rate-limit save
   - Simulate raise of HTTP 429 mid-fetch and assert partial artifact is saved and valid (flattened & consistent)

## Recommendations (remediation summary)

1. Make emergency and partial save paths use the same processing pipeline as the normal path (i.e., call flatten_nested_fields + escape_multiline before DataExporter.write_with_format_selection). This can be done in APIDataFetcher._save_recovered_data/_emergency_save_and_raise/_save_partial_data_on_error.

2. Ensure SQLiteDatabaseWriter._process_data also calls DataProcessingUtils.flatten_nested_fields before determining fields and building schema. This guarantees schema parity between CSV and SQLite outputs.

3. Verify ENDPOINT_PRIMARY_KEY_STRATEGIES includes an explicit mapping for "listOrgSites" that selects 'natural_pk' with primary_key ["id"] or at minimum a unique_constraints ["id"] plus an index on 'id'. Add unit tests.

4. Avoid destructive DELETE for fallback strategy when a stable business key exists. Prefer upsert strategies. If fallback is truly required to be replace-all, document and limit its use.

5. Add unit and integration tests described in the Test cases section to cover normal, partial, and emergency save flows.

6. Document CSV column naming rules for flattened lists/dicts so downstream consumers can rely on stable column names.

## Assumptions

- listOrgSites returns per-site objects that include a top-level "id" and "name" fields in typical responses.
- OUTPUT_FORMAT global is reliably set to either "csv" or "sqlite" prior to invocation.
- Database file path (DATABASE_PATH) is writable when OUTPUT_FORMAT=sqlite.

## Risks remaining after fixes

- Complex nested site objects will still produce many sparse columns after flattening; consider a schema design for site details vs contacts in the future.
- If Mist API changes field names (e.g., id -> site_id) the endpoint mapping must be updated accordingly.

## Next steps (for planning)

- Implement remediation items 1-4 in sequence and create unit tests 1-5.
- Run integration tests against a sample org (or recorded API responses) to validate AC-001..AC-006.
- If changes to DB schema semantics are introduced, coordinate with downstream consumers that read the SQLite database.


SUCCESS: Spec ready for planning
