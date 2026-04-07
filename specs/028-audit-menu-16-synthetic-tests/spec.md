# Spec

## Summary of current state
- Metadata: menu_id=16, function_ref=GatewayTestExporter.synthetic_tests, spec_dir=`specs/028-audit-menu-16-synthetic-tests`.
- SQL status: SQL NON-COMPLIANT: no PK strategy declared, no `api_function_name` provided to exporter, and no tests exist.

## Purpose
Allow operators to export synthetic gateway test results in CSV and SQLite (dual output) for audit, trend analysis, and incident investigation.

## Stakeholders
- NOC engineers (primary users)
- Platform engineers (DB/export backend)
- QA/Test engineers
- Documentation/ops authors

## Acceptance criteria
1. Functional
   - GatewayTestExporter.synthetic_tests exposes the export operation and returns structured records amenable to CSV/SQLite export.
   - Exporting supports CSV and SQLite using existing DataExporter patterns.
2. SQL/DB
   - The endpoint is SQL-compliant: an entry exists in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (or equivalent) for this operation.
   - Required `api_function_name` metadata is supplied and used when calling DataExporter.write_with_format_selection (for provenance and schema generation).
   - Upsert behavior: for the recommended PK strategy (composite_pk), export into SQLite must perform an upsert (INSERT OR REPLACE) keyed by the composite PK so repeated runs don't create duplicates but update existing records.
3. Quality
   - Unit tests cover record flattening, PK derivation, and successful call-path into DataExporter (mocked).
   - Integration tests execute a full export into a temporary SQLite DB and assert table schema, indexes, and upsert semantics.
4. Documentation
   - Spec exists in `specs/028-audit-menu-16-synthetic-tests` and README updated with menu metadata.

## Required API function name (SQL relevant)
- Use function_ref value: GatewayTestExporter.synthetic_tests
- This string (or a stable mapping) must be provided to DataExporter as `api_function_name` when writing SQL-backed exports for traceability and schema mapping.

## Recommended primary-key strategy and rationale
- Recommendation: composite_pk
  - Suggested primary_key fields: ["gateway_id", "test_run_id", "timestamp"]
  - Reasoning: synthetic test results are time-series and may have multiple runs per gateway. A composite PK using gateway identifier + per-run identifier + timestamp prevents duplicates while preserving time granularity. It supports deterministic upserts (INSERT OR REPLACE). If the data contains a unique record-level UUID from the API, prefer natural_pk using that; otherwise composite_pk is the safe choice.

## SQL upsert behavior (detailed)
- For composite_pk: generate table with PRIMARY KEY on the composite columns and use `INSERT OR REPLACE` for upsert semantics.
- Indexes: add an index on `gateway_id` and optionally `timestamp` to support queries by gateway and time range.

## Test plan outline
1. Unit tests
   - Validate exporter function builds normalized records with required keys (gateway_id, test_run_id, timestamp, metrics...).
   - Mock DataExporter.write_with_format_selection and assert it is called with `api_function_name` and expected filename/format flags.
   - PK derivation unit tests to ensure consistent keys from sample API payloads.
2. Integration tests
   - Run GatewayTestExporter.synthetic_tests end-to-end to write to a temp SQLite DB and CSV files; verify table existence, schema, indexes, and data fidelity.
   - Verify upsert semantics: run export twice with controlled modified payload and assert table row count does not increase and values update.
3. Performance/edge tests
   - Export a large synthetic payload to ensure batching/rate-limiting works and the DB handles upserts within acceptable time bounds.

## Notes / Constraints
- Place spec artifacts in `specs/028-audit-menu-16-synthetic-tests` per metadata.
- Because there is no existing PK strategy or tests, the first implementation steps must add the endpoint PK configuration and tests before enabling automated production exports