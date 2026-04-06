# Spec

## Summary of current state
- Metadata: menu_id=119, description="Zone Configuration Analysis", function_ref=ZoneConfigurationAnalyzer.analyze
- Notes: "Needs PK/api_function_name verification, no tests"
- SQL export is relevant (sql_export_relevant=1)

## Purpose
Provide a menu operation that analyzes zone configurations (zones/policies) and exports results (CSV/SQLite). The analyzer is invoked via ZoneConfigurationAnalyzer.analyze and results must be persisted/exportable with correct primary-key semantics so SQL exports/upserts are reliable.

## Stakeholders
- NOC Engineers (primary users)
- Cloud/Platform engineers (integration)
- QA/Test engineers
- Documentation owner

## Acceptance criteria
1. Analyzer integration
   - The UI/menu operation invokes ZoneConfigurationAnalyzer.analyze (api_function_name must be verified and registered).
2. Export behavior
   - Dual-output supported: CSV and SQLite via existing DataExporter pattern (write_with_format_selection).
3. SQL upsert semantics
   - Data written to SQLite must use deterministic upsert behavior to avoid duplicates.
   - If natural_pk strategy chosen: tables support primary key(s) and use INSERT OR REPLACE (or equivalent) to upsert.
   - If composite_pk strategy chosen: composite UNIQUE constraint + INSERT OR REPLACE / upsert semantics applied.
   - Auto-increment_with_unique must be avoided for stable zone identity unless no stable key exists.
4. Schema and PK registration
   - An ENDPOINT_PRIMARY_KEY_STRATEGIES entry (or equivalent metadata) must be defined for this operation before implementation, including 'api_function_name' recorded for exporter telemetry.
5. Tests
   - Unit tests for analyzer logic
   - Integration tests that run the analyzer end-to-end and verify exported SQLite rows and upsert behavior

## Required API function name (SQL relevant)
- Required/expected: ZoneConfigurationAnalyzer.analyze
- Action: verify this symbol exists, confirm its exported path/signature, and ensure api_function_name recorded exactly as above in the metadata used by export routines.

## Recommended primary-key strategy and rationale
- Recommendation: natural_pk
  - Reason: Zone records (zones, zone-ids) are typically stable resources with API-provided IDs or stable unique names; using natural PKs (e.g., ['id'] or ['org_id','id'] or ['site_id','id'] depending on scope) allows safe INSERT OR REPLACE upserts and predictable deduplication.
- When to use composite_pk
  - If analyzer produces time-series or per-scan entries where the same zone may produce multiple records (timestamped), use composite_pk with keys like ['id','scan_timestamp'].
- Avoid auto_increment_with_unique unless the dataset is an aggregation/summary with no stable external key.

## Test plan outline
1. Unit tests
   - Analyzer input/output edge cases, null handling, flattening correctness.
   - Mock Mist API responses and validate analyzer transformations.
2. Integration tests
   - End-to-end call to ZoneConfigurationAnalyzer.analyze (can run with recorded fixtures) then DataExporter.write_with_format_selection to SQLite and CSV.
   - Validate resulting SQLite schema contains expected PKs and indexes.
3. SQL verification
   - Create initial SQLite export, re-run analyzer with updated/identical data, verify upsert semantics (no duplicate natural PKs; rows updated or replaced as expected).
   - Verify uniqueness constraints and upsert SQL used by exporter.
4. Regression and performance
   - Test with realistic dataset sizes to ensure exporter/SQL operations scale.

## Deliverables for implement phase (preparation)
- Verified api_function_name mapping
- Chosen PK strategy and explicit primary_key column list
- Spec files under specs/089-audit-menu-119-zone-analysis
- Test scaffolding and SQL schema drafts

